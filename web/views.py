from pathlib import Path
from datetime import timedelta
import logging
import json
import csv
from datetime import datetime
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Max
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.decorators.cache import cache_page
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import connection
from django_ratelimit.decorators import ratelimit

from .models import Medicion
from .utils import extract_exif_metadata, compress_and_resize_image

logger = logging.getLogger(__name__)


def health_check(request):
	"""Health check endpoint para monitoring y load balancers"""
	try:
		# Verificar conexión a la base de datos
		with connection.cursor() as cursor:
			cursor.execute("SELECT 1")
		
		# Verificar que Redis esté disponible (si está configurado)
		cache_status = 'not_configured'
		try:
			from django.core.cache import cache
			cache.set('health_check', 'ok', 10)
			if cache.get('health_check') == 'ok':
				cache_status = 'connected'
			else:
				cache_status = 'error'
		except Exception:
			cache_status = 'unavailable'
		
		return JsonResponse({
			'status': 'healthy',
			'database': 'connected',
			'cache': cache_status,
			'timestamp': timezone.now().isoformat()
		})
	except Exception as e:
		logger.exception("Health check failed")
		return JsonResponse({
			'status': 'unhealthy',
			'error': str(e),
			'timestamp': timezone.now().isoformat()
		}, status=503)


@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
	"""Vista de login con autenticación Django"""
	if request.user.is_authenticated:
		return redirect('dashboard')
	
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			# Limpiar caché del usuario al hacer login
			from django.core.cache import cache
			cache.delete(f'dashboard_mediciones_{user.id}')
			return redirect('dashboard')
		else:
			messages.error(request, 'Usuario o contraseña incorrectos')
	
	return render(request, "web/login.html")


def logout_view(request):
	"""Vista para cerrar sesión"""
	# Limpiar caché del usuario al cerrar sesión
	from django.core.cache import cache
	cache.delete(f'dashboard_mediciones_{request.user.id}')
	logout(request)
	messages.success(request, 'Sesión cerrada correctamente')
	return redirect('login')


@login_required
def dashboard(request):
	"""Dashboard del operario con sus últimas mediciones"""
	if request.user.is_staff:
		# Si es staff, mostrar últimas mediciones de todas las empresas
		mediciones = Medicion.objects.select_related('user').all().order_by('-timestamp')[:10]
	else:
		# Si es operario, mostrar solo sus mediciones
		mediciones = Medicion.objects.filter(user=request.user).order_by('-timestamp')[:5]
	
	context = {
		'mediciones': mediciones,
	}
	return render(request, "web/dashboard.html", context)


