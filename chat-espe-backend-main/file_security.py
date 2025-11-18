import hashlib
import os
import tempfile
import mimetypes
import subprocess
import logging
import io
import json
import numpy as np
import shutil
import zlib
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Dependencias con manejo de errores
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    from PIL import Image, ImageChops, ImageStat
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from scipy import stats, signal
    import scipy.fftpack as fftpack
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import stegano
    from stegano import lsb
    HAS_STEGANO = True
except ImportError:
    HAS_STEGANO = False

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Niveles de amenaza detectados"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityReport:
    """Reporte detallado de seguridad"""
    is_safe: bool
    threat_level: ThreatLevel
    confidence: float
    issues: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    recommendations: List[str]


class SteganographyDetector:
    """Detector avanzado de esteganografía"""

    def __init__(self):
        self.chi_square_threshold = 0.01  # p-value para prueba chi-cuadrado (más permisivo)
        self.entropy_threshold = 7.5  # Umbral de entropía estándar
        self.lsb_threshold = 0.25  # Umbral LSB más sensible para detectar steganografía
        self.confidence_threshold = 0.5  # Umbral de confianza más accesible
        self.stego_entropy_threshold = 7.8  # Umbral alto pero no extremo

    # =====================
    # Utilidades adaptativas
    # =====================
    def compute_image_complexity(self, image_path: str) -> Dict[str, Any]:
        """Calcula métricas de complejidad visual para ajustar umbrales dinámicamente.
        No depende de valores 'quemados' sino de cuantiles relativos de la propia imagen.
        """
        metrics: Dict[str, Any] = {
            'edge_density': 0.0,
            'color_variance': 0.0,
            'saturation_variance': 0.0,
            'block_uniformity': 0.0,
            'jpeg_quality_estimate': None,
            'complexity_score': 0.0,
            'format': None
        }
        if not HAS_PIL:
            return metrics
        try:
            img = Image.open(image_path)
            metrics['format'] = img.format
            # Convertir a RGB para métricas consistentes
            if img.mode != 'RGB':
                img = img.convert('RGB')
            arr = np.array(img)
            h, w, _ = arr.shape
            # Escalado liviano para acelerar
            scale_factor = 256 / max(h, w) if max(h, w) > 256 else 1.0
            if scale_factor < 1.0:
                new_size = (int(w * scale_factor), int(h * scale_factor))
                img_small = img.resize(new_size, Image.BILINEAR)
                arr_small = np.array(img_small)
            else:
                arr_small = arr
            # Edge density vía gradiente simple (Sobel aproximado)
            gray = np.mean(arr_small, axis=2).astype(np.float32)
            gy = np.abs(np.diff(gray, axis=0, prepend=gray[0:1]))
            gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, 0:1]))
            edges = (gx + gy)
            edge_density = float(np.mean(edges > (edges.mean() + edges.std())))
            metrics['edge_density'] = edge_density
            # Varianza de color
            metrics['color_variance'] = float(
                np.mean([np.var(arr_small[:, :, i]) for i in range(3)]))
            # Saturación aproximada (HSV)
            hsv = []
            for row in arr_small:
                for r, g, b in row:
                    mx = max(r, g, b)
                    mn = min(r, g, b)
                    sat = 0 if mx == 0 else (mx - mn) / mx
                    hsv.append(sat)
            sat_arr = np.array(hsv, dtype=np.float32)
            metrics['saturation_variance'] = float(np.var(sat_arr))
            # Uniformidad de bloques 8x8 (indicador de compresión JPEG múltiple)
            block_uniform_scores = []
            gray_small = gray if scale_factor == 1.0 else np.mean(arr_small,
                                                                  axis=2)
            bh, bw = gray_small.shape
            for y in range(0, bh - 8, 8):
                for x in range(0, bw - 8, 8):
                    block = gray_small[y:y + 8, x:x + 8]
                    block_var = np.var(block)
                    block_uniform_scores.append(block_var)
            if block_uniform_scores:
                # Uniformidad inversa: bloques con muy baja varianza sugieren compresión fuerte
                avg_block_var = np.mean(block_uniform_scores)
                metrics['block_uniformity'] = float(1.0 /
                                                    (1.0 + avg_block_var))
            # Estimación de calidad JPEG (si aplica)
            if img.format == 'JPEG' and hasattr(
                    img, 'quantization') and img.quantization:
                # Usar promedio simple de tablas de cuantización para estimar calidad relativa
                q_tables = img.quantization
                if isinstance(q_tables, dict):
                    q_vals = []
                    for k, v in q_tables.items():
                        q_vals.extend(v)
                    if q_vals:
                        # Calidad inversa a cuantización promedio
                        avg_q = np.mean(q_vals)
                        metrics['jpeg_quality_estimate'] = float(
                            1.0 / (1.0 + (avg_q / 50.0)))
            # Combinar métricas en score de complejidad (normalizar cada componente)
            comp_components = []
            # Normalizaciones suaves (evitar datos quemados: usar escalas relativas)
            comp_components.append(edge_density)
            comp_components.append(np.tanh(metrics['color_variance'] / 5000.0))
            comp_components.append(
                np.tanh(metrics['saturation_variance'] * 2.0))
            comp_components.append(metrics['block_uniformity'])
            if metrics['jpeg_quality_estimate'] is not None:
                comp_components.append(metrics['jpeg_quality_estimate'])
            metrics['complexity_score'] = float(
                np.clip(np.mean(comp_components), 0.0, 1.0))
            return metrics
        except Exception as e:
            logger.warning(f"Fallo en compute_image_complexity: {e}")
            return metrics

    def adaptive_lsb_threshold(self,
                               complexity: Dict[str, Any]) -> Dict[str, float]:
        """Genera umbrales adaptativos para análisis LSB basados en complejidad y formato.
        Devuelve dict con deviation_minor, deviation_moderate, deviation_strong.
        """
        base = 0.5  # centro ideal
        comp = complexity.get('complexity_score', 0.5)
        fmt = (complexity.get('format') or '').upper()
        # Ajustar sensibilidad: imágenes muy complejas => más tolerancia (umbrales más altos)
        tolerance_factor = 0.05 + comp * 0.15  # rango 0.05 - 0.20
        # Formato BMP suele no tener compresión => distribución más natural => usar menor tolerancia
        if fmt == 'BMP':
            tolerance_factor *= 0.7
        elif fmt in (
                'PNG',
                'WEBP'):  # formatos sin pérdidas o con compresión distinta
            tolerance_factor *= 1.0
        elif fmt == 'JPEG':  # compresión con pérdidas introduce ruido => más tolerancia
            tolerance_factor *= 1.3
        # Derivar umbrales escalonados
        deviation_minor = 0.20 + tolerance_factor * 0.5
        deviation_moderate = deviation_minor + 0.05 + tolerance_factor * 0.3
        deviation_strong = deviation_moderate + 0.07 + tolerance_factor * 0.2
        return {
            'minor': float(deviation_minor),
            'moderate': float(deviation_moderate),
            'strong': float(deviation_strong)
        }

    def rs_analysis(self, image_path: str) -> Tuple[bool, float]:
        """Realiza RS Steganalysis básica para estimar alteraciones LSB.
        Devuelve (detected, confidence). Implementación ligera adaptada.
        """
        if not HAS_PIL:
            return False, 0.0
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            arr = np.array(img)
            # Usar solo un canal para rapidez
            channel = arr[:, :, 0].astype(np.int16)  # prevenir overflow
            # Submuestreo si es muy grande
            h, w = channel.shape
            max_side = 512
            if max(h, w) > max_side:
                scale = max_side / float(max(h, w))
                new_size = (int(w * scale), int(h * scale))
                channel = np.array(
                    Image.fromarray(channel.astype(np.uint8)).resize(
                        new_size, Image.BILINEAR)).astype(np.int16)
            # Formar grupos de 4 píxeles en bloques 2x2
            regular = 0
            singular = 0
            flipped_change = 0
            total_groups = 0
            for y in range(0, channel.shape[0] - 1, 2):
                for x in range(0, channel.shape[1] - 1, 2):
                    block = channel[y:y + 2, x:x + 2].flatten()
                    total_groups += 1
                    # Función de discriminación: suma de diferencias absolutas adyacentes
                    d_orig = int(
                        abs(int(block[0]) - int(block[1])) +
                        abs(int(block[1]) - int(block[2])) +
                        abs(int(block[2]) - int(block[3])))
                    # Flip LSB de cada píxel
                    flipped = np.array([(int(b) ^ 1) for b in block],
                                       dtype=np.int16)
                    d_flip = int(
                        abs(int(flipped[0]) - int(flipped[1])) +
                        abs(int(flipped[1]) - int(flipped[2])) +
                        abs(int(flipped[2]) - int(flipped[3])))
                    if d_flip > d_orig:
                        regular += 1
                    elif d_flip < d_orig:
                        singular += 1
                    flipped_change += abs(d_flip - d_orig)
            if total_groups == 0:
                return False, 0.0
            # En imágenes naturales R ≈ S. En stego LSB, diferencia entre R y S aumenta.
            diff = abs(regular - singular) / float(total_groups)
            avg_change = flipped_change / float(total_groups)
            # Confianza basada en combinación de diff y cambio promedio
            confidence = np.tanh((diff * 3.0) + (avg_change / 50.0))
            detected = confidence > 0.3 and diff > 0.02
            return bool(detected), float(confidence)
        except Exception as e:
            logger.warning(f"RS analysis error: {e}")
            return False, 0.0

    def lsb_sequence_metrics(self, image_path: str) -> Dict[str, float]:
        """Calcula métricas adicionales sobre la secuencia de LSB para mejorar detección.
        Incluye: autocorrelación lag-1, varianza de bloques, runs test aproximado.
        """
        metrics = {
            'autocorr_lag1': 0.0,
            'block_variance_lsb': 0.0,
            'runs_z': 0.0
        }
        if not HAS_PIL:
            return metrics
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            arr = np.array(img)
            channel = arr[:, :, 0].ravel()
            lsb = (channel & 1).astype(np.int8)
            n = len(lsb)
            if n < 1000:
                return metrics
            # Autocorrelación lag-1
            lsb_mean = lsb.mean()
            num = np.sum((lsb[:-1] - lsb_mean) * (lsb[1:] - lsb_mean))
            den = np.sum((lsb - lsb_mean)**2) + 1e-9
            metrics['autocorr_lag1'] = float(num / den)
            # Varianza de bloques (32 bits)
            block_size = 32
            blocks = lsb[:(n // block_size) * block_size].reshape(
                -1, block_size)
            block_counts = blocks.sum(
                axis=1) / block_size  # proporción de 1s por bloque
            metrics['block_variance_lsb'] = float(np.var(block_counts))
            # Runs test (secuencia de cambios)
            runs = 1 + np.sum(lsb[1:] != lsb[:-1])
            n1 = float(np.sum(lsb, dtype=np.int64))
            n0 = float(n - n1)
            if n1 > 0 and n0 > 0:
                expected_runs = ((2.0 * n1 * n0) / n) + 1.0
                # Fórmula clásica con prevención de overflow: usar float64 y clamp
                var_runs_raw = (2.0 * n1 * n0 * (2.0 * n1 * n0 - n))
                denom = (n**2 * (n - 1)) + 1e-9
                var_runs = var_runs_raw / denom
                # Evitar valores extremos que produzcan sqrt inválida
                if var_runs < 1e-12:
                    var_runs = 1e-12
                z = (runs - expected_runs) / np.sqrt(var_runs)
                # Limitar z-score para estabilidad
                metrics['runs_z'] = float(np.clip(z, -10.0, 10.0))
            return metrics
        except Exception as e:
            logger.warning(f"LSB sequence metrics error: {e}")
            return metrics

    def check_steghide(self, file_path: str) -> Tuple[bool, str]:
        """Intenta ejecutar `steghide info` para detectar datos embebidos (si está instalado).
        Devuelve (detected, raw_output_or_error).
        """
        try:
            steghide_bin = shutil.which('steghide')
            if not steghide_bin:
                return False, 'steghide_not_found'
            # Ejecutar comando info. No necesita contraseña para inspección.
            proc = subprocess.run([steghide_bin, 'info', file_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=20)
            out = (proc.stdout or '') + (proc.stderr or '')
            # Buscar indicios en la salida
            lowered = out.lower()
            if 'no embedded data' in lowered or 'no embedded' in lowered:
                return False, out
            if 'embedded' in lowered or 'file:' in lowered:
                return True, out
            return False, out
        except Exception as e:
            logger.warning(f"steghide check failed: {e}")
            return False, f'error:{e}'

    def run_sharp_analysis(self, file_path: str) -> Dict[str, Any]:
        """Llama al script Node `tools/sharp_analyze.js` si `node` y el script existen.
        Devuelve dict con estadísticas o {} si no disponible.
        """
        try:
            node_bin = shutil.which('node')
            script = os.path.join(os.path.dirname(__file__), 'tools',
                                  'sharp_analyze.js')
            if not node_bin or not os.path.exists(script):
                return {}
            proc = subprocess.run([node_bin, script, file_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=25)
            out = proc.stdout.strip() or proc.stderr.strip()
            if not out:
                return {}
            # Puede devolver JSON o texto
            try:
                return json.loads(out)
            except Exception:
                return {'raw': out}
        except Exception as e:
            logger.warning(f"Sharp analysis failed: {e}")
            return {}

    def crypto_entropy_analysis(self, file_path: str) -> Dict[str, Any]:
        """Análisis complementario para detectar bloques cifrados/compactados:
        - Entropía Shannon por bloques
        - Ratio de compresión (zlib)
        - Chi-cuadrado simple sobre bytes
        Devuelve dict con métricas y flag 'suspicious'
        """
        result = {
            'entropy': 0.0,
            'compress_ratio': 1.0,
            'chi_square_p': 1.0,
            'suspicious': False
        }
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            if not data:
                return result

            # Entropía global (por bytes)
            counts = np.bincount(np.frombuffer(data, dtype=np.uint8))
            probs = counts[counts > 0] / float(len(data))
            entropy = -float(np.sum(probs *
                                    np.log2(probs))) if probs.size > 0 else 0.0
            result['entropy'] = entropy

            # Compresibilidad con zlib
            try:
                comp = zlib.compress(data, level=6)
                ratio = len(comp) / max(1, len(data))
                result['compress_ratio'] = float(ratio)
            except Exception:
                result['compress_ratio'] = 1.0

            # Chi-square sobre bytes vs uniforme
            expected = len(data) / 256.0
            obs = counts.astype(np.float64)
            chi_sq = float(np.sum((obs - expected)**2 / (expected + 1e-9)))
            # p-approximation usando scipy si disponible
            if HAS_SCIPY:
                try:
                    from scipy.stats import chi2
                    p = 1 - chi2.cdf(chi_sq, df=255)
                except Exception:
                    p = float(np.exp(-chi_sq / (len(data) * 0.5)))
            else:
                p = float(np.exp(-chi_sq / (len(data) * 0.5)))
            result['chi_square_p'] = float(p)

            # Heurística: alta entropía (>7.8) y compresibilidad baja (>0.9) => sospechoso
            if entropy > 7.8 and result['compress_ratio'] > 0.9:
                result['suspicious'] = True
            if result['chi_square_p'] < 0.001:
                result['suspicious'] = True

            return result
        except Exception as e:
            logger.warning(f"crypto entropy analysis failed: {e}")
            return result

    def calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash SHA-256 del archivo para verificación de integridad"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _is_high_detail_image(self, image_path: str) -> bool:
        """Detecta si una imagen tiene naturalmente alta entropía por ser muy detallada"""
        if not HAS_PIL:
            return False

        try:
            img = Image.open(image_path)
            width, height = img.size

            # Imágenes muy grandes tienden a tener más entropía natural
            if width * height > 1000000:  # > 1MP
                return True

            # Convertir a escala de grises para análisis de textura
            if img.mode != 'L':
                img = img.convert('L')

            # Muestra pequeña para análisis
            img_small = img.resize((100, 100))
            pixels = np.array(img_small)

            # Calcular varianza simple como indicador de textura/detalle
            pixel_variance = np.var(pixels)

            # Si hay mucha variación, es una imagen con mucho detalle
            return pixel_variance > 2000

        except Exception:
            return False

    def detect_lsb_steganography(self, image_path: str) -> Tuple[bool, float]:
        """
        Detecta esteganografía LSB (Least Significant Bit)
        """
        if not HAS_PIL:
            return False, 0.0

        try:
            # Cargar imagen y preparar
            img = Image.open(image_path)
            original_format = img.format
            if img.mode != 'RGB':
                img = img.convert('RGB')
            width, height = img.size
            pixels = np.array(img)

            # Métricas de complejidad para umbrales dinámicos
            complexity = self.compute_image_complexity(image_path)
            adaptive = self.adaptive_lsb_threshold(complexity)

            # Submuestreo controlado para eficiencia
            max_pixels = 60000
            total_pixels = width * height
            if total_pixels > max_pixels:
                step = max(1, int(np.sqrt(total_pixels / max_pixels)))
                pixels_sample = pixels[::step, ::step]
            else:
                pixels_sample = pixels

            # Extraer LSB de cada canal
            lsb_values: List[int] = []
            for channel in range(3):
                channel_data = pixels_sample[:, :, channel].ravel()
                # Vectorizado para velocidad
                lsb_values.extend((channel_data & 1).tolist())

            sample_size = len(lsb_values)
            if sample_size < 800:  # Muy poca muestra -> no concluyente
                return False, 0.0

            ones = sum(lsb_values)
            ratio = ones / sample_size
            deviation = abs(ratio - 0.5)

            # RS Steganalysis complementaria
            rs_detected, rs_conf = self.rs_analysis(image_path)
            seq_metrics = self.lsb_sequence_metrics(image_path)

            # Ajustes de confianza según métricas de secuencia
            autocorr = seq_metrics['autocorr_lag1']
            block_var = seq_metrics['block_variance_lsb']
            runs_z = abs(
                seq_metrics['runs_z'])  # desviación absoluta de runs esperados

            # Incrementos suaves basados en patrones anómalos
            if abs(autocorr) > 0.15:
                rs_conf += 0.05 * min(abs(autocorr), 0.5)
            if block_var < 0.0005 and deviation < minor_thr:  # distribución excesivamente uniforme por bloque
                rs_conf += 0.08
            if runs_z > 2.2:
                rs_conf += 0.07

            # BMP específico: distribución suele ser más cercana al 50%.
            bmp_adjust = 0.0
            if original_format == 'BMP':
                bmp_adjust = 0.05  # Más rigor en desviaciones: bajar tolerancia efectiva

            # Dinámica de decisión sin 'datos quemados': utilizar niveles adaptativos
            minor_thr = adaptive['minor'] - bmp_adjust
            moderate_thr = adaptive['moderate'] - bmp_adjust
            strong_thr = adaptive['strong'] - bmp_adjust

            # Calcular confianza incremental
            confidence = 0.0
            detected = False

            if deviation >= strong_thr:
                confidence += np.tanh((deviation - strong_thr) * 6.0) * 0.6
                detected = True
            elif deviation >= moderate_thr:
                confidence += np.tanh((deviation - moderate_thr) * 5.0) * 0.45
                # Requiere soporte de RS para declarar sospechoso
                detected = rs_detected and rs_conf > 0.25
            elif deviation >= minor_thr:
                confidence += np.tanh((deviation - minor_thr) * 4.0) * 0.25
                detected = rs_detected and rs_conf > 0.35

            # Incorporar señal RS
            if rs_detected:
                confidence += rs_conf * 0.4
                if not detected and rs_conf > 0.55 and deviation > minor_thr * 0.9:
                    detected = True

            # Penalizar muestras demasiado pequeñas
            if sample_size < 4000:
                confidence *= 0.6
                if confidence < 0.3:
                    detected = False

            # Patrones de herramientas: ajustar si la desviación cae en ventanas simétricas
            # Usamos adaptive en lugar de rangos fijos; derivar ventanas alrededor de moderate/strong
            pattern_window_low = moderate_thr + (strong_thr -
                                                 moderate_thr) * 0.15
            pattern_window_high = strong_thr + (strong_thr -
                                                moderate_thr) * 0.4
            if pattern_window_low <= deviation <= pattern_window_high:
                confidence *= 1.15
                if rs_conf > 0.3:
                    detected = True

            # Normalizar confianza
            confidence = float(np.clip(confidence, 0.0, 1.0))
            return bool(detected), confidence

        except Exception as e:
            logger.error(f"Error en detección LSB: {e}")
            return False, 0.0

    def chi_square_test(self, image_path: str) -> Tuple[bool, float]:
        """
        Prueba chi-cuadrado para detectar alteraciones estadísticas
        """
        if not HAS_PIL or not HAS_SCIPY:
            return False, 0.0

        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            pixels = np.array(img)

            # Realizar prueba chi-cuadrado en cada canal
            p_values = []
            for channel in range(3):
                channel_data = pixels[:, :, channel].flatten()

                # Crear pares de valores
                pairs = [(channel_data[i], channel_data[i + 1])
                         for i in range(0,
                                        len(channel_data) - 1, 2)]

                # Contar frecuencias
                even_count = sum(1 for p in pairs if p[0] % 2 == 0)
                odd_count = len(pairs) - even_count

                # Prueba chi-cuadrado
                expected = len(pairs) / 2
                chi_stat = ((even_count - expected)**2 +
                            (odd_count - expected)**2) / expected

                p_value = 1 - stats.chi2.cdf(chi_stat, df=1)
                p_values.append(p_value)

            # Si algún p-value es muy bajo, hay alteración
            min_p = min(p_values)
            avg_p = np.mean(p_values)

            # Steganografía suele tener p-values muy bajos en múltiples canales
            low_p_count = sum(1 for p in p_values if p < 0.05)

            is_suspicious = min_p < self.chi_square_threshold or (
                low_p_count >= 2 and avg_p < 0.1)

            if low_p_count >= 2:
                confidence = min(1.0, (1 - avg_p) *
                                 1.5)  # Múltiples canales afectados
            else:
                confidence = 1 - min_p

            return is_suspicious, min(confidence, 1.0)

        except Exception as e:
            logger.error(f"Error en prueba chi-cuadrado: {e}")
            return False, 0.0

    def entropy_analysis(self, image_path: str) -> Tuple[bool, float]:
        """
        Análisis de entropía para detectar datos ocultos
        """
        if not HAS_PIL:
            return False, 0.0

        try:
            with open(image_path, 'rb') as f:
                data = f.read()

            # Calcular entropía de Shannon
            byte_counts = np.bincount(np.frombuffer(data, dtype=np.uint8))
            probabilities = byte_counts[byte_counts > 0] / len(data)
            entropy = -np.sum(probabilities * np.log2(probabilities))

            # Alta entropía puede indicar datos cifrados/comprimidos ocultos
            is_suspicious = entropy > self.stego_entropy_threshold

            # Análisis de entropía contextual
            # Imágenes con mucho detalle/textura pueden tener entropía naturalmente alta

            file_size = len(data)

            # Ajustar umbrales según el tamaño del archivo
            # Ajustar thresholds según tamaño de archivo
            if file_size < 50000:  # Archivo pequeño - más tolerante
                base_threshold = self.entropy_threshold + 0.2
                stego_threshold = self.stego_entropy_threshold + 0.15
            elif file_size > 500000:  # Archivo grande - estándar
                base_threshold = self.entropy_threshold
                stego_threshold = self.stego_entropy_threshold
            else:  # Archivo mediano - ligeramente tolerante
                base_threshold = self.entropy_threshold + 0.1
                stego_threshold = self.stego_entropy_threshold + 0.05

            if entropy > stego_threshold:  # Entropía muy alta - probable steganografía
                confidence = min((entropy - stego_threshold) / 0.3, 1.0)
                is_suspicious = True
            elif entropy > base_threshold:  # Entropía alta - investigar
                excess = entropy - base_threshold
                confidence = excess / 0.5
                # Solo marcar como sospechoso si supera threshold más alto
                is_suspicious = entropy > (base_threshold + 0.3)
            else:
                confidence = 0.0
                is_suspicious = False

            return is_suspicious, confidence

        except Exception as e:
            logger.error(f"Error en análisis de entropía: {e}")
            return False, 0.0

    def detect_visual_attacks(self, image_path: str) -> Tuple[bool, List[str]]:
        """
        Detecta ataques visuales y anomalías
        """
        if not HAS_PIL:
            return False, []

        issues = []

        try:
            img = Image.open(image_path)
            width, height = img.size

            # 1. Verificar tamaño sospechoso
            if width * height > 25_000_000:  # >25 megapíxeles
                issues.append("Imagen excesivamente grande")

            # 2. Verificar proporciones inusuales
            ratio = max(width, height) / min(width, height)
            if ratio > 20:
                issues.append("Proporciones inusuales de imagen")

            # 3. Verificar canales alfa sospechosos
            if img.mode in ('RGBA', 'LA'):
                alpha = img.getchannel('A')
                alpha_stats = ImageStat.Stat(alpha)

                # Si el canal alfa tiene patrones inusuales
                if alpha_stats.stddev[0] > 100:
                    issues.append("Canal alfa con patrones sospechosos")

            # 4. Detectar áreas con ruido excesivo
            if HAS_CV2:
                img_cv = cv2.imread(image_path)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

                if laplacian_var > 5000:
                    issues.append("Niveles de ruido anormales detectados")

            return len(issues) > 0, issues

        except Exception as e:
            logger.error(f"Error en detección visual: {e}")
            return False, []

    def frequency_domain_analysis(self, image_path: str) -> Tuple[bool, float]:
        """
        Análisis en dominio de frecuencia (FFT) para detectar alteraciones
        """
        if not HAS_PIL or not HAS_SCIPY:
            return False, 0.0

        try:
            img = Image.open(image_path).convert('L')  # Escala de grises
            img_array = np.array(img)

            # Aplicar FFT
            f_transform = fftpack.fft2(img_array)
            f_shift = fftpack.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)

            # Analizar el espectro
            center = np.array(magnitude_spectrum.shape) // 2
            radius = min(center) // 4

            # Extraer región central
            y, x = np.ogrid[:magnitude_spectrum.shape[0], :magnitude_spectrum.
                            shape[1]]
            mask = (x - center[1])**2 + (y - center[0])**2 <= radius**2

            central_energy = np.sum(magnitude_spectrum[mask])
            total_energy = np.sum(magnitude_spectrum)

            # Ratio de energía central vs total
            energy_ratio = central_energy / total_energy

            # Si hay mucha energía en frecuencias altas, puede ser sospechoso
            is_suspicious = energy_ratio < 0.3
            confidence = 1.0 - energy_ratio if energy_ratio < 0.5 else 0.0

            return is_suspicious, confidence

        except Exception as e:
            logger.error(f"Error en análisis FFT: {e}")
            return False, 0.0


class EnhancedFileSecurityValidator:
    """Validador de seguridad mejorado con detección de esteganografía"""

    def __init__(self):
        self.stego_detector = SteganographyDetector()
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
            b'onerror=', b'<jsp:', b'Runtime.exec'
        ]
        # Firmas de herramientas de esteganografía conocidas
        self.stego_tool_signatures = [
            b'OpenStego', b'steghide', b'outguess', b'jsteg',
            b'F5-steganography', b'camouflage', b'SilentEye'
        ]

    def _higher_threat(self, a: ThreatLevel, b: ThreatLevel) -> ThreatLevel:
        """Devuelve el nivel de amenaza más grave entre `a` y `b`."""
        order = [
            ThreatLevel.SAFE, ThreatLevel.LOW, ThreatLevel.MEDIUM,
            ThreatLevel.HIGH, ThreatLevel.CRITICAL
        ]
        try:
            return a if order.index(a) >= order.index(b) else b
        except Exception:
            return b

    def validate_file(self, file_path: str,
                      original_filename: str) -> SecurityReport:
        """
        Validación completa con análisis de esteganografía
        """
        issues = []
        warnings = []
        metadata = {}
        recommendations = []
        threat_level = ThreatLevel.SAFE
        confidence_scores = []

        try:
            # 1. Validaciones básicas
            basic_result = self._basic_validations(file_path,
                                                   original_filename)
            if not basic_result['passed']:
                issues.extend(basic_result['issues'])
                threat_level = ThreatLevel.HIGH

            # 2. Escanear firmas de herramientas de esteganografía
            if self._scan_stego_signatures(file_path):
                issues.append(
                    "Detectada firma de herramienta de esteganografía")
                threat_level = ThreatLevel.CRITICAL

            # Obtener tipo MIME
            mime_type = self._get_mime_type(file_path, original_filename)
            file_type = self._get_file_category(mime_type)

            # 3. Análisis específico para imágenes
            if file_type == 'image':
                stego_results = self._analyze_image_steganography(file_path)

                if stego_results['has_steganography'] and stego_results[
                        'confidence'] > 0.8:
                    # Verificar que tengamos múltiples indicadores positivos
                    positive_indicators = sum([
                        stego_results['details'].get('lsb_analysis', {}).get(
                            'detected', False), stego_results['details'].get(
                                'chi_square', {}).get('detected', False),
                        stego_results['details'].get('frequency_analysis',
                                                     {}).get(
                                                         'detected', False)
                    ])

                    if positive_indicators >= 2:  # Al menos 2 métodos deben detectar steganografía
                        issues.append(
                            f"Esteganografía detectada con alta confianza ({stego_results['confidence']:.1%}, indicadores: {positive_indicators})"
                        )
                        threat_level = ThreatLevel.CRITICAL
                        recommendations.append(
                            "Rechazar archivo - contenido oculto detectado con múltiples métodos"
                        )
                    else:
                        # Solo un indicador positivo - marcar como sospechoso pero no rechazar
                        warnings.append(
                            f"Posible esteganografía detectada (confianza: {stego_results['confidence']:.1%})"
                        )
                        if threat_level == ThreatLevel.SAFE:
                            threat_level = ThreatLevel.LOW
                elif stego_results['has_steganography']:
                    # Si se detectó steganografía, rechazar independientemente de la confianza
                    threat_level = ThreatLevel.HIGH
                    issues.append(
                        f"Steganografía detectada (confianza: {stego_results['confidence']:.1%})"
                    )
                    recommendations.append(
                        "Rechazar archivo - contenido oculto detectado")

                    # Agregar detalles específicos de lo que se detectó
                    lsb_detected = stego_results['details'].get(
                        'lsb_analysis', {}).get('detected', False)
                    entropy_detected = stego_results['details'].get(
                        'entropy_analysis', {}).get('detected', False)
                    chi_detected = stego_results['details'].get(
                        'chi_square', {}).get('detected', False)

                    detected_methods = []
                    if lsb_detected:
                        detected_methods.append(
                            f"LSB ({stego_results['details']['lsb_analysis']['confidence']:.1%})"
                        )
                    if entropy_detected:
                        detected_methods.append(
                            f"Entropía ({stego_results['details']['entropy_analysis']['confidence']:.1%})"
                        )
                    if chi_detected:
                        detected_methods.append(
                            f"Chi-cuadrado ({stego_results['details']['chi_square']['confidence']:.1%})"
                        )

                    if detected_methods:
                        issues.append(
                            f"Métodos que detectaron steganografía: {', '.join(detected_methods)}"
                        )

                if stego_results['warnings']:
                    warnings.extend(stego_results['warnings'])

                metadata['steganography_analysis'] = stego_results['details']
                confidence_scores.append(stego_results['confidence'])

                # Análisis visual adicional
                has_visual_issues, visual_issues = self.stego_detector.detect_visual_attacks(
                    file_path)
                if has_visual_issues:
                    warnings.extend(visual_issues)
                    if threat_level == ThreatLevel.SAFE:
                        threat_level = ThreatLevel.MEDIUM

                # Análisis estructural BMP (solo si el MIME indicado es BMP)
                if mime_type == 'image/bmp':
                    bmp_ok, bmp_issues, bmp_meta = self._analyze_bmp_structure(
                        file_path)
                    metadata['bmp_structure'] = bmp_meta
                    if not bmp_ok:
                        issues.extend(bmp_issues)
                        threat_level = self._higher_threat(
                            threat_level, ThreatLevel.HIGH)
                    else:
                        for bi in bmp_issues:
                            if any(term in bi for term in [
                                    "firma JPEG", "firma PNG", "inconsistente",
                                    "offset", "relleno"
                            ]):
                                issues.append(bi)
                                threat_level = self._higher_threat(
                                    threat_level, ThreatLevel.HIGH)
                            else:
                                warnings.append(bi)

                # Mismatch extensión BMP vs formato real
                if original_filename.lower().endswith(
                        '.bmp') and mime_type != 'image/bmp':
                    try:
                        if HAS_PIL:
                            real_img = Image.open(file_path)
                            real_fmt = real_img.format
                        else:
                            real_fmt = 'desconocido'
                    except Exception:
                        real_fmt = 'error'
                    issues.append(
                        f"Extensión .bmp no coincide con contenido real (formato: {real_fmt}, MIME: {mime_type})"
                    )
                    threat_level = self._higher_threat(threat_level,
                                                       ThreatLevel.HIGH)

            # 4. Análisis de metadatos
            metadata_issues = self._analyze_metadata(file_path, file_type)
            if metadata_issues:
                warnings.extend(metadata_issues)
                if len(metadata_issues) > 3:
                    threat_level = self._higher_threat(threat_level,
                                                       ThreatLevel.MEDIUM)

            # 5. Verificar integridad estructural
            if not self._verify_file_structure(file_path, mime_type):
                issues.append("Estructura de archivo corrupta o alterada")
                threat_level = self._higher_threat(threat_level,
                                                   ThreatLevel.HIGH)

            # 6. Análisis de entropía general (solo para archivos grandes)
            file_size = os.path.getsize(file_path)
            if file_size > 100000:  # Solo analizar entropía en archivos > 100KB
                has_high_entropy, entropy_confidence = self.stego_detector.entropy_analysis(
                    file_path)
                if has_high_entropy and entropy_confidence > 0.5:
                    warnings.append(
                        f"Entropía anormalmente alta ({entropy_confidence:.1%}) - posibles datos comprimidos/cifrados"
                    )
                    confidence_scores.append(
                        entropy_confidence *
                        0.5)  # Reducir peso de la entropía
                    # Solo cambiar threat_level si la confianza es muy alta
                    if entropy_confidence > 0.8 and threat_level == ThreatLevel.SAFE:
                        threat_level = ThreatLevel.LOW

            # Calcular confianza promedio
            avg_confidence = np.mean(
                confidence_scores) if confidence_scores else 0.0

            # Determinar si es seguro
            is_safe = len(issues) == 0 and threat_level in [
                ThreatLevel.SAFE, ThreatLevel.LOW
            ]

            # Generar recomendaciones
            if is_safe:
                if warnings:
                    recommendations.append(
                        "Archivo aprobado con advertencias - monitorear")
                else:
                    recommendations.append("Archivo seguro para uso")
            else:
                if threat_level == ThreatLevel.CRITICAL:
                    recommendations.append(
                        "RECHAZAR INMEDIATAMENTE - Alto riesgo de seguridad")
                elif threat_level == ThreatLevel.HIGH:
                    recommendations.append(
                        "Rechazar archivo - múltiples problemas de seguridad")
                else:
                    recommendations.append(
                        "Requerir revisión manual antes de aprobar")

            # Si el archivo pasa pero necesita limpieza
            if is_safe and file_type == 'image' and (warnings
                                                     or avg_confidence > 0.2):
                recommendations.append(
                    "Considerar re-encoding de la imagen para eliminar datos ocultos"
                )
                metadata['needs_sanitization'] = True

            return SecurityReport(is_safe=is_safe,
                                  threat_level=threat_level,
                                  confidence=avg_confidence,
                                  issues=issues,
                                  warnings=warnings,
                                  metadata=metadata,
                                  recommendations=recommendations)

        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return SecurityReport(
                is_safe=False,
                threat_level=ThreatLevel.HIGH,
                confidence=0.0,
                issues=[f"Error durante validación: {str(e)}"],
                warnings=[],
                metadata={},
                recommendations=["Rechazar archivo - error de validación"])

    def _basic_validations(self, file_path: str,
                           original_filename: str) -> Dict:
        """Validaciones básicas de seguridad"""
        issues = []

        # Tamaño del archivo
        if os.path.getsize(file_path) > self.max_file_size:
            issues.append(
                f"Archivo excede tamaño máximo ({self.max_file_size / 1024 / 1024}MB)"
            )

        # Nombre de archivo sospechoso
        suspicious_patterns = ['..', '~', '${', '%(', '<', '>', '|', '&']
        for pattern in suspicious_patterns:
            if pattern in original_filename:
                issues.append(
                    f"Nombre de archivo contiene patrón sospechoso: {pattern}")

        # Múltiples extensiones
        if original_filename.count('.') > 2:
            issues.append(
                "Archivo con múltiples extensiones (posible polyglot)")

        # Escanear firmas maliciosas básicas (solo en archivos de texto o ejecutables)
        file_ext = original_filename.lower().split(
            '.')[-1] if '.' in original_filename else ''
        # Solo escanear firmas en archivos que podrían contener código
        if file_ext in [
                'html', 'htm', 'php', 'js', 'jsp', 'asp', 'txt', 'xml'
        ]:
            with open(file_path, 'rb') as f:
                content = f.read(min(1024 * 1024, os.path.getsize(file_path)))
                for signature in self.malicious_signatures:
                    if signature in content:
                        issues.append(
                            f"Firma maliciosa detectada: {signature.decode('utf-8', errors='ignore')[:20]}"
                        )

        return {'passed': len(issues) == 0, 'issues': issues}

    def _scan_stego_signatures(self, file_path: str) -> bool:
        """Escanea firmas de herramientas de esteganografía"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                for signature in self.stego_tool_signatures:
                    if signature in content:
                        logger.warning(f"Detectada firma de {signature}")
                        return True
            return False
        except Exception:
            return False

    def _analyze_bmp_structure(
            self, file_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Analiza estructura interna BMP para detectar archivos disfrazados o corruptos"""
        issues: List[str] = []
        meta: Dict[str, Any] = {}
        try:
            with open(file_path, 'rb') as f:
                header = f.read(54)
                if len(header) < 54:
                    issues.append("BMP: encabezado incompleto")
                    return False, issues, meta
                if header[0:2] != b'BM':
                    issues.append("BMP: firma BM ausente")
                    return False, issues, meta
                file_size = int.from_bytes(header[2:6], 'little', signed=False)
                pixel_offset = int.from_bytes(header[10:14],
                                              'little',
                                              signed=False)
                dib_header_size = int.from_bytes(header[14:18],
                                                 'little',
                                                 signed=False)
                width = int.from_bytes(header[18:22], 'little', signed=True)
                height = int.from_bytes(header[22:26], 'little', signed=True)
                planes = int.from_bytes(header[26:28], 'little', signed=False)
                bpp = int.from_bytes(header[28:30], 'little', signed=False)
                compression = int.from_bytes(header[30:34],
                                             'little',
                                             signed=False)
                meta.update({
                    'file_size_declared': file_size,
                    'pixel_offset': pixel_offset,
                    'dib_header_size': dib_header_size,
                    'width': width,
                    'height': height,
                    'planes': planes,
                    'bits_per_pixel': bpp,
                    'compression': compression
                })
                if planes != 1:
                    issues.append("BMP: planes != 1")
                valid_dib_sizes = {12, 40, 52, 56, 108, 124}
                if dib_header_size not in valid_dib_sizes:
                    issues.append(f"BMP: tamaño DIB inusual {dib_header_size}")
                if bpp not in (1, 4, 8, 16, 24, 32):
                    issues.append(
                        f"BMP: profundidad de bits no soportada {bpp}")
                if width <= 0 or abs(height) <= 0:
                    issues.append("BMP: dimensiones inválidas")
                real_size = os.path.getsize(file_path)
                meta['file_size_real'] = real_size
                if abs(real_size - file_size) > max(1024, file_size * 0.03):
                    issues.append(
                        "BMP: tamaño declarado vs real inconsistente")
                if pixel_offset < 54 or pixel_offset > file_size:
                    issues.append("BMP: offset de píxeles fuera de rango")
                row_size = ((bpp * width + 31) // 32) * 4
                expected_pixels = row_size * abs(height)
                meta['expected_pixel_bytes'] = expected_pixels
                if file_size < pixel_offset + expected_pixels:
                    issues.append("BMP: tamaño insuficiente para datos")
                f.seek(0)
                first_chunk = f.read(4096)
                if b'JFIF' in first_chunk or first_chunk.startswith(
                        b'\xFF\xD8'):
                    issues.append("BMP: contiene firma JPEG (posible disfraz)")
                if b'PNG' in first_chunk[0:64]:
                    issues.append("BMP: contiene firma PNG inesperada")
                nulls_header = first_chunk[54:256].count(0)
                meta['null_bytes_header_region'] = nulls_header
                if nulls_header > 180:
                    issues.append("BMP: relleno excesivo en cabecera")
            ok = True
            for i in issues:
                if any(term in i for term in [
                        "inconsistente", "firma JPEG", "firma PNG", "offset",
                        "encabezado incompleto", "firma BM ausente"
                ]):
                    ok = False
                    break
            return ok, issues, meta
        except Exception as e:
            issues.append(f"BMP: error analizando ({e})")
            return False, issues, meta

    def _analyze_image_steganography(self, file_path: str) -> Dict:
        """Análisis completo de esteganografía en imágenes"""
        results = {
            'has_steganography': False,
            'confidence': 0.0,
            'warnings': [],
            'details': {}
        }

        confidence_scores = []

        # 1. Detección LSB
        lsb_detected, lsb_confidence = self.stego_detector.detect_lsb_steganography(
            file_path)
        if lsb_detected:
            results['warnings'].append(
                f"Posible esteganografía LSB ({lsb_confidence:.1%})")
            confidence_scores.append(lsb_confidence)
        complexity_info = self.stego_detector.compute_image_complexity(
            file_path)
        seq_metrics = self.stego_detector.lsb_sequence_metrics(file_path)
        results['details']['lsb_analysis'] = {
            'detected': lsb_detected,
            'confidence': lsb_confidence,
            'complexity': complexity_info,
            'sequence_metrics': seq_metrics
        }

        # 2. Prueba Chi-cuadrado
        chi_detected, chi_confidence = self.stego_detector.chi_square_test(
            file_path)
        if chi_detected:
            results['warnings'].append(
                f"Anomalía estadística detectada ({chi_confidence:.1%})")
            confidence_scores.append(chi_confidence)
        results['details']['chi_square'] = {
            'detected': chi_detected,
            'confidence': chi_confidence
        }

        # 3. Análisis de frecuencia
        freq_detected, freq_confidence = self.stego_detector.frequency_domain_analysis(
            file_path)
        if freq_detected:
            results['warnings'].append(
                f"Anomalías en dominio de frecuencia ({freq_confidence:.1%})")
            confidence_scores.append(freq_confidence)
        results['details']['frequency_analysis'] = {
            'detected': freq_detected,
            'confidence': freq_confidence
        }

        # 3.5. Análisis de entropía específico para la imagen
        entropy_detected, entropy_confidence = self.stego_detector.entropy_analysis(
            file_path)
        if entropy_detected:
            results['warnings'].append(
                f"Entropía anormalmente alta ({entropy_confidence:.1%})")
            confidence_scores.append(entropy_confidence)
        results['details']['entropy_analysis'] = {
            'detected': entropy_detected,
            'confidence': entropy_confidence
        }

        # 4. Intentar extraer mensaje con Stegano (si está disponible)
        if HAS_STEGANO:
            try:
                secret = lsb.reveal(file_path)
                if secret and len(secret) > 10:
                    results['warnings'].append(
                        "MENSAJE OCULTO EXTRAÍDO CON ÉXITO")
                    results['has_steganography'] = True
                    confidence_scores.append(1.0)
                    results['details']['stegano_extraction'] = True
            except Exception:
                results['details']['stegano_extraction'] = False

        # 4.5 Intentar con steghide (herramienta externa) si está presente
        try:
            steghide_detected, steghide_out = self.stego_detector.check_steghide(
                file_path)
            results['details']['steghide'] = {
                'detected':
                bool(steghide_detected),
                'output':
                steghide_out
                if isinstance(steghide_out, str) else str(steghide_out)
            }
            if steghide_detected:
                results['warnings'].append(
                    'Steghide: datos embebidos detectados')
                confidence_scores.append(0.9)
        except Exception as e:
            logger.debug(f"steghide check exception: {e}")

        # 4.6 Análisis con sharp (Node) si está disponible (script en tools/sharp_analyze.js)
        try:
            sharp_info = self.stego_detector.run_sharp_analysis(file_path)
            results['details']['sharp_analysis'] = sharp_info
            # Si sharp reporta alta entropía por canal, incrementar confianza de entropía
            if isinstance(sharp_info, dict) and sharp_info.get('ok'):
                stats = sharp_info.get('stats', {})
                ent_list = stats.get('channel_entropy') or []
                if ent_list and max(ent_list) > 7.7:
                    results['warnings'].append(
                        'Sharp: entropía por canal elevada')
                    confidence_scores.append(0.4)
        except Exception as e:
            logger.debug(f"sharp check exception: {e}")

        # 4.7 Análisis de entropía criptográfica adicional (compresibilidad / chi)
        try:
            crypto_info = self.stego_detector.crypto_entropy_analysis(
                file_path)
            results['details']['crypto_entropy'] = crypto_info
            if crypto_info.get('suspicious'):
                results['warnings'].append(
                    'Patrón criptográfico/comprimido detectado (alta entropía, baja compresibilidad)'
                )
                confidence_scores.append(0.6)
            else:
                # Si compresibilidad baja pero entropía no tan alta, añadir señal menor
                if crypto_info.get('compress_ratio',
                                   1.0) > 0.95 and crypto_info.get(
                                       'entropy', 0.0) > 7.4:
                    confidence_scores.append(0.25)
        except Exception as e:
            logger.debug(f"crypto entropy exception: {e}")

        # Sistema de scoring adaptativo sin datos fijos rígidos
        if confidence_scores:
            avg_confidence = float(np.mean(confidence_scores))
            max_confidence = float(max(confidence_scores))
            results['confidence'] = avg_confidence

            # Extraer confianzas individuales
            lsb_section = results['details'].get('lsb_analysis', {})
            lsb_conf = float(lsb_section.get('confidence', 0))
            complexity_info = lsb_section.get('complexity', {})
            comp_score = float(complexity_info.get('complexity_score', 0.5))
            entropy_conf = float(results['details'].get(
                'entropy_analysis', {}).get('confidence', 0))
            chi_conf = float(results['details'].get('chi_square',
                                                    {}).get('confidence', 0))
            freq_conf = float(results['details'].get('frequency_analysis',
                                                     {}).get('confidence', 0))

            confidences = {
                'lsb': lsb_conf,
                'entropy': entropy_conf,
                'chi': chi_conf,
                'freq': freq_conf
            }

            # Peso base ajustado por tipo de señal; se recalibra dinámicamente según dispersión
            # No se usan valores absolutos preestablecidos sino relaciones internas
            base_weights = {
                'lsb': 0.35,
                'entropy': 0.25,
                'chi': 0.20,
                'freq': 0.20
            }

            # Ajuste por fuerza relativa (z-score simple sobre el vector de confianzas >0)
            non_zero = [c for c in confidences.values() if c > 0]
            if non_zero:
                mean_c = np.mean(non_zero)
                std_c = np.std(non_zero) if np.std(non_zero) > 1e-6 else 1.0
                dynamic_weights = {}
                for k, c in confidences.items():
                    if c <= 0:
                        dynamic_weights[k] = 0.0
                        continue
                    z = (c - mean_c) / std_c
                    # Mapear z a factor multiplicativo suavizado
                    factor = 1.0 + np.tanh(z / 2.0) * 0.5
                    dynamic_weights[k] = base_weights[k] * factor
                # Normalizar pesos
                total_w = sum(dynamic_weights.values()) or 1.0
                for k in dynamic_weights:
                    dynamic_weights[k] /= total_w
            else:
                dynamic_weights = {k: v for k, v in base_weights.items()}
                total_w = sum(dynamic_weights.values())
                for k in dynamic_weights:
                    dynamic_weights[k] /= total_w

            # Calcular score compuesto
            composite_score = 0.0
            method_flags = 0
            strong_flags = 0
            for k, c in confidences.items():
                w = dynamic_weights.get(k, 0.0)
                composite_score += c * w
                # Determinar si el método es positivo usando umbral relativo: > (media - 20%)
                if non_zero:
                    rel_threshold = mean_c * 0.8
                else:
                    rel_threshold = 0.3
                if c > rel_threshold:
                    method_flags += 1
                if c > (mean_c + (std_c if non_zero else 0.3)):
                    strong_flags += 1

            # Incorporar extracción directa si existe

            # Extracción exitosa de mensaje - evidencia definitiva
            if 'stegano_extraction' in results['details'] and results[
                    'details']['stegano_extraction']:
                results['has_steganography'] = True
                results['warnings'].append(
                    "Mensaje oculto extraído exitosamente")
                composite_score = max(composite_score, 0.95)
                strong_flags += 1

            # Criterios de detección rebalanceados para detectar steganografía real
            else:
                # Usar composite_score y conteos relativos en lugar de umbrales fijos
                # Reglas dinámicas:
                #  - Si hay >=2 métodos por encima del umbral relativo y al menos 1 fuerte -> stego
                #  - O si composite_score > media_conf + std/2
                #  - O LSB moderado junto con entropía estable elevada
                mean_conf_all = avg_confidence
                std_conf_all = float(np.std(confidence_scores)) if len(
                    confidence_scores) > 1 else 0.0
                dynamic_gate = mean_conf_all + std_conf_all * 0.5
                # Caso especial: alta entropía + baja LSB + baja complejidad -> sospechoso
                entropy_high_pattern = entropy_conf > 0.55 and lsb_conf < 0.1 and comp_score < 0.65
                if entropy_high_pattern:
                    method_flags += 1
                    results['warnings'].append(
                        "Patrón de entropía alta con LSB plano en imagen de complejidad moderada"
                    )

                if (
                        method_flags >= 2 and strong_flags >= 1
                ) or composite_score > dynamic_gate or entropy_high_pattern:
                    results['has_steganography'] = True
                    results['warnings'].append(
                        f"Detección combinada consistente (métodos={method_flags}, fuertes={strong_flags}, score={composite_score:.2f})"
                    )
                elif lsb_conf > 0.18 and entropy_conf > mean_conf_all * 0.9 and composite_score > mean_conf_all * 1.1:
                    results['has_steganography'] = True
                    results['warnings'].append(
                        f"Patrón LSB + entropía correlacionados (LSB={lsb_conf:.1%}, ENT={entropy_conf:.1%})"
                    )

            # Registrar detalles de scoring
            results['details']['scoring'] = {
                'composite_score': composite_score,
                'method_flags': method_flags,
                'strong_flags': strong_flags,
                'dynamic_gate': dynamic_gate if confidence_scores else 0.0,
                'weights': dynamic_weights
            }

            # Debug info actualizado
            results['details']['detected_methods'] = method_flags
            results['details']['strong_indicators'] = strong_flags

        else:
            results['confidence'] = 0.0

        return results

    def _analyze_metadata(self, file_path: str, file_type: str) -> List[str]:
        """Analiza metadatos en busca de información sospechosa"""
        issues = []

        if not HAS_PIL or file_type != 'image':
            return issues

        try:
            img = Image.open(file_path)

            # Verificar EXIF
            if hasattr(img, 'getexif'):
                exif = img.getexif()
                if exif:
                    suspicious_tags = [
                        'Software', 'Comment', 'UserComment',
                        'ImageDescription'
                    ]
                    for tag_id, value in exif.items():
                        if tag_id in suspicious_tags:
                            if isinstance(value, str):
                                # Buscar patrones sospechosos
                                if any(pattern in value.lower()
                                       for pattern in [
                                           'script', 'eval', 'exec', 'base64',
                                           'stego'
                                       ]):
                                    issues.append(
                                        f"Metadato sospechoso en EXIF: {tag_id}"
                                    )

            # Verificar otros metadatos
            if hasattr(img, 'info'):
                for key, value in img.info.items():
                    if isinstance(value, str) and len(value) > 1000:
                        issues.append(f"Metadato excesivamente largo: {key}")

                    # Verificar si hay datos base64
                    if isinstance(value, str) and 'base64' in value.lower():
                        issues.append(
                            f"Posibles datos codificados en metadato: {key}")

        except Exception as e:
            logger.error(f"Error analizando metadatos: {e}")

        return issues

    def _verify_file_structure(self, file_path: str, mime_type: str) -> bool:
        """Verifica la estructura interna del archivo"""
        try:
            if mime_type and mime_type.startswith('image/'):
                if HAS_PIL:
                    if mime_type == 'image/bmp':
                        try:
                            with open(file_path, 'rb') as f:
                                header = f.read(54)
                                if len(header) < 54 or header[0:2] != b'BM':
                                    return False
                                file_size = int.from_bytes(header[2:6],
                                                           'little',
                                                           signed=False)
                                pixel_offset = int.from_bytes(header[10:14],
                                                              'little',
                                                              signed=False)
                                width = int.from_bytes(header[18:22],
                                                       'little',
                                                       signed=True)
                                height = int.from_bytes(header[22:26],
                                                        'little',
                                                        signed=True)
                                planes = int.from_bytes(header[26:28],
                                                        'little',
                                                        signed=False)
                                bpp = int.from_bytes(header[28:30],
                                                     'little',
                                                     signed=False)
                                if planes != 1 or bpp not in (1, 4, 8, 16, 24,
                                                              32):
                                    return False
                                if width <= 0 or abs(height) <= 0:
                                    return False
                                real_size = os.path.getsize(file_path)
                                if abs(real_size - file_size) > max(
                                        512, file_size * 0.02):
                                    return False
                                if pixel_offset < 54 or pixel_offset > file_size:
                                    return False
                        except Exception:
                            return False
                    img = Image.open(file_path)
                    img.verify()
                    return True

            # Para otros tipos, verificación básica
            with open(file_path, 'rb') as f:
                header = f.read(512)
                # Verificar que no sea un archivo vacío o corrupto
                return len(header) > 0

        except Exception:
            return False

    def _get_mime_type(self, file_path: str, original_filename: str) -> str:
        """Obtiene el tipo MIME real del archivo"""
        if HAS_MAGIC:
            try:
                return magic.from_file(file_path, mime=True)
            except:
                pass

        mime_type, _ = mimetypes.guess_type(original_filename)
        return mime_type or 'application/octet-stream'

    def _get_file_category(self, mime_type: str) -> str:
        """Obtiene la categoría del archivo basada en MIME type"""
        # Preferir coincidencias explícitas
        for category, types in self.allowed_mime_types.items():
            if mime_type in types:
                return category
        # Fallback: cualquier mime que empiece con 'image/' tratarla como imagen
        if mime_type and mime_type.startswith('image/'):
            return 'image'
        return 'unknown'

    def sanitize_image(self, input_path: str, output_path: str) -> bool:
        """
        Sanitiza una imagen eliminando metadatos y re-encoding
        """
        if not HAS_PIL:
            return False

        try:
            # Abrir imagen
            img = Image.open(input_path)

            # Convertir a RGB si es necesario (elimina canal alfa)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Crear fondo blanco
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(
                    img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Guardar sin metadatos
            img.save(output_path, 'JPEG', quality=85, optimize=True, exif=b'')

            logger.info(f"Imagen sanitizada guardada en: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error sanitizando imagen: {e}")
            return False


# Función helper para uso directo
def validate_uploaded_file(file_path: str,
                           original_filename: str,
                           auto_sanitize: bool = True) -> Dict[str, Any]:
    """
    Función principal para validar archivos subidos
    
    Args:
        file_path: Ruta al archivo temporal
        original_filename: Nombre original del archivo
        auto_sanitize: Si sanitizar automáticamente imágenes sospechosas
    
    Returns:
        Diccionario con resultados de validación
    """
    validator = EnhancedFileSecurityValidator()
    report = validator.validate_file(file_path, original_filename)

    result = {
        'is_safe': report.is_safe,
        'threat_level': report.threat_level.value,
        'confidence': report.confidence,
        'issues': report.issues,
        'warnings': report.warnings,
        'recommendations': report.recommendations,
        'metadata': report.metadata
    }

    # Si es una imagen y necesita sanitización
    if (auto_sanitize and report.metadata.get('needs_sanitization')
            and report.threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW]):

        sanitized_path = file_path.replace('.', '_sanitized.')
        if validator.sanitize_image(file_path, sanitized_path):
            result['sanitized_file'] = sanitized_path
            result['message'] = "Archivo sanitizado exitosamente"

    return result


if __name__ == "__main__":
    # Ejemplo de uso
    import sys

    if len(sys.argv) < 2:
        print("Uso: python enhanced_file_security.py <archivo>")
        sys.exit(1)

    test_file = sys.argv[1]
    print(f"\n🔍 Analizando: {test_file}\n")

    result = validate_uploaded_file(test_file, os.path.basename(test_file))

    print(f"✅ Seguro: {result['is_safe']}")
    print(f"⚠️  Nivel de amenaza: {result['threat_level']}")
    print(f"📊 Confianza: {result['confidence']:.1%}")

    if result['issues']:
        print(f"\n❌ Problemas encontrados:")
        for issue in result['issues']:
            print(f"  - {issue}")

    if result['warnings']:
        print(f"\n⚠️  Advertencias:")
        for warning in result['warnings']:
            print(f"  - {warning}")

    print(f"\n💡 Recomendaciones:")
    for rec in result['recommendations']:
        print(f"  - {rec}")

    if 'sanitized_file' in result:
        print(
            f"\n✨ Archivo sanitizado guardado en: {result['sanitized_file']}")
