import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from web.models import EmpresaPerfil

# Datos de empresas con sus ubicaciones
datos_empresas = {
    'petroargentina': {
        'ubicacion': 'Pozo A-12, Zona Noroeste, Salta - Argentina',
        'descripcion': 'Plataforma de extracción de petróleo. Pozo activo con alta producción. Monitoreo semanal requerido.'
    },
    'ypf_norte': {
        'ubicacion': 'Complejo YPF Norte, Vaca Muerta, Neuquén - Argentina',
        'descripcion': 'Centro de distribución principal. Múltiples pozos bajo supervisión. Control de calidad estricto.'
    },
    'shell_vaca_muerta': {
        'ubicacion': 'Formación Vaca Muerta, Cuenca Neuquina - Argentina',
        'descripcion': 'Operación conjunta. Pozo de alta profundidad. Requiere mediciones precisas.'
    },
    'pan_american_energy': {
        'ubicacion': 'Zona de Magallanes, Santa Cruz - Argentina',
        'descripcion': 'Operación en región austral. Condiciones climáticas extremas. Vigilancia intensiva.'
    },
    'tecpetrol_sa': {
        'ubicacion': 'Pozo Centro, Salta - Argentina',
        'descripcion': 'Producción media. Pozo consolidado con estabilidad operativa.'
    },
    'pluspetrol': {
        'ubicacion': 'Campo Aguada Pichana, Neuquén - Argentina',
        'descripcion': 'Operaciones en marcha. Sistema de monitoreo continuo implementado.'
    },
    'total_austral': {
        'ubicacion': 'Punta Delgada, Tierra del Fuego - Argentina',
        'descripcion': 'Operación offshore. Mediciones críticas para seguridad operacional.'
    },
    'cgc': {
        'ubicacion': 'Pozo Sur, Chubut - Argentina',
        'descripcion': 'Producción regulada. Pozo de importancia estratégica regional.'
    },
}

for username, info in datos_empresas.items():
    try:
        user = User.objects.get(username=username)
        # Crear o actualizar perfil
        perfil, created = EmpresaPerfil.objects.get_or_create(usuario=user)
        perfil.ubicacion = info['ubicacion']
        perfil.descripcion = info['descripcion']
        perfil.save()
        status = '✓ Creado' if created else '✓ Actualizado'
        print(f"{status}: {username}")
    except User.DoesNotExist:
        print(f"✗ No encontrado: {username}")

print("\n¡Perfiles creados exitosamente!")
