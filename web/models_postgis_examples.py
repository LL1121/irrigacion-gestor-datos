"""
EJEMPLOS DE MODELOS CON POSTGIS - NO USAR DIRECTAMENTE
Este archivo contiene ejemplos de referencia para implementar PostGIS
en Django (GeoDjango) y SQLAlchemy (GeoAlchemy2).
"""

# ============================================================================
# OPCIÓN 1: GeoDjango (Django + PostGIS)
# ============================================================================
"""
REQUISITOS:
1. Instalar PostGIS: https://postgis.net/install/
2. Instalar GDAL/GEOS (dependencias de GeoDjango)
3. pip install psycopg2-binary
4. Actualizar settings.py:
   - Agregar 'django.contrib.gis' a INSTALLED_APPS
   - Cambiar ENGINE a 'django.contrib.gis.db.backends.postgis'

EJEMPLO DE MODELO:
"""

from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class MedicionPostGIS(gis_models.Model):
    """Modelo de medición usando PostGIS PointField"""
    user = gis_models.ForeignKey(User, on_delete=gis_models.SET_NULL, null=True)
    value = gis_models.DecimalField(max_digits=10, decimal_places=2)
    
    # PointField para almacenar coordenadas (usa PostGIS)
    # SRID 4326 = WGS84 (sistema estándar GPS)
    location = gis_models.PointField(
        srid=4326, 
        null=True, 
        blank=True,
        help_text="Ubicación GPS (PostGIS Point)"
    )
    
    photo = gis_models.ImageField(upload_to='evidencias/')
    # Dual timestamps
    captured_at = gis_models.DateTimeField(null=True, blank=True)
    uploaded_at = gis_models.DateTimeField(auto_now_add=True)
    timestamp = gis_models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validación de Null Island (0,0)"""
        if self.location and self.location.x == 0 and self.location.y == 0:
            raise ValidationError("La coordenada no puede ser (0,0).")
    
    @property
    def maps_url(self):
        """Genera URL de Google Maps desde el PointField"""
        if not self.location:
            return None
        
        # Extraer lat/lon del Point
        lon = self.location.x  # Longitud
        lat = self.location.y  # Latitud
        
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    
    @staticmethod
    def create_point(latitude, longitude):
        """Helper para crear Point desde lat/lon"""
        from django.contrib.gis.geos import Point
        # Point(longitude, latitude) - ORDEN IMPORTANTÍSIMO
        return Point(longitude, latitude, srid=4326)


# ============================================================================
# OPCIÓN 2: SQLAlchemy + GeoAlchemy2 (Flask/FastAPI)
# ============================================================================
"""
REQUISITOS:
1. pip install geoalchemy2 psycopg2-binary
2. Base de datos PostgreSQL con extensión PostGIS habilitada

EJEMPLO DE MODELO:
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, func
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely.geometry import Point as ShapelyPoint

Base = declarative_base()

class MedicionSQLAlchemy(Base):
    __tablename__ = 'mediciones'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    value = Column(Numeric(10, 2))
    
    # Geometry column para PostGIS
    location = Column(
        Geometry('POINT', srid=4326),
        nullable=True,
        comment="Ubicación GPS (PostGIS Point)"
    )
    
    photo_path = Column(String(500))
    # Dual timestamps
    captured_at = Column(DateTime)
    uploaded_at = Column(DateTime, server_default=func.now())
    timestamp = Column(DateTime)
    
    @property
    def maps_url(self):
        """Genera URL de Google Maps desde Geometry"""
        if not self.location:
            return None
        
        # Convertir WKB a Shapely Point
        point = to_shape(self.location)
        lon = point.x
        lat = point.y
        
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    
    @staticmethod
    def create_point_wkb(latitude, longitude):
        """Helper para crear Point desde lat/lon"""
        from geoalchemy2.shape import from_shape
        # Crear Shapely Point (lon, lat)
        point = ShapelyPoint(longitude, latitude)
        # Convertir a WKB para GeoAlchemy2
        return from_shape(point, srid=4326)

    def validate_location(self):
        """Validación de Null Island (0,0)"""
        if not self.location:
            return
        point = to_shape(self.location)
        if point.x == 0 and point.y == 0:
            raise ValueError("La coordenada no puede ser (0,0).")


# ============================================================================
# MIGRACIÓN: Convertir floats a PointField en Django existente
# ============================================================================
"""
PASOS PARA MIGRAR TU MODELO ACTUAL:

1. Instalar GeoDjango (ver requisitos arriba)

2. Agregar nuevo campo PointField (NO eliminar floats aún):
   
   from django.contrib.gis.db import models as gis_models
   
   class Medicion(models.Model):
       # ... campos existentes ...
       captured_latitude = models.FloatField(...)  # Mantener temporalmente
       captured_longitude = models.FloatField(...) # Mantener temporalmente
       
       # NUEVO campo PostGIS
       location = gis_models.PointField(srid=4326, null=True, blank=True)

3. Ejecutar migraciones:
   python manage.py makemigrations
   python manage.py migrate

4. Migración de datos (crear migración manual):
   
   from django.contrib.gis.geos import Point
   
   def migrate_coordinates(apps, schema_editor):
       Medicion = apps.get_model('web', 'Medicion')
       for medicion in Medicion.objects.all():
           if medicion.captured_latitude and medicion.captured_longitude:
               medicion.location = Point(
                   medicion.captured_longitude,  # X = longitude
                   medicion.captured_latitude,   # Y = latitude
                   srid=4326
               )
               medicion.save()

5. Después de verificar, eliminar campos float antiguos en otra migración
"""

# ============================================================================
# ATOMICIDAD: Guardar archivo + DB en una sola transacción
# ============================================================================
"""
EJEMPLO DJANGO (transaction.atomic):

from django.db import transaction

def guardar_medicion_atomic(user, value, photo_file, lat=None, lon=None):
    with transaction.atomic():
        medicion = MedicionPostGIS(user=user, value=value)
        if lat is not None and lon is not None:
            medicion.location = MedicionPostGIS.create_point(lat, lon)
        medicion.photo = photo_file
        medicion.save()
        # Si ocurre un error aquí, se revierte todo (DB + archivo)
        return medicion
"""
