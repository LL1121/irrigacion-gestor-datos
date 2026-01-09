# Mejoras de Robustez y Validaciones - Sistema Irrigación

## 📋 Resumen de Cambios

Se ha implementado un sistema robusto de validación de datos en el modelo `Medicion` con múltiples capas de protección tanto en el backend como en el frontend.

---

## 🔒 Validaciones Implementadas

### 1. **Validación de Valores Negativos**
- **Ubicación:** Modelo `Medicion.clean()` + Template frontend
- **Regla:** `valor_caudalimetro >= 0`
- **Acción:** 
  - Backend: Raise `ValidationError` si es negativo
  - Frontend: Input con `min="0"` + validación JavaScript
- **Mensaje:** "El valor del caudalímetro no puede ser negativo."

### 2. **Validación de Fechas Futuras**
- **Ubicación:** Modelo `Medicion.clean()`
- **Regla:** `timestamp` no puede ser en el futuro
- **Acción:** Raise `ValidationError` si es futuro
- **Mensaje:** "La fecha y hora no pueden ser en el futuro."

### 3. **Validación de Tamaño de Archivo**
- **Ubicación:** Modelo `Medicion.clean()` + Template frontend + JavaScript
- **Límite:** Máximo 10MB
- **Acciones:**
  - Backend: Verifica `photo.size <= 10MB`
  - Frontend: Monitorea archivo en tiempo real
  - JavaScript: Deshabilita botón submit si excede 10MB
- **Mensaje:** "El archivo es demasiado grande. Tamaño máximo: 10MB."

### 4. **Validación de Consistencia (Opcional)**
- **Ubicación:** Modelo `Medicion.clean()`
- **Regla:** El valor no debe ser menor que la última medición validada del mismo usuario
- **Acción:** Advertencia (NO error crítico)
- **Propósito:** Prevenir entrada ilógica donde el caudalímetro "retrocede"
- **Mensaje:** "Advertencia: Este valor es menor que la última medición validada. Verifica que el caudalímetro no haya retrocedido."

---

## 🛡️ Mecanismo de Ejecución

### En el Backend (`web/models.py`)
```python
def clean(self):
    """Validaciones de negocio"""
    # Todas las validaciones se ejecutan aquí
    # Se levanta ValidationError si hay problemas
    raise ValidationError(errors)

def save(self, *args, **kwargs):
    """Fuerza ejecución de validaciones"""
    self.full_clean()  # Llama a clean() internamente
    super().save(*args, **kwargs)
```

**Beneficio:** Las validaciones se ejecutan siempre, incluso si se crea un objeto desde Django Shell o Admin.

### En el Frontend (`templates/web/formulario.html`)
1. **HTML5 Validation:** Input con `min="0"`, `required`, `type="number"`
2. **JavaScript en tiempo real:** Monitorea cambios de archivo
3. **Validación antes de envío:** Verifica valores antes de POST

**Beneficio:** Retroalimentación inmediata sin necesidad de ir al servidor.

---

## 🔄 Flujo de Validación

```
Usuario carga medición
    ↓
[Frontend] HTML5 input validations (min=0, required, etc)
    ↓
[Frontend] JavaScript event listeners validan archivo en tiempo real
    ↓
Usuario hace submit
    ↓
[Frontend] JavaScript final check antes de POST
    ↓
[Backend] Vista cargar_medicion() recibe POST
    ↓
[Backend] Crea objeto Medicion()
    ↓
[Backend] medicion.save() ejecuta full_clean()
    ↓
[Backend] Medicion.clean() ejecuta todas las validaciones
    ↓
✅ Si todo OK → Guardado en BD
❌ Si error → ValidationError → Mensaje de error al usuario
```

---

## 📝 Manejo de Errores en la Vista

### `views.py` - `cargar_medicion()`

```python
@login_required
def cargar_medicion(request):
    if request.method == 'POST':
        try:
            # ... crear medición ...
            medicion.save()  # Full_clean se ejecuta aquí
            messages.success(request, 'Medición guardada exitosamente')
            
        except ValidationError as e:
            # Mostrar cada error de validación al usuario
            for field, error_list in e.error_dict.items():
                for error in error_list:
                    messages.error(request, f'{field}: {error.message}')
            return redirect('cargar')
```

**Resultado:** Cada error de validación se muestra como un mensaje amigable al usuario.

---

## 🧪 Cómo Probar

### Test 1: Valor Negativo
```bash
# Frontend: Intenta ingresar -100
# Resultado: Input rechaza valor, no permite envío

# O si se bypasea frontend:
# Backend: ValidationError levantado
# Usuario ve: "value: El valor del caudalímetro no puede ser negativo."
```

### Test 2: Archivo Demasiado Grande
```bash
# Frontend: Selecciona imagen > 10MB
# Resultado: Warning rojo aparece, botón submit se deshabilita

# Si se intenta enviar (bypass):
# Backend: ValidationError levantado
# Usuario ve: "photo: El archivo es demasiado grande. Tamaño máximo: 10MB"
```

### Test 3: Fecha Futura
```python
# Desde Django Shell:
from web.models import Medicion
from datetime import timedelta
from django.utils import timezone

m = Medicion(
    user=User.objects.first(),
    value=100,
    timestamp=timezone.now() + timedelta(hours=1)
)
m.save()  # ❌ ValidationError levantado

# Resultado: "timestamp: La fecha y hora no pueden ser en el futuro."
```

### Test 4: Consistencia de Valores
```python
# Si el usuario tiene medición validada con valor 500
# E intenta guardar una nueva con valor 400
# Resultado: Advertencia (no error crítico)
# Mensaje: "Advertencia: Este valor es menor que la última medición validada..."
```

---

## 🚀 Beneficios

✅ **Datos Integrales:** Imposible guardar datos inválidos  
✅ **Experiencia UX:** Retroalimentación en tiempo real  
✅ **Seguridad:** Múltiples capas de validación  
✅ **Auditoría:** Previene datos ilógicos (valores "hacia atrás")  
✅ **Performance:** No gasta almacenamiento en archivos gigantes  
✅ **Consistencia:** Funciona desde cualquier interfaz (web, admin, shell)

---

## 📊 Capas de Protección

| Capa | Componente | Beneficio |
|------|-----------|-----------|
| **1** | HTML5 Validation | Feedback instantáneo |
| **2** | JavaScript | Validación sin servidor |
| **3** | Backend Model.clean() | Garantía de integridad |
| **4** | Django ValidationError | Mensajes claros al usuario |
| **5** | Mensaje al usuario | UX amigable |

---

## ⚙️ Próximos Pasos Sugeridos

1. **Logging:** Registrar todos los intentos de validación fallida
2. **Rate Limiting:** Limitar intentos de carga por usuario
3. **Backup Automático:** Snapshot diario de mediciones
4. **Testing Automatizado:** Unit tests para cada validación
5. **Monitoreo:** Alertas si hay muchos errores de validación

---

**Última actualización:** 8 de Enero de 2026  
**Estado:** ✅ Implementado y funcional
