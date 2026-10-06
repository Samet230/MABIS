"""Segmentation module for ZooID (MABIS)."""

from src.segmentation.cat_segmenter import CatFaceSegmenter
from src.segmentation.cattle_segmenter import CattleMuzzleSegmenter
from src.segmentation.dog_segmenter import DogMuzzleSegmenter
from src.segmentation.router import SegmentationRouter, segment_roi

__all__ = [
    "CattleMuzzleSegmenter",
    "DogMuzzleSegmenter",
    "CatFaceSegmenter",
    "SegmentationRouter",
    "segment_roi",
]
