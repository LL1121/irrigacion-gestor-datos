from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Medicion, EmpresaPerfil


class Command(BaseCommand):
    help = 'Llenar las coordenadas de mediciones antiguas con valores del perfil de empresa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Mostrar qué se haría sin hacer cambios'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Obtener todas las mediciones que NO tengan coordenadas
        mediciones_sin_coords = Medicion.objects.filter(
            captured_latitude__isnull=True
        ).select_related('user')
        
        count = 0
        
        for medicion in mediciones_sin_coords:
            try:
                # Obtener el EmpresaPerfil del usuario
                empresa_perfil = EmpresaPerfil.objects.get(usuario=medicion.user)
                
                if empresa_perfil.latitude and empresa_perfil.longitude:
                    if not dry_run:
                        medicion.captured_latitude = empresa_perfil.latitude
                        medicion.captured_longitude = empresa_perfil.longitude
                        medicion.target_latitude = empresa_perfil.latitude
                        medicion.target_longitude = empresa_perfil.longitude
                        medicion.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Medición {medicion.id} ({medicion.user.username}): '
                            f'{empresa_perfil.latitude}, {empresa_perfil.longitude}'
                        )
                    )
                    count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Medición {medicion.id} ({medicion.user.username}): '
                            f'EmpresaPerfil sin coordenadas'
                        )
                    )
            except EmpresaPerfil.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Medición {medicion.id} ({medicion.user.username}): '
                        f'No tiene EmpresaPerfil'
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Se hubieran actualizado {count} mediciones'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Se actualizaron {count} mediciones exitosamente')
            )
