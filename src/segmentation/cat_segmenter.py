from pathlib import Path
from typing import Final, Optional, Tuple
import cv2
import numpy as np

from src.utils.config import ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH
from src.utils.logger import GetLogger

loggerInstance = GetLogger("CatSegmenter")

CASCADE_PATH_DEFAULT: Final[Path] = (
    Path(__file__).resolve().parent / "cascades" / "haarcascade_frontalcatface.xml"
)
DEFAULT_CAT_FACE_SCALE_FACTOR: Final[float] = 1.1
DEFAULT_CAT_FACE_MIN_NEIGHBORS: Final[int] = 3
DEFAULT_FACE_EXPANSION_RATIO: Final[float] = 1.15


class CatFaceSegmenter:
    """Kedi yüz ve kafa bölgesini Haar cascade ve kontur yöntemleriyle segmente eder."""

    def __init__(
        self,
        targetWidth: int = ROI_TARGET_WIDTH,
        targetHeight: int = ROI_TARGET_HEIGHT,
        cascadeFilePath: Path = CASCADE_PATH_DEFAULT,
    ) -> None:
        """Kedi yüz segmentasyon modülünü başlatır.

        Args:
            targetWidth: Çıktı ROI hedef genişliği.
            targetHeight: Çıktı ROI hedef yüksekliği.
            cascadeFilePath: Kedi yüz Haar cascade xml dosya yolu.
        """
        self.targetWidth = targetWidth
        self.targetHeight = targetHeight
        self.cascadeClassifier: Optional[cv2.CascadeClassifier] = None

        resolvedCascade = Path(cascadeFilePath).resolve()
        if hasattr(cv2, "CascadeClassifier") and resolvedCascade.is_file():
            try:
                self.cascadeClassifier = cv2.CascadeClassifier(str(resolvedCascade))
                if self.cascadeClassifier.empty():
                    loggerInstance.warning(
                        f"Haar cascade dosyası yüklenemedi: {resolvedCascade}"
                    )
                    self.cascadeClassifier = None
            except Exception as cascadeException:
                loggerInstance.warning(
                    f"Cascade başlatma hatası: {cascadeException}"
                )
                self.cascadeClassifier = None
        else:
            loggerInstance.warning(
                f"Kedi yüz cascade kullanılamıyor (Dosya: {resolvedCascade.is_file()}, Destek: {hasattr(cv2, 'CascadeClassifier')})"
            )

    def CropSquareRegion(
        self,
        inputImage: np.ndarray,
        centerCoordinateX: int,
        centerCoordinateY: int,
        squareSideLength: int,
    ) -> np.ndarray:
        """Belirtilen merkez etrafında kare bir bölgeyi sınır aşımı olmadan kırpar ve normalize eder."""
        imageHeight = inputImage.shape[0]
        imageWidth = inputImage.shape[1]

        halfSide = squareSideLength // 2
        boxLeft = max(0, centerCoordinateX - halfSide)
        boxTop = max(0, centerCoordinateY - halfSide)
        boxRight = min(imageWidth, boxLeft + squareSideLength)
        boxBottom = min(imageHeight, boxTop + squareSideLength)

        if (boxRight - boxLeft) < squareSideLength:
            boxLeft = max(0, boxRight - squareSideLength)
        if (boxBottom - boxTop) < squareSideLength:
            boxTop = max(0, boxBottom - squareSideLength)

        croppedRegion = inputImage[boxTop:boxBottom, boxLeft:boxRight]
        resizedRoi = cv2.resize(
            croppedRegion,
            (self.targetWidth, self.targetHeight),
            interpolation=cv2.INTER_AREA if (boxRight - boxLeft) > self.targetWidth else cv2.INTER_CUBIC,
        )
        return resizedRoi

    def FallbackCenterCrop(self, inputImage: np.ndarray) -> np.ndarray:
        """Yüz tespit edilemediğinde görüntünün merkez üst bölgesinden kare bir ROI çıkarır."""
        imageHeight = inputImage.shape[0]
        imageWidth = inputImage.shape[1]

        centerCoordinateX = imageWidth // 2
        centerCoordinateY = int(imageHeight * 0.48)
        squareSideLength = int(min(imageWidth, imageHeight) * 0.70)

        return self.CropSquareRegion(
            inputImage,
            centerCoordinateX,
            centerCoordinateY,
            squareSideLength,
        )

    def SegmentFace(self, inputImage: np.ndarray) -> np.ndarray:
        """Kedi görüntüsünden yüz/kafa bölgesini tespit edip $300 \times 300$ ROI döndürür.

        Args:
            inputImage: Ham veya ön işlenmiş kedi görüntüsü.

        Returns:
            np.ndarray: (300, 300) normalize yüz ROI matrisi.
        """
        if inputImage is None or inputImage.size == 0:
            raise ValueError("Girdi görüntüsü boş veya geçersiz.")

        try:
            if len(inputImage.shape) == 3:
                grayImage = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)
            else:
                grayImage = inputImage

            imageHeight = grayImage.shape[0]
            imageWidth = grayImage.shape[1]

            # 1. Haar Cascade ile yüz tespiti dene
            if self.cascadeClassifier is not None:
                minSizeDimension = max(50, int(min(imageWidth, imageHeight) * 0.15))
                detectedFaces = self.cascadeClassifier.detectMultiScale(
                    grayImage,
                    scaleFactor=DEFAULT_CAT_FACE_SCALE_FACTOR,
                    minNeighbors=DEFAULT_CAT_FACE_MIN_NEIGHBORS,
                    minSize=(minSizeDimension, minSizeDimension),
                )

                if len(detectedFaces) > 0:
                    # En büyük yüz kutusunu seç
                    bestFace = max(
                        detectedFaces,
                        key=lambda rect: rect[2] * rect[3],
                    )
                    faceX, faceY, faceWidth, faceHeight = bestFace

                    centerCoordinateX = faceX + faceWidth // 2
                    centerCoordinateY = faceY + faceHeight // 2
                    squareSideLength = int(
                        max(faceWidth, faceHeight) * DEFAULT_FACE_EXPANSION_RATIO
                    )

                    return self.CropSquareRegion(
                        grayImage,
                        centerCoordinateX,
                        centerCoordinateY,
                        squareSideLength,
                    )

            loggerInstance.debug("Kedi yüz cascade tespiti boş döndü; merkez kırpma uygulanıyor.")
            return self.FallbackCenterCrop(grayImage)

        except Exception as segmentationException:
            loggerInstance.error(f"Kedi yüz segmentasyon hatası: {segmentationException}")
            if len(inputImage.shape) == 3:
                grayFallback = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)
            else:
                grayFallback = inputImage
            return self.FallbackCenterCrop(grayFallback)
