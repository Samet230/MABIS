import tempfile
from pathlib import Path
from typing import List
import cv2
import numpy as np
import pytest

from src.database.db_manager import DatabaseManager
from src.features.feature_extractor import extract_features
from src.matching.matcher import MatchingEngine
from src.preprocessing.preprocessor import preprocess
from src.segmentation.router import segment_roi


def GenerateDistinctCattleImage(patternType: str, isQuery: bool = False) -> np.ndarray:
    """Biyometrik olarak ayırt edici yapısal burun deseni (sırtlar, oluklar, boncuklar) üretir.

    Args:
        patternType: 'horizontal' | 'vertical' | 'beaded' | 'diagonal'.
        isQuery: True ise ikinci bir çekimi simüle etmek için hafif aydınlatma ve yumuşatma uygular.

    Returns:
        np.ndarray: 400x400 BGR sentetik sığır burun görüntüsü.
    """
    imageMatrix = np.full((400, 400, 3), 160, dtype=np.uint8)

    # Burun taban alanı (koyu elips)
    cv2.ellipse(imageMatrix, (200, 200), (130, 90), 0, 0, 360, (65, 65, 65), -1)

    # Desene özgü yapısal doku
    if patternType == "horizontal":
        for coordY in range(140, 260, 12):
            cv2.line(imageMatrix, (100, coordY), (300, coordY), (25, 25, 25), 3)
    elif patternType == "vertical":
        for coordX in range(110, 290, 12):
            cv2.line(imageMatrix, (coordX, 130), (coordX, 270), (25, 25, 25), 3)
    elif patternType == "beaded":
        for coordY in range(130, 270, 15):
            for coordX in range(110, 290, 15):
                cv2.circle(imageMatrix, (coordX, coordY), 5, (20, 20, 20), -1)
    elif patternType == "diagonal":
        for offset in range(-80, 80, 14):
            cv2.line(
                imageMatrix,
                (120 + offset, 140),
                (260 + offset, 260),
                (25, 25, 25),
                3,
            )

    # Burun delikleri
    cv2.circle(imageMatrix, (140, 200), 16, (20, 20, 20), -1)
    cv2.circle(imageMatrix, (260, 200), 16, (20, 20, 20), -1)

    if isQuery:
        # İkinci çekim simülasyonu: Hafif bulanıklık ve parlaklık farkı
        blurredImage = cv2.GaussianBlur(imageMatrix, (3, 3), 0.6)
        queryAdjusted = np.clip(blurredImage.astype(np.int16) + 8, 0, 255)
        return queryAdjusted.astype(np.uint8)

    return imageMatrix


def test_cattle_end_to_end_vertical_slice():
    """Sığır türü için ham görüntüden kimlik tespitine uçtan uca dikey dilim testi."""
    with tempfile.TemporaryDirectory() as tempDir:
        testDbPath = Path(tempDir) / "cattle_e2e.db"
        dbManager = DatabaseManager(databasePath=testDbPath)
        matcher = MatchingEngine(databaseManager=dbManager, metric="chi_square")

        animalPatterns = [
            ("cow_alpha", "horizontal"),
            ("cow_bravo", "vertical"),
            ("cow_charlie", "beaded"),
            ("cow_delta", "diagonal"),
        ]

        # 1. Kayıt Aşaması (Registration Flow): Galeri görüntülerini kaydet
        for animalId, patternType in animalPatterns:
            rawGalleryImage = GenerateDistinctCattleImage(patternType=patternType, isQuery=False)

            # Standart pipeline akışı
            preprocessedImage = preprocess(rawGalleryImage)
            muzzleRoi = segment_roi(preprocessedImage, species="cattle")
            featureVector = extract_features(muzzleRoi, method="lbp_glcm")

            dbManager.RegisterAnimal(
                animalId=animalId,
                speciesName="cattle",
                featureVector=featureVector,
                metadataDict={"split": "gallery", "pattern": patternType},
            )

        assert dbManager.CountRecords("cattle") == 4

        # 2. Sorgulama Aşaması (Identification Flow): İkinci çekim sorgu görüntüleriyle sorgula
        correctMatchesCount = 0

        for expectedAnimalId, patternType in animalPatterns:
            rawQueryImage = GenerateDistinctCattleImage(patternType=patternType, isQuery=True)

            # Sorgu akışı
            preprocessedQuery = preprocess(rawQueryImage)
            queryRoi = segment_roi(preprocessedQuery, species="cattle")
            queryFeatures = extract_features(queryRoi, method="lbp_glcm")

            # Eşleştirme (Rank-1)
            matchPredictions = matcher.Identify(
                featureVector=queryFeatures,
                speciesName="cattle",
                topK=1,
            )

            assert len(matchPredictions) > 0
            predictedAnimalId, confidenceScore = matchPredictions[0]

            if predictedAnimalId == expectedAnimalId:
                correctMatchesCount += 1

            assert confidenceScore > 0.0

        # Kapalı-küme uçtan uca Rank-1 doğruluk testi (%100 doğru eşleşme)
        rank1Accuracy = correctMatchesCount / len(animalPatterns)
        assert rank1Accuracy == 1.0
