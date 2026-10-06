from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.utils.logger import GetLogger

loggerInstance = GetLogger("BiometricEvaluator")


class BiometricEvaluator:
    """Biyometrik tanıma ve sınıflandırma başarı metriklerini (Rank-1, F1, Precision, Recall) hesaplar."""

    def __init__(self) -> None:
        """Değerlendiriciyi başlatır."""
        pass

    @staticmethod
    def NormalizePredictions(
        rawPredictions: Sequence[Union[str, List[Tuple[str, float]], List[str]]],
    ) -> List[str]:
        """Farklı biçimlerdeki tahmin listesini Rank-1 tahmin kimliklerine dönüştürür."""
        normalizedList: List[str] = []
        for predictionItem in rawPredictions:
            if isinstance(predictionItem, str):
                normalizedList.append(predictionItem)
            elif isinstance(predictionItem, (list, tuple)) and len(predictionItem) > 0:
                firstItem = predictionItem[0]
                if isinstance(firstItem, (list, tuple)) and len(firstItem) >= 1:
                    # [(animalId, confidence), ...] biçimi
                    normalizedList.append(str(firstItem[0]))
                else:
                    normalizedList.append(str(firstItem))
            else:
                normalizedList.append("")
        return normalizedList

    def Evaluate(
        self,
        predictionsList: Sequence[Any],
        groundTruthList: Sequence[str],
    ) -> Dict[str, Any]:
        """Tahminler ile gerçek etiketleri kıyaslayarak kapsamlı değerlendirme raporu üretir.

        Args:
            predictionsList: Rank-1 tahmin kimlikleri listesi.
            groundTruthList: Gerçek hayvan kimlikleri listesi.

        Returns:
            Dict[str, Any]: Rank-1 doğruluk, Precision, Recall, F1 ve Confusion Matrix.
        """
        if len(predictionsList) != len(groundTruthList):
            raise ValueError(
                f"Tahmin boyutu ({len(predictionsList)}) ile "
                f"gerçek etiket boyutu ({len(groundTruthList)}) eşit olmalıdır."
            )

        totalSamplesCount = len(groundTruthList)
        if totalSamplesCount == 0:
            return {
                "totalSamples": 0,
                "correctSamples": 0,
                "rank1Accuracy": 0.0,
            }

        cleanedPredictions = self.NormalizePredictions(predictionsList)
        cleanedGroundTruth = [str(labelItem) for labelItem in groundTruthList]

        uniqueClasses = sorted(list(set(cleanedGroundTruth)))

        # Rank-1 Doğruluk hesabı
        correctMatchesCount = sum(
            1
            for predictedId, trueId in zip(cleanedPredictions, cleanedGroundTruth)
            if predictedId == trueId
        )
        rank1Accuracy = float(correctMatchesCount / totalSamplesCount)

        try:
            precisionMacro = float(
                precision_score(
                    cleanedGroundTruth,
                    cleanedPredictions,
                    labels=uniqueClasses,
                    average="macro",
                    zero_division=0,
                )
            )
            recallMacro = float(
                recall_score(
                    cleanedGroundTruth,
                    cleanedPredictions,
                    labels=uniqueClasses,
                    average="macro",
                    zero_division=0,
                )
            )
            f1Macro = float(
                f1_score(
                    cleanedGroundTruth,
                    cleanedPredictions,
                    labels=uniqueClasses,
                    average="macro",
                    zero_division=0,
                )
            )

            precisionWeighted = float(
                precision_score(
                    cleanedGroundTruth,
                    cleanedPredictions,
                    labels=uniqueClasses,
                    average="weighted",
                    zero_division=0,
                )
            )
            recallWeighted = float(
                recall_score(
                    cleanedGroundTruth,
                    cleanedPredictions,
                    labels=uniqueClasses,
                    average="weighted",
                    zero_division=0,
                )
            )
            f1Weighted = float(
                f1_score(
                    cleanedGroundTruth,
                    cleanedPredictions,
                    labels=uniqueClasses,
                    average="weighted",
                    zero_division=0,
                )
            )

            confusionMatrixArray = confusion_matrix(
                cleanedGroundTruth,
                cleanedPredictions,
                labels=uniqueClasses,
            )

            detailedReportDictionary = classification_report(
                cleanedGroundTruth,
                cleanedPredictions,
                labels=uniqueClasses,
                output_dict=True,
                zero_division=0,
            )

            evaluationResults = {
                "totalSamples": totalSamplesCount,
                "correctSamples": correctMatchesCount,
                "rank1Accuracy": rank1Accuracy,
                "precisionMacro": precisionMacro,
                "recallMacro": recallMacro,
                "f1Macro": f1Macro,
                "precisionWeighted": precisionWeighted,
                "recallWeighted": recallWeighted,
                "f1Weighted": f1Weighted,
                "classes": uniqueClasses,
                "confusionMatrix": confusionMatrixArray.tolist(),
                "detailedReport": detailedReportDictionary,
            }
            return evaluationResults

        except Exception as evalException:
            loggerInstance.error(f"Metrik hesaplama hatası: {evalException}")
            return {
                "totalSamples": totalSamplesCount,
                "correctSamples": correctMatchesCount,
                "rank1Accuracy": rank1Accuracy,
                "error": str(evalException),
            }

    @staticmethod
    def CalculateDecidabilityIndex(
        genuineScores: Sequence[float],
        impostorScores: Sequence[float],
    ) -> float:
        """İki skor dağılımı arasındaki Ayırt Edilebilirlik İndeksini (Decidability Index - d') hesaplar."""
        if len(genuineScores) == 0 or len(impostorScores) == 0:
            return 0.0

        genuineArray = np.asarray(genuineScores, dtype=np.float64)
        impostorArray = np.asarray(impostorScores, dtype=np.float64)

        meanGenuine = float(np.mean(genuineArray))
        meanImpostor = float(np.mean(impostorArray))
        varGenuine = float(np.var(genuineArray))
        varImpostor = float(np.var(impostorArray))

        denominator = np.sqrt(0.5 * (varGenuine + varImpostor))
        if denominator == 0.0:
            return 0.0

        return float(abs(meanGenuine - meanImpostor) / denominator)

    @staticmethod
    def CalculateVerificationMetrics(
        genuineScores: Sequence[float],
        impostorScores: Sequence[float],
        decisionThreshold: float,
    ) -> Dict[str, float]:
        """Belirtilen eşik değeri için FAR, FRR ve Doğruluk (Accuracy) metriklerini hesaplar.

        Args:
            genuineScores: Aynı bireye ait çiftlerin güven skorları.
            impostorScores: Farklı bireylere ait çiftlerin güven skorları.
            decisionThreshold: Kabul/ret eşiği.

        Returns:
            Dict[str, float]: FAR, FRR, TAR, Doğruluk ve örnek sayıları.
        """
        totalGenuine = len(genuineScores)
        totalImpostor = len(impostorScores)

        if totalGenuine == 0 or totalImpostor == 0:
            raise ValueError("Genuine veya Impostor skor listesi boş olamaz.")

        falseAcceptancesCount = sum(
            1 for scoreItem in impostorScores if scoreItem >= decisionThreshold
        )
        falseRejectionsCount = sum(
            1 for scoreItem in genuineScores if scoreItem < decisionThreshold
        )

        falseAcceptanceRate = float(falseAcceptancesCount / totalImpostor)
        falseRejectionRate = float(falseRejectionsCount / totalGenuine)
        trueAcceptanceRate = 1.0 - falseRejectionRate

        totalPairs = totalGenuine + totalImpostor
        correctDecisions = (totalGenuine - falseRejectionsCount) + (
            totalImpostor - falseAcceptancesCount
        )
        overallAccuracy = float(correctDecisions / totalPairs)

        return {
            "threshold": decisionThreshold,
            "falseAcceptanceRate": falseAcceptanceRate,
            "falseRejectionRate": falseRejectionRate,
            "trueAcceptanceRate": trueAcceptanceRate,
            "accuracy": overallAccuracy,
            "totalGenuine": float(totalGenuine),
            "totalImpostor": float(totalImpostor),
        }

    def CalculateEER(
        self,
        genuineScores: Sequence[float],
        impostorScores: Sequence[float],
        numThresholds: int = 1000,
    ) -> Tuple[float, float]:
        """FAR ve FRR'nin eşitlendiği Eşit Hata Oranını (EER) ve optimal eşik değerini bulur.

        Returns:
            Tuple[float, float]: (eer_degeri, optimal_esik)
        """
        if len(genuineScores) == 0 or len(impostorScores) == 0:
            return 0.0, 0.5

        allScores = np.concatenate([genuineScores, impostorScores])
        minScore = float(np.min(allScores))
        maxScore = float(np.max(allScores))

        thresholdValues = np.linspace(minScore, maxScore, numThresholds)
        bestDifference = float("inf")
        optimalThreshold = 0.5
        calculatedEER = 0.0

        for candidateThreshold in thresholdValues:
            metricsDict = self.CalculateVerificationMetrics(
                genuineScores=genuineScores,
                impostorScores=impostorScores,
                decisionThreshold=float(candidateThreshold),
            )
            currentFar = metricsDict["falseAcceptanceRate"]
            currentFrr = metricsDict["falseRejectionRate"]
            difference = abs(currentFar - currentFrr)

            if difference < bestDifference:
                bestDifference = difference
                optimalThreshold = float(candidateThreshold)
                calculatedEER = float(0.5 * (currentFar + currentFrr))

        return calculatedEER, optimalThreshold


