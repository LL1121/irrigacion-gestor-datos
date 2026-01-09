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


def medicion_photo_path(instance, filename):
	"""Generar ruta dinámica: evidencias/YEAR/WEEK/user_id/filename"""
	year = timezone.now().year
	week = timezone.now().isocalendar()[1]
	user_id = instance.user.id
	return f"evidencias/{year}/{week}/{user_id}/{filename}"


class EmpresaPerfil(models.Model):
	"""Perfil adicional de la empresa con información operativa"""
	usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="empresa_perfil", help_text="Usuario que representa a la empresa")
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
	is_valid = models.BooleanField(default=False, help_text="¿La medición ha sido validada?")
	target_latitude = models.FloatField(null=True, blank=True, help_text="Latitud objetivo / esperada")
	target_longitude = models.FloatField(null=True, blank=True, help_text="Longitud objetivo / esperada")

	class Meta:
		verbose_name = "Medición"
		verbose_name_plural = "Mediciones"
		ordering = ["-timestamp"]

	def __str__(self):
		return f"{self.value} m³/h - {self.ubicacion_manual or 'Sin ubicación'} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"

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
		
		if errors:
			raise ValidationError(errors)

	def save(self, *args, **kwargs):
		"""Validar y comprimir imagen antes de guardar"""
		self.full_clean()

		# Comprimir imagen si existe
		if self.photo:
			try:
				img = Image.open(self.photo)

				# Convertir a RGB para evitar problemas con transparencias
				if img.mode != 'RGB':
					img = img.convert('RGB')

				# Redimensionar si excede 1000px en algún eje
				max_size = 1000
				if img.width > max_size or img.height > max_size:
					img.thumbnail((max_size, max_size), Image.LANCZOS)

				# Guardar en buffer como JPEG con calidad 70
				buffer = BytesIO()
				img.save(buffer, format='JPEG', quality=70)
				buffer.seek(0)

				# Crear archivo en memoria reemplazando el original
				file_name, _ = os.path.splitext(self.photo.name)
				optimized_file = InMemoryUploadedFile(
					buffer,
					field_name=self.photo.field.name,
					name=f"{file_name}.jpg",
					content_type='image/jpeg',
					size=buffer.getbuffer().nbytes,
					charset=None,
				)
				self.photo = optimized_file
			except Exception:
				# Si falla la compresión, continuar con la imagen original
				pass

		super().save(*args, **kwargs)
