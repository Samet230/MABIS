from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.database.db_manager import DatabaseManager
from src.evaluation.evaluator import BiometricEvaluator
from src.evaluation.visualizer import ResultVisualizer
from src.features.glcm_extractor import GlcmFeatureExtractor
from src.features.lbp_extractor import LbpFeatureExtractor
from src.matching.matcher import MatchingEngine
from src.preprocessing.preprocessor import ImagePreprocessor
from src.segmentation.router import segment_roi
from src.utils.config import FIGURES_DIR, PROJECT_ROOT_DIR, TABLES_DIR
from src.utils.image_io import ReadImage
from src.utils.logger import GetLogger

loggerInstance = GetLogger("ParameterTuner")


class ParameterTuner:
    """Ön işleme, doku analizi ve eşleştirme hiperparametrelerini sistematik olarak optimize eden modül."""

    def __init__(
        self,
        temporaryDatabasePath: Optional[Path] = None,
    ) -> None:
        """Hiperparametre ayarlayıcıyı başlatır."""
        self.databasePath = (
            Path(temporaryDatabasePath).resolve()
            if temporaryDatabasePath
            else Path("data/database/tuning_temp.db").resolve()
        )
        self.evaluator = BiometricEvaluator()
        self.visualizer = ResultVisualizer()

    def EvaluateConfiguration(
        self,
        configurationDict: Dict[str, Any],
        galleryList: List[Dict[str, str]],
        testList: List[Dict[str, str]],
        speciesName: str,
    ) -> Dict[str, Any]:
        """Tek bir parametre kombinasyonunu galeri ve test setleri üzerinde değerlendirir."""
        # 1. Ön İşleyiciyi Parametrelere Göre Yapılandır
        claheClipLimit = configurationDict.get("claheClipLimit", 2.0)
        claheGridSize = configurationDict.get("claheGridSize", (8, 8))
        preprocessorInstance = ImagePreprocessor(
            claheClipLimit=claheClipLimit,
            claheTileGridSize=claheGridSize,
        )

        # 2. Öznitelik Çıkarıcıları Yapılandır
        lbpRadius = configurationDict.get("lbpRadius", 1)
        lbpPoints = configurationDict.get("lbpPoints", 8)
        lbpGridX = configurationDict.get("lbpGrid", 4)
        lbpExtractorInstance = LbpFeatureExtractor(
            radius=lbpRadius,
            pointsCount=lbpPoints,
            gridCellsX=lbpGridX,
            gridCellsY=lbpGridX,
        )

        glcmLevels = configurationDict.get("glcmLevels", 16)
        glcmDistances = configurationDict.get("glcmDistances", (1, 2, 3))
        glcmExtractorInstance = GlcmFeatureExtractor(
            grayLevelsCount=glcmLevels,
            distances=glcmDistances,
        )

        featureMethod = configurationDict.get("featureMethod", "lbp_glcm")
        metricName = configurationDict.get("metric", "chi_square")

        def ExtractFeaturesForConfig(roiMatrix: np.ndarray) -> np.ndarray:
            if featureMethod == "lbp":
                return lbpExtractorInstance.ExtractFeatures(roiMatrix)
            elif featureMethod == "glcm":
                return glcmExtractorInstance.ExtractFeatures(roiMatrix)
            else:
                vectorLbp = lbpExtractorInstance.ExtractFeatures(roiMatrix)
                vectorGlcm = glcmExtractorInstance.ExtractFeatures(roiMatrix)
                combined = np.concatenate([vectorLbp, vectorGlcm])
                normVal = np.linalg.norm(combined)
                if normVal > 0.0:
                    combined /= normVal
                return combined.astype(np.float32)

        # 3. Veritabanını Temizle ve Galeriyi Kaydet
        dbManager = DatabaseManager(databasePath=self.databasePath)
        dbManager.ClearDatabase()

        startTime = time.time()

        for galleryItem in galleryList:
            animalId = galleryItem["animalId"]
            imagePath = PROJECT_ROOT_DIR / galleryItem["imagePath"]
            if not imagePath.is_file():
                imagePath = PROJECT_ROOT_DIR / "data" / galleryItem["imagePath"]

            loadedImage = ReadImage(imagePath)
            if loadedImage is None:
                continue

            preprocessed = preprocessorInstance.ProcessImage(loadedImage)
            roi = segment_roi(preprocessed, speciesName)
            features = ExtractFeaturesForConfig(roi)

            dbManager.RegisterAnimal(
                animalId=animalId,
                speciesName=speciesName,
                featureVector=features,
            )

        # 4. Test Sorgularını Çalıştır
        matchingEngine = MatchingEngine(databaseManager=dbManager, metric=metricName)
        predictionsList = []
        groundTruthList = []

        for testItem in testList:
            expectedAnimalId = testItem["animalId"]
            imagePath = PROJECT_ROOT_DIR / testItem["imagePath"]
            if not imagePath.is_file():
                imagePath = PROJECT_ROOT_DIR / "data" / testItem["imagePath"]

            loadedImage = ReadImage(imagePath)
            if loadedImage is None:
                continue

            preprocessed = preprocessorInstance.ProcessImage(loadedImage)
            roi = segment_roi(preprocessed, speciesName)
            queryFeatures = ExtractFeaturesForConfig(roi)

            matchResults = matchingEngine.Identify(
                featureVector=queryFeatures,
                speciesName=speciesName,
                topK=1,
            )

            predictedId = matchResults[0][0] if matchResults else ""
            predictionsList.append(predictedId)
            groundTruthList.append(expectedAnimalId)

        elapsedTime = time.time() - startTime

        # 5. Metrikleri Hesapla
        evalMetrics = self.evaluator.Evaluate(predictionsList, groundTruthList)
        rank1Accuracy = evalMetrics.get("rank1Accuracy", 0.0)

        resultDictionary = {
            "configName": configurationDict.get("name", "Unnamed"),
            "claheClipLimit": claheClipLimit,
            "claheGridSize": f"{claheGridSize[0]}x{claheGridSize[1]}",
            "lbpRadius": lbpRadius,
            "lbpPoints": lbpPoints,
            "lbpGrid": f"{lbpGridX}x{lbpGridX}",
            "glcmLevels": glcmLevels,
            "featureMethod": featureMethod,
            "metric": metricName,
            "rank1Accuracy": rank1Accuracy,
            "f1Macro": evalMetrics.get("f1Macro", 0.0),
            "precisionMacro": evalMetrics.get("precisionMacro", 0.0),
            "recallMacro": evalMetrics.get("recallMacro", 0.0),
            "durationSeconds": round(elapsedTime, 3),
        }
        return resultDictionary

    def RunGridSearch(
        self,
        splitMetadata: Dict[str, Any],
        candidateConfigurations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Aday konfigürasyon listesi üzerinde arama yapar ve en başarılı yapılandırmayı seçer."""
        speciesName = splitMetadata["species"]
        galleryList = splitMetadata["gallery"]
        testList = splitMetadata["test"]

        # Varsayılan sistematik aday konfigürasyonlar
        if not candidateConfigurations:
            candidateConfigurations = [
                {
                    "name": "Config_1_Baseline",
                    "claheClipLimit": 2.0,
                    "claheGridSize": (8, 8),
                    "lbpRadius": 1,
                    "lbpPoints": 8,
                    "lbpGrid": 4,
                    "glcmLevels": 16,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "lbp_glcm",
                    "metric": "chi_square",
                },
                {
                    "name": "Config_2_HighContrast",
                    "claheClipLimit": 3.5,
                    "claheGridSize": (8, 8),
                    "lbpRadius": 1,
                    "lbpPoints": 8,
                    "lbpGrid": 4,
                    "glcmLevels": 16,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "lbp_glcm",
                    "metric": "chi_square",
                },
                {
                    "name": "Config_3_FineGrid_LBP",
                    "claheClipLimit": 2.0,
                    "claheGridSize": (4, 4),
                    "lbpRadius": 1,
                    "lbpPoints": 8,
                    "lbpGrid": 4,
                    "glcmLevels": 32,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "lbp_glcm",
                    "metric": "chi_square",
                },
                {
                    "name": "Config_4_ExtendedRadius_LBP",
                    "claheClipLimit": 2.0,
                    "claheGridSize": (8, 8),
                    "lbpRadius": 3,
                    "lbpPoints": 24,
                    "lbpGrid": 3,
                    "glcmLevels": 16,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "lbp_glcm",
                    "metric": "chi_square",
                },
                {
                    "name": "Config_5_Cosine_Metric",
                    "claheClipLimit": 2.0,
                    "claheGridSize": (8, 8),
                    "lbpRadius": 1,
                    "lbpPoints": 8,
                    "lbpGrid": 4,
                    "glcmLevels": 16,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "lbp_glcm",
                    "metric": "cosine",
                },
                {
                    "name": "Config_6_Only_LBP",
                    "claheClipLimit": 2.0,
                    "claheGridSize": (8, 8),
                    "lbpRadius": 1,
                    "lbpPoints": 8,
                    "lbpGrid": 4,
                    "glcmLevels": 16,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "lbp",
                    "metric": "chi_square",
                },
                {
                    "name": "Config_7_Only_GLCM",
                    "claheClipLimit": 2.0,
                    "claheGridSize": (8, 8),
                    "lbpRadius": 1,
                    "lbpPoints": 8,
                    "lbpGrid": 4,
                    "glcmLevels": 16,
                    "glcmDistances": (1, 2, 3),
                    "featureMethod": "glcm",
                    "metric": "chi_square",
                },
            ]

        loggerInstance.info(
            f"Parametre optimizasyonu başlatıldı ({speciesName}): {len(candidateConfigurations)} konfigürasyon test edilecek."
        )

        allResultsList: List[Dict[str, Any]] = []

        for candidateConfig in candidateConfigurations:
            configName = candidateConfig.get("name", "Unnamed")
            loggerInstance.info(f"Test ediliyor: {configName}...")
            evaluationResult = self.EvaluateConfiguration(
                configurationDict=candidateConfig,
                galleryList=galleryList,
                testList=testList,
                speciesName=speciesName,
            )
            allResultsList.append(evaluationResult)
            loggerInstance.info(
                f"[{configName}] Rank-1: %{evaluationResult['rank1Accuracy'] * 100.0:.2f} | "
                f"Macro-F1: {evaluationResult['f1Macro']:.4f} | "
                f"Süre: {evaluationResult['durationSeconds']}s"
            )

        # Sonuçları DataFrame'e dönüştür ve Rank-1 doğruluğuna göre sırala
        resultsDataFrame = pd.DataFrame(allResultsList)
        resultsDataFrame.sort_values(by=["rank1Accuracy", "f1Macro"], ascending=[False, False], inplace=True)

        # Tabloyu CSV olarak kaydet
        outputCsvPath = TABLES_DIR / f"parameter_tuning_{speciesName}.csv"
        resultsDataFrame.to_csv(outputCsvPath, index=False, encoding="utf-8-sig")
        loggerInstance.info(f"Parametre ayarlama tablosu kaydedildi: {outputCsvPath}")

        # Karşılaştırma grafiği çiz
        self.PlotTuningChart(resultsDataFrame, speciesName)

        bestConfigurationResult = resultsDataFrame.iloc[0].to_dict()
        loggerInstance.info(
            f"En iyi konfigürasyon seçildi: {bestConfigurationResult['configName']} "
            f"(Rank-1: %{bestConfigurationResult['rank1Accuracy'] * 100.0:.2f})"
        )

        return {
            "species": speciesName,
            "bestConfiguration": bestConfigurationResult,
            "allResults": allResultsList,
            "csvPath": str(outputCsvPath),
        }

    @staticmethod
    def PlotTuningChart(resultsDataFrame: pd.DataFrame, speciesName: str) -> Path:
        """Konfigürasyonların Rank-1 doğruluklarını gösteren grafik üretir."""
        destinationPath = FIGURES_DIR / f"parameter_tuning_{speciesName}.png"

        configNames = resultsDataFrame["configName"].tolist()
        accuracyValues = [val * 100.0 for val in resultsDataFrame["rank1Accuracy"].tolist()]

        plt.figure(figsize=(10, 5))
        barColors = ["#1b4f72" if idx == 0 else "#2e86c1" for idx in range(len(configNames))]
        barObjects = plt.bar(configNames, accuracyValues, color=barColors, width=0.55)

        plt.axhline(90.0, color="#cb4335", linestyle="--", linewidth=1.5, label="Hedef Başarı (%90)")
        plt.ylim(0, 110)
        plt.title(f"Hiperparametre Ayarlama Sonuçları — {speciesName.upper()} (Rank-1 Doğruluk)", fontsize=12, pad=12)
        plt.xlabel("Konfigürasyon", fontsize=10)
        plt.ylabel("Rank-1 Doğruluk (%)", fontsize=10)
        plt.xticks(rotation=25, ha="right", fontsize=9)
        plt.legend(loc="lower right")

        for individualBar in barObjects:
            barHeight = individualBar.get_height()
            plt.text(
                individualBar.get_x() + individualBar.get_width() / 2.0,
                barHeight + 1.5,
                f"%{barHeight:.1f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

        plt.tight_layout()
        plt.savefig(destinationPath, dpi=300)
        plt.close()
        return destinationPath
