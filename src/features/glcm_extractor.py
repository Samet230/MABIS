from typing import Final, List, Tuple
import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

from src.utils.config import (
    GLCM_ANGLES,
    GLCM_DISTANCES,
    GLCM_GRAY_LEVELS,
    GLCM_PROPERTIES,
)
from src.utils.logger import GetLogger

loggerInstance = GetLogger("GlcmExtractor")


class GlcmFeatureExtractor:
    """GLCM (Gray-Level Co-occurrence Matrix) doku istatistiklerini çıkaran modül."""

    def __init__(
        self,
        grayLevelsCount: int = GLCM_GRAY_LEVELS,
        distances: Tuple[int, ...] = GLCM_DISTANCES,
        angles: Tuple[float, ...] = GLCM_ANGLES,
        properties: Tuple[str, ...] = GLCM_PROPERTIES,
    ) -> None:
        """GLCM çıkarıcısını başlatır.

        Args:
            grayLevelsCount: Gri seviye kuantalama adımı (varsayılan: 16).
            distances: İncelenecek piksel mesafeleri.
            angles: İncelenecek yön açıları (radyan).
            properties: Çıkarılacak istatistiksel öznitelikler.
        """
        self.grayLevelsCount = grayLevelsCount
        self.distances = list(distances)
        self.angles = list(angles)
        self.properties = list(properties)

    def QuantizeGrayscale(self, grayImage: np.ndarray) -> np.ndarray:
        """256 seviyeli görüntüyü belirtilen seviye sayısına (16) kuantalar."""
        scalingFactor = self.grayLevelsCount / 256.0
        quantizedImage = (grayImage * scalingFactor).astype(np.uint8)
        # Sınır taşmalarını engelle
        quantizedImage = np.clip(quantizedImage, 0, self.grayLevelsCount - 1)
        return quantizedImage

    def ExtractFeatures(self, roiImage: np.ndarray) -> np.ndarray:
        """Girdi ROI görüntüsünden normalize GLCM doku istatistik vektörünü çıkarır.

        Args:
            roiImage: (H, W) gri seviye veya BGR ROI matrisi.

        Returns:
            np.ndarray: L2 normalize edilmiş 1D öznitelik vektörü.
        """
        if roiImage is None or roiImage.size == 0:
            raise ValueError("ROI görüntüsü boş veya geçersiz.")

        try:
            if len(roiImage.shape) == 3:
                grayRoi = cv2.cvtColor(roiImage, cv2.COLOR_BGR2GRAY)
            else:
                grayRoi = roiImage

            quantizedRoi = self.QuantizeGrayscale(grayRoi)

            glcmMatrix = graycomatrix(
                quantizedRoi,
                distances=self.distances,
                angles=self.angles,
                levels=self.grayLevelsCount,
                symmetric=True,
                normed=True,
            )

            featureValuesList: List[float] = []

            for propertyName in self.properties:
                propertyMatrix = graycoprops(glcmMatrix, prop=propertyName)
                # Her özellik için tüm mesafe ve açılardaki değerleri ekle
                featureValuesList.extend(propertyMatrix.ravel().tolist())

            featureVector = np.array(featureValuesList, dtype=np.float32)

            # L2 normalizasyonu
            vectorNorm = np.linalg.norm(featureVector)
            if vectorNorm > 0.0:
                featureVector /= vectorNorm

            return featureVector

        except Exception as glcmException:
            loggerInstance.error(f"GLCM öznitelik çıkarımı hatası: {glcmException}")
            raise
