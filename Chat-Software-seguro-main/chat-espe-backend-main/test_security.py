#!/usr/bin/env python3
"""
Script de prueba para el sistema de seguridad de archivos mejorado
"""

import os
import sys
import tempfile
from typing import Tuple
from PIL import Image
import numpy as np
from file_security import EnhancedFileSecurityValidator


def create_test_image(filename: str,
                      width: int = 200,
                      height: int = 200) -> str:
    """Crea imagen limpia con distribución natural sin datos quemados.
    Se usa ruido gaussian moderado y ligera mezcla de gradientes para simular fotografía.
    """
    # Gradiente base
    x = np.linspace(0, 1, width, dtype=np.float32)
    y = np.linspace(0, 1, height, dtype=np.float32)
    xv, yv = np.meshgrid(x, y)
    base = (0.4 + 0.6 * xv * yv)
    # Añadir ruido suavizado
    noise = np.random.normal(0.0, 0.12, (height, width)).astype(np.float32)
    img_f = np.clip(base + noise, 0, 1)
    # Convertir a RGB con ligeras variaciones
    r = img_f
    g = np.clip(img_f * 0.95 + np.random.normal(0, 0.03, img_f.shape), 0, 1)
    b = np.clip(img_f * 1.05 + np.random.normal(0, 0.03, img_f.shape), 0, 1)
    arr = (np.stack([r, g, b], axis=2) * 255).astype(np.uint8)
    img = Image.fromarray(arr, 'RGB')
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    img.save(temp_path, 'PNG')
    return temp_path


def embed_message_lsb(image: Image.Image, message: bytes) -> Image.Image:
    """Embebe un mensaje simple en los LSB de una imagen (canal R).
    No usa datos quemados; longitud y patrón derivan del mensaje real.
    """
    arr = np.array(image.convert('RGB'))
    flat = arr[:, :, 0].flatten()  # canal rojo
    bits = []
    for byte in message:
        for i in range(8):
            bits.append((byte >> i) & 1)
    # Limitar por tamaño
    max_bits = min(len(flat), len(bits))
    for i in range(max_bits):
        flat[i] = (flat[i] & 0xFE) | bits[i]
    arr[:, :, 0] = flat.reshape(arr[:, :, 0].shape)
    return Image.fromarray(arr, 'RGB')


def create_suspicious_image(filename: str,
                            width: int = 200,
                            height: int = 200,
                            fmt: str = 'PNG') -> str:
    """Crea imagen sospechosa con mensaje embebido y ligero camuflaje estadístico."""
    base_path = create_test_image(f"base_{filename}", width, height)
    base_img = Image.open(base_path)
    # Mensaje variable (simula contenido oculto)
    secret = os.urandom(64)  # 64 bytes pseudo-aleatorios
    stego_img = embed_message_lsb(base_img, secret)
    # Pequeño ajuste de ruido para intentar camuflar
    arr = np.array(stego_img)
    jitter = np.random.randint(0, 2, arr.shape[:2], dtype=np.uint8)
    arr[:, :, 1] = (arr[:, :, 1]
                    & 0xFE) | jitter  # introducir patrón leve en canal G
    stego_img = Image.fromarray(arr, 'RGB')
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    stego_img.save(temp_path, fmt)
    # Limpiar base
    if os.path.exists(base_path):
        os.unlink(base_path)
    return temp_path


def create_bmp_stego_pair() -> Tuple[str, str]:
    """Genera par (clean.bmp, stego.bmp) para pruebas específicas de BMP."""
    clean_path = create_test_image('clean_bmp.bmp', 180, 180)
    clean_img = Image.open(clean_path)
    # Re-guardar realmente en BMP
    clean_img.save(clean_path, 'BMP')
    stego_img = embed_message_lsb(clean_img,
                                  b'BMP_STEGO_EXAMPLE_' + os.urandom(16))
    stego_path = os.path.join(tempfile.gettempdir(), 'stego_bmp.bmp')
    stego_img.save(stego_path, 'BMP')
    return clean_path, stego_path


