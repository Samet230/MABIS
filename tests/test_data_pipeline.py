import tempfile
from pathlib import Path
import cv2
import numpy as np
import pytest

from src.data.convert_dataset import DatasetConverter
from src.data.split_data import DatasetSplitter


def CreateSyntheticSharpImage(filePath: Path, patternNumber: int) -> None:
    """Belirtilen dosyaya keskin, yüksek varyanslı sentetik bir görüntü yazar."""
    syntheticMatrix = np.zeros((150, 150, 3), dtype=np.uint8)
    # Yüksek kontrastlı dama tahtası ve çizgiler
    syntheticMatrix[::4, ::4] = (255, 255, 255)
    cv2.putText(
        syntheticMatrix,
        f"ID_{patternNumber}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2,
    )
    filePath.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(filePath), syntheticMatrix)


def CreateSyntheticBlurryImage(filePath: Path) -> None:
    """Belirtilen dosyaya tamamen düz (bulanık/varyansı sıfır) bir görüntü yazar."""
    blurryMatrix = np.full((150, 150, 3), 120, dtype=np.uint8)
    filePath.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(filePath), blurryMatrix)


def test_dataset_converter_and_splitter_pipeline():
    """Veri dönüştürme ve bölümleme hattının entegre testini gerçekleştirir."""
    with tempfile.TemporaryDirectory() as temporaryWorkspace:
        workspacePath = Path(temporaryWorkspace)
        sourceDir = workspacePath / "raw_external"
        targetRawDir = workspacePath / "data" / "raw"
        splitsDir = workspacePath / "data" / "splits"

        # Birey 1: 5 adet keskin görüntü (kabul edilmeli)
        animal1Dir = sourceDir / "cow_alpha"
        for imageIdx in range(1, 6):
            CreateSyntheticSharpImage(animal1Dir / f"photo_{imageIdx}.jpg", imageIdx)

        # Birey 2: 4 adet keskin görüntü (kabul edilmeli)
        animal2Dir = sourceDir / "cow_beta"
        for imageIdx in range(1, 5):
            CreateSyntheticSharpImage(animal2Dir / f"cam_{imageIdx}.jpg", imageIdx + 10)

        # Birey 3: 2 keskin, 3 bulanık görüntü (geçerli adet 2 < 4 olduğu için elenmeli)
        animal3Dir = sourceDir / "cow_gamma"
        CreateSyntheticSharpImage(animal3Dir / "good_1.jpg", 30)
        CreateSyntheticSharpImage(animal3Dir / "good_2.jpg", 31)
        CreateSyntheticBlurryImage(animal3Dir / "bad_1.jpg")
        CreateSyntheticBlurryImage(animal3Dir / "bad_2.jpg")
        CreateSyntheticBlurryImage(animal3Dir / "bad_3.jpg")

        # 1. Dönüştürme Adımı
        converterInstance = DatasetConverter(
            targetRawDirectory=targetRawDir,
            blurThreshold=50.0,
            minImagesPerAnimal=4,
            minDimensions=(100, 100),
        )

        conversionReport = converterInstance.ConvertFolder(
            sourceDirectory=sourceDir,
            speciesName="cattle",
        )

        assert conversionReport["acceptedAnimalsCount"] == 2
        assert conversionReport["rejectedAnimalsCount"] == 1
        assert "cow_gamma" in conversionReport["rejectedAnimals"]
        assert conversionReport["totalAcceptedImages"] == 9

        # Hedef dizin kontrolü
        cattleRawDir = targetRawDir / "cattle"
        assert cattleRawDir.is_dir()
        convertedAnimals = list(cattleRawDir.iterdir())
        assert len(convertedAnimals) == 2

        # 2. Bölümleme Adımı (Train / Test Split)
        splitterInstance = DatasetSplitter(
            rawDirectory=targetRawDir,
            splitsDirectory=splitsDir,
        )

        splitMetadata = splitterInstance.CreateClosedSetSplit(
            speciesName="cattle",
            randomSeed=42,
            trainRatio=0.75,
            minImagesPerAnimal=4,
        )

        assert splitMetadata["totalQualifiedAnimals"] == 2
        assert splitMetadata["galleryCount"] > 0
        assert splitMetadata["testCount"] > 0
        assert splitMetadata["galleryCount"] + splitMetadata["testCount"] == 9

        # Her iki hayvanın da hem galeride hem testte temsil edildiğini doğrula (kapalı-küme)
        galleryAnimalIds = {item["animalId"] for item in splitMetadata["gallery"]}
        testAnimalIds = {item["animalId"] for item in splitMetadata["test"]}
        assert len(galleryAnimalIds) == 2
        assert len(testAnimalIds) == 2

        # Çoklu tohum testini doğrula
        generatedSplits = splitterInstance.GenerateMultiSeedSplits(
            speciesName="cattle",
            seedList=(42, 100),
        )
        assert len(generatedSplits) == 2
        for splitFile in generatedSplits:
            assert splitFile.is_file()
            loadedData = DatasetSplitter.LoadSplit(splitFile)
            assert loadedData["species"] == "cattle"
