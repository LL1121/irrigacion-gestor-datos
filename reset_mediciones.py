import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from web.models import Medicion
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

print('Borrando mediciones actuales...')
deleted = Medicion.objects.all().delete()
print(f'Borradas: {deleted[0]} mediciones')

usuario = User.objects.first()

if usuario:
    print('Creando nuevas mediciones...')
    
    # 2 mediciones superpuestas en el mismo punto
    m1 = Medicion.objects.create(
        user=usuario,
        value=150,
        ubicacion_manual='Pozo Norte A',
        captured_latitude=-35.48,
        captured_longitude=-69.57,
        timestamp=timezone.now()
    )
    
    m2 = Medicion.objects.create(
        user=usuario,
        value=175,
        ubicacion_manual='Pozo Norte B',
        captured_latitude=-35.48,
        captured_longitude=-69.57,
        timestamp=timezone.now() - timedelta(hours=2)
    )
    
    # 2 mediciones en puntos únicos
    m3 = Medicion.objects.create(
        user=usuario,
        value=200,
        ubicacion_manual='Pozo Sur',
        captured_latitude=-35.465,
        captured_longitude=-69.585,
        timestamp=timezone.now() - timedelta(hours=5)
    )
    
    m4 = Medicion.objects.create(
        user=usuario,
        value=126,
        ubicacion_manual='Pozo Este',
        captured_latitude=-35.470,
        captured_longitude=-69.590,
        timestamp=timezone.now() - timedelta(hours=10)
    )
    
    print(f'✓ Creadas 4 mediciones:')
    print(f'  - 2 superpuestas en ({m1.captured_latitude}, {m1.captured_longitude})')
    print(f'  - 1 única en ({m3.captured_latitude}, {m3.captured_longitude})')
    print(f'  - 1 única en ({m4.captured_latitude}, {m4.captured_longitude})')
    print('\n¡Listo! Recargá el mapa para ver los cambios')
else:
    print('Error: No hay usuario en la base de datos')
