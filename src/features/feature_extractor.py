from typing import Final, Optional
import numpy as np

from src.features.glcm_extractor import GlcmFeatureExtractor
from src.features.keypoint_extractor import KeypointFeatureExtractor
from src.features.lbp_extractor import LbpFeatureExtractor
from src.utils.config import (
    METHOD_GLCM,
    METHOD_LBP,
    METHOD_LBP_GLCM,
    METHOD_ORB,
    METHOD_SIFT,
    VALID_FEATURE_METHODS,
)
from src.utils.logger import GetLogger

loggerInstance = GetLogger("FeatureExtractor")


class UnifiedFeatureExtractor:
    """Tüm klasik öznitelik çıkarıcıları (LBP, GLCM, SIFT, ORB ve Füzyon) yöneten birleşik sınıf."""

    def __init__(self) -> None:
        """Öznitelik çıkarıcı modüllerini başlatır."""
        self.lbpExtractor = LbpFeatureExtractor()
        self.glcmExtractor = GlcmFeatureExtractor()
        self.keypointExtractor = KeypointFeatureExtractor()

    def ExtractFeatures(
        self,
        roiImage: np.ndarray,
        method: str = METHOD_LBP,
    ) -> np.ndarray:
        """Belirtilen yönteme göre öznitelik vektörü veya tanımlayıcı matrisi üretir.

        Args:
            roiImage: (H, W) boyutunda normalize ROI görüntüsü.
            method: 'lbp', 'glcm', 'lbp_glcm', 'sift' veya 'orb'.

        Returns:
            np.ndarray: Çıkarılan öznitelik vektörü veya matrisi.
        """
        if roiImage is None or roiImage.size == 0:
            raise ValueError("ROI görüntüsü boş veya geçersiz.")

        normalizedMethod = method.strip().lower()
        if normalizedMethod not in VALID_FEATURE_METHODS:
            raise ValueError(
                f"Desteklenmeyen öznitelik yöntemi: '{method}'. "
                f"Desteklenenler: {VALID_FEATURE_METHODS}"
            )

        try:
            if normalizedMethod == METHOD_LBP:
                return self.lbpExtractor.ExtractFeatures(roiImage)

            elif normalizedMethod == METHOD_GLCM:
                return self.glcmExtractor.ExtractFeatures(roiImage)

            elif normalizedMethod == METHOD_LBP_GLCM:
                # Öznitelik seviyesinde birleşim (Feature-level fusion)
                lbpVector = self.lbpExtractor.ExtractFeatures(roiImage)
                glcmVector = self.glcmExtractor.ExtractFeatures(roiImage)
                concatenatedVector = np.concatenate([lbpVector, glcmVector])

                # Birleşik L2 normalizasyonu
                vectorNorm = np.linalg.norm(concatenatedVector)
                if vectorNorm > 0.0:
                    concatenatedVector /= vectorNorm
                return concatenatedVector.astype(np.float32)

            elif normalizedMethod == METHOD_SIFT:
                return self.keypointExtractor.ExtractFeatures(roiImage, method="sift")

            elif normalizedMethod == METHOD_ORB:
                return self.keypointExtractor.ExtractFeatures(roiImage, method="orb")

            else:
                raise ValueError(f"İşlenemeyen yöntem: {normalizedMethod}")

        except Exception as extractionException:
            loggerInstance.error(
                f"Öznitelik çıkarım hatası ({method}): {extractionException}"
            )
            raise


# Dokümanlarda tanımlanan standart sözleşme fonksiyonu (ARCHITECTURE.md ve AGENTS.md)
_defaultExtractor = UnifiedFeatureExtractor()


def extract_features(roi: np.ndarray, method: str = METHOD_LBP) -> np.ndarray:
    """ZooID standart modül sözleşmesine uygun öznitelik çıkarım fonksiyonu.

    Args:
        roi: 300x300 normalize edilmiş ROI görüntüsü.
        method: Kullanılacak öznitelik yöntemi ('lbp' | 'glcm' | 'lbp_glcm' | 'sift' | 'orb').

    Returns:
        np.ndarray: Öznitelik vektörü veya tanımlayıcı matrisi.
    """
    return _defaultExtractor.ExtractFeatures(roi, method=method)
