from typing import Final, Tuple
import cv2
import numpy as np

from src.utils.config import ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH
from src.utils.logger import GetLogger

loggerInstance = GetLogger("DogSegmenter")

# Sabitler (Köpek yüzü burun bölgesi oranları)
DEFAULT_NOSE_REGION_Y_MIN_RATIO: Final[float] = 0.40
DEFAULT_NOSE_REGION_Y_MAX_RATIO: Final[float] = 0.85
DEFAULT_NOSE_REGION_X_MIN_RATIO: Final[float] = 0.20
DEFAULT_NOSE_REGION_X_MAX_RATIO: Final[float] = 0.80
MIN_DOG_NOSE_CONTOUR_AREA: Final[float] = 200.0


class DogMuzzleSegmenter:
    """Köpek yüz görüntülerinden burun desenini izole eden segmentasyon modülü."""

    def __init__(
        self,
        targetWidth: int = ROI_TARGET_WIDTH,
        targetHeight: int = ROI_TARGET_HEIGHT,
    ) -> None:
        """Köpek segmentasyon nesnesini başlatır.

        Args:
            targetWidth: Çıktı ROI hedef genişliği.
            targetHeight: Çıktı ROI hedef yüksekliği.
        """
        self.targetWidth = targetWidth
        self.targetHeight = targetHeight

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

    def FallbackProportionalCrop(self, inputImage: np.ndarray) -> np.ndarray:
        """Burun konturu bulunamazsa köpek yüzünün alt-orta bölgesini kırpar."""
        imageHeight = inputImage.shape[0]
        imageWidth = inputImage.shape[1]

        centerCoordinateX = imageWidth // 2
        centerCoordinateY = int(imageHeight * 0.62)
        squareSideLength = int(min(imageWidth, imageHeight) * 0.45)

        return self.CropSquareRegion(
            inputImage,
            centerCoordinateX,
            centerCoordinateY,
            squareSideLength,
        )

    def SegmentMuzzle(self, inputImage: np.ndarray) -> np.ndarray:
        """Köpek yüz görüntüsünden burun bölgesini tespit edip $300 \times 300$ ROI döndürür.

        Args:
            inputImage: Ham veya ön işlenmiş görüntü (BGR veya Gri).

        Returns:
            np.ndarray: (300, 300) normalize burun ROI matrisi.
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

            # Köpek yüzünde burun bölgesi alt-orta kısımdadır
            searchYMin = int(imageHeight * DEFAULT_NOSE_REGION_Y_MIN_RATIO)
            searchYMax = int(imageHeight * DEFAULT_NOSE_REGION_Y_MAX_RATIO)
            searchXMin = int(imageWidth * DEFAULT_NOSE_REGION_X_MIN_RATIO)
            searchXMax = int(imageWidth * DEFAULT_NOSE_REGION_X_MAX_RATIO)

            subRegion = grayImage[searchYMin:searchYMax, searchXMin:searchXMax]

            if subRegion.size > 0:
                # Köpek burun derisi genellikle koyudur: Otsu ile koyu bölge tespiti
                _, subThresholded = cv2.threshold(
                    subRegion,
                    0,
                    255,
                    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
                )

                contourList, _ = cv2.findContours(
                    subThresholded,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE,
                )

                bestContour = None
                maxContourArea = 0.0

                for candidateContour in contourList:
                    contourArea = cv2.contourArea(candidateContour)
                    if contourArea < MIN_DOG_NOSE_CONTOUR_AREA:
                        continue
                    if contourArea > maxContourArea:
                        maxContourArea = contourArea
                        bestContour = candidateContour

                if bestContour is not None:
                    contourBoundingBox = cv2.boundingRect(bestContour)
                    # Orijinal koordinatlara geri dönüştür
                    centerCoordinateX = searchXMin + contourBoundingBox[0] + contourBoundingBox[2] // 2
                    centerCoordinateY = searchYMin + contourBoundingBox[1] + contourBoundingBox[3] // 2
                    squareSideLength = int(
                        max(contourBoundingBox[2], contourBoundingBox[3]) * 1.4
                    )
                    squareSideLength = max(
                        squareSideLength, int(min(imageWidth, imageHeight) * 0.35)
                    )

                    return self.CropSquareRegion(
                        grayImage,
                        centerCoordinateX,
                        centerCoordinateY,
                        squareSideLength,
                    )

            loggerInstance.debug("Köpek burun konturu bulunamadı; oransal alt-orta kırpma uygulanıyor.")
            return self.FallbackProportionalCrop(grayImage)

        except Exception as segmentationException:
            loggerInstance.error(f"Köpek segmentasyon hatası: {segmentationException}")
            if len(inputImage.shape) == 3:
                grayFallback = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)
            else:
                grayFallback = inputImage
            return self.FallbackProportionalCrop(grayFallback)
