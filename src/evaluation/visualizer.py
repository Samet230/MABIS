from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import matplotlib
# Sunucu/test ortamında GUI penceresi açılmasını engellemek için 'Agg' backend
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.utils.config import FIGURES_DIR, TABLES_DIR
from src.utils.logger import GetLogger

loggerInstance = GetLogger("ResultVisualizer")


class ResultVisualizer:
    """Akademik rapor ve makale için grafik, ısı haritası ve özet tabloları üreten sınıf."""

    def __init__(
        self,
        figuresDirectory: Path = FIGURES_DIR,
        tablesDirectory: Path = TABLES_DIR,
    ) -> None:
        """Görselleştiriciyi başlatır."""
        self.figuresDirectory = Path(figuresDirectory).resolve()
        self.tablesDirectory = Path(tablesDirectory).resolve()
        self.figuresDirectory.mkdir(parents=True, exist_ok=True)
        self.tablesDirectory.mkdir(parents=True, exist_ok=True)

    def PlotConfusionMatrix(
        self,
        confusionMatrixArray: Union[List[List[int]], Any],
        classLabels: Sequence[str],
        outputFileName: str = "confusion_matrix.png",
        plotTitle: str = "ZooID Biyometrik Tanıma Karmaşıklık Matrisi",
    ) -> Path:
        """Karmaşıklık matrisini ısı haritası olarak çizer ve kaydeder."""
        destinationPath = self.figuresDirectory / outputFileName

        plt.figure(figsize=(8, 6))
        sns.heatmap(
            confusionMatrixArray,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=classLabels,
            yticklabels=classLabels,
            cbar=True,
        )
        plt.title(plotTitle, fontsize=12, pad=12)
        plt.xlabel("Tahmin Edilen Birey", fontsize=10)
        plt.ylabel("Gerçek Birey", fontsize=10)
        plt.tight_layout()

        plt.savefig(destinationPath, dpi=300)
        plt.close()
        loggerInstance.info(f"Karmaşıklık matrisi kaydedildi: {destinationPath}")
        return destinationPath

    def PlotMethodComparison(
        self,
        comparisonData: Dict[str, float],
        outputFileName: str = "method_comparison.png",
        metricName: str = "Rank-1 Doğruluk",
    ) -> Path:
        """Farklı öznitelik çıkarma yöntemlerinin başarı oranlarını çubuk grafik olarak çizer."""
        destinationPath = self.figuresDirectory / outputFileName

        methodsList = list(comparisonData.keys())
        scoresList = [comparisonData[key] * 100.0 for key in methodsList]

        plt.figure(figsize=(9, 5))
        barColors = ["#2b5c8f", "#3c7cb8", "#4e9ce0", "#68b5f0", "#1a3b5c"][:len(methodsList)]
        barContainer = plt.bar(methodsList, scoresList, color=barColors, width=0.55)

        plt.axhline(90.0, color="#d9534f", linestyle="--", linewidth=1.5, label="Hedef Başarı (%90)")
        plt.ylim(0, 105)
        plt.title(f"Öznitelik Çıkarma Yöntemleri Karşılaştırması ({metricName})", fontsize=12, pad=12)
        plt.xlabel("Yöntem", fontsize=10)
        plt.ylabel(f"{metricName} (%)", fontsize=10)
        plt.legend(loc="lower right")

        # Çubukların üstüne sayısal yüzdeleri yaz
        for individualBar in barContainer:
            barHeight = individualBar.get_height()
            plt.text(
                individualBar.get_x() + individualBar.get_width() / 2.0,
                barHeight + 1.5,
                f"%{barHeight:.1f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        plt.tight_layout()
        plt.savefig(destinationPath, dpi=300)
        plt.close()
        loggerInstance.info(f"Yöntem karşılaştırma grafiği kaydedildi: {destinationPath}")
        return destinationPath

    def SaveSummaryTable(
        self,
        recordRows: List[Dict[str, Any]],
        outputFileName: str = "evaluation_summary.csv",
    ) -> Path:
        """Deney sonuçlarını pandas DataFrame üzerinden CSV tablosu olarak kaydeder."""
        destinationPath = self.tablesDirectory / outputFileName
        dataframeInstance = pd.DataFrame(recordRows)
        dataframeInstance.to_csv(destinationPath, index=False, encoding="utf-8-sig")
        loggerInstance.info(f"Özet tablo kaydedildi: {destinationPath}")
        return destinationPath