@login_required
@login_required
@ratelimit(key='user_or_ip', rate='10/m', block=True)
def cargar_medicion(request):
	"""Vista para cargar nueva medición con manejo robusto de errores y rate limiting"""
	if request.method == 'POST':
		temp_storage = None
		temp_name = None
		temp_full_path = None
		try:
			# ===== RATE LIMITING: Check if user submitted a measurement less than 30 seconds ago =====
			last_medicion = Medicion.objects.filter(user=request.user).order_by('-timestamp').first()
			
			if last_medicion:
				time_since_last = timezone.now() - last_medicion.timestamp
				if time_since_last < timedelta(seconds=30):
					messages.warning(request, 'Espere unos segundos antes de enviar otra medición')
					return redirect('dashboard')

			# Obtener datos del formulario
			valor_caudalimetro = request.POST.get('valor_caudalimetro')
			foto_evidencia = request.FILES.get('foto_evidencia')
			observaciones = request.POST.get('observaciones', '')
			
			# Validar que el valor no esté vacío
			if not valor_caudalimetro:
				messages.error(request, 'El valor del caudalímetro es obligatorio')
				return redirect('cargar')
			
			# Obtener ubicación de la empresa del usuario
			try:
				from .models import EmpresaPerfil
				empresa_perfil = EmpresaPerfil.objects.get(usuario=request.user)
				ubicacion_manual = empresa_perfil.ubicacion or f"Ubicación de {request.user.username}"
			except EmpresaPerfil.DoesNotExist:
				# Si no tiene empresa perfil, usar el nombre de usuario
				ubicacion_manual = f"Ubicación de {request.user.username}"
			
			# Flujo robusto: guardar archivo temporal y confirmar tras commit
			temp_storage = FileSystemStorage(location=str(Path(settings.MEDIA_ROOT) / "tmp_uploads"))

			if foto_evidencia:
				temp_name = temp_storage.save(
					f"tmp_{request.user.id}_{uuid.uuid4().hex}_{foto_evidencia.name}",
					foto_evidencia
				)
				temp_full_path = temp_storage.path(temp_name)

			with transaction.atomic():
				# Crear medición sin foto (se adjunta tras commit)
				medicion = Medicion(
					user=request.user,
					value=valor_caudalimetro,
					ubicacion_manual=ubicacion_manual,
					photo=None,
					observation=observaciones,
				)
				medicion.save()

				if temp_full_path:
					def finalize_photo_upload():
						try:
							# Extraer EXIF antes de comprimir
							with open(temp_full_path, "rb") as f:
								metadata = extract_exif_metadata(f)

							# Comprimir y optimizar
							with open(temp_full_path, "rb") as f:
								compressed_buffer = compress_and_resize_image(
									f,
									max_size=1280,
									quality=70
								)

							# Si falla compresión, usar original
							if not compressed_buffer:
								with open(temp_full_path, "rb") as f:
									compressed_buffer = ContentFile(f.read())
							else:
								compressed_buffer = ContentFile(compressed_buffer.getvalue())

							# Guardar foto optimizada sin reprocesar en save()
							medicion._skip_image_processing = True
							medicion.photo.save(
								foto_evidencia.name,
								compressed_buffer,
								save=False
							)

							# Guardar coordenadas y timestamp EXIF si existen
							if metadata.get('latitude') is not None:
								medicion.captured_latitude = metadata['latitude']
							if metadata.get('longitude') is not None:
								medicion.captured_longitude = metadata['longitude']
							if metadata.get('timestamp') is not None:
								medicion.captured_at = metadata['timestamp']

							medicion.save(update_fields=[
								"photo",
								"captured_latitude",
								"captured_longitude",
								"captured_at"
							])
						except Exception:
							logger.exception("Error finalizando carga de foto", extra={"user_id": request.user.id})
							# Si falla el guardado del archivo, eliminar el registro
							medicion.delete()
						finally:
							# Limpiar archivo temporal
							try:
								if temp_name and temp_storage.exists(temp_name):
									temp_storage.delete(temp_name)
							except Exception:
								pass

					transaction.on_commit(finalize_photo_upload)
			
			messages.success(request, 'Medición guardada exitosamente')
			return redirect('dashboard')
		
		except ValueError as e:
			logger.warning("Error de validación en cargar_medicion", extra={"error": str(e), "user_id": request.user.id})
			messages.error(request, f'Error en los datos: {str(e)}')
			return redirect('cargar')
		except Exception as e:
			logger.exception("Error al guardar medición", extra={"user_id": request.user.id})
			# Limpiar archivo temporal si algo falla antes del commit
			try:
				if temp_storage and temp_name and temp_storage.exists(temp_name):
					temp_storage.delete(temp_name)
			except Exception:
				pass
			from django.core.exceptions import ValidationError
			if isinstance(e, ValidationError):
				# Mostrar cada error de validación
				for field, error_list in e.error_dict.items():
					for error in error_list:
						messages.error(request, f'{field}: {error.message}')
			else:
				messages.error(request, 'Error al guardar la medición. Por favor, intenta nuevamente.')
			return redirect('cargar')
	
	return render(request, "web/formulario.html")


def service_worker(request):
	sw_file = Path(settings.BASE_DIR) / "static" / "sw.js"
	if not sw_file.exists():
		return HttpResponseNotFound("Service worker not found")
	return FileResponse(open(sw_file, "rb"), content_type="application/javascript")


