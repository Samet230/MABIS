import cv2
import numpy as np
import pytest

from src.segmentation.cat_segmenter import CatFaceSegmenter
from src.segmentation.cattle_segmenter import CattleMuzzleSegmenter
from src.segmentation.dog_segmenter import DogMuzzleSegmenter
from src.segmentation.router import SegmentationRouter, segment_roi
from src.utils.config import ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH


def test_cattle_segmenter():
    """Sığır burun segmentasyonunun doğru boyutta ROI döndürdüğünü test eder."""
    syntheticImage = np.full((400, 400), 200, dtype=np.uint8)
    # Merkeze koyu bir burun deseni simüle et
    cv2.circle(syntheticImage, (200, 200), 70, 40, -1)

    segmenter = CattleMuzzleSegmenter()
    croppedRoi = segmenter.SegmentMuzzle(syntheticImage)

    assert croppedRoi is not None
    assert croppedRoi.shape == (ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH)
    assert croppedRoi.dtype == np.uint8


def test_dog_segmenter():
    """Köpek burun segmentasyonunun doğru boyutta ROI döndürdüğünü test eder."""
    syntheticImage = np.full((400, 400), 180, dtype=np.uint8)
    # Alt-orta bölgeye koyu bir burun lekesi simüle et (y=260, x=200)
    cv2.circle(syntheticImage, (200, 260), 45, 30, -1)

    segmenter = DogMuzzleSegmenter()
    croppedRoi = segmenter.SegmentMuzzle(syntheticImage)

    assert croppedRoi is not None
    assert croppedRoi.shape == (ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH)
    assert croppedRoi.dtype == np.uint8


def test_cat_segmenter():
    """Kedi yüz segmentasyonunun (cascade veya fallback) doğru boyutta ROI döndürdüğünü test eder."""
    syntheticImage = np.full((350, 350, 3), 150, dtype=np.uint8)

    segmenter = CatFaceSegmenter()
    croppedRoi = segmenter.SegmentFace(syntheticImage)

    assert croppedRoi is not None
    assert croppedRoi.shape == (ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH)
    assert croppedRoi.dtype == np.uint8


def test_segmentation_router_and_interface():
    """segment_roi standart arayüzünün 3 tür için de çalıştığını test eder."""
    sampleImage = np.full((300, 300, 3), 120, dtype=np.uint8)

    for speciesName in ("cattle", "dog", "cat"):
        roiResult = segment_roi(sampleImage, speciesName)
        assert roiResult is not None
        assert roiResult.shape == (ROI_TARGET_HEIGHT, ROI_TARGET_WIDTH)

    # Geçersiz tür testi
    with pytest.raises(ValueError):
        segment_roi(sampleImage, "unsupported_species")
