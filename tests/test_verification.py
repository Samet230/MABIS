import numpy as np
import pytest

from src.database.db_manager import DatabaseManager
from src.matching.matcher import (
    DEFAULT_OPEN_SET_REJECTION_THRESHOLD,
    DEFAULT_VERIFICATION_THRESHOLD,
    UNKNOWN_ANIMAL_LABEL,
    MatchingEngine,
    identify,
    verify,
)


@pytest.fixture
def mockDatabaseManager(tmp_path):
    """Geçici test veritabanı oluşturan fixture."""
    testDbFile = tmp_path / "test_verification.db"
    dbManager = DatabaseManager(databasePath=testDbFile)

    # 1D özellik vektörleri ile iki hayvan kaydet
    vectorA1 = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    vectorA2 = np.array([0.11, 0.19, 0.31, 0.39], dtype=np.float32)
    vectorB = np.array([0.9, 0.8, 0.1, 0.2], dtype=np.float32)

    dbManager.RegisterAnimal("cattle_001", "cattle", vectorA1)
    dbManager.RegisterAnimal("cattle_001", "cattle", vectorA2)
    dbManager.RegisterAnimal("cattle_002", "cattle", vectorB)

    yield dbManager


def test_verification_genuine_match(mockDatabaseManager):
    """Aynı hayvana ait sorgunun 1:1 doğrulamada kabul edilmesi doğrulanır."""
    engine = MatchingEngine(databaseManager=mockDatabaseManager)
    queryFeature = np.array([0.105, 0.205, 0.295, 0.395], dtype=np.float32)

    isAccepted, score = engine.Verify(
        featureVector=queryFeature,
        claimedAnimalId="cattle_001",
        speciesName="cattle",
        verificationThreshold=0.80,
    )

    assert isAccepted is True
    assert score > 0.80


def test_verification_impostor_rejection(mockDatabaseManager):
    """Farklı bir hayvana ait sorgunun 1:1 doğrulamada reddedilmesi doğrulanır."""
    engine = MatchingEngine(databaseManager=mockDatabaseManager)
    queryFeature = np.array([0.9, 0.8, 0.1, 0.2], dtype=np.float32)  # cattle_002 özelliği

    isAccepted, score = engine.Verify(
        featureVector=queryFeature,
        claimedAnimalId="cattle_001",  # cattle_001 olduğunu iddia ediyor
        speciesName="cattle",
        verificationThreshold=0.80,
    )

    assert isAccepted is False
    assert score < 0.80


def test_verification_nonexistent_animal(mockDatabaseManager):
    """Veritabanında olmayan bir kimlik iddia edildiğinde False dönmesi doğrulanır."""
    engine = MatchingEngine(databaseManager=mockDatabaseManager)
    queryFeature = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

    isAccepted, score = engine.Verify(
        featureVector=queryFeature,
        claimedAnimalId="cattle_999",
        speciesName="cattle",
    )

    assert isAccepted is False
    assert score == 0.0


def test_open_set_rejection(mockDatabaseManager):
    """Veritabanındaki hiçbir adaya benzemeyen bir sorgunun 'unknown' olarak reddedilmesi doğrulanır."""
    engine = MatchingEngine(databaseManager=mockDatabaseManager)
    # Tamamen alakasız ve aşırı uç bir vektör
    outlierFeature = np.array([100.0, 50.0, 20.0, 80.0], dtype=np.float32)

    results = engine.Identify(
        featureVector=outlierFeature,
        speciesName="cattle",
        topK=1,
        minConfidenceThreshold=0.50,
    )

    assert len(results) == 1
    assert results[0][0] == UNKNOWN_ANIMAL_LABEL
    assert results[0][1] < 0.50
