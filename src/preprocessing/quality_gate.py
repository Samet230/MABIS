from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Final, List, Optional, Tuple, Union
import cv2
import numpy as np

from src.utils.config import (
    DEFAULT_LAPLACIAN_BLUR_THRESHOLD,
    MIN_IMAGE_DIMENSIONS,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
)
from src.utils.logger import GetLogger

loggerInstance = GetLogger("QualityGate")

# Kalite kapısı eşik değerleri ve sabitleri
DEFAULT_MIN_BRIGHTNESS: Final[float] = 40.0
DEFAULT_MAX_BRIGHTNESS: Final[float] = 225.0
DEFAULT_MIN_CONTRAST_STD: Final[float] = 20.0
DEFAULT_MIN_ROI_COVERAGE_RATIO: Final[float] = 0.15
DEFAULT_MAX_ASPECT_RATIO: Final[float] = 3.0


@dataclass
class QualityAssessmentResult:
    """Kalite kontrol sonucunu ve ayrıntılı tanısal metrikleri tutan veri sınıfı."""

    isPassed: bool
    rejectionReasons: List[str] = field(default_factory=list)
    blurScore: float = 0.0
    meanBrightness: float = 0.0
    contrastStd: float = 0.0
    imageWidth: int = 0
    imageHeight: int = 0
    aspectRatio: float = 1.0

    def ToDictionary(self) -> Dict[str, Union[bool, List[str], float, int]]:
        """Sonuçları sözlük biçimine dönüştürür."""
        return {
            "isPassed": self.isPassed,
            "rejectionReasons": self.rejectionReasons,
            "blurScore": round(self.blurScore, 2),
            "meanBrightness": round(self.meanBrightness, 2),
            "contrastStd": round(self.contrastStd, 2),
            "imageWidth": self.imageWidth,
            "imageHeight": self.imageHeight,
            "aspectRatio": round(self.aspectRatio, 2),
        }


