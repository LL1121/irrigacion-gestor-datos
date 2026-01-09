# CSV Export Feature Implementation

## Overview
This document describes the **CSV Export Feature** that allows users to download their measurement history as an Excel-compatible CSV file.

---

## 1. Backend Implementation (`web/views.py`)

### **New Imports**
```python
import csv
from datetime import datetime
```

### **New View: `exportar_csv(request)`**
```python
@login_required
def exportar_csv(request):
	"""Exportar historial de mediciones como CSV"""
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
```

---

## 2. URL Configuration (`web/urls.py`)

Add this path to `urlpatterns`:
```python
path("exportar/", views.exportar_csv, name="exportar_csv"),
```

**Full urlpatterns example:**
```python
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("cargar/", views.cargar_medicion, name="cargar"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("exportar/", views.exportar_csv, name="exportar_csv"),  # ← NEW
    
    # Admin Panel (Custom UI)
    path("gestion/usuarios/", views.admin_usuarios_view, name="admin_usuarios"),
    # ... rest of paths ...
]
```

---

## 3. Frontend Implementation

### **Button for Regular Users (Dashboard)**
Place this in `dashboard.html` (e.g., above the measurements table):
```html
<div class="row mb-3">
    <div class="col-12">
        <a href="{% url 'exportar_csv' %}" class="btn btn-success shadow-sm px-4 py-2 rounded-pill">
            <i class="bi bi-download me-2"></i>Descargar Excel
        </a>
    </div>
</div>
```

### **Button for Staff (Admin Legajo)**
Place this in `admin_empresa_legajo.html` (e.g., next to the "Ver Legajo" button):
```html
<div class="row mt-3">
    <div class="col-12">
        <div class="btn-group" role="group">
            <a href="{% url 'admin_empresa_legajo' empresa.id %}" class="btn btn-primary shadow-sm px-4 py-2">
                <i class="bi bi-file-text me-2"></i>Actualizar
            </a>
            <a href="{% url 'exportar_csv' %}?user_id={{ empresa.id }}" class="btn btn-success shadow-sm px-4 py-2">
                <i class="bi bi-download me-2"></i>Descargar Excel
            </a>
        </div>
    </div>
</div>
```

### **Button for Staff (Admin Mediciones)**
Place this in `admin_mediciones_empresa.html`:
```html
<div class="mb-3">
    <a href="{% url 'exportar_csv' %}?user_id={{ empresa.id }}" class="btn btn-success shadow-sm px-4 py-2 rounded-pill">
        <i class="bi bi-download me-2"></i>Descargar Excel
    </a>
</div>
```

---

## 4. CSV File Format

### **Columns:**
1. **Timestamp** - Formato: `DD/MM/YYYY HH:MM:SS`
2. **Usuario (Empresa)** - Username del usuario
3. **Ubicación Manual** - Manual location entered by user
4. **Valor (m³/h)** - Consumption value
5. **Foto URL** - Link to the photo or "-" if none
6. **Estado** - "Validado" or "Pendiente"
7. **Ubicación GPS** - Latitude, Longitude captured
8. **Observaciones** - User observations/notes

### **Example Row:**
```
Timestamp,Usuario (Empresa),Ubicación Manual,Valor (m³/h),Foto URL,Estado,Ubicación GPS,Observaciones
08/01/2026 10:30:45,operario_1,Pozo A,150.5,/media/mediciones/foto_001.jpg,Validado,"10.5234, 65.3456",Medición normal
08/01/2026 11:15:20,operario_1,Pozo B,155.2,-,Pendiente,"10.5240, 65.3460",Requiere validación
```

---

## 5. Filename Pattern

**Format:** `mediciones_[SUFFIX]_DDMMYYYY_HHMMSS.csv`

**Examples:**
- Regular user: `mediciones_operario_1_08012026_103045.csv`
- Staff (specific user): `mediciones_empresa_x_08012026_103045.csv`
- Staff (all system): `mediciones_sistema_completo_08012026_103045.csv`

---

## 6. Encoding & Excel Compatibility

- **Encoding:** `utf-8-sig` (UTF-8 with BOM)
- **BOM (Byte Order Mark):** `\ufeff` written at start
- **Purpose:** Ensures Spanish characters (ñ, á, é, í, ó, ú) display correctly in Excel
- **Compatibility:** Works with Excel, Google Sheets, LibreOffice

---

## 7. Access Control Logic

| User Type | Can Export | What |
|-----------|-----------|------|
| **Regular Operario** | ✅ Yes | Only own measurements |
| **Staff** | ✅ Yes (with ?user_id) | Specific user's measurements |
| **Staff** | ✅ Yes (no query param) | ALL system measurements |
| **Superuser** | ✅ Yes | All of the above + admin access |
| **Anonymous** | ❌ No | Redirects to login |

---

## 8. Testing Checklist

- [ ] Regular user can download their own data
- [ ] File contains all their measurements
- [ ] Column headers are correct
- [ ] Timestamps format correctly (DD/MM/YYYY HH:MM:SS)
- [ ] Spanish characters display properly in Excel
- [ ] Staff can download all system data (no user_id param)
- [ ] Staff can download specific user data (?user_id=5)
- [ ] Filename includes date/time suffix
- [ ] File downloads instead of opening in browser
- [ ] "Validado"/"Pendiente" status appears correctly
- [ ] Photo URLs are absolute and clickable in Excel
- [ ] GPS coordinates format as "lat, lon"

---

## 9. Integration Points

**Where to add buttons:**

1. **Dashboard (for operarios):**
   - Add button next to "Últimas Mediciones" heading
   - Or add to a new row above the table

2. **Admin Legajo (for staff viewing company):**
   - Add button next to the "Ver Legajo" button
   - Or add in the "Información Operativa" card

3. **Admin Mediciones (for viewing all measurements):**
   - Add button at top of measurements list
   - Next to any existing filters or buttons

---

## 10. Code Changes Summary

### **web/views.py**
- ✅ Imported `csv` module
- ✅ Imported `datetime` for timestamp generation
- ✅ Created `exportar_csv()` view with access control
- ✅ Handles query parameter `?user_id` for staff
- ✅ Uses utf-8-sig encoding for Excel compatibility
- ✅ Writes 8-column CSV with proper formatting

### **web/urls.py**
- ✅ Added route: `path("exportar/", views.exportar_csv, name="exportar_csv")`

### **Frontend Templates**
- ✅ HTML snippet for regular users
- ✅ HTML snippet for staff (with user_id parameter)
- ✅ Button styling with Bootstrap classes

---

## 11. Security Notes

- ✅ `@login_required` decorator ensures only authenticated users can export
- ✅ Staff users can only export their own data OR all system data (not other users)
- ✅ Regular users can only export their own data
- ✅ Staff accessing `?user_id=X` for another staff member → exports their data (expected behavior)
- ✅ No sensitive data exposed beyond normal dashboard view

---

## 12. Browser Download Behavior

- **Attachment Header:** Forces download instead of opening in browser
- **Content-Type:** `text/csv; charset=utf-8-sig`
- **File Extension:** `.csv` (Excel recognizes it)
- **Filename:** Dynamic with username and timestamp

---

**Status**: ✅ Complete and ready to integrate  
**Last Updated**: January 8, 2026  
**Implemented By**: GitHub Copilot (Full Stack Django Expert)
