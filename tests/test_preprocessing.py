import numpy as np
import pytest

from src.preprocessing.preprocessor import ImagePreprocessor, preprocess


def test_preprocessor_basic_flow():
    """Ön işleme adımlarının BGR görüntü üzerinde doğru çalıştığını test eder."""
    # 200x200 3 kanallı rastgele BGR görüntü
    syntheticBgr = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)

    preprocessedOutput = preprocess(syntheticBgr)

    assert preprocessedOutput is not None
    assert len(preprocessedOutput.shape) == 2
    assert preprocessedOutput.shape == (200, 200)
    assert preprocessedOutput.dtype == np.uint8


def test_preprocessor_grayscale_input():
    """Ön işlemenin doğrudan gri seviye girdiyi de kabul ettiğini test eder."""
    syntheticGray = np.random.randint(0, 256, (150, 180), dtype=np.uint8)

    preprocessedOutput = preprocess(syntheticGray)

    assert preprocessedOutput.shape == (150, 180)
    assert preprocessedOutput.dtype == np.uint8


def test_preprocessor_invalid_input():
    """Geçersiz veya boş girdilerde hata fırlatıldığını test eder."""
    preprocessorInstance = ImagePreprocessor()

    with pytest.raises(ValueError):
        preprocessorInstance.ProcessImage(None)

    with pytest.raises(ValueError):
        preprocessorInstance.ProcessImage(np.array([]))