@login_required
def get_weekly_route_data(request):
	"""
	API endpoint que retorna GeoJSON con las mediciones de la semana actual.
	Parámetros opcionales: start_date, end_date (formato YYYY-MM-DD)
	"""
	from django.http import JsonResponse
	
	# Obtener rango de fechas (default: semana actual)
	today = timezone.now().date()
	week_start = today - timedelta(days=today.weekday())  # Lunes
	week_end = week_start + timedelta(days=6)  # Domingo
	
	# Parámetros opcionales
	start_date_param = request.GET.get('start_date')
	end_date_param = request.GET.get('end_date')
	
	if start_date_param:
		try:
			week_start = datetime.strptime(start_date_param, '%Y-%m-%d').date()
		except ValueError:
			pass
	
	if end_date_param:
		try:
			week_end = datetime.strptime(end_date_param, '%Y-%m-%d').date()
		except ValueError:
			pass
	
	# Determinar si el usuario actual es staff o regular
	if request.user.is_staff:
		# Staff ve todas las mediciones de la semana
		mediciones = Medicion.objects.filter(
			timestamp__date__gte=week_start,
			timestamp__date__lte=week_end,
			captured_latitude__isnull=False,
			captured_longitude__isnull=False
		).exclude(
			captured_latitude=0,
			captured_longitude=0
		).select_related('user').only(
			'id', 'captured_latitude', 'captured_longitude',
			'ubicacion_manual', 'value', 'timestamp', 'user__username'
		).order_by('-timestamp')
	else:
		# Usuario regular solo ve sus propias mediciones
		mediciones = Medicion.objects.filter(
			user=request.user,
			timestamp__date__gte=week_start,
			timestamp__date__lte=week_end,
			captured_latitude__isnull=False,
			captured_longitude__isnull=False
		).exclude(
			captured_latitude=0,
			captured_longitude=0
		).only(
			'id', 'captured_latitude', 'captured_longitude',
			'ubicacion_manual', 'value', 'timestamp'
		).order_by('-timestamp')
	
	# Construir GeoJSON FeatureCollection
	features = []
	for medicion in mediciones:
		feature = {
			"type": "Feature",
			"geometry": {
				"type": "Point",
				"coordinates": [medicion.captured_longitude, medicion.captured_latitude]
			},
			"properties": {
				"id": medicion.id,
				"popup_title": medicion.timestamp.strftime('%d/%m %H:%M') + "hs",
				"operator_name": medicion.user.username,
				"value": str(medicion.value),
				"ubicacion": medicion.ubicacion_manual or "Sin ubicación",
				"detail_url": f"/gestion/empresas/{medicion.user.id}/mediciones/",
				"is_valid": medicion.is_valid
			}
		}
		features.append(feature)
	
	# GeoJSON FeatureCollection
	geojson_data = {
		"type": "FeatureCollection",
		"features": features,
		"properties": {
			"week_start": week_start.isoformat(),
			"week_end": week_end.isoformat(),
			"count": len(features)
		}
	}
	
	return JsonResponse(geojson_data)


@login_required
@login_required
@cache_page(60)
def weekly_route(request):
	"""Vista que renderiza el mapa semanal"""
	return render(request, "web/weekly_route.html")


@login_required
def api_docs(request):
	"""Vista simple de documentación de endpoints"""
	return render(request, "web/api_docs.html")


# Staff Command Center
class StaffCheckMixin(UserPassesTestMixin):
	"""Mixin para verificar que el usuario sea staff"""
	def test_func(self):
		return self.request.user.is_staff


# Admin Panel Views (Custom)
@login_required
def admin_usuarios_view(request):
	"""Vista para gestionar usuarios"""
	if not request.user.is_staff:
		messages.error(request, 'No tienes permisos para acceder a esta sección')
		return redirect('dashboard')
	
	usuarios = User.objects.annotate(
		latest_measurement=Max('mediciones__timestamp')
	).order_by('-latest_measurement')
	
	return render(request, 'web/admin_usuarios.html', {'usuarios': usuarios})


