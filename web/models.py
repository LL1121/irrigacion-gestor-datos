from io import BytesIO
import os
import sys

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

from .utils import extract_exif_metadata, compress_and_resize_image, generate_unique_filename


def medicion_photo_path(instance, filename):
	"""Generar ruta dinámica con nombre único: evidencias/YEAR/WEEK/user_id/unique_filename"""
	year = timezone.now().year
	week = timezone.now().isocalendar()[1]
	user_id = instance.user.id
	
	# Generar nombre único para evitar colisiones
	unique_filename = generate_unique_filename(user_id, filename)
	
	return f"evidencias/{year}/{week}/{user_id}/{unique_filename}"


class EmpresaPerfil(models.Model):
	"""Perfil adicional de la empresa con información operativa"""
	usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="empresa_perfil", help_text="Usuario que representa a la empresa")
	icono = models.ImageField(upload_to="empresa_iconos/", null=True, blank=True, help_text="Ícono / logo de la empresa")
	ubicacion = models.CharField(max_length=300, null=True, blank=True, help_text="Ubicación geográfica de la empresa / pozo")
	descripcion = models.TextField(null=True, blank=True, help_text="Descripción general de la empresa")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Perfil de Empresa"
		verbose_name_plural = "Perfiles de Empresa"

	def __str__(self):
		return f"Perfil - {self.usuario.username}"


