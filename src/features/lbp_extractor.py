from typing import Final, Tuple
import cv2
import numpy as np
from skimage.feature import local_binary_pattern

from src.utils.config import (
    LBP_DEFAULT_POINTS,
    LBP_DEFAULT_RADIUS,
    LBP_METHOD_UNIFORM,
)
from src.utils.logger import GetLogger

loggerInstance = GetLogger("LbpExtractor")

DEFAULT_GRID_CELLS_X: Final[int] = 4
DEFAULT_GRID_CELLS_Y: Final[int] = 4


class LbpFeatureExtractor:
    """LBP (Local Binary Pattern) doku özniteliklerini ızgara tabanlı histogramlarla çıkaran modül."""

    def __init__(
        self,
        radius: int = LBP_DEFAULT_RADIUS,
        pointsCount: int = LBP_DEFAULT_POINTS,
        method: str = LBP_METHOD_UNIFORM,
        gridCellsX: int = DEFAULT_GRID_CELLS_X,
        gridCellsY: int = DEFAULT_GRID_CELLS_Y,
    ) -> None:
        """LBP öznitelik çıkarıcısını başlatır.

        Args:
            radius: Dairesel komşuluk yarıçapı.
            pointsCount: Örneklenen komşu nokta sayısı.
            method: LBP türevi ('uniform' önerilir).
            gridCellsX: Yatay ızgara bölüntü sayısı.
            gridCellsY: Dikey ızgara bölüntü sayısı.
        """
        self.radius = radius
        self.pointsCount = pointsCount
        self.method = method
        self.gridCellsX = gridCellsX
        self.gridCellsY = gridCellsY
        # Uniform LBP için bin sayısı: pointsCount + 2
        self.binsCount = self.pointsCount + 2 if method == "uniform" else 256

    def ExtractCellHistogram(self, lbpCellMatrix: np.ndarray) -> np.ndarray:
        """Tek bir ızgara hücresinin normalize LBP histogramını hesaplar."""
        cellHistogram, _ = np.histogram(
            lbpCellMatrix.ravel(),
            bins=self.binsCount,
            range=(0, self.binsCount),
            density=False,
        )
        floatHistogram = cellHistogram.astype(np.float32)
        sumValues = floatHistogram.sum()
        if sumValues > 0.0:
            floatHistogram /= sumValues
        return floatHistogram

    def ExtractFeatures(self, roiImage: np.ndarray) -> np.ndarray:
        """Girdi ROI görüntüsünden ızgara tabanlı mekânsal LBP histogram vektörünü çıkarır.

        Args:
            roiImage: (H, W) gri seviye veya BGR ROI matrisi.

        Returns:
            np.ndarray: L2 normalize edilmiş 1D öznitelik vektörü.
        """
        if roiImage is None or roiImage.size == 0:
            raise ValueError("ROI görüntüsü boş veya geçersiz.")

        try:
            if len(roiImage.shape) == 3:
                grayRoi = cv2.cvtColor(roiImage, cv2.COLOR_BGR2GRAY)
            else:
                grayRoi = roiImage

            lbpImage = local_binary_pattern(
                grayRoi,
                P=self.pointsCount,
                R=self.radius,
                method=self.method,
            )

            roiHeight = lbpImage.shape[0]
            roiWidth = lbpImage.shape[1]
            cellHeight = roiHeight // self.gridCellsY
            cellWidth = roiWidth // self.gridCellsX

            histogramVectorList = []

            for gridRowIndex in range(self.gridCellsY):
                rowStart = gridRowIndex * cellHeight
                rowEnd = (
                    (gridRowIndex + 1) * cellHeight
                    if gridRowIndex < self.gridCellsY - 1
                    else roiHeight
                )

                for gridColIndex in range(self.gridCellsX):
                    colStart = gridColIndex * cellWidth
                    colEnd = (
                        (gridColIndex + 1) * cellWidth
                        if gridColIndex < self.gridCellsX - 1
                        else roiWidth
                    )

                    cellMatrix = lbpImage[rowStart:rowEnd, colStart:colEnd]
                    cellHistogram = self.ExtractCellHistogram(cellMatrix)
                    histogramVectorList.append(cellHistogram)

            concatenatedVector = np.concatenate(histogramVectorList)

            # L2 normalizasyonu
            l2Norm = np.linalg.norm(concatenatedVector)
            if l2Norm > 0.0:
                concatenatedVector /= l2Norm

            return concatenatedVector.astype(np.float32)

        except Exception as lbpException:
            loggerInstance.error(f"LBP öznitelik çıkarımı hatası: {lbpException}")
            raise