class QualityGate:
    """FR-01 standardına uygun biyometrik görüntü kalite denetleyicisi."""

    def __init__(
        self,
        blurThreshold: float = DEFAULT_LAPLACIAN_BLUR_THRESHOLD,
        minBrightness: float = DEFAULT_MIN_BRIGHTNESS,
        maxBrightness: float = DEFAULT_MAX_BRIGHTNESS,
        minContrastStd: float = DEFAULT_MIN_CONTRAST_STD,
        minDimensions: Tuple[int, int] = MIN_IMAGE_DIMENSIONS,
        maxAspectRatio: float = DEFAULT_MAX_ASPECT_RATIO,
    ) -> None:
        """Kalite kapısı parametrelerini başlatır."""
        self.blurThreshold = blurThreshold
        self.minBrightness = minBrightness
        self.maxBrightness = maxBrightness
        self.minContrastStd = minContrastStd
        self.minDimensions = minDimensions
        self.maxAspectRatio = maxAspectRatio

    @staticmethod
    def CalculateLaplacianBlurScore(grayImage: np.ndarray) -> float:
        """Görüntünün Laplacian operatörü varyansını (netlik skorunu) hesaplar."""
        laplacianMatrix = cv2.Laplacian(grayImage, cv2.CV_64F)
        return float(laplacianMatrix.var())

    @staticmethod
    def ConvertToGrayscale(imageMatrix: np.ndarray) -> np.ndarray:
        """Girdi matrisini güvenli şekilde tek kanallı gri seviyeye dönüştürür."""
        if imageMatrix.ndim == 2:
            return imageMatrix
        elif imageMatrix.ndim == 3 and imageMatrix.shape[2] == 3:
            return cv2.cvtColor(imageMatrix, cv2.COLOR_BGR2GRAY)
        elif imageMatrix.ndim == 3 and imageMatrix.shape[2] == 4:
            return cv2.cvtColor(imageMatrix, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError(f"Desteklenmeyen kanal formatı: {imageMatrix.shape}")

    def AssessQuality(
        self,
        inputImage: np.ndarray,
    ) -> QualityAssessmentResult:
        """Görüntüyü tüm kalite kriterlerine göre denetler.

        Args:
            inputImage: Renkli veya gri seviye görüntü matrisi.

        Returns:
            QualityAssessmentResult: Denetim sonucu ve tespit edilen hatalar.
        """
        if inputImage is None or inputImage.size == 0:
            return QualityAssessmentResult(
                isPassed=False,
                rejectionReasons=["Görüntü verisi boş veya geçersiz."],
            )

        rejectionReasonsList: List[str] = []
        imageHeight, imageWidth = inputImage.shape[:2]

        # 1. Çözünürlük ve boyut kontrolü
        minRequiredWidth, minRequiredHeight = self.minDimensions
        if imageWidth < minRequiredWidth or imageHeight < minRequiredHeight:
            rejectionReasonsList.append(
                f"Yetersiz çözünürlük: ({imageWidth}x{imageHeight}). "
                f"Asgari gereksinim: ({minRequiredWidth}x{minRequiredHeight})."
            )

        # 2. En/Boy oranı kontrolü (aşırı basık veya dar açılı çekimlerin elenmesi)
        longerSide = max(imageWidth, imageHeight)
        shorterSide = max(1, min(imageWidth, imageHeight))
        computedAspectRatio = float(longerSide / shorterSide)
        if computedAspectRatio > self.maxAspectRatio:
            rejectionReasonsList.append(
                f"Aşırı orantısız kadraj en/boy oranı: {computedAspectRatio:.2f} > {self.maxAspectRatio}."
            )

        try:
            grayMatrix = self.ConvertToGrayscale(inputImage)
        except Exception as conversionException:
            return QualityAssessmentResult(
                isPassed=False,
                rejectionReasons=[f"Renk uzayı dönüşüm hatası: {conversionException}"],
                imageWidth=imageWidth,
                imageHeight=imageHeight,
                aspectRatio=computedAspectRatio,
            )

        # 3. Bulanıklık (Blur) kontrolü
        calculatedBlurScore = self.CalculateLaplacianBlurScore(grayMatrix)
        if calculatedBlurScore < self.blurThreshold:
            rejectionReasonsList.append(
                f"Görüntü bulanık (Laplacian varyansı: {calculatedBlurScore:.1f} < {self.blurThreshold}). "
                "Lütfen kamerayı sabit tutup odaklayarak tekrar çekiniz."
            )

        # 4. Pozlama / Parlaklık ve kontrast kontrolü
        meanPixelBrightness = float(np.mean(grayMatrix))
        contrastStandardDeviation = float(np.std(grayMatrix))

        if meanPixelBrightness < self.minBrightness:
            rejectionReasonsList.append(
                f"Görüntü aşırı karanlık / yetersiz aydınlatılmış (ortalama: {meanPixelBrightness:.1f} < {self.minBrightness})."
            )
        elif meanPixelBrightness > self.maxBrightness:
            rejectionReasonsList.append(
                f"Görüntü aşırı parlak / pozlama patlamış (ortalama: {meanPixelBrightness:.1f} > {self.maxBrightness})."
            )

        if contrastStandardDeviation < self.minContrastStd:
            rejectionReasonsList.append(
                f"Görüntü kontrastı yetersiz (standart sapma: {contrastStandardDeviation:.1f} < {self.minContrastStd})."
            )

        isQualityPassed = len(rejectionReasonsList) == 0

        return QualityAssessmentResult(
            isPassed=isQualityPassed,
            rejectionReasons=rejectionReasonsList,
            blurScore=calculatedBlurScore,
            meanBrightness=meanPixelBrightness,
            contrastStd=contrastStandardDeviation,
            imageWidth=imageWidth,
            imageHeight=imageHeight,
            aspectRatio=computedAspectRatio,
        )


# Singleton varsayılan kalite kapısı
_defaultQualityGate = QualityGate()


def check_quality(
    image: np.ndarray,
    blur_threshold: float = DEFAULT_LAPLACIAN_BLUR_THRESHOLD,
) -> Tuple[bool, str, Dict[str, float]]:
    """ZooID standart modül sözleşmesine uygun kalite kontrol fonksiyonu.

    Args:
        image: Ham görüntü matrisi.
        blur_threshold: Bulanıklık eşiği.

    Returns:
        Tuple[bool, str, Dict[str, float]]: (kabul_edildi_mi, red_sebebi, metrikler_sözlüğü)
    """
    customQualityGate = (
        _defaultQualityGate
        if blur_threshold == DEFAULT_LAPLACIAN_BLUR_THRESHOLD
        else QualityGate(blurThreshold=blur_threshold)
    )
    assessmentResult = customQualityGate.AssessQuality(image)
    joinedReasons = "; ".join(assessmentResult.rejectionReasons) if assessmentResult.rejectionReasons else "OK"
    metricsDictionary = {
        "blur_score": assessmentResult.blurScore,
        "mean_brightness": assessmentResult.meanBrightness,
        "contrast_std": assessmentResult.contrastStd,
        "width": float(assessmentResult.imageWidth),
        "height": float(assessmentResult.imageHeight),
    }
    return assessmentResult.isPassed, joinedReasons, metricsDictionary
