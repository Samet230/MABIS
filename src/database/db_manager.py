import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from src.utils.config import DATA_DIR, VALID_SPECIES
from src.utils.image_io import ValidateSpecies
from src.utils.logger import GetLogger

loggerInstance = GetLogger("DatabaseManager")

DEFAULT_DATABASE_PATH: Path = DATA_DIR / "database" / "mabis_features.db"


class DatabaseManager:
    """Hayvan biyometrik öznitelik kayıtlarını SQLite veritabanında saklayan ve yöneten sınıf."""

    def __init__(self, databasePath: Path = DEFAULT_DATABASE_PATH) -> None:
        """Veritabanı yöneticisini başlatır ve tablo şemasını oluşturur."""
        self.databasePath = Path(databasePath).resolve()
        self.databasePath.parent.mkdir(parents=True, exist_ok=True)
        self.InitializeSchema()

    def GetConnection(self) -> sqlite3.Connection:
        """Yeni bir SQLite bağlantısı oluşturur."""
        return sqlite3.connect(str(self.databasePath))

    def InitializeSchema(self) -> None:
        """Öznitelik kayıt tablosunu ve indeksleri başlatır."""
        databaseConnection = self.GetConnection()
        try:
            cursorInstance = databaseConnection.cursor()
            cursorInstance.execute(
                """
                CREATE TABLE IF NOT EXISTS animal_records (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    animal_id TEXT NOT NULL,
                    species TEXT NOT NULL,
                    feature_bytes BLOB NOT NULL,
                    feature_shape TEXT NOT NULL,
                    feature_dtype TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cursorInstance.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_species 
                ON animal_records (species);
                """
            )
            cursorInstance.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_animal_id 
                ON animal_records (animal_id);
                """
            )
            databaseConnection.commit()
        except Exception as schemaException:
            loggerInstance.error(f"Veritabanı şema başlatma hatası: {schemaException}")
            raise
        finally:
            databaseConnection.close()

    def RegisterAnimal(
        self,
        animalId: str,
        speciesName: str,
        featureVector: np.ndarray,
        metadataDict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Yeni bir hayvan öznitelik kaydını veritabanına ekler."""
        if not animalId or not isinstance(animalId, str):
            raise ValueError("Geçersiz animalId.")

        if not ValidateSpecies(speciesName):
            raise ValueError(
                f"Geçersiz tür '{speciesName}'. Desteklenenler: {VALID_SPECIES}"
            )

        if featureVector is None:
            raise ValueError("Kaydedilecek öznitelik vektörü None olamaz.")

        if featureVector.size == 0:
            columnCount = featureVector.shape[1] if featureVector.ndim > 1 else 1
            featureVector = np.zeros((1, columnCount), dtype=featureVector.dtype)

        normalizedSpecies = speciesName.strip().lower()
        featureBytes = featureVector.tobytes()
        featureShapeString = json.dumps(list(featureVector.shape))
        featureDtypeString = str(featureVector.dtype)
        metadataJsonString = json.dumps(metadataDict if metadataDict else {}, ensure_ascii=False)

        databaseConnection = self.GetConnection()
        try:
            cursorInstance = databaseConnection.cursor()
            cursorInstance.execute(
                """
                INSERT INTO animal_records (
                    animal_id, species, feature_bytes, feature_shape, feature_dtype, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    animalId,
                    normalizedSpecies,
                    featureBytes,
                    featureShapeString,
                    featureDtypeString,
                    metadataJsonString,
                ),
            )
            databaseConnection.commit()
        except Exception as insertException:
            loggerInstance.error(
                f"Hayvan kaydı eklenemedi ({animalId}, {speciesName}): {insertException}"
            )
            raise
        finally:
            databaseConnection.close()

    def GetRecordsBySpecies(
        self,
        speciesName: str,
    ) -> List[Tuple[str, np.ndarray, Dict[str, Any]]]:
        """Belirtilen türe ait tüm kayıtlı öznitelikleri ve kimlikleri döndürür."""
        if not ValidateSpecies(speciesName):
            raise ValueError(f"Geçersiz tür: {speciesName}")

        normalizedSpecies = speciesName.strip().lower()
        retrievedRecords: List[Tuple[str, np.ndarray, Dict[str, Any]]] = []

        databaseConnection = self.GetConnection()
        try:
            cursorInstance = databaseConnection.cursor()
            cursorInstance.execute(
                """
                SELECT animal_id, feature_bytes, feature_shape, feature_dtype, metadata_json
                FROM animal_records
                WHERE species = ?;
                """,
                (normalizedSpecies,),
            )
            queryRows = cursorInstance.fetchall()

            for queryRow in queryRows:
                animalId = queryRow[0]
                rawBytes = queryRow[1]
                shapeList = json.loads(queryRow[2])
                dtypeObject = np.dtype(queryRow[3])
                metadataDictionary = json.loads(queryRow[4]) if queryRow[4] else {}

                reconstructedArray = np.frombuffer(rawBytes, dtype=dtypeObject).reshape(
                    tuple(shapeList)
                )
                retrievedRecords.append((animalId, reconstructedArray, metadataDictionary))

            return retrievedRecords

        except Exception as queryException:
            loggerInstance.error(
                f"Kayıtlar getirilemedi ({speciesName}): {queryException}"
            )
            raise
        finally:
            databaseConnection.close()

    def ClearDatabase(self, speciesName: Optional[str] = None) -> None:
        """Veritabanındaki kayıtları temizler."""
        databaseConnection = self.GetConnection()
        try:
            cursorInstance = databaseConnection.cursor()
            if speciesName:
                cursorInstance.execute(
                    "DELETE FROM animal_records WHERE species = ?;",
                    (speciesName.strip().lower(),),
                )
            else:
                cursorInstance.execute("DELETE FROM animal_records;")
            databaseConnection.commit()
        except Exception as deleteException:
            loggerInstance.error(f"Veritabanı temizleme hatası: {deleteException}")
            raise
        finally:
            databaseConnection.close()

    def CountRecords(self, speciesName: Optional[str] = None) -> int:
        """Kayıtlı hayvan öznitelik sayısını döndürür."""
        databaseConnection = self.GetConnection()
        try:
            cursorInstance = databaseConnection.cursor()
            if speciesName:
                cursorInstance.execute(
                    "SELECT COUNT(*) FROM animal_records WHERE species = ?;",
                    (speciesName.strip().lower(),),
                )
            else:
                cursorInstance.execute("SELECT COUNT(*) FROM animal_records;")
            countResult = cursorInstance.fetchone()[0]
            return int(countResult)
        except Exception as countException:
            loggerInstance.error(f"Kayıt sayımı hatası: {countException}")
            return 0
        finally:
            databaseConnection.close()


# Standart sözleşme için varsayılan tekil veritabanı örneği (AGENTS.md ve ARCHITECTURE.md)
_defaultDatabaseManager = DatabaseManager()


def register(animal_id: str, species: str, feature_vector: np.ndarray) -> None:
    """ZooID standart modül sözleşmesine uygun hayvan kayıt fonksiyonu.

    Args:
        animal_id: Hayvan kimliği (string).
        species: Tür adı ('cattle' | 'dog' | 'cat').
        feature_vector: Kaydedilecek öznitelik vektörü.
    """
    _defaultDatabaseManager.RegisterAnimal(
        animalId=animal_id,
        speciesName=species,
        featureVector=feature_vector,
    )
