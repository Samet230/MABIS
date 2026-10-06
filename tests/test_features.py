import cv2
import numpy as np
import pytest

from src.features.feature_extractor import UnifiedFeatureExtractor, extract_features
from src.features.glcm_extractor import GlcmFeatureExtractor
from src.features.keypoint_extractor import KeypointFeatureExtractor
from src.features.lbp_extractor import LbpFeatureExtractor


@pytest.fixture
def sample_roi():
    """Testler için sentetik 300x300 desenli gri seviye ROI üretir."""
    syntheticMatrix = np.zeros((300, 300), dtype=np.uint8)
    # Doku desenleri ve gradyanlar
    for rowIdx in range(300):
        syntheticMatrix[rowIdx, :] = (rowIdx * 2) % 256
    # Belirgin anahtar noktalar için daireler ve çizgiler
    cv2.circle(syntheticMatrix, (150, 150), 30, 255, -1)
    cv2.circle(syntheticMatrix, (80, 80), 15, 255, -1)
    cv2.circle(syntheticMatrix, (220, 220), 15, 255, -1)
    cv2.rectangle(syntheticMatrix, (50, 200), (250, 230), 255, -1)
    return syntheticMatrix


def test_lbp_extractor(sample_roi):
    """LBP öznitelik çıkarıcısının boyutunu ve normalizasyonunu test eder."""
    extractor = LbpFeatureExtractor(gridCellsX=4, gridCellsY=4)
    featureVector = extractor.ExtractFeatures(sample_roi)

    assert featureVector is not None
    assert featureVector.ndim == 1
    # 4x4 = 16 ızgara hücresi * 10 bin = 160 boyut
    assert len(featureVector) == 160
    assert np.isclose(np.linalg.norm(featureVector), 1.0, atol=1e-4)


def test_glcm_extractor(sample_roi):
    """GLCM öznitelik çıkarıcısının boyutunu ve normalizasyonunu test eder."""
    extractor = GlcmFeatureExtractor()
    featureVector = extractor.ExtractFeatures(sample_roi)

    assert featureVector is not None
    assert featureVector.ndim == 1
    # 6 özellik * 3 mesafe * 4 açı = 72 boyut
    assert len(featureVector) == 72
    assert np.isclose(np.linalg.norm(featureVector), 1.0, atol=1e-4)


def test_keypoint_extractor(sample_roi):
    """SIFT ve ORB anahtar nokta çıkarıcılarının çalıştığını test eder."""
    extractor = KeypointFeatureExtractor()

    # SIFT testi
    siftKeypoints, siftDescriptors = extractor.ExtractKeypointsAndDescriptors(
        sample_roi, method="sift"
    )
    assert len(siftKeypoints) > 0
    assert siftDescriptors.shape[0] == len(siftKeypoints)
    assert siftDescriptors.shape[1] == 128

    # ORB testi
    orbKeypoints, orbDescriptors = extractor.ExtractKeypointsAndDescriptors(
        sample_roi, method="orb"
    )
    assert len(orbKeypoints) > 0
    assert orbDescriptors.shape[0] == len(orbKeypoints)
    assert orbDescriptors.shape[1] == 32


def test_unified_extract_features(sample_roi):
    """extract_features standart sözleşme fonksiyonunun tüm metotlarını test eder."""
    # LBP
    lbpVec = extract_features(sample_roi, method="lbp")
    assert len(lbpVec) == 160

    # GLCM
    glcmVec = extract_features(sample_roi, method="glcm")
    assert len(glcmVec) == 72

    # LBP + GLCM Füzyon (160 + 72 = 232)
    fusionVec = extract_features(sample_roi, method="lbp_glcm")
    assert len(fusionVec) == 232
    assert np.isclose(np.linalg.norm(fusionVec), 1.0, atol=1e-4)

    # SIFT (128 tanımlayıcı + 2 koordinat = 130 boyut)
    siftDesc = extract_features(sample_roi, method="sift")
    assert siftDesc.ndim == 2
    assert siftDesc.shape[1] in (128, 130)

    # ORB (32 tanımlayıcı + 2 koordinat = 34 boyut)
    orbDesc = extract_features(sample_roi, method="orb")
    assert orbDesc.ndim == 2
    assert orbDesc.shape[1] in (32, 34)

    # Geçersiz metot testi
    with pytest.raises(ValueError):
        extract_features(sample_roi, method="invalid_method")
