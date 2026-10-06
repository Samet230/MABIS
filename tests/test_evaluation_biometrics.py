import numpy as np
import pytest

from src.evaluation.evaluator import (
    BiometricEvaluator,
    evaluate_verification,
)


def test_calculate_verification_metrics_perfect_separation():
    """Tamamen ayrışan iki dağılımda FAR=0, FRR=0 ve %100 doğruluk test edilir."""
    evaluator = BiometricEvaluator()
    genuineScores = [0.8, 0.85, 0.9, 0.95, 0.99]
    impostorScores = [0.05, 0.1, 0.15, 0.2, 0.25]

    metrics = evaluator.CalculateVerificationMetrics(
        genuineScores=genuineScores,
        impostorScores=impostorScores,
        decisionThreshold=0.5,
    )

    assert metrics["falseAcceptanceRate"] == 0.0
    assert metrics["falseRejectionRate"] == 0.0
    assert metrics["trueAcceptanceRate"] == 1.0
    assert metrics["accuracy"] == 1.0


def test_calculate_eer_symmetric_distributions():
    """Simetrik ve bilinen dağılımlarda EER ve optimal eşik hesaplaması test edilir."""
    evaluator = BiometricEvaluator()
    genuineScores = [0.5, 0.6, 0.7, 0.8, 0.9]
    impostorScores = [0.1, 0.2, 0.3, 0.4, 0.5]

    eerValue, optimalThreshold = evaluator.CalculateEER(
        genuineScores=genuineScores,
        impostorScores=impostorScores,
    )

    assert 0.0 <= eerValue <= 0.5
    assert 0.3 <= optimalThreshold <= 0.7


def test_calculate_decidability_index():
    """Ayırt edilebilirlik indeksi (d') hesabı test edilir."""
    evaluator = BiometricEvaluator()
    genuineScores = [0.8, 0.82, 0.84, 0.86]
    impostorScores = [0.1, 0.12, 0.14, 0.16]

    dPrime = evaluator.CalculateDecidabilityIndex(genuineScores, impostorScores)
    assert dPrime > 5.0  # Mükemmel ayrışma


def test_evaluate_verification_contract_function():
    """evaluate_verification modül sözleşme fonksiyonu test edilir."""
    genuineScores = [0.75, 0.85, 0.90]
    impostorScores = [0.10, 0.15, 0.20]

    report = evaluate_verification(
        genuine_scores=genuineScores,
        impostor_scores=impostorScores,
    )

    assert "falseAcceptanceRate" in report
    assert "falseRejectionRate" in report
    assert "eer" in report
    assert "optimalThreshold" in report
    assert "decidabilityIndex" in report
    assert report["eer"] == 0.0
