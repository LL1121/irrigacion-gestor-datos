import random
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from web.models import Medicion


class Command(BaseCommand):
	help = 'Crea empresas petroleras ficticias con mediciones de prueba'

	def add_arguments(self, parser):
		parser.add_argument(
			'--empresas',
			type=int,
			default=5,
			help='Número de empresas a crear'
		)
		parser.add_argument(
			'--mediciones',
			type=int,
			default=10,
			help='Mediciones por empresa'
		)

	def handle(self, *args, **options):
		num_empresas = options['empresas']
		num_mediciones = options['mediciones']

		empresas_nombres = [
			'PetroArgentina', 'YPF Norte', 'Shell Vaca Muerta', 
			'Pan American Energy', 'Tecpetrol SA', 'Pluspetrol',
			'Total Austral', 'CGC', 'Wintershall Dea', 'Vista Oil'
		]

		ubicaciones = [
			'Pozo Norte-12', 'Pozo Sur-08', 'Pozo Este-05', 
			'Pozo Oeste-03', 'Pozo Central-01', 'Sector A-14',
			'Batería 7', 'Yacimiento Loma Campana', 'Pozo Fortin de Piedra',
			'Lindero Atravesado', 'Vaca Muerta Central'
		]

		self.stdout.write(self.style.SUCCESS(f'Creando {num_empresas} empresas...'))

		empresas_creadas = []
		for i in range(min(num_empresas, len(empresas_nombres))):
			username = empresas_nombres[i].lower().replace(' ', '_')
			
			# Verificar si ya existe
			if User.objects.filter(username=username).exists():
				self.stdout.write(self.style.WARNING(f'Usuario {username} ya existe, saltando...'))
				empresas_creadas.append(User.objects.get(username=username))
				continue

			user = User.objects.create_user(
				username=username,
				email=f'{username}@petroleo.com.ar',
				password='demo123',
				first_name=empresas_nombres[i],
				is_staff=False
			)
			empresas_creadas.append(user)
			self.stdout.write(self.style.SUCCESS(f'✓ Creada empresa: {empresas_nombres[i]} (user: {username}, pass: demo123)'))

		self.stdout.write(self.style.SUCCESS(f'\nCreando {num_mediciones} mediciones por empresa...'))

		for empresa in empresas_creadas:
			for j in range(num_mediciones):
				# Generar timestamp aleatorio en los últimos 30 días
				dias_atras = random.randint(0, 30)
				horas_atras = random.randint(0, 23)
				timestamp = timezone.now() - timezone.timedelta(days=dias_atras, hours=horas_atras)

				# Valor aleatorio del caudalímetro
				valor = Decimal(random.uniform(500.0, 2500.0)).quantize(Decimal('0.01'))

				# Ubicación aleatoria
				ubicacion = random.choice(ubicaciones)

				# Crear imagen ficticia con el valor
				img = self.crear_imagen_caudalimetro(valor, ubicacion)

				# Crear medición
				medicion = Medicion(
					user=empresa,
					value=valor,
					ubicacion_manual=ubicacion,
					timestamp=timestamp,
					observation=f'Medición de prueba #{j+1}' if random.random() > 0.7 else '',
					captured_latitude=random.uniform(-40.0, -30.0),
					captured_longitude=random.uniform(-70.0, -60.0),
					is_valid=random.choice([True, True, True, False])  # 75% válidas
				)
				
				# Guardar imagen
				medicion.photo.save(
					f'medicion_{empresa.username}_{j+1}.png',
					ContentFile(img.getvalue()),
					save=False
				)
				medicion.save()

			self.stdout.write(self.style.SUCCESS(f'✓ {num_mediciones} mediciones creadas para {empresa.username}'))

		self.stdout.write(self.style.SUCCESS(f'\n¡Listo! Se crearon {len(empresas_creadas)} empresas con {num_mediciones} mediciones cada una.'))
		self.stdout.write(self.style.WARNING('\nCredenciales de acceso:'))
		for empresa in empresas_creadas:
			self.stdout.write(f'  Usuario: {empresa.username} | Contraseña: demo123')

	def crear_imagen_caudalimetro(self, valor, ubicacion):
		"""Crea una imagen ficticia de un caudalímetro con el valor"""
		# Crear imagen 800x600
		img = Image.new('RGB', (800, 600), color=(240, 240, 240))
		draw = ImageDraw.Draw(img)

		# Dibujar marco del "caudalímetro"
		draw.rectangle([50, 50, 750, 550], fill=(255, 255, 255), outline=(100, 100, 100), width=5)

		# Título
		draw.rectangle([50, 50, 750, 120], fill=(44, 95, 141))
		
		# Texto del valor (grande)
		draw.rectangle([150, 200, 650, 380], fill=(240, 248, 255), outline=(44, 95, 141), width=3)
		
		# Agregar texto (sin fuente custom para evitar dependencias)
		draw.text((400, 85), "CAUDALÍMETRO DIGITAL", fill=(255, 255, 255), anchor="mm")
		draw.text((400, 290), f"{valor} m³/h", fill=(44, 95, 141), anchor="mm")
		draw.text((400, 450), ubicacion, fill=(100, 100, 100), anchor="mm")
		draw.text((400, 520), f"Timestamp: {timezone.now().strftime('%d/%m/%Y %H:%M')}", fill=(150, 150, 150), anchor="mm")

		# Guardar en BytesIO
		output = BytesIO()
		img.save(output, format='PNG')
		output.seek(0)
		return output