def test_validator():
    """Prueba el validador con diferentes tipos de imágenes"""
    validator = EnhancedFileSecurityValidator()

    print("🔍 Probando sistema de detección de steganografía mejorado\n")

    # Prueba 1: Imagen normal
    print("📝 Prueba 1: Imagen normal")
    normal_image = create_test_image("test_normal.jpg")
    try:
        report = validator.validate_file(normal_image, "test_normal.jpg")
        print(
            f"   Resultado: {'✅ SEGURO' if report.is_safe else '❌ RECHAZADO'}")
        print(f"   Nivel de amenaza: {report.threat_level.value}")
        print(f"   Confianza: {report.confidence:.1%}")
        if report.issues:
            print(f"   Problemas: {report.issues}")
        if report.warnings:
            print(f"   Advertencias: {report.warnings[:2]}")  # Solo mostrar 2
    except Exception as e:
        print(f"   Error: {e}")
    finally:
        if os.path.exists(normal_image):
            os.unlink(normal_image)

    print()

    # Prueba 2: Imagen sospechosa (LSB embed)
    print("📝 Prueba 2: Imagen con mensaje oculto LSB")
    suspicious_image = create_suspicious_image("test_suspicious.png")
    try:
        report = validator.validate_file(suspicious_image,
                                         "test_suspicious.png")
        print(
            f"   Resultado: {'✅ SEGURO' if report.is_safe else '❌ RECHAZADO'}")
        print(f"   Nivel de amenaza: {report.threat_level.value}")
        print(f"   Confianza: {report.confidence:.1%}")
        if report.issues:
            print(f"   Problemas: {report.issues}")
        if report.warnings:
            print(f"   Advertencias: {report.warnings[:2]}")
    except Exception as e:
        print(f"   Error: {e}")
    finally:
        if os.path.exists(suspicious_image):
            os.unlink(suspicious_image)

    print()

    # Prueba 3: Par BMP limpio vs stego
    print("📝 Prueba 3: Par BMP limpio vs stego")
    clean_bmp, stego_bmp = create_bmp_stego_pair()
    for label, path in [("BMP limpio", clean_bmp), ("BMP stego", stego_bmp)]:
        try:
            report = validator.validate_file(path, os.path.basename(path))
            print(
                f"   {label}: {'✅ SEGURO' if report.is_safe else '❌ RECHAZADO'} | Conf: {report.confidence:.1%} | Nivel: {report.threat_level.value}"
            )
        except Exception as e:
            print(f"   Error {label}: {e}")
    # Limpiar bmp temporales
    for p in [clean_bmp, stego_bmp]:
        if os.path.exists(p):
            os.unlink(p)

    # Prueba 4: Si existe un archivo específico, probarlo
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        if os.path.exists(test_file):
            print(
                f"📝 Prueba 4: Archivo proporcionado ({os.path.basename(test_file)})"
            )
            try:
                report = validator.validate_file(test_file,
                                                 os.path.basename(test_file))
                print(
                    f"   Resultado: {'✅ SEGURO' if report.is_safe else '❌ RECHAZADO'}"
                )
                print(f"   Nivel de amenaza: {report.threat_level.value}")
                print(f"   Confianza: {report.confidence:.1%}")
                if report.issues:
                    print(f"   Problemas: {report.issues}")
                if report.warnings:
                    print(f"   Advertencias: {report.warnings[:3]}")

                # Mostrar detalles del análisis de steganografía si es una imagen
                if 'steganography_analysis' in report.metadata:
                    stego_details = report.metadata['steganography_analysis']
                    print(f"   📊 Análisis detallado:")
                    for method, details in stego_details.items():
                        if isinstance(details, dict) and 'detected' in details:
                            status = "✓ Detectado" if details[
                                'detected'] else "○ No detectado"
                            conf = f" ({details.get('confidence', 0):.1%})" if 'confidence' in details else ""
                            print(f"      {method}: {status}{conf}")

            except Exception as e:
                print(f"   Error: {e}")

    print("\n🎯 Configuración actual:")
    stego_detector = validator.stego_detector
    print(f"   • Umbral LSB: {stego_detector.lsb_threshold}")
    print(f"   • Umbral entropía: {stego_detector.entropy_threshold}")
    print(f"   • Umbral chi-cuadrado: {stego_detector.chi_square_threshold}")
    print(f"   • Umbral confianza: {stego_detector.confidence_threshold}")


if __name__ == "__main__":
    test_validator()
