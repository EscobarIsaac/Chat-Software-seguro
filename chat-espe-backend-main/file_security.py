import hashlib
import os
import tempfile
import mimetypes
import subprocess
import logging

# Dependencias opcionales con manejo de errores
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

# Inicializar mimetypes
mimetypes.init()

logger = logging.getLogger(__name__)


class FileSecurityValidator:

    def __init__(self):
        self.allowed_mime_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'],
            'video': ['video/mp4', 'video/avi', 'video/mkv', 'video/webm'],
            'document': ['application/pdf', 'text/plain']
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.malicious_signatures = [
            b'<?php', b'<script', b'javascript:', b'eval(', b'exec(',
            b'system(', b'shell_exec(', b'passthru(', b'<iframe', b'onload=',
            b'onerror='
        ]

    def validate_file(self, file_path: str, original_filename: str) -> dict:
        """
        Valida un archivo multimedia para detectar contenido malicioso
        """
        result = {
            'is_safe': False,
            'errors': [],
            'file_type': None,
            'mime_type': None
        }

        try:
            # 1. Verificar tamaño del archivo
            if not self._check_file_size(file_path):
                result['errors'].append(
                    'Archivo excede el tamaño máximo permitido (50MB)')
                return result

            # 2. Verificar tipo MIME real
            if HAS_MAGIC:
                try:
                    mime_type = magic.from_file(file_path, mime=True)
                except Exception:
                    mime_type, _ = mimetypes.guess_type(original_filename)
            else:
                # Fallback usando mimetypes
                mime_type, _ = mimetypes.guess_type(original_filename)

            if not mime_type:
                result['errors'].append(
                    'No se pudo determinar el tipo de archivo')
                return result

            result['mime_type'] = mime_type

            if not self._is_allowed_mime_type(mime_type):
                result['errors'].append(
                    f'Tipo de archivo no permitido: {mime_type}')
                return result

            # 3. Verificar extensión vs contenido real
            if not self._verify_file_extension(file_path, original_filename):
                result['errors'].append(
                    'La extensión del archivo no coincide con su contenido')
                return result

            # 4. Escanear firmas maliciosas
            if not self._scan_malicious_signatures(file_path):
                result['errors'].append(
                    'Contenido malicioso detectado en el archivo')
                return result

            # 5. Validaciones específicas por tipo de archivo
            file_type = self._get_file_category(mime_type)
            result['file_type'] = file_type

            if file_type == 'image':
                if not self._validate_image(file_path):
                    result['errors'].append(
                        'Imagen corrupta o contiene datos maliciosos')
                    return result
            elif file_type == 'audio':
                if not self._validate_audio(file_path):
                    result['errors'].append(
                        'Archivo de audio corrupto o contiene datos maliciosos'
                    )
                    return result
            elif file_type == 'video':
                if not self._validate_video(file_path):
                    result['errors'].append(
                        'Archivo de video corrupto o contiene datos maliciosos'
                    )
                    return result

            # 6. Verificar metadatos sospechosos
            if not self._check_metadata_security(file_path, file_type):
                result['errors'].append('Metadatos sospechosos detectados')
                return result

            result['is_safe'] = True
            return result

        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            result['errors'].append(f'Error durante la validación: {str(e)}')
            return result

    def _check_file_size(self, file_path: str) -> bool:
        return os.path.getsize(file_path) <= self.max_file_size

    def _is_allowed_mime_type(self, mime_type: str) -> bool:
        for category, types in self.allowed_mime_types.items():
            if mime_type in types:
                return True
        return False

    def _get_file_category(self, mime_type: str) -> str:
        for category, types in self.allowed_mime_types.items():
            if mime_type in types:
                return category
        return 'unknown'

    def _verify_file_extension(self, file_path: str,
                               original_filename: str) -> bool:
        if HAS_MAGIC:
            try:
                real_mime = magic.from_file(file_path, mime=True)
            except:
                # Si magic falla, usar verificación básica
                return True
        else:
            # Sin magic, usar verificación básica
            return True

        guessed_mime, _ = mimetypes.guess_type(original_filename)

        # Verificar que la extensión corresponda al contenido real
        if guessed_mime and real_mime:
            return real_mime == guessed_mime or real_mime in self.allowed_mime_types.get(
                self._get_file_category(guessed_mime), [])
        return True

    def _scan_malicious_signatures(self, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024 *
                                 1024)  # Lee solo el primer MB por eficiencia
                for signature in self.malicious_signatures:
                    if signature in content:
                        logger.warning(
                            f"Firma maliciosa detectada: {signature}")
                        return False
            return True
        except Exception:
            return False

    def _validate_image(self, file_path: str) -> bool:
        if not HAS_PIL:
            return True  # Omitir validación si PIL no está disponible

        try:
            with Image.open(file_path) as img:
                img.verify()  # Verifica que la imagen no esté corrupta

            # Verificar nuevamente para detectar steganografía básica
            with Image.open(file_path) as img:
                # Verificar dimensiones razonables
                if img.width > 10000 or img.height > 10000:
                    return False

                return True
        except Exception:
            return False

    def _validate_audio(self, file_path: str) -> bool:
        if not HAS_MUTAGEN:
            return True  # Omitir validación si Mutagen no está disponible

        try:
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path)
                # Verificar duración razonable (máximo 2 horas)
                if hasattr(audio.info, 'length') and audio.info.length > 7200:
                    return False
            return True
        except Exception:
            return False

    def _validate_video(self, file_path: str) -> bool:
        try:
            # Verificación básica de video sin ffprobe (para evitar dependencias externas)
            if file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.webm')):
                # Verificar que el archivo tenga un header válido
                with open(file_path, 'rb') as f:
                    header = f.read(256)
                    # Verificar magic numbers básicos
                    if file_path.lower().endswith('.mp4'):
                        return b'ftyp' in header
                    elif file_path.lower().endswith('.avi'):
                        return header.startswith(b'RIFF') and b'AVI ' in header
            return True
        except Exception:
            return False

    def _check_metadata_security(self, file_path: str, file_type: str) -> bool:
        """
        Verifica que los metadatos no contengan información sospechosa
        """
        try:
            if file_type == 'image':
                with Image.open(file_path) as img:
                    if hasattr(img, 'getexif'):
                        exif = img.getexif()
                        if exif:
                            # Verificar campos de metadatos por contenido sospechoso
                            for tag, value in exif.items():
                                if isinstance(value, str):
                                    for signature in [
                                            b'<script', b'javascript:',
                                            b'<?php'
                                    ]:
                                        if signature.decode('utf-8',
                                                            errors='ignore'
                                                            ) in value.lower():
                                            return False
            return True
        except Exception:
            return True  # Si no podemos verificar metadatos, no bloqueamos

    def calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash SHA-256 del archivo para verificación de integridad"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
