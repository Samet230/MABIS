from typing import Final, Optional, Tuple
import cv2
import numpy as np

from src.utils.config import ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH
from src.utils.logger import GetLogger

loggerInstance = GetLogger("CattleSegmenter")

# Sabitler (Magic number engelleme)
DEFAULT_MIN_CONTOUR_AREA: Final[float] = 400.0
DEFAULT_MORPHOLOGY_KERNEL_SIZE: Final[int] = 5
DEFAULT_CENTER_CROP_RATIO: Final[float] = 0.65


class CattleMuzzleSegmenter:
    """Sığır ve manda burun desenini eşikleme ve morfolojik analizle segmente eder."""

    def __init__(
        self,
        targetWidth: int = ROI_TARGET_WIDTH,
        targetHeight: int = ROI_TARGET_HEIGHT,
        minContourArea: float = DEFAULT_MIN_CONTOUR_AREA,
    ) -> None:
        """Sığır segmentasyon nesnesini başlatır.

        Args:
            targetWidth: Çıktı ROI hedef genişliği.
            targetHeight: Çıktı ROI hedef yüksekliği.
            minContourArea: Dikkate alınacak minimum kontur alanı.
        """
        self.targetWidth = targetWidth
        self.targetHeight = targetHeight
        self.minContourArea = minContourArea
        self.morphologyKernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (DEFAULT_MORPHOLOGY_KERNEL_SIZE, DEFAULT_MORPHOLOGY_KERNEL_SIZE),
        )

    def CropSquareRegion(
        self,
        inputImage: np.ndarray,
        centerCoordinateX: int,
        centerCoordinateY: int,
        squareSideLength: int,
    ) -> np.ndarray:
        """Belirtilen merkez etrafında kare bir bölgeyi sınır aşımı olmadan kırpar ve normalize eder.

        Args:
            inputImage: Kaynak görüntü matrisi.
            centerCoordinateX: Merkez X koordinatı.
            centerCoordinateY: Merkez Y koordinatı.
            squareSideLength: Kırpılacak karenin kenar uzunluğu.

        Returns:
            np.ndarray: Hedef boyutta (targetWidth x targetHeight) kare ROI.
        """
        imageHeight = inputImage.shape[0]
        imageWidth = inputImage.shape[1]

        halfSide = squareSideLength // 2
        boxLeft = max(0, centerCoordinateX - halfSide)
        boxTop = max(0, centerCoordinateY - halfSide)
        boxRight = min(imageWidth, boxLeft + squareSideLength)
        boxBottom = min(imageHeight, boxTop + squareSideLength)

        # Genişlik veya yükseklik sınır dışına taştıysa başlangıç noktasını ayarla
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
        """Kontur tespit edilemediğinde görüntünün merkezinden kare bir ROI çıkarır.

        Args:
            inputImage: Kaynak görüntü matrisi.

        Returns:
            np.ndarray: Merkez kare ROI.
        """
        imageHeight = inputImage.shape[0]
        imageWidth = inputImage.shape[1]
        centerCoordinateX = imageWidth // 2
        centerCoordinateY = imageHeight // 2
        squareSideLength = int(min(imageWidth, imageHeight) * DEFAULT_CENTER_CROP_RATIO)

        return self.CropSquareRegion(
            inputImage,
            centerCoordinateX,
            centerCoordinateY,
            squareSideLength,
        )

    def SegmentMuzzle(self, inputImage: np.ndarray) -> np.ndarray:
        """Girdi görüntüsünden sığır burun desenini izole eder ve normalize kare ROI üretir.

        Args:
            inputImage: Ham veya ön işlenmiş görüntü (BGR veya Gri).

        Returns:
            np.ndarray: (300, 300) boyutunda segmente edilmiş burun ROI matrisi.
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

            # 1. Otsu eşikleme ile burun olukları ve koyu alanları tespit et
            _, binaryThresholded = cv2.threshold(
                grayImage,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
            )

            # 2. Morfolojik temizleme (açma-kapama)
            cleanedBinary = cv2.morphologyEx(
                binaryThresholded,
                cv2.MORPH_CLOSE,
                self.morphologyKernel,
            )
            cleanedBinary = cv2.morphologyEx(
                cleanedBinary,
                cv2.MORPH_OPEN,
                self.morphologyKernel,
            )

            # 3. Konturları bul
            contourList, _ = cv2.findContours(
                cleanedBinary,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            # Görüntünün kenar sınırlarından kaçınmak için merkez 80%'lik alanı kontrol et
            marginHorizontal = int(imageWidth * 0.1)
            marginVertical = int(imageHeight * 0.1)
            centerRegionXMin = marginHorizontal
            centerRegionXMax = imageWidth - marginHorizontal
            centerRegionYMin = marginVertical
            centerRegionYMax = imageHeight - marginVertical

            bestContour = None
            maxContourArea = 0.0

            for candidateContour in contourList:
                contourArea = cv2.contourArea(candidateContour)
                if contourArea < self.minContourArea:
                    continue

                contourBoundingBox = cv2.boundingRect(candidateContour)
                contourCenterX = contourBoundingBox[0] + contourBoundingBox[2] // 2
                contourCenterY = contourBoundingBox[1] + contourBoundingBox[3] // 2

                # Merkez bölgeye yakınlık kontrolü
                isInsideCenterRegion = (
                    centerRegionXMin <= contourCenterX <= centerRegionXMax
                    and centerRegionYMin <= contourCenterY <= centerRegionYMax
                )

                if isInsideCenterRegion and contourArea > maxContourArea:
                    maxContourArea = contourArea
                    bestContour = candidateContour

            if bestContour is not None:
                contourBoundingBox = cv2.boundingRect(bestContour)
                centerCoordinateX = contourBoundingBox[0] + contourBoundingBox[2] // 2
                centerCoordinateY = contourBoundingBox[1] + contourBoundingBox[3] // 2
                squareSideLength = int(
                    max(contourBoundingBox[2], contourBoundingBox[3]) * 1.2
                )
                # Minimum kenar sınırı
                squareSideLength = max(squareSideLength, int(min(imageWidth, imageHeight) * 0.4))
                return self.CropSquareRegion(
                    grayImage,
                    centerCoordinateX,
                    centerCoordinateY,
                    squareSideLength,
                )

            # Belirgin kontur bulunamazsa güvenli merkez kırpma uygula
            loggerInstance.debug("Belirgin sığır burun konturu bulunamadı; merkez kırpma uygulanıyor.")
            return self.FallbackCenterCrop(grayImage)

        except Exception as segmentationException:
            loggerInstance.error(f"Sığır segmentasyon hatası: {segmentationException}")
            if len(inputImage.shape) == 3:
                grayFallback = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)
            else:
                grayFallback = inputImage
            return self.FallbackCenterCrop(grayFallback)
