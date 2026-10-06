from typing import Dict, Final
import numpy as np

from src.segmentation.cat_segmenter import CatFaceSegmenter
from src.segmentation.cattle_segmenter import CattleMuzzleSegmenter
from src.segmentation.dog_segmenter import DogMuzzleSegmenter
from src.utils.config import ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH, VALID_SPECIES
from src.utils.image_io import ValidateSpecies
from src.utils.logger import GetLogger

loggerInstance = GetLogger("SegmentationRouter")


class SegmentationRouter:
    """Hayvan türüne göre uygun ROI segmentasyon modülünü çalıştıran yönlendirici sınıf."""

    def __init__(
        self,
        targetWidth: int = ROI_TARGET_WIDTH,
        targetHeight: int = ROI_TARGET_HEIGHT,
    ) -> None:
        """Yönlendiriciyi başlatır ve türe özel segmentasyon nesnelerini hazırlar."""
        self.targetWidth = targetWidth
        self.targetHeight = targetHeight

        self.cattleSegmenter = CattleMuzzleSegmenter(
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
        self.dogSegmenter = DogMuzzleSegmenter(
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )
        self.catSegmenter = CatFaceSegmenter(
            targetWidth=targetWidth,
            targetHeight=targetHeight,
        )

    def SegmentRoi(self, inputImage: np.ndarray, speciesName: str) -> np.ndarray:
        """Belirtilen türe göre uygun segmentasyon algoritmasını çalıştırır.

        Args:
            inputImage: Ham veya ön işlenmiş girdi görüntüsü.
            speciesName: Hedef tür adı ('cattle', 'dog', 'cat').

        Returns:
            np.ndarray: (300, 300) normalize edilmiş ROI matrisi.
        """
        if inputImage is None or inputImage.size == 0:
            raise ValueError("Girdi görüntüsü boş veya None.")

        if not ValidateSpecies(speciesName):
            raise ValueError(
                f"Geçersiz tür '{speciesName}'. Desteklenenler: {VALID_SPECIES}"
            )

        normalizedSpecies = speciesName.strip().lower()

        try:
            if normalizedSpecies == "cattle":
                croppedRoi = self.cattleSegmenter.SegmentMuzzle(inputImage)
            elif normalizedSpecies == "dog":
                croppedRoi = self.dogSegmenter.SegmentMuzzle(inputImage)
            elif normalizedSpecies == "cat":
                croppedRoi = self.catSegmenter.SegmentFace(inputImage)
            else:
                raise ValueError(f"Bilinmeyen tür dalı: {normalizedSpecies}")

            # Boyut güvencesi
            if croppedRoi.shape[:2] != (self.targetHeight, self.targetWidth):
                import cv2
                croppedRoi = cv2.resize(
                    croppedRoi,
                    (self.targetWidth, self.targetHeight),
                )

            return croppedRoi

        except Exception as routerException:
            loggerInstance.error(
                f"Segmentasyon yönlendiricisinde hata ({speciesName}): {routerException}"
            )
            raise


# Dokümanlarda tanımlanan standart sözleşme fonksiyonu (ARCHITECTURE.md ve AGENTS.md)
_defaultRouter = SegmentationRouter()


def segment_roi(image: np.ndarray, species: str) -> np.ndarray:
    """ZooID standart modül sözleşmesine uygun segmentasyon fonksiyonu.

    Args:
        image: Ham veya ön işlenmiş görüntü matrisi.
        species: Tür adı ('cattle' | 'dog' | 'cat').

    Returns:
        np.ndarray: (300, 300) normalize edilmiş ROI görüntüsü.
    """
    return _defaultRouter.SegmentRoi(image, species)
