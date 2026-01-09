from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import reverse
from django.db import models

from .models import Medicion, EmpresaPerfil


@admin.register(EmpresaPerfil)
class EmpresaPerfilAdmin(admin.ModelAdmin):
	list_display = ("usuario", "ubicacion", "updated_at")
	search_fields = ("usuario__username", "ubicacion")
	fieldsets = (
		("Información Básica", {
			"fields": ("usuario", "ubicacion", "descripcion")
		}),
		("Auditoría", {
			"fields": ("created_at", "updated_at"),
			"classes": ("collapse",)
		}),
	)
	readonly_fields = ("created_at", "updated_at")


@admin.register(Medicion)
class MedicionAdmin(admin.ModelAdmin):
	"""
	Admin Panel para Mediciones en modo READ-ONLY.
	Previene edición, eliminación o creación manual de datos.
	Los datos solo pueden provenir de la aplicación.
	"""
	
	# === PERMISOS (READ-ONLY) ===
	def has_add_permission(self, request):
		"""Prevenir creación manual de mediciones"""
		return False
	
	def has_change_permission(self, request, obj=None):
		"""Prevenir edición de mediciones existentes"""
		return False
	
	def has_delete_permission(self, request, obj=None):
		"""Prevenir eliminación de mediciones"""
		return False
	
	# === VISUALIZACIÓN ===
	list_display = (
		"timestamp_formatted",
		"user",
		"ubicacion_manual",
		"value_formatted",
		"is_valid_icon",
		"foto_preview"
	)
	
	list_filter = (
		"is_valid",
		"timestamp",
		"user",
		"ubicacion_manual"
	)
	
	search_fields = (
		"user__username",
		"ubicacion_manual",
		"observation"
	)
	
	readonly_fields = (
		"timestamp",
		"photo",
		"captured_latitude",
		"captured_longitude",
		"target_latitude",
		"target_longitude",
		"user",
		"value",
		"ubicacion_manual",
		"observation",
		"is_valid",
		"foto_preview_large",
		"metadata_info"
	)
	
	fieldsets = (
		("📋 Información de Medición", {
			"fields": (
				"timestamp",
				"user",
				"value",
				"ubicacion_manual",
				"observation"
			)
		}),
		("📸 Evidencia Fotográfica", {
			"fields": (
				"photo",
				"foto_preview_large"
			)
		}),
		("📍 Geolocalización Capturada", {
			"fields": (
				"captured_latitude",
				"captured_longitude"
			)
		}),
		("🎯 Geolocalización Objetivo", {
			"fields": (
				"target_latitude",
				"target_longitude"
			)
		}),
		("✅ Validación", {
			"fields": ("is_valid",)
		}),
		("ℹ️ Metadatos", {
			"fields": ("metadata_info",),
			"classes": ("collapse",)
		}),
	)
	
	def get_ordering(self, request):
		"""Ordenar por fecha más reciente primero"""
		return ["-timestamp"]
	
	# === MÉTODOS DE VISUALIZACIÓN ===
	
	def timestamp_formatted(self, obj):
		"""Mostrar timestamp con formato legible"""
		return obj.timestamp.strftime("%d/%m/%Y %H:%M:%S")
	timestamp_formatted.short_description = "Fecha y Hora"
	timestamp_formatted.admin_order_field = "timestamp"
	
	def value_formatted(self, obj):
		"""Mostrar valor con unidades"""
		return f"{obj.value} m³/h"
	value_formatted.short_description = "Valor"
	value_formatted.admin_order_field = "value"
	
	def is_valid_icon(self, obj):
		"""Mostrar estado de validación con icono"""
		if obj.is_valid:
			return mark_safe(
				'<span style="color: green; font-weight: bold;">✓ Verificado</span>'
			)
		else:
			return mark_safe(
				'<span style="color: orange; font-weight: bold;">⊘ Pendiente</span>'
			)
	is_valid_icon.short_description = "Estado"
	is_valid_icon.admin_order_field = "is_valid"
	
	def foto_preview(self, obj):
		"""Mostrar thumbnail de la foto en la lista"""
		if obj.photo:
			return mark_safe(
				f'<a href="{obj.photo.url}" target="_blank">'
				f'<img src="{obj.photo.url}" width="50" height="50" '
				f'style="border-radius: 4px; object-fit: cover;" alt="Foto">'
				f'</a>'
			)
		return mark_safe('<span style="color: #ccc;">Sin foto</span>')
	foto_preview.short_description = "📸 Foto"
	
	def foto_preview_large(self, obj):
		"""Mostrar foto grande en la vista de detalle"""
		if obj.photo:
			return mark_safe(
				f'<a href="{obj.photo.url}" target="_blank">'
				f'<img src="{obj.photo.url}" style="max-width: 400px; '
				f'max-height: 400px; border-radius: 8px; margin-top: 10px;" alt="Foto">'
				f'</a><br><small><a href="{obj.photo.url}" target="_blank">Abrir en nueva pestaña</a></small>'
			)
		return mark_safe('<p style="color: #999;">No hay foto disponible</p>')
	foto_preview_large.short_description = "Foto Grande"
	
	def metadata_info(self, obj):
		"""Mostrar información de metadatos"""
		# Calcular tamaño de foto
		foto_size = f"{obj.photo.size / (1024*1024):.2f} MB" if obj.photo else 'N/A'
		
		info = f"""
		<div style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
			<p><strong>ID:</strong> {obj.id}</p>
			<p><strong>Usuario:</strong> {obj.user.username if obj.user else 'N/A'}</p>
			<p><strong>Registrado:</strong> {obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')}</p>
			<p><strong>Archivo:</strong> {obj.photo.name if obj.photo else 'Sin archivo'}</p>
			<p><strong>Tamaño foto:</strong> {foto_size}</p>
		</div>
		"""
		return mark_safe(info)
	metadata_info.short_description = "Información Técnica"
	
	def has_view_permission(self, request, obj=None):
		"""Permitir visualización (lectura) a todos los staff"""
		return True
	
	class Media:
		css = {
			"all": ("admin/css/medicion_custom.css",)
		}
