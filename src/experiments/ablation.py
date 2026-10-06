import argparse
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import numpy as np

from src.database.db_manager import DatabaseManager
from src.evaluation.evaluator import BiometricEvaluator
from src.evaluation.visualizer import ResultVisualizer
from src.features.feature_extractor import extract_features
from src.matching.matcher import MatchingEngine
from src.preprocessing.preprocessor import preprocess
from src.segmentation.router import segment_roi
from src.utils.config import (
    METHOD_GLCM,
    METHOD_LBP,
    METHOD_LBP_GLCM,
    METHOD_ORB,
    METHOD_SIFT,
    PROJECT_ROOT_DIR,
    VALID_FEATURE_METHODS,
)
from src.utils.image_io import ReadImage
from src.utils.logger import GetLogger

loggerInstance = GetLogger("AblationExperiment")


class AblationExperiment:
    """Farklı öznitelik çıkarma yöntemlerinin başarı ve hızını karşılaştıran deney modülü."""

    def __init__(
        self,
        experimentDatabasePath: Optional[Path] = None,
    ) -> None:
        """Deney modülünü başlatır."""
        self.evaluator = BiometricEvaluator()
        self.visualizer = ResultVisualizer()
        self.databasePath = (
            experimentDatabasePath
            if experimentDatabasePath
            else Path("data/database/ablation_temp.db").resolve()
        )

    def RunAblationOnSplit(
        self,
        splitMetadata: Dict[str, Any],
        methodsToTest: Optional[List[str]] = None,
        outputPlotName: str = "ablation_comparison.png",
    ) -> Dict[str, Dict[str, Any]]:
        """Verilen kapalı-küme ayrım verisi üzerinde yöntem karşılaştırma deneyini yürütür.

        Args:
            splitMetadata: DatasetSplitter tarafından üretilen ayrım verisi.
            methodsToTest: Test edilecek yöntemler listesi (None ise tümü).
            outputPlotName: Kaydedilecek karşılaştırma grafiği adı.

        Returns:
            Dict[str, Dict[str, Any]]: Her yöntem için başarı metrikleri ve süreler.
        """
        methodsList = methodsToTest if methodsToTest else list(VALID_FEATURE_METHODS)
        speciesName = splitMetadata["species"]
        galleryList = splitMetadata["gallery"]
        testList = splitMetadata["test"]

        loggerInstance.info(
            f"Ablation deneyi başlatılıyor ({speciesName}): {len(methodsList)} yöntem, "
            f"{len(galleryList)} galeri, {len(testList)} test örneği."
        )

        overallResults: Dict[str, Dict[str, Any]] = {}
        comparisonScoreMap: Dict[str, float] = {}
        summaryTableRows: List[Dict[str, Any]] = []

        for selectedMethod in methodsList:
            loggerInstance.info(f"Yöntem test ediliyor: '{selectedMethod}'...")
            dbManager = DatabaseManager(databasePath=self.databasePath)
            dbManager.ClearDatabase()

            startTime = time.time()

            # 1. Galeri Kaydı
            for galleryItem in galleryList:
                animalId = galleryItem["animalId"]
                imageRelativePath = galleryItem["imagePath"]
                imageFullPath = PROJECT_ROOT_DIR / imageRelativePath
                if not imageFullPath.is_file():
                    imageFullPath = PROJECT_ROOT_DIR / "data" / imageRelativePath

                imageArray = ReadImage(imageFullPath)
                if imageArray is None:
                    continue

                preprocessedImage = preprocess(imageArray)
                roiImage = segment_roi(preprocessedImage, speciesName)
                featureVector = extract_features(roiImage, method=selectedMethod)

                dbManager.RegisterAnimal(
                    animalId=animalId,
                    speciesName=speciesName,
                    featureVector=featureVector,
                )

            matchingEngine = MatchingEngine(databaseManager=dbManager)

            # 2. Test Sorguları
            predictionsList = []
            groundTruthList = []

            for testItem in testList:
                expectedAnimalId = testItem["animalId"]
                imageRelativePath = testItem["imagePath"]
                imageFullPath = PROJECT_ROOT_DIR / imageRelativePath
                if not imageFullPath.is_file():
                    imageFullPath = PROJECT_ROOT_DIR / "data" / imageRelativePath

                imageArray = ReadImage(imageFullPath)
                if imageArray is None:
                    continue

                preprocessedImage = preprocess(imageArray)
                roiImage = segment_roi(preprocessedImage, speciesName)
                queryFeature = extract_features(roiImage, method=selectedMethod)

                predictions = matchingEngine.Identify(
                    featureVector=queryFeature,
                    speciesName=speciesName,
                    topK=1,
                )

                predictedId = predictions[0][0] if predictions else ""
                predictionsList.append(predictedId)
                groundTruthList.append(expectedAnimalId)

            elapsedDuration = time.time() - startTime

            # 3. Metrik Değerlendirme
            evaluationReport = self.evaluator.Evaluate(
                predictionsList=predictionsList,
                groundTruthList=groundTruthList,
            )

            rank1Accuracy = evaluationReport.get("rank1Accuracy", 0.0)
            comparisonScoreMap[selectedMethod] = rank1Accuracy

            methodSummary = {
                "species": speciesName,
                "method": selectedMethod,
                "rank1Accuracy": rank1Accuracy,
                "precisionMacro": evaluationReport.get("precisionMacro", 0.0),
                "recallMacro": evaluationReport.get("recallMacro", 0.0),
                "f1Macro": evaluationReport.get("f1Macro", 0.0),
                "totalSamples": evaluationReport.get("totalSamples", 0),
                "durationSeconds": round(elapsedDuration, 2),
            }
            overallResults[selectedMethod] = methodSummary
            summaryTableRows.append(methodSummary)

            loggerInstance.info(
                f"[{selectedMethod}] Tamamlandı -> Rank-1: %{rank1Accuracy * 100.0:.2f}, "
                f"Süre: {elapsedDuration:.2f}s"
            )

        # Karşılaştırma grafiği ve özet tablo oluştur
        try:
            self.visualizer.PlotMethodComparison(
                comparisonData=comparisonScoreMap,
                outputFileName=outputPlotName,
                metricName="Rank-1 Doğruluk",
            )
            self.visualizer.SaveSummaryTable(
                recordRows=summaryTableRows,
                outputFileName=f"ablation_summary_{speciesName}.csv",
            )
        except Exception as visException:
            loggerInstance.warning(f"Görselleştirme oluşturulamadı: {visException}")

        return overallResults
