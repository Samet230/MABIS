import tempfile
from pathlib import Path
import numpy as np
import pytest

from src.database.db_manager import DatabaseManager


def test_database_manager_crud():
    """Veritabanı kayıt ekleme, tür bazlı filtreleme ve temizleme işlevlerini test eder."""
    with tempfile.TemporaryDirectory() as tempDir:
        dbPath = Path(tempDir) / "test_mabis.db"
        manager = DatabaseManager(databasePath=dbPath)

        # 1. Kayıt ekleme
        vec1 = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        vec2 = np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32)
        vecDog = np.array([0.9, 0.1, 0.2, 0.3], dtype=np.float32)

        manager.RegisterAnimal("animal_001", "cattle", vec1, {"source": "zenodo"})
        manager.RegisterAnimal("animal_002", "cattle", vec2)
        manager.RegisterAnimal("animal_dog_01", "dog", vecDog)

        assert manager.CountRecords() == 3
        assert manager.CountRecords("cattle") == 2
        assert manager.CountRecords("dog") == 1
        assert manager.CountRecords("cat") == 0

        # 2. Kayıtları getirme ve tür izolasyonu
        cattleRecords = manager.GetRecordsBySpecies("cattle")
        assert len(cattleRecords) == 2

        animalId, retrievedVec, metadata = cattleRecords[0]
        assert animalId == "animal_001"
        assert np.allclose(retrievedVec, vec1)
        assert metadata.get("source") == "zenodo"

        # 3. Temizleme
        manager.ClearDatabase("cattle")
        assert manager.CountRecords("cattle") == 0
        assert manager.CountRecords("dog") == 1

        manager.ClearDatabase()
        assert manager.CountRecords() == 0


def test_database_2d_descriptors():
    """2D tanımlayıcı matrislerinin (SIFT/ORB) veritabanında doğru saklandığını test eder."""
    with tempfile.TemporaryDirectory() as tempDir:
        dbPath = Path(tempDir) / "test_descriptors.db"
        manager = DatabaseManager(databasePath=dbPath)

        siftMatrix = np.random.randn(25, 128).astype(np.float32)
        manager.RegisterAnimal("cow_sift_01", "cattle", siftMatrix)

        records = manager.GetRecordsBySpecies("cattle")
        assert len(records) == 1
        animalId, retrievedMatrix, _ = records[0]
        assert animalId == "cow_sift_01"
        assert retrievedMatrix.shape == (25, 128)
        assert np.allclose(retrievedMatrix, siftMatrix)
