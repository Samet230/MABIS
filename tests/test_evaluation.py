import tempfile
from pathlib import Path
import numpy as np
import pytest

from src.evaluation.evaluator import BiometricEvaluator, evaluate
from src.evaluation.visualizer import ResultVisualizer


def test_evaluator_perfect_predictions():
    """Tüm tahminlerin doğru olduğu senaryoda metriklerin 1.0 olduğunu test eder."""
    groundTruth = ["cow_1", "cow_2", "cow_3", "cow_4"]
    predictions = ["cow_1", "cow_2", "cow_3", "cow_4"]

    results = evaluate(predictions, groundTruth)

    assert results["totalSamples"] == 4
    assert results["correctSamples"] == 4
    assert results["rank1Accuracy"] == 1.0
    assert results["precisionMacro"] == 1.0
    assert results["recallMacro"] == 1.0
    assert results["f1Macro"] == 1.0
    assert "confusionMatrix" in results


def test_evaluator_imperfect_predictions():
    """Kısmi yanlış tahminlerde metriklerin doğru hesaplandığını test eder."""
    groundTruth = ["dog_1", "dog_2", "dog_3", "dog_4"]
    # dog_3 yerine yanlışlıkla dog_1 tahmin edilmiş (3/4 = 0.75)
    predictions = ["dog_1", "dog_2", "dog_1", "dog_4"]

    results = evaluate(predictions, groundTruth)

    assert results["totalSamples"] == 4
    assert results["correctSamples"] == 3
    assert results["rank1Accuracy"] == 0.75
    assert results["recallMacro"] < 1.0


def test_evaluator_tuple_predictions_normalization():
    """[(animalId, confidence), ...] biçimindeki tahminlerin normalize edilmesini test eder."""
    groundTruth = ["cat_1", "cat_2"]
    tuplePredictions = [[("cat_1", 0.95)], [("cat_2", 0.88)]]

    results = evaluate(tuplePredictions, groundTruth)
    assert results["rank1Accuracy"] == 1.0


def test_result_visualizer_outputs():
    """Görselleştiricinin PNG ve CSV dosyalarını hatasız ürettiğini test eder."""
    with tempfile.TemporaryDirectory() as tempDir:
        figuresDir = Path(tempDir) / "figures"
        tablesDir = Path(tempDir) / "tables"

        visualizer = ResultVisualizer(figuresDirectory=figuresDir, tablesDirectory=tablesDir)

        # 1. Confusion Matrix çizimi
        confMatrix = [[5, 1], [0, 6]]
        labels = ["class_A", "class_B"]
        cmPath = visualizer.PlotConfusionMatrix(confMatrix, labels, outputFileName="test_cm.png")
        assert cmPath.is_file()
        assert cmPath.stat().st_size > 0

        # 2. Yöntem karşılaştırma grafiği
        comparisonData = {"lbp": 0.85, "glcm": 0.80, "lbp_glcm": 0.92}
        chartPath = visualizer.PlotMethodComparison(comparisonData, outputFileName="test_bar.png")
        assert chartPath.is_file()
        assert chartPath.stat().st_size > 0

        # 3. CSV Tablosu kaydı
        rows = [
            {"method": "lbp", "rank1Accuracy": 0.85},
            {"method": "glcm", "rank1Accuracy": 0.80},
        ]
        csvPath = visualizer.SaveSummaryTable(rows, outputFileName="test_summary.csv")
        assert csvPath.is_file()
        assert csvPath.stat().st_size > 0