# Dokümanlarda tanımlanan standart sözleşme fonksiyonu (ARCHITECTURE.md ve AGENTS.md)
_defaultEvaluator = BiometricEvaluator()


def evaluate(predictions: list, ground_truth: list) -> dict:
    """ZooID standart modül sözleşmesine uygun değerlendirme fonksiyonu.

    Args:
        predictions: Model tahminleri listesi.
        ground_truth: Gerçek hayvan ID etiketleri listesi.

    Returns:
        dict: Değerlendirme metrikleri ve başarı oranları.
    """
    return _defaultEvaluator.Evaluate(
        predictionsList=predictions,
        groundTruthList=ground_truth,
    )


def evaluate_verification(
    genuine_scores: Sequence[float],
    impostor_scores: Sequence[float],
    threshold: Optional[float] = None,
) -> Dict[str, float]:
    """ZooID standart 1:1 doğrulama ve EER değerlendirme fonksiyonu.

    Args:
        genuine_scores: Gerçek eşleşme skorları.
        impostor_scores: Sahte eşleşme skorları.
        threshold: İsteğe bağlı sabit eşik. Verilmezse optimal EER eşiği hesaplanır.

    Returns:
        Dict[str, float]: FAR, FRR, EER, d_prime ve eşik sonuçları.
    """
    eerValue, optimalThreshold = _defaultEvaluator.CalculateEER(
        genuineScores=genuine_scores,
        impostorScores=impostor_scores,
    )
    selectedThreshold = optimalThreshold if threshold is None else threshold
    metricsReport = _defaultEvaluator.CalculateVerificationMetrics(
        genuineScores=genuine_scores,
        impostorScores=impostor_scores,
        decisionThreshold=selectedThreshold,
    )
    decidabilityIndex = _defaultEvaluator.CalculateDecidabilityIndex(
        genuineScores=genuine_scores,
        impostorScores=impostor_scores,
    )
    metricsReport["eer"] = eerValue
    metricsReport["optimalThreshold"] = optimalThreshold
    metricsReport["decidabilityIndex"] = decidabilityIndex
    return metricsReport
