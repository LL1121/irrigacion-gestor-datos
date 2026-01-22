"""
Utilidades para procesamiento de imágenes y extracción de metadatos EXIF
"""
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from io import BytesIO


def extract_exif_metadata(image_file):
    """
    Extrae metadatos EXIF de un archivo de imagen (DateTimeOriginal y GPS coords).
    
    Args:
        image_file: File object o path de imagen
        
    Returns:
        dict: {
            'timestamp': datetime object o None,
            'latitude': float (decimal degrees) o None,
            'longitude': float (decimal degrees) o None
        }
    """
    result = {
        'timestamp': None,
        'latitude': None,
        'longitude': None
    }
    
    try:
        # Abrir imagen
        img = Image.open(image_file)
        
        # Extraer datos EXIF
        exif_data = img._getexif()
        
        if not exif_data:
            return result
        
        # Convertir tags numéricos a nombres legibles
        exif = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value
        
        # Extraer DateTimeOriginal
        if 'DateTimeOriginal' in exif:
            try:
                dt_str = exif['DateTimeOriginal']
                # Formato típico: "2024:01:15 14:30:45"
                result['timestamp'] = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            except (ValueError, TypeError):
                pass
        
        # Extraer GPS
        if 'GPSInfo' in exif:
            gps_info = {}
            for key, val in exif['GPSInfo'].items():
                decode = GPSTAGS.get(key, key)
                gps_info[decode] = val
            
            # Convertir coordenadas DMS a Decimal
            lat = _convert_gps_to_decimal(
                gps_info.get('GPSLatitude'),
                gps_info.get('GPSLatitudeRef')
            )
            lon = _convert_gps_to_decimal(
                gps_info.get('GPSLongitude'),
                gps_info.get('GPSLongitudeRef')
            )
            
            result['latitude'] = lat
            result['longitude'] = lon
    
    except Exception as e:
        # Si falla la extracción, devolver diccionario con None
        pass
    
    return result


def _convert_gps_to_decimal(dms_tuple, ref):
    """
    Convierte coordenadas GPS de formato DMS (Degrees/Minutes/Seconds) a Decimal Degrees.
    
    Args:
        dms_tuple: Tupla (degrees, minutes, seconds) - cada valor puede ser Rational
        ref: 'N', 'S', 'E', 'W' - referencia para signo
        
    Returns:
        float: Coordenada en grados decimales (negativo para S/W)
    """
    if not dms_tuple or not ref:
        return None
    
    try:
        # Extraer grados, minutos, segundos
        degrees = float(dms_tuple[0])
        minutes = float(dms_tuple[1])
        seconds = float(dms_tuple[2])
        
        # Convertir a decimal
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        # Aplicar signo negativo para Sur y Oeste
        if ref in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    
    except (IndexError, TypeError, ValueError, ZeroDivisionError):
        return None


def compress_and_resize_image(image_file, max_size=1280, quality=70):
    """
    Comprime y redimensiona una imagen para optimización de almacenamiento.
    
    Args:
        image_file: File object, path, o BytesIO con imagen
        max_size: Tamaño máximo del lado más largo en píxeles (default: 1280)
        quality: Calidad JPEG 1-100 (default: 70)
        
    Returns:
        BytesIO: Buffer con imagen optimizada en formato JPEG
    """
    try:
        # Abrir imagen
        img = Image.open(image_file)
        
        # CRUCIAL: Corregir orientación basándose en EXIF
        # Esto asegura que fotos verticales permanezcan verticales
        img = ImageOps.exif_transpose(img)
        
        # Convertir a RGB (necesario para PNGs con transparencia)
        if img.mode != 'RGB':
            # Si tiene canal alpha, usar fondo blanco
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Alpha channel como mask
                img = background
            else:
                img = img.convert('RGB')
        
        # Redimensionar manteniendo aspect ratio
        # Obtener dimensiones actuales
        width, height = img.size
        longest_side = max(width, height)
        
        # Solo redimensionar si excede el máximo
        if longest_side > max_size:
            # Calcular nuevo tamaño manteniendo proporción
            if width > height:
                new_width = max_size
                new_height = int((height / width) * max_size)
            else:
                new_height = max_size
                new_width = int((width / height) * max_size)
            
            # Redimensionar con LANCZOS (alta calidad)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Guardar en buffer como JPEG optimizado sin EXIF
        output_buffer = BytesIO()
        img.save(
            output_buffer,
            format='JPEG',
            quality=quality,
            optimize=True,
            exif=b''  # Elimina metadata EXIF para ahorrar espacio
        )
        output_buffer.seek(0)
        
        return output_buffer
    
    except Exception as e:
        # Si falla, devolver None
        return None