class Medicion(models.Model):
	"""Modelo de medición de caudalímetro con validaciones estrictas"""
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="mediciones", help_text="Usuario que cargó la medición")
	value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valor del caudalímetro (m³/h)")
	ubicacion_manual = models.CharField(max_length=200, null=True, blank=True, help_text="Para uso interno de operarios")
	photo = models.ImageField(upload_to=medicion_photo_path, null=True, blank=True, help_text="Fotografía de evidencia")
	timestamp = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora de registro")
	observation = models.TextField(null=True, blank=True, help_text="Observaciones adicionales (opcional)")
	
	# Campos de auditoría / validación offline
	captured_latitude = models.FloatField(null=True, blank=True, help_text="Latitud capturada en el dispositivo")
	captured_longitude = models.FloatField(null=True, blank=True, help_text="Longitud capturada en el dispositivo")
	captured_at = models.DateTimeField(null=True, blank=True, help_text="Fecha/hora capturada desde EXIF del dispositivo")
	uploaded_at = models.DateTimeField(
		default=timezone.now,
		help_text="Fecha/hora en que el servidor recibió la medición"
	)
	is_valid = models.BooleanField(default=False, help_text="¿La medición ha sido validada?")
	target_latitude = models.FloatField(null=True, blank=True, help_text="Latitud objetivo / esperada")
	target_longitude = models.FloatField(null=True, blank=True, help_text="Longitud objetivo / esperada")

	class Meta:
		verbose_name = "Medición"
		verbose_name_plural = "Mediciones"
		ordering = ["-timestamp"]
		indexes = [
			models.Index(fields=['-timestamp']),
			models.Index(fields=['user', '-timestamp']),
			models.Index(fields=['captured_latitude', 'captured_longitude']),
			models.Index(fields=['is_valid']),
		]

	def __str__(self):
		return f"{self.value} m³/h - {self.ubicacion_manual or 'Sin ubicación'} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"

	@property
	def maps_url(self):
		"""
		Genera URL de Google Maps con las coordenadas capturadas.
		
		Returns:
			str: URL de Google Maps o None si no hay coordenadas
		"""
		if self.captured_latitude is None or self.captured_longitude is None:
			return None
		
		# Formato: https://www.google.com/maps/search/?api=1&query=lat,lon
		return f"https://www.google.com/maps/search/?api=1&query={self.captured_latitude},{self.captured_longitude}"
	
	@property
	def has_location(self):
		"""Verifica si tiene coordenadas GPS capturadas"""
		return self.captured_latitude is not None and self.captured_longitude is not None

	def clean(self):
		"""Validaciones de negocio para la medición"""
		errors = {}
		
		# 1. Validar que el valor no sea negativo
		if self.value is not None and self.value < 0:
			errors['value'] = "El valor del caudalímetro no puede ser negativo."
		
		# 2. Validar que el timestamp no sea en el futuro
		if self.timestamp and self.timestamp > timezone.now():
			errors['timestamp'] = "La fecha y hora no pueden ser en el futuro."
		
		# 3. Validar tamaño de archivo (máximo 10MB)
		if self.photo:
			# Si el archivo no tiene size (nuevo archivo), obtenerlo
			file_size = None
			try:
				if hasattr(self.photo, 'size'):
					file_size = self.photo.size
				elif hasattr(self.photo.file, 'size'):
					file_size = self.photo.file.size
				elif hasattr(self.photo, 'file') and hasattr(self.photo.file, 'seek'):
					# Para archivos que no tienen size directo
					current_position = self.photo.file.tell()
					self.photo.file.seek(0, 2)  # Ir al final
					file_size = self.photo.file.tell()
					self.photo.file.seek(current_position)  # Volver a la posición original
			except Exception as e:
				pass
			
			max_size = 10 * 1024 * 1024  # 10MB
			if file_size and file_size > max_size:
				errors['photo'] = f"El archivo es demasiado grande. Tamaño máximo: 10MB. Tamaño actual: {file_size / (1024*1024):.2f}MB"
		
		# 4. Validación de consistencia: el valor no debe ser menor que la medición anterior
		if self.user and self.value is not None:
			previous_measurement = Medicion.objects.filter(
				user=self.user,
				is_valid=True
			).exclude(pk=self.pk).order_by('-timestamp').first()
			
			if previous_measurement and self.value < previous_measurement.value:
				# Advertencia (no error crítico, pero informativo)
				errors['value'] = (
					f"Advertencia: Este valor ({self.value}) es menor que la última medición validada "
					f"({previous_measurement.value}). Verifica que el caudalímetro no haya retrocedido."
				)

		# 5. Validación de Null Island (0,0)
		if self.captured_latitude == 0 and self.captured_longitude == 0:
			errors['captured_latitude'] = "La coordenada no puede ser (0,0)."
			errors['captured_longitude'] = "La coordenada no puede ser (0,0)."
		
		if errors:
			raise ValidationError(errors)

	def save(self, *args, **kwargs):
		"""Validar, extraer EXIF y comprimir imagen antes de guardar"""
		self.full_clean()

		# Permitir omitir el procesamiento si ya se optimizó el archivo
		if getattr(self, "_skip_image_processing", False):
			self._skip_image_processing = False
			super().save(*args, **kwargs)
			return

		# Procesar imagen si existe
		if self.photo:
			try:
				# 1. EXTRAER EXIF PRIMERO (antes de comprimir y perder metadata)
				metadata = extract_exif_metadata(self.photo)
				
				# Guardar coordenadas GPS si existen en EXIF
				if metadata['latitude'] is not None:
					self.captured_latitude = metadata['latitude']
				if metadata['longitude'] is not None:
					self.captured_longitude = metadata['longitude']
				# Guardar timestamp capturado desde EXIF si existe
				if metadata['timestamp'] is not None:
					self.captured_at = metadata['timestamp']
				
				# 2. COMPRIMIR Y OPTIMIZAR imagen
				# Resetear puntero del archivo antes de comprimir
				if hasattr(self.photo, 'seek'):
					self.photo.seek(0)
				
				compressed_buffer = compress_and_resize_image(
					self.photo,
					max_size=1280,
					quality=70
				)
				
				if compressed_buffer:
					# 3. REEMPLAZAR con versión optimizada
					file_name, _ = os.path.splitext(self.photo.name)
					optimized_file = InMemoryUploadedFile(
						compressed_buffer,
						field_name=self.photo.field.name,
						name=f"{file_name}.jpg",
						content_type='image/jpeg',
						size=sys.getsizeof(compressed_buffer.getvalue()),
						charset=None,
					)
					self.photo = optimized_file
			except Exception as e:
				# Si falla el procesamiento, continuar con la imagen original
				pass

		super().save(*args, **kwargs)
