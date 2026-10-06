from typing import Final, List, Optional, Tuple
import cv2
import numpy as np

from src.utils.logger import GetLogger

loggerInstance = GetLogger("KeypointExtractor")

DEFAULT_MAX_KEYPOINTS: Final[int] = 600
DEFAULT_ORB_FAST_THRESHOLD: Final[int] = 7
DEFAULT_ORB_EDGE_THRESHOLD: Final[int] = 12
DEFAULT_SIFT_CONTRAST_THRESHOLD: Final[float] = 0.02
DEFAULT_SIFT_EDGE_THRESHOLD: Final[float] = 15.0
SIFT_DESCRIPTOR_DIMENSION: Final[int] = 128
ORB_DESCRIPTOR_DIMENSION: Final[int] = 32
COORDINATE_DIMENSION: Final[int] = 2


class KeypointFeatureExtractor:
    """SIFT ve ORB anahtar nokta ve tanımlayıcı (descriptor) çıkarıcı modülü."""

    def __init__(self, maxKeypoints: int = DEFAULT_MAX_KEYPOINTS) -> None:
        """Anahtar nokta çıkarıcıyı başlatır.

        Args:
            maxKeypoints: Tespit edilecek azami anahtar nokta adedi.
        """
        self.maxKeypoints = maxKeypoints
        self.siftDetector = cv2.SIFT_create(
            nfeatures=self.maxKeypoints,
            contrastThreshold=DEFAULT_SIFT_CONTRAST_THRESHOLD,
            edgeThreshold=DEFAULT_SIFT_EDGE_THRESHOLD,
        )
        self.orbDetector = cv2.ORB_create(
            nfeatures=self.maxKeypoints,
            fastThreshold=DEFAULT_ORB_FAST_THRESHOLD,
            edgeThreshold=DEFAULT_ORB_EDGE_THRESHOLD,
        )

    def ExtractKeypointsAndDescriptors(
        self,
        roiImage: np.ndarray,
        method: str = "sift",
    ) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """Görüntüden anahtar noktaları ve tanımlayıcı matrisini çıkarır.

        Args:
            roiImage: Girdi ROI görüntüsü (Gri veya BGR).
            method: 'sift' veya 'orb'.

        Returns:
            Tuple[List[cv2.KeyPoint], np.ndarray]: Anahtar noktalar ve tanımlayıcı matrisi (N, D).
        """
        if roiImage is None or roiImage.size == 0:
            raise ValueError("ROI görüntüsü boş veya geçersiz.")

        if len(roiImage.shape) == 3:
            grayRoi = cv2.cvtColor(roiImage, cv2.COLOR_BGR2GRAY)
        else:
            grayRoi = roiImage

        normalizedMethod = method.strip().lower()
        try:
            if normalizedMethod == "sift":
                keypointsList, descriptorMatrix = self.siftDetector.detectAndCompute(
                    grayRoi,
                    None,
                )
                if descriptorMatrix is None or descriptorMatrix.size == 0:
                    descriptorMatrix = np.zeros(
                        (1, SIFT_DESCRIPTOR_DIMENSION), dtype=np.float32
                    )
                else:
                    descriptorMatrix = descriptorMatrix.astype(np.float32)
            elif normalizedMethod == "orb":
                keypointsList, descriptorMatrix = self.orbDetector.detectAndCompute(
                    grayRoi,
                    None,
                )
                if descriptorMatrix is None or descriptorMatrix.size == 0:
                    descriptorMatrix = np.zeros(
                        (1, ORB_DESCRIPTOR_DIMENSION), dtype=np.uint8
                    )
            else:
                raise ValueError(
                    f"Bilinmeyen anahtar nokta metodu: {method}. 'sift' veya 'orb' kullanın."
                )

            return keypointsList if keypointsList is not None else [], descriptorMatrix

        except Exception as keypointException:
            loggerInstance.error(
                f"Anahtar nokta çıkarımı hatası ({method}): {keypointException}"
            )
            emptyDimension = (
                SIFT_DESCRIPTOR_DIMENSION
                if normalizedMethod == "sift"
                else ORB_DESCRIPTOR_DIMENSION
            )
            return [], np.zeros(
                (1, emptyDimension),
                dtype=np.float32 if normalizedMethod == "sift" else np.uint8,
            )

    def ExtractFeatures(
        self,
        roiImage: np.ndarray,
        method: str = "sift",
    ) -> np.ndarray:
        """Standart extract_features sözleşmesi için RANSAC uyumlu paketlenmiş öznitelik matrisi döndürür.

        İlk 2 sütun (x, y) anahtar nokta koordinatlarını, sonraki sütunlar tanımlayıcı vektörlerini içerir.
        """
        keypointsList, descriptorMatrix = self.ExtractKeypointsAndDescriptors(
            roiImage,
            method=method,
        )
        normalizedMethod = method.strip().lower()
        emptyDimension = (
            SIFT_DESCRIPTOR_DIMENSION
            if normalizedMethod == "sift"
            else ORB_DESCRIPTOR_DIMENSION
        )

        if not keypointsList or descriptorMatrix is None or descriptorMatrix.shape[0] == 0:
            return np.zeros(
                (1, COORDINATE_DIMENSION + emptyDimension), dtype=np.float32
            )

        if len(keypointsList) != descriptorMatrix.shape[0]:
            return np.zeros(
                (1, COORDINATE_DIMENSION + emptyDimension), dtype=np.float32
            )

        coordinateArray = np.array(
            [[keypointItem.pt[0], keypointItem.pt[1]] for keypointItem in keypointsList],
            dtype=np.float32,
        )
        packedFeatures = np.hstack([coordinateArray, descriptorMatrix.astype(np.float32)])
        return packedFeatures.astype(np.float32)
