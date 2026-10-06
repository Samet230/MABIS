import tempfile
from pathlib import Path
import cv2
import numpy as np
import pytest

from src.database.db_manager import DatabaseManager
from src.evaluation.evaluator import evaluate
from src.features.feature_extractor import extract_features
from src.matching.matcher import MatchingEngine
from src.preprocessing.preprocessor import preprocess
from src.segmentation.router import segment_roi


def GenerateSpeciesSampleImage(speciesName: str, patternSeed: int, isQuery: bool = False) -> np.ndarray:
    """Belirli bir türe ve desene göre sentetik test görüntüsü üretir."""
    imageMatrix = np.full((350, 350, 3), 150, dtype=np.uint8)

    if speciesName == "cattle":
        # Sığır burun deseni
        cv2.ellipse(imageMatrix, (175, 175), (100, 70), 0, 0, 360, (60, 60, 60), -1)
        # Desene göre çizgiler
        lineStep = 12 + (patternSeed % 3) * 4
        for coordY in range(125, 225, lineStep):
            cv2.line(imageMatrix, (100, coordY), (250, coordY), (20, 20, 20), 2)
        cv2.circle(imageMatrix, (135, 175), 14, (20, 20, 20), -1)
        cv2.circle(imageMatrix, (215, 175), 14, (20, 20, 20), -1)

    elif speciesName == "dog":
        # Köpek yüzü ve alt-orta burun lekesi
        cv2.circle(imageMatrix, (175, 175), 120, (110, 110, 110), -1)
        # Burun lekesi (y=215, x=175)
        cv2.ellipse(imageMatrix, (175, 215), (45, 30), 0, 0, 360, (30, 30, 30), -1)
        # Desene göre iç doku
        for coordX in range(145, 205, 10 + (patternSeed % 2) * 5):
            cv2.line(imageMatrix, (coordX, 200), (coordX, 230), (10, 10, 10), 2)

    elif speciesName == "cat":
        # Kedi yüzü ve kulaklar
        cv2.circle(imageMatrix, (175, 175), 100, (130, 130, 130), -1)
        # Kulak üçgenleri
        triangleLeft = np.array([[100, 110], [130, 40], [150, 100]])
        triangleRight = np.array([[200, 100], [220, 40], [250, 110]])
        cv2.fillPoly(imageMatrix, [triangleLeft, triangleRight], (100, 100, 100))
        # Gözler ve bıyık çizgileri
        cv2.circle(imageMatrix, (140, 150), 12, (20, 20, 20), -1)
        cv2.circle(imageMatrix, (210, 150), 12, (20, 20, 20), -1)
        whiskerStep = 8 + (patternSeed % 3) * 3
        for offset in range(-15, 20, whiskerStep):
            cv2.line(imageMatrix, (80, 185 + offset), (150, 185 + offset), (40, 40, 40), 2)
            cv2.line(imageMatrix, (200, 185 + offset), (270, 185 + offset), (40, 40, 40), 2)

    if isQuery:
        blurred = cv2.GaussianBlur(imageMatrix, (3, 3), 0.5)
        adjusted = np.clip(blurred.astype(np.int16) + 6, 0, 255)
        return adjusted.astype(np.uint8)

    return imageMatrix


def test_multi_species_pipeline_integration():
    """3 türün (cattle, dog, cat) tek veritabanı ve eşleştirme hattında entegre çalıştığını test eder."""
    with tempfile.TemporaryDirectory() as tempDir:
        testDbPath = Path(tempDir) / "multi_species.db"
        dbManager = DatabaseManager(databasePath=testDbPath)
        matcher = MatchingEngine(databaseManager=dbManager, metric="chi_square")

        speciesDefinitions = [
            ("cattle", ["cow_1", "cow_2"]),
            ("dog", ["dog_1", "dog_2"]),
            ("cat", ["cat_1", "cat_2"]),
        ]

        # 1. Tüm türlerin galeri kayıtlarını veritabanına ekle
        for speciesName, animalIdList in speciesDefinitions:
            for seedIdx, animalId in enumerate(animalIdList, start=1):
                rawImage = GenerateSpeciesSampleImage(speciesName, seedIdx, isQuery=False)
                preprocessed = preprocess(rawImage)
                roi = segment_roi(preprocessed, speciesName)
                features = extract_features(roi, method="lbp_glcm")

                dbManager.RegisterAnimal(
                    animalId=animalId,
                    speciesName=speciesName,
                    featureVector=features,
                )

        assert dbManager.CountRecords() == 6
        assert dbManager.CountRecords("cattle") == 2
        assert dbManager.CountRecords("dog") == 2
        assert dbManager.CountRecords("cat") == 2

        # 2. Her türü kendi sorgu görüntüleriyle doğrula
        allPredictions = []
        allGroundTruth = []

        for speciesName, animalIdList in speciesDefinitions:
            for seedIdx, expectedAnimalId in enumerate(animalIdList, start=1):
                rawQuery = GenerateSpeciesSampleImage(speciesName, seedIdx, isQuery=True)
                preprocessed = preprocess(rawQuery)
                roi = segment_roi(preprocessed, speciesName)
                queryFeatures = extract_features(roi, method="lbp_glcm")

                predictions = matcher.Identify(
                    featureVector=queryFeatures,
                    speciesName=speciesName,
                    topK=1,
                )

                assert len(predictions) > 0
                predictedId, confidence = predictions[0]

                allPredictions.append(predictedId)
                allGroundTruth.append(expectedAnimalId)
                assert confidence > 0.0

        # Değerlendirme modülünü çalıştır
        evalResults = evaluate(allPredictions, allGroundTruth)
        assert evalResults["totalSamples"] == 6
        assert evalResults["rank1Accuracy"] >= 0.83  # En az 5/6 veya 6/6
        assert "confusionMatrix" in evalResults