@login_required
def admin_crear_usuario_view(request):
	"""Crear nuevo usuario (solo superusuario)"""
	if not request.user.is_superuser:
		return redirect('dashboard')
	
	if request.method == 'POST':
		username = request.POST.get('username')
		email = request.POST.get('email')
		password = request.POST.get('password')
		tipo = request.POST.get('tipo')
		
		if User.objects.filter(username=username).exists():
			messages.error(request, f'El usuario {username} ya existe')
			return redirect('admin_usuarios')
		
		user = User.objects.create_user(
			username=username,
			email=email,
			password=password,
			is_staff=(tipo == 'staff')
		)
		messages.success(request, f'Usuario {username} creado exitosamente')
		return redirect('admin_usuarios')
	
	return redirect('admin_usuarios')


@login_required
def admin_editar_usuario_view(request, user_id):
	"""Editar usuario existente (solo superusuario)"""
	if not request.user.is_superuser:
		return redirect('dashboard')
	
	usuario = get_object_or_404(User, id=user_id)
	
	if request.method == 'POST':
		new_username = request.POST.get('username')
		# Verificar que el username no exista (excepto si es el mismo)
		if User.objects.filter(username=new_username).exclude(id=usuario.id).exists():
			messages.error(request, f'El usuario {new_username} ya existe')
			return render(request, 'web/admin_editar_usuario.html', {'usuario': usuario})
		
		usuario.username = new_username
		usuario.email = request.POST.get('email')
		password = request.POST.get('password')
		
		if password:
			usuario.set_password(password)
		
		usuario.save()
		
		messages.success(request, f'Usuario {usuario.username} actualizado')
		return redirect('admin_usuarios')
	
	return render(request, 'web/admin_editar_usuario.html', {'usuario': usuario})


@login_required
def admin_eliminar_usuario_view(request, user_id):
	"""Eliminar usuario (solo superusuario)"""
	if not request.user.is_superuser:
		return redirect('dashboard')
	
	if request.method == 'POST':
		usuario = get_object_or_404(User, id=user_id)
		if not usuario.is_superuser:
			username = usuario.username
			usuario.delete()
			messages.success(request, f'Usuario {username} eliminado')
		else:
			messages.error(request, 'No se puede eliminar un superusuario')
	
	return redirect('admin_usuarios')


@login_required
def admin_empresas_view(request):
	"""Lista de empresas con sus estadísticas"""
	if not request.user.is_staff:
		return redirect('dashboard')
	
	from django.db.models import Count
	empresas = User.objects.filter(
		is_staff=False, 
		is_superuser=False
	).select_related('empresa_perfil').prefetch_related('mediciones').annotate(
		total_mediciones=Count('mediciones'),
		latest_measurement=Max('mediciones__timestamp')
	).order_by('-latest_measurement')
	
	return render(request, 'web/admin_empresas.html', {'empresas': empresas})


