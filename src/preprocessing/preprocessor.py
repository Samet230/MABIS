from typing import Final, Optional, Tuple
import cv2
import numpy as np

from src.utils.logger import GetLogger

loggerInstance = GetLogger("Preprocessor")

# Ön işleme parametre sabitleri (Magic numbers engellendi)
DEFAULT_CLAHE_CLIP_LIMIT: Final[float] = 2.0
DEFAULT_CLAHE_TILE_GRID: Final[Tuple[int, int]] = (8, 8)
DEFAULT_MEDIAN_KERNEL_SIZE: Final[int] = 3


class ImagePreprocessor:
    """Görüntü kalitesini artırmak için klasik ön işleme tekniklerini (CLAHE, filtreleme) uygular."""

    def __init__(
        self,
        claheClipLimit: float = DEFAULT_CLAHE_CLIP_LIMIT,
        claheTileGridSize: Tuple[int, int] = DEFAULT_CLAHE_TILE_GRID,
        medianKernelSize: int = DEFAULT_MEDIAN_KERNEL_SIZE,
    ) -> None:
        """Ön işleyiciyi başlatır.

        Args:
            claheClipLimit: Kontrast sınırlama eşiği.
            claheTileGridSize: Izgara hücre boyutu (genişlik, yükseklik).
            medianKernelSize: Medyan filtre çekirdek boyutu (tek sayı olmalıdır).
        """
        self.claheClipLimit = claheClipLimit
        self.claheTileGridSize = claheTileGridSize
        # Medyan filtre çekirdeği tek sayı olmalıdır
        self.medianKernelSize = (
            medianKernelSize if medianKernelSize % 2 != 0 else medianKernelSize + 1
        )
        self.claheObject = cv2.createCLAHE(
            clipLimit=self.claheClipLimit,
            tileGridSize=self.claheTileGridSize,
        )

    def ConvertToGrayscale(self, inputImage: np.ndarray) -> np.ndarray:
        """Görüntüyü gerekiyorsa gri seviyeye dönüştürür.

        Args:
            inputImage: BGR veya tek kanallı gri matris.

        Returns:
            np.ndarray: Tek kanallı gri seviye matrisi.
        """
        if len(inputImage.shape) == 2:
            return inputImage

        if len(inputImage.shape) == 3:
            channelCount = inputImage.shape[2]
            if channelCount == 3:
                return cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)
            elif channelCount == 4:
                return cv2.cvtColor(inputImage, cv2.COLOR_BGRA2GRAY)

        raise ValueError(f"Desteklenmeyen kanal sayısı: {inputImage.shape}")

    def ApplyClahe(self, grayImage: np.ndarray) -> np.ndarray:
        """Gri seviye görüntüye CLAHE ile kontrast iyileştirmesi uygular.

        Args:
            grayImage: Tek kanallı gri seviye matrisi.

        Returns:
            np.ndarray: Kontrastı dengelenmiş gri görüntü.
        """
        return self.claheObject.apply(grayImage)

    def ApplyMedianFilter(self, grayImage: np.ndarray) -> np.ndarray:
        """Tuz-biber gürültüsünü gidermek için medyan filtresi uygular.

        Args:
            grayImage: Gri seviye matrisi.

        Returns:
            np.ndarray: Gürültüsü azaltılmış görüntü.
        """
        return cv2.medianBlur(grayImage, self.medianKernelSize)

    def ProcessImage(self, inputImage: np.ndarray) -> np.ndarray:
        """Ön işleme adımlarını (Gri dönüşüm -> CLAHE -> Medyan filtre) sırayla uygular.

        Args:
            inputImage: Ham girdi matrisi.

        Returns:
            np.ndarray: Ön işlenmiş normalize edilmiş gri seviye matrisi.
        """
        if inputImage is None or inputImage.size == 0:
            raise ValueError("Girdi görüntüsü boş veya None.")

        try:
            grayImage = self.ConvertToGrayscale(inputImage)
            contrastEnhancedImage = self.ApplyClahe(grayImage)
            filteredImage = self.ApplyMedianFilter(contrastEnhancedImage)
            return filteredImage
        except Exception as processingException:
            loggerInstance.error(f"Ön işleme sırasında hata: {processingException}")
            raise


# Dokümanlarda tanımlanan standart sözleşme fonksiyonu (ARCHITECTURE.md ve AGENTS.md)
_defaultPreprocessor = ImagePreprocessor()


def preprocess(image: np.ndarray) -> np.ndarray:
    """ZooID standart modül sözleşmesine uygun ön işleme fonksiyonu.

    Args:
        image: Ham girdi görüntüsü (BGR veya Gri).

    Returns:
        np.ndarray: Ön işlenmiş gri seviye matrisi.
    """
    return _defaultPreprocessor.ProcessImage(image)
