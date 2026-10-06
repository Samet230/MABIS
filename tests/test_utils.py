import tempfile
from pathlib import Path
import cv2
import numpy as np
import pytest

from src.utils.config import (
    DEFAULT_LAPLACIAN_BLUR_THRESHOLD,
    ROI_TARGET_SIZE,
    VALID_SPECIES,
)
from src.utils.image_io import (
    CalculateLaplacianVariance,
    CheckImageQuality,
    ReadImage,
    SaveImage,
    ValidateSpecies,
)


def test_config_constants():
    """Temel konfigürasyon sabitlerinin doğruluğunu denetler."""
    assert "cattle" in VALID_SPECIES
    assert "dog" in VALID_SPECIES
    assert "cat" in VALID_SPECIES
    assert ROI_TARGET_SIZE == (300, 300)


def test_species_validation():
    """Tür doğrulama işlevini test eder."""
    assert ValidateSpecies("cattle") is True
    assert ValidateSpecies("dog") is True
    assert ValidateSpecies("cat") is True
    assert ValidateSpecies("CATTLE") is True
    assert ValidateSpecies("horse") is False
    assert ValidateSpecies("") is False


def test_image_save_and_read():
    """Sentetik bir görüntünün diske kaydedilip geri okunmasını test eder."""
    syntheticImage = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(syntheticImage, (100, 100), 50, (255, 255, 255), -1)

    with tempfile.TemporaryDirectory() as temporaryDir:
        testImagePath = Path(temporaryDir) / "test_sample.jpg"
        saveSuccess = SaveImage(testImagePath, syntheticImage)
        assert saveSuccess is True
        assert testImagePath.is_file()

        loadedImage = ReadImage(testImagePath)
        assert loadedImage is not None
        assert loadedImage.shape == (200, 200, 3)

        loadedGrayImage = ReadImage(testImagePath, asGrayscale=True)
        assert loadedGrayImage is not None
        assert loadedGrayImage.shape == (200, 200)


def test_laplacian_variance_and_quality():
    """Laplacian varyansı ve görüntü kalite kontrolünü test eder."""
    # Düz/tekdüze siyah görüntü (bulanık/düşük varyans)
    flatImage = np.full((200, 200, 3), 128, dtype=np.uint8)
    flatVariance = CalculateLaplacianVariance(flatImage)
    assert flatVariance == 0.0

    isQualityOk, rejectionReason, calculatedVariance = CheckImageQuality(
        flatImage,
        blurThreshold=50.0,
    )
    assert isQualityOk is False
    assert "Bulanık" in rejectionReason

    # Yüksek frekanslı dama tahtası deseni (keskin/yüksek varyans)
    checkerboardImage = np.zeros((200, 200), dtype=np.uint8)
    checkerboardImage[::2, ::2] = 255
    checkerboardImage[1::2, 1::2] = 255
    sharpVariance = CalculateLaplacianVariance(checkerboardImage)
    assert sharpVariance > 100.0

    isSharpQualityOk, _, _ = CheckImageQuality(
        checkerboardImage,
        blurThreshold=50.0,
    )
    assert isSharpQualityOk is True


def test_image_resolution_rejection():
    """Minimum çözünürlüğün altındaki görüntülerin elenmesini test eder."""
    smallImage = np.ones((50, 50, 3), dtype=np.uint8) * 200
    isQualityOk, rejectionReason, _ = CheckImageQuality(smallImage)
    assert isQualityOk is False
    assert "Düşük çözünürlük" in rejectionReason