@login_required
def admin_empresa_legajo_view(request, user_id):
	"""Legajo completo de una empresa con todas sus mediciones y gráfico personalizado"""
	if not request.user.is_staff:
		return redirect('dashboard')
	
	from django.db.models import Count, Avg, Min, Max
	empresa = get_object_or_404(User.objects.select_related('empresa_perfil'), id=user_id, is_staff=False)
	
	# Usar queryset base para evitar duplicación
	mediciones_qs = Medicion.objects.filter(user=empresa)
	
	# Estadísticas avanzadas (una sola query)
	stats = mediciones_qs.aggregate(
		total=Count('id'),
		validadas=Count('id', filter=models.Q(is_valid=True)),
		pendientes=Count('id', filter=models.Q(is_valid=False)),
		promedio=Avg('value'),
		minimo=Min('value'),
		maximo=Max('value'),
		primera_medicion=Min('timestamp'),
		ultima_medicion=Max('timestamp')
	)
	
	# Calcular porcentaje de validación
	if stats['total'] > 0:
		stats['porcentaje_validadas'] = round((stats['validadas'] / stats['total']) * 100)
		stats['umbral_pendientes'] = round(stats['total'] * 0.2)  # 20% del total
	else:
		stats['porcentaje_validadas'] = 0
		stats['umbral_pendientes'] = 0
	
	# Preparar datos para Chart.js - Últimas 20 mediciones (solo campos necesarios)
	chart_mediciones = mediciones_qs.only('timestamp', 'value').order_by('timestamp')[:20]
	chart_labels = [med.timestamp.strftime('%d/%m %H:%M') for med in chart_mediciones]
	chart_data = [float(med.value) for med in chart_mediciones]
	
	# Mediciones para la tabla (lazy load)
	mediciones = mediciones_qs.order_by('-timestamp')
	
	context = {
		'empresa': empresa,
		'mediciones': mediciones,
		'stats': stats,
		'chart_labels': json.dumps(chart_labels),
		'chart_data': json.dumps(chart_data),
		'has_chart_data': len(chart_data) > 0,
	}
	return render(request, 'web/admin_empresa_legajo.html', context)


@login_required
def admin_mediciones_empresa_view(request, user_id):
	"""Ver mediciones de una empresa específica"""
	if not request.user.is_staff:
		return redirect('dashboard')
	
	empresa = get_object_or_404(User.objects.select_related('empresa_perfil'), id=user_id, is_staff=False)
	mediciones = Medicion.objects.filter(user=empresa).select_related('user').order_by('-timestamp')
	
	return render(request, 'web/admin_mediciones_empresa.html', {
		'mediciones': mediciones,
		'empresa': empresa
	})


@login_required
def admin_validar_medicion_view(request, medicion_id):
	"""Validar una medición"""
	if not request.user.is_staff:
		return redirect('dashboard')
	
	if request.method == 'POST':
		medicion = get_object_or_404(Medicion, id=medicion_id)
		medicion.is_valid = True
		medicion.save()
		messages.success(request, 'Medición validada correctamente')
		return redirect('admin_mediciones_empresa', user_id=medicion.user.id)
	
	return redirect('admin_empresas')


@login_required
def admin_eliminar_medicion_view(request, medicion_id):
	"""Eliminar una medición"""
	if not request.user.is_staff:
		return redirect('dashboard')
	
	if request.method == 'POST':
		medicion = get_object_or_404(Medicion, id=medicion_id)
		user_id = medicion.user.id
		medicion.delete()
		messages.success(request, 'Medición eliminada')
		return redirect('admin_mediciones_empresa', user_id=user_id)
	
	return redirect('admin_empresas')


