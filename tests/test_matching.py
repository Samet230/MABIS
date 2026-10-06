import tempfile
from pathlib import Path
import numpy as np
import pytest

from src.database.db_manager import DatabaseManager
from src.matching.matcher import MatchingEngine


def test_distance_metrics():
    """Mesafe ve benzerlik fonksiyonlarının doğru çalıştığını test eder."""
    vecA = np.array([0.2, 0.3, 0.5], dtype=np.float32)
    vecB = np.array([0.2, 0.3, 0.5], dtype=np.float32)
    vecC = np.array([0.8, 0.1, 0.1], dtype=np.float32)

    # Aynı vektörler
    chiDistIdentical = MatchingEngine.CalculateChiSquareDistance(vecA, vecB)
    assert np.isclose(chiDistIdentical, 0.0, atol=1e-5)

    cosSimIdentical = MatchingEngine.CalculateCosineSimilarity(vecA, vecB)
    assert np.isclose(cosSimIdentical, 1.0, atol=1e-5)

    # Farklı vektörler
    chiDistDiff = MatchingEngine.CalculateChiSquareDistance(vecA, vecC)
    assert chiDistDiff > 0.0

    cosSimDiff = MatchingEngine.CalculateCosineSimilarity(vecA, vecC)
    assert cosSimDiff < 1.0


def test_matching_engine_identify():
    """Eşleştirme motorunun sorgu vektörünü doğru adayla Rank-1 eşleştirdiğini test eder."""
    with tempfile.TemporaryDirectory() as tempDir:
        dbPath = Path(tempDir) / "test_matcher.db"
        dbManager = DatabaseManager(databasePath=dbPath)
        matcher = MatchingEngine(databaseManager=dbManager, metric="chi_square")

        # Veritabanına 3 farklı birey kaydet
        vecCowA = np.array([0.6, 0.2, 0.1, 0.1], dtype=np.float32)
        vecCowB = np.array([0.1, 0.7, 0.1, 0.1], dtype=np.float32)
        vecCowC = np.array([0.1, 0.1, 0.7, 0.1], dtype=np.float32)

        dbManager.RegisterAnimal("cow_A", "cattle", vecCowA)
        dbManager.RegisterAnimal("cow_B", "cattle", vecCowB)
        dbManager.RegisterAnimal("cow_C", "cattle", vecCowC)

        # cow_A'ya çok yakın hafif gürültülü bir sorgu vektörü
        queryVecA = np.array([0.58, 0.21, 0.11, 0.10], dtype=np.float32)

        matches = matcher.Identify(queryVecA, speciesName="cattle", topK=2)

        assert len(matches) == 2
        bestMatchAnimalId, bestConfidence = matches[0]
        # Rank-1 tahmini kesinlikle cow_A olmalıdır
        assert bestMatchAnimalId == "cow_A"
        assert bestConfidence > 0.90
        # Rank-2 güven skoru Rank-1'den düşük olmalıdır
        assert matches[0][1] >= matches[1][1]


def test_matching_empty_database():
    """Veritabanında kayıt yokken güvenli şekilde boş liste döndürüldüğünü test eder."""
    with tempfile.TemporaryDirectory() as tempDir:
        dbPath = Path(tempDir) / "empty.db"
        dbManager = DatabaseManager(databasePath=dbPath)
        matcher = MatchingEngine(databaseManager=dbManager)

        dummyVec = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        matches = matcher.Identify(dummyVec, speciesName="cattle")
        assert matches == []
