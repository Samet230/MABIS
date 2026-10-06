from pathlib import Path
from typing import Optional, Tuple, Union
import cv2
import numpy as np

from src.utils.config import (
    DEFAULT_LAPLACIAN_BLUR_THRESHOLD,
    MIN_IMAGE_DIMENSIONS,
    VALID_SPECIES,
)
from src.utils.logger import GetLogger

loggerInstance = GetLogger("ImageIO")


def ReadImage(
    imagePath: Union[str, Path],
    asGrayscale: bool = False,
) -> Optional[np.ndarray]:
    """Görüntüyü diskten güvenli şekilde okur (Windows Unicode karakter uyumlu).

    Args:
        imagePath: Okunacak görüntü dosyasının yolu.
        asGrayscale: True ise doğrudan gri seviye olarak okur.

    Returns:
        Optional[np.ndarray]: Başarılı ise görüntü matrisi, aksi halde None.
    """
    resolvedPath = Path(imagePath).resolve()
    if not resolvedPath.is_file():
        loggerInstance.error(f"Görüntü dosyası bulunamadı: {resolvedPath}")
        return None

    try:
        # np.fromfile ve cv2.imdecode kullanımı Windows Türkçe karakter/boşluk sorunlarını engeller
        fileBytes = np.fromfile(str(resolvedPath), dtype=np.uint8)
        readFlag = cv2.IMREAD_GRAYSCALE if asGrayscale else cv2.IMREAD_COLOR
        decodedImage = cv2.imdecode(fileBytes, readFlag)

        if decodedImage is None or decodedImage.size == 0:
            loggerInstance.warning(f"Görüntü verisi çözülemedi veya boş: {resolvedPath}")
            return None

        return decodedImage
    except Exception as readException:
        loggerInstance.error(f"Görüntü okuma hatası ({resolvedPath}): {readException}")
        return None


def SaveImage(
    outputPath: Union[str, Path],
    imageArray: np.ndarray,
) -> bool:
    """Görüntüyü diske güvenli şekilde kaydeder (Windows Unicode karakter uyumlu).

    Args:
        outputPath: Kaydedilecek hedef dosya yolu.
        imageArray: Kaydedilecek numpy matrisi.

    Returns:
        bool: İşlem başarılı ise True, aksi halde False.
    """
    if imageArray is None or imageArray.size == 0:
        loggerInstance.error("Kaydedilecek görüntü matrisi boş veya geçersiz.")
        return False

    resolvedPath = Path(outputPath).resolve()
    try:
        resolvedPath.parent.mkdir(parents=True, exist_ok=True)
        fileExtension = resolvedPath.suffix.lower()
        if not fileExtension:
            fileExtension = ".jpg"
            resolvedPath = resolvedPath.with_suffix(fileExtension)

        encodingSuccess, encodedBytes = cv2.imencode(fileExtension, imageArray)
        if not encodingSuccess:
            loggerInstance.error(f"Görüntü format kodlama başarısız oldu: {resolvedPath}")
            return False

        encodedBytes.tofile(str(resolvedPath))
        return True
    except Exception as saveException:
        loggerInstance.error(f"Görüntü kaydetme hatası ({resolvedPath}): {saveException}")
        return False


def CalculateLaplacianVariance(imageArray: np.ndarray) -> float:
    """Görüntünün Laplacian varyansını (odak/bulanıklık skoru) hesaplar.

    Düşük varyans görüntünün bulanık olduğunu, yüksek varyans ise keskin olduğunu gösterir.

    Args:
        imageArray: BGR veya gri seviye görüntü matrisi.

    Returns:
        float: Laplacian varyans skoru.
    """
    if imageArray is None or imageArray.size == 0:
        return 0.0

    try:
        if len(imageArray.shape) == 3:
            grayImage = cv2.cvtColor(imageArray, cv2.COLOR_BGR2GRAY)
        else:
            grayImage = imageArray

        laplacianMatrix = cv2.Laplacian(grayImage, cv2.CV_64F)
        varianceScore = float(laplacianMatrix.var())
        return varianceScore
    except Exception as varianceException:
        loggerInstance.error(f"Laplacian varyansı hesaplanamadı: {varianceException}")
        return 0.0


def CheckImageQuality(
    imageArray: np.ndarray,
    blurThreshold: float = DEFAULT_LAPLACIAN_BLUR_THRESHOLD,
    minResolution: Tuple[int, int] = MIN_IMAGE_DIMENSIONS,
) -> Tuple[bool, str, float]:
    """Görüntünün çözünürlük ve netlik kriterlerini karşılayıp karşılamadığını denetler.

    Args:
        imageArray: Denetlenecek görüntü.
        blurThreshold: Minimum kabul edilebilir Laplacian varyansı.
        minResolution: (minimumGenişlik, minimumYükseklik) demeti.

    Returns:
        Tuple[bool, str, float]: (UygunMu, Açıklama, HesaplananVaryans).
    """
    if imageArray is None or imageArray.size == 0:
        return False, "Görüntü boş", 0.0

    imageHeight = imageArray.shape[0]
    imageWidth = imageArray.shape[1]
    minRequiredWidth = minResolution[0]
    minRequiredHeight = minResolution[1]

    if imageWidth < minRequiredWidth or imageHeight < minRequiredHeight:
        rejectionReason = (
            f"Düşük çözünürlük: {imageWidth}x{imageHeight} < {minRequiredWidth}x{minRequiredHeight}"
        )
        return False, rejectionReason, 0.0

    laplacianVariance = CalculateLaplacianVariance(imageArray)
    if laplacianVariance < blurThreshold:
        rejectionReason = (
            f"Bulanık görüntü: Varyans {laplacianVariance:.2f} < Eşik {blurThreshold:.2f}"
        )
        return False, rejectionReason, laplacianVariance

    return True, "Görüntü kalitesi yeterli", laplacianVariance


def ValidateSpecies(speciesName: str) -> bool:
    """Verilen tür adının projede desteklenen türlerden biri olup olmadığını doğrular.

    Args:
        speciesName: Denetlenecek tür ('cattle', 'dog', 'cat').

    Returns:
        bool: Tür destekleniyorsa True, aksi halde False.
    """
    if not isinstance(speciesName, str):
        return False
    normalizedSpecies = speciesName.strip().lower()
    return normalizedSpecies in VALID_SPECIES