@login_required
def admin_editar_perfil_empresa_view(request, user_id):
	"""Editar perfil de empresa (username, email, ubicación y descripción) - solo superusuario"""
	if not request.user.is_superuser:
		return redirect('dashboard')
	
	empresa = get_object_or_404(User, id=user_id, is_staff=False)
	
	# Obtener o crear el perfil
	perfil, created = empresa.empresa_perfil, None
	try:
		perfil = empresa.empresa_perfil
	except:
		from .models import EmpresaPerfil
		perfil = EmpresaPerfil.objects.create(usuario=empresa)
	
	if request.method == 'POST':
		# Actualizar datos de usuario
		new_username = request.POST.get('username', '').strip()
		new_email = request.POST.get('email', '').strip()
		
		# Validar username único (si se está cambiando)
		if new_username and new_username != empresa.username:
			if User.objects.filter(username=new_username).exists():
				messages.error(request, 'El nombre de usuario ya está en uso')
				return redirect('admin_editar_perfil_empresa', user_id=empresa.id)
			empresa.username = new_username
		
		# Actualizar email
		empresa.email = new_email
		empresa.save()
		
		# Actualizar perfil
		perfil.descripcion = request.POST.get('descripcion', '')
		
		# Procesar coordenadas GPS
		latitude_str = request.POST.get('latitude', '').strip()
		longitude_str = request.POST.get('longitude', '').strip()
		
		if latitude_str and longitude_str:
			try:
				perfil.latitude = float(latitude_str)
				perfil.longitude = float(longitude_str)
				perfil.save()
				
				# Geocodificación inversa automática
				location_name = perfil.update_location_from_coordinates()
				if location_name:
					messages.success(request, f'Coordenadas actualizadas. Ubicación: {location_name}')
				else:
					messages.warning(request, 'Coordenadas guardadas pero no se pudo obtener el nombre de ubicación')
			except ValueError:
				messages.error(request, 'Coordenadas inválidas. Usa formato decimal (ej: -35.4695, -69.5797)')
		else:
			# Si no hay coordenadas, permitir ubicación manual
			perfil.ubicacion = request.POST.get('ubicacion', '')
		
		# Actualizar ícono
		icono_file = request.FILES.get('icono')
		if icono_file:
			perfil.icono = icono_file
		
		perfil.save()
		
		messages.success(request, f'Información de {empresa.username} actualizada correctamente')
		return redirect('admin_empresa_legajo', user_id=empresa.id)
	
	context = {
		'empresa': empresa,
		'perfil': perfil,
	}
	return render(request, 'web/admin_editar_perfil_empresa.html', context)


@login_required
def exportar_csv(request):
	"""Exportar historial de mediciones como CSV"""
	try:
		# Determinar qué mediciones exportar según permisos
		if request.user.is_staff:
			# Si es staff, verificar si se pasó user_id para exportar mediciones específicas
			user_id = request.GET.get('user_id')
			if user_id:
				# Exportar mediciones de un usuario específico
				try:
					usuario = User.objects.get(id=user_id)
					mediciones = Medicion.objects.filter(user=usuario).order_by('-timestamp')
					filename_suffix = f"_{usuario.username}"
				except User.DoesNotExist:
					messages.error(request, 'Usuario no encontrado')
					return redirect('dashboard')
			else:
				# Exportar todas las mediciones del sistema
				mediciones = Medicion.objects.all().order_by('-timestamp')
				filename_suffix = "_sistema_completo"
		else:
			# Usuario regular: exportar solo sus mediciones
			mediciones = Medicion.objects.filter(user=request.user).order_by('-timestamp')
			filename_suffix = f"_{request.user.username}"
		
		# Crear respuesta CSV con encoding utf-8-sig (para soporte de caracteres españoles en Excel)
		response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
		
		# Generar nombre de archivo con fecha actual
		fecha_actual = datetime.now().strftime('%d%m%Y_%H%M%S')
		filename = f'mediciones{filename_suffix}_{fecha_actual}.csv'
		response['Content-Disposition'] = f'attachment; filename="{filename}"'
		
		# Escribir BOM para UTF-8 (para Excel)
		response.write('\ufeff')
		
		# Crear escritor CSV
		writer = csv.writer(response)
		
		# Escribir encabezados
		writer.writerow(['Timestamp', 'Usuario (Empresa)', 'Ubicación Manual', 'Valor (m³/h)', 'Foto URL', 'Estado', 'Ubicación GPS', 'Observaciones'])
		
		# Escribir datos de mediciones
		for medicion in mediciones:
			writer.writerow([
				medicion.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
				medicion.user.username,
				medicion.ubicacion_manual or '-',
				medicion.value,
				medicion.photo.url if medicion.photo else '-',
				'Validado' if medicion.is_valid else 'Pendiente',
				f"{medicion.captured_latitude or '-'}, {medicion.captured_longitude or '-'}",
				medicion.observation or '-'
			])

		return response
	except Exception:
		logger.exception("Error exportando CSV", extra={"user_id": request.user.id})
		messages.error(request, 'Error al exportar CSV. Inténtalo nuevamente.')
		return redirect('dashboard')
	
	return response
