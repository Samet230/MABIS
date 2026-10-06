import cv2
import numpy as np
import pytest

from src.preprocessing.species_validator import SpeciesValidator


@pytest.fixture
def speciesValidatorInstance():
    """SpeciesValidator fixture'ı."""
    return SpeciesValidator()


def CreateSyntheticCattleMuzzle() -> np.ndarray:
    """Yatay iki belirgin delik barındıran sığır burun desenini simüle eder."""
    img = np.ones((300, 400, 3), dtype=np.uint8) * 140
    # İki yatay simetrik koyu burun deliği ekle
    cv2.ellipse(img, (120, 180), (35, 20), 0, 0, 360, (20, 20, 20), thickness=-1)
    cv2.ellipse(img, (280, 180), (35, 20), 0, 0, 360, (20, 20, 20), thickness=-1)
    # Mikro-oluk dokusu
    noise = np.random.randint(-15, 15, (300, 400, 3), dtype=np.int16)
    noisyImg = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisyImg


def CreateSyntheticDogNose() -> np.ndarray:
    """Merkezi kalp/üçgen şekilli tek burun pedi barındıran köpek burnunu simüle eder."""
    img = np.ones((300, 300, 3), dtype=np.uint8) * 180
    # Merkezde tek koyu burun pedi
    trianglePoints = np.array([[150, 90], [90, 180], [210, 180]], np.int32)
    cv2.fillPoly(img, [trianglePoints], (25, 25, 25))
    cv2.circle(img, (120, 160), 12, (10, 10, 10), -1)
    cv2.circle(img, (180, 160), 12, (10, 10, 10), -1)
    return img


def test_cattle_muzzle_anatomy_detection(speciesValidatorInstance):
    """Sığır burnundaki yatay çift delik anatomisinin tespit edilmesi test edilir."""
    cattleImage = CreateSyntheticCattleMuzzle()
    anatomy = speciesValidatorInstance.AnalyzeMuzzleAnatomy(cattleImage)
    assert anatomy["hasDualHorizontalNostrils"] is True
    assert anatomy["nostrilSeparationDistance"] > 0.25


def test_dog_muzzle_anatomy_detection(speciesValidatorInstance):
    """Köpek burnundaki merkezi burun pedi anatomisinin tespit edilmesi test edilir."""
    dogImage = CreateSyntheticDogNose()
    anatomy = speciesValidatorInstance.AnalyzeMuzzleAnatomy(dogImage)
    assert anatomy["hasDualHorizontalNostrils"] is False
    assert anatomy["isDogNosePadCandidate"] is True


def test_cross_species_rejection_cattle_in_dog_category(speciesValidatorInstance):
    """Köpek kategorisinde büyükbaş sığır burnu yüklendiğinde reddedilmesi test edilir."""
    cattleImage = CreateSyntheticCattleMuzzle()
    isValid, message, detectedSpecies = speciesValidatorInstance.ValidateCategory(
        imageMatrix=cattleImage,
        selectedCategory="stray",
        selectedSubType="dog",
    )
    assert isValid is False
    assert detectedSpecies == "cattle"
    assert "büyükbaş" in message.lower()


def test_cross_species_rejection_dog_in_cattle_category(speciesValidatorInstance):
    """Büyükbaş kategorisinde köpek burnu yüklendiğinde reddedilmesi test edilir."""
    dogImage = CreateSyntheticDogNose()
    isValid, message, detectedSpecies = speciesValidatorInstance.ValidateCategory(
        imageMatrix=dogImage,
        selectedCategory="cattle",
    )
    assert isValid is False
    assert detectedSpecies == "dog"
    assert "köpek" in message.lower()


def test_matching_category_passes(speciesValidatorInstance):
    """Büyükbaş kategorisinde doğru büyükbaş burnu yüklendiğinde onaylanması test edilir."""
    cattleImage = CreateSyntheticCattleMuzzle()
    isValid, message, detectedSpecies = speciesValidatorInstance.ValidateCategory(
        imageMatrix=cattleImage,
        selectedCategory="cattle",
    )
    assert isValid is True
    assert detectedSpecies == "cattle"


def test_cross_species_rejection_cattle_in_cat_category(speciesValidatorInstance):
    """Kedi kategorisinde büyükbaş sığır burnu yüklendiğinde reddedilmesi test edilir."""
    cattleImage = CreateSyntheticCattleMuzzle()
    isValid, message, detectedSpecies = speciesValidatorInstance.ValidateCategory(
        imageMatrix=cattleImage,
        selectedCategory="stray",
        selectedSubType="cat",
    )
    assert isValid is False
    assert detectedSpecies == "cattle"
    assert "büyükbaş" in message.lower()


def test_cross_species_rejection_dog_in_cat_category(speciesValidatorInstance):
    """Kedi kategorisinde köpek burnu yüklendiğinde reddedilmesi test edilir."""
    dogImage = CreateSyntheticDogNose()
    isValid, message, detectedSpecies = speciesValidatorInstance.ValidateCategory(
        imageMatrix=dogImage,
        selectedCategory="stray",
        selectedSubType="cat",
    )
    assert isValid is False
    assert detectedSpecies == "dog"
    assert "köpek" in message.lower()

