import cv2
import numpy as np
import pytest

from src.preprocessing.quality_gate import QualityGate, check_quality


def test_quality_gate_sharp_image_passes():
    """Yeterli kontrasta ve keskinliğe sahip sentetik görüntünün kalite kapısından geçmesi beklenir."""
    syntheticSharpImage = np.random.randint(50, 200, (300, 300, 3), dtype=np.uint8)
    # Belirgin çizgiler ve köşeler ekle
    cv2.rectangle(syntheticSharpImage, (50, 50), (250, 250), (0, 0, 0), thickness=5)
    cv2.circle(syntheticSharpImage, (150, 150), 40, (255, 255, 255), thickness=-1)

    gateInstance = QualityGate(blurThreshold=50.0)
    result = gateInstance.AssessQuality(syntheticSharpImage)

    assert result.isPassed is True
    assert len(result.rejectionReasons) == 0
    assert result.blurScore > 50.0
    assert 40.0 <= result.meanBrightness <= 225.0


def test_quality_gate_blurred_image_rejection():
    """Ağır bulanıklaştırılmış bir görüntünün bulanıklık sebebiyle reddedilmesi doğrulanır."""
    baseImage = np.random.randint(60, 180, (250, 250, 3), dtype=np.uint8)
    blurredImage = cv2.GaussianBlur(baseImage, (25, 25), 10.0)

    gateInstance = QualityGate(blurThreshold=100.0)
    result = gateInstance.AssessQuality(blurredImage)

    assert result.isPassed is False
    assert any("bulanık" in reason.lower() for reason in result.rejectionReasons)


def test_quality_gate_dark_and_bright_rejection():
    """Aşırı karanlık ve aşırı parlak patlamış görüntülerin elenmesi doğrulanır."""
    darkImage = np.full((200, 200, 3), 15, dtype=np.uint8)
    brightImage = np.full((200, 200, 3), 245, dtype=np.uint8)

    gateInstance = QualityGate()

    darkResult = gateInstance.AssessQuality(darkImage)
    assert darkResult.isPassed is False
    assert any("karanlık" in reason.lower() for reason in darkResult.rejectionReasons)

    brightResult = gateInstance.AssessQuality(brightImage)
    assert brightResult.isPassed is False
    assert any("parlak" in reason.lower() for reason in brightResult.rejectionReasons)


def test_quality_gate_resolution_and_aspect_ratio():
    """Düşük çözünürlüklü veya aşırı basık en/boy oranına sahip görüntülerin elenmesi doğrulanır."""
    lowResImage = np.ones((80, 80, 3), dtype=np.uint8) * 128
    gateInstance = QualityGate(minDimensions=(120, 120), maxAspectRatio=3.0)
    lowResResult = gateInstance.AssessQuality(lowResImage)
    assert lowResResult.isPassed is False
    assert any("çözünürlük" in reason.lower() for reason in lowResResult.rejectionReasons)

    distortedImage = np.ones((400, 100, 3), dtype=np.uint8) * 128
    distortedResult = gateInstance.AssessQuality(distortedImage)
    assert distortedResult.isPassed is False
    assert any("en/boy" in reason.lower() for reason in distortedResult.rejectionReasons)


def test_check_quality_contract_function():
    """check_quality sözleşme fonksiyonunun doğru tipleri döndürmesi doğrulanır."""
    sampleImage = np.ones((200, 200, 3), dtype=np.uint8) * 100
    isPassed, reasonText, metricsDict = check_quality(sampleImage)
    assert isinstance(isPassed, bool)
    assert isinstance(reasonText, str)
    assert "blur_score" in metricsDict
    assert "mean_brightness" in metricsDict
