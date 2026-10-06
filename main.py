import argparse
from pathlib import Path
import sys
from typing import List, Optional

from src.data.convert_dataset import DatasetConverter
from src.data.split_data import DatasetSplitter
from src.database.db_manager import DatabaseManager
from src.evaluation.evaluator import evaluate
from src.experiments.ablation import AblationExperiment
from src.features.feature_extractor import extract_features
from src.matching.matcher import MatchingEngine
from src.preprocessing.preprocessor import preprocess
from src.segmentation.router import segment_roi
from src.utils.config import (
    DEFAULT_RANDOM_SEEDS,
    DEFAULT_TRAIN_RATIO,
    METHOD_LBP_GLCM,
    VALID_FEATURE_METHODS,
    VALID_SPECIES,
)
from src.utils.image_io import ReadImage, ValidateSpecies
from src.utils.logger import GetLogger

loggerInstance = GetLogger("MainCLI")


def HandleRegisterCommand(argumentNamespace: argparse.Namespace) -> int:
    """Hayvan biyometrik kaydını gerçekleştirir."""
    imagePath = Path(argumentNamespace.image).resolve()
    speciesName = argumentNamespace.species.strip().lower()
    animalId = argumentNamespace.id.strip()
    featureMethod = argumentNamespace.method.strip().lower()

    if not ValidateSpecies(speciesName):
        loggerInstance.error(f"Geçersiz tür '{speciesName}'. Desteklenenler: {VALID_SPECIES}")
        return 1

    inputImage = ReadImage(imagePath)
    if inputImage is None:
        loggerInstance.error(f"Görüntü dosyası okunamadı: {imagePath}")
        return 1

    try:
        preprocessed = preprocess(inputImage)
        roi = segment_roi(preprocessed, speciesName)
        features = extract_features(roi, method=featureMethod)

        dbManager = DatabaseManager()
        dbManager.RegisterAnimal(
            animalId=animalId,
            speciesName=speciesName,
            featureVector=features,
            metadataDict={"sourcePath": str(imagePath), "method": featureMethod},
        )
        print(f"[BAŞARILI] '{animalId}' ({speciesName}) sisteme başarıyla kaydedildi.")
        return 0
    except Exception as registerException:
        loggerInstance.error(f"Kayıt hatası: {registerException}")
        return 1


def HandleIdentifyCommand(argumentNamespace: argparse.Namespace) -> int:
    """Sorgu görüntüsü üzerinden kimlik tespitini gerçekleştirir."""
    imagePath = Path(argumentNamespace.image).resolve()
    speciesName = argumentNamespace.species.strip().lower()
    featureMethod = argumentNamespace.method.strip().lower()
    topK = int(argumentNamespace.top_k)

    if not ValidateSpecies(speciesName):
        loggerInstance.error(f"Geçersiz tür: '{speciesName}'")
        return 1

    inputImage = ReadImage(imagePath)
    if inputImage is None:
        loggerInstance.error(f"Görüntü dosyası okunamadı: {imagePath}")
        return 1

    try:
        preprocessed = preprocess(inputImage)
        roi = segment_roi(preprocessed, speciesName)
        features = extract_features(roi, method=featureMethod)

        matcher = MatchingEngine()
        predictions = matcher.Identify(
            featureVector=features,
            speciesName=speciesName,
            topK=topK,
        )

        if not predictions:
            print(f"[UYARI] '{speciesName}' için veritabanında eşleşen kayıt bulunamadı.")
            return 0

        print(f"\n--- Kimlik Tespit Sonuçları ({speciesName.upper()}) ---")
        for rankIndex, (predictedAnimalId, confidenceScore) in enumerate(predictions, start=1):
            percentageScore = confidenceScore * 100.0
            print(f"Rank-{rankIndex}: Birey ID = '{predictedAnimalId}' | Güven Skoru = %{percentageScore:.2f}")
        return 0
    except Exception as identifyException:
        loggerInstance.error(f"Tanıma hatası: {identifyException}")
        return 1


def HandleVerifyCommand(argumentNamespace: argparse.Namespace) -> int:
    """1:1 Hayvan kimlik doğrulamasını (Verification) gerçekleştirir."""
    imagePath = Path(argumentNamespace.image).resolve()
    claimedAnimalId = argumentNamespace.id.strip()
    speciesName = argumentNamespace.species.strip().lower()
    featureMethod = argumentNamespace.method.strip().lower()
    threshold = float(argumentNamespace.threshold)

    if not ValidateSpecies(speciesName):
        loggerInstance.error(f"Geçersiz tür: '{speciesName}'")
        return 1

    inputImage = ReadImage(imagePath)
    if inputImage is None:
        loggerInstance.error(f"Görüntü okunamadı: {imagePath}")
        return 1

    try:
        preprocessed = preprocess(inputImage)
        roi = segment_roi(preprocessed, speciesName)
        features = extract_features(roi, method=featureMethod)

        matcher = MatchingEngine()
        isAccepted, confidenceScore = matcher.Verify(
            featureVector=features,
            claimedAnimalId=claimedAnimalId,
            speciesName=speciesName,
            verificationThreshold=threshold,
        )

        decisionText = "KABUL EDİLDİ (EŞLEŞTİ)" if isAccepted else "REDDEDİLDİ (EŞLEŞMEDİ)"
        print(f"\n--- 1:1 Doğrulama Sonucu ---")
        print(f"İddia Edilen ID : {claimedAnimalId}")
        print(f"Tür             : {speciesName.upper()}")
        print(f"Karar           : {decisionText}")
        print(f"Güven Skoru     : %{confidenceScore * 100:.2f} (Eşik: %{threshold * 100:.2f})")
        return 0 if isAccepted else 2
    except Exception as verifyException:
        loggerInstance.error(f"Doğrulama hatası: {verifyException}")
        return 1


def HandleWebCommand(argumentNamespace: argparse.Namespace) -> int:
    """Mobil telefon simülasyonlu Flask web arayüzünü başlatır."""
    from src.web.app import app

    hostAddress = argumentNamespace.host
    portNumber = int(argumentNamespace.port)
    print(f"\n ZooID Mobil Web Arayüzü Başlatılıyor: http://{hostAddress}:{portNumber}")
    print(" (Tarayıcınızdan açıp fotoğraf çekebilir veya yükleyebilirsiniz.)\n")
    try:
        app.run(host=hostAddress, port=portNumber, debug=False)
        return 0
    except Exception as webException:
        loggerInstance.error(f"Web sunucusu hatası: {webException}")
        return 1


def HandleSplitCommand(argumentNamespace: argparse.Namespace) -> int:
    """Veri seti üzerinde train/test ayrımı oluşturur."""
    speciesName = argumentNamespace.species.strip().lower()
    randomSeed = int(argumentNamespace.seed)
    trainRatio = float(argumentNamespace.train_ratio)

    splitter = DatasetSplitter()
    try:
        metadata = splitter.CreateClosedSetSplit(
            speciesName=speciesName,
            randomSeed=randomSeed,
            trainRatio=trainRatio,
        )
        print(f"[BAŞARILI] Ayrım tamamlandı: {metadata['totalQualifiedAnimals']} birey, "
              f"{metadata['galleryCount']} galeri, {metadata['testCount']} test görüntüsü.")
        return 0
    except Exception as splitException:
        loggerInstance.error(f"Bölümleme hatası: {splitException}")
        return 1


def HandleConvertCommand(argumentNamespace: argparse.Namespace) -> int:
    """Harici veri setini standart formata dönüştürür."""
    sourceDirectory = Path(argumentNamespace.source).resolve()
    speciesName = argumentNamespace.species.strip().lower()

    converter = DatasetConverter()
    try:
        report = converter.ConvertFolder(sourceDirectory=sourceDirectory, speciesName=speciesName)
        print(f"[BAŞARILI] Dönüştürme tamamlandı: {report['acceptedAnimalsCount']} birey, "
              f"{report['totalAcceptedImages']} geçerli görüntü kaydedildi.")
        return 0
    except Exception as convertException:
        loggerInstance.error(f"Dönüştürme hatası: {convertException}")
        return 1


def HandleAblationCommand(argumentNamespace: argparse.Namespace) -> int:
    """Ablation yöntem karşılaştırma deneyini çalıştırır."""
    splitFilePath = Path(argumentNamespace.split_file).resolve()
    if not splitFilePath.is_file():
        loggerInstance.error(f"Ayrım dosyası bulunamadı: {splitFilePath}")
        return 1

    try:
        splitData = DatasetSplitter.LoadSplit(splitFilePath)
        experiment = AblationExperiment()
        results = experiment.RunAblationOnSplit(splitMetadata=splitData)
        print("\n--- Ablation Yöntem Karşılaştırma Sonuçları ---")
        for methodName, methodStats in results.items():
            rankAccuracy = methodStats.get("rank1Accuracy", 0.0) * 100.0
            print(f"Yöntem: {methodName:<12} | Rank-1 Doğruluk: %{rankAccuracy:.2f} | "
                  f"Süre: {methodStats.get('durationSeconds', 0.0)}s")
        return 0
    except Exception as ablationException:
        loggerInstance.error(f"Ablation çalıştırma hatası: {ablationException}")
        return 1


def BuildCommandLineParser() -> argparse.ArgumentParser:
    """Komut satırı argüman ayrıştırıcısını yapılandırır."""
    parser = argparse.ArgumentParser(
        prog="zooid",
        description="ZooID (MABIS) — Çoklu Tür Hayvan Biyometrik Kimlik Tespit Sistemi",
    )
    subparsers = parser.add_subparsers(dest="command", help="Alt komutlar")

    # register
    registerParser = subparsers.add_parser("register", help="Hayvanı sisteme kaydet")
    registerParser.add_argument("--image", required=True, help="Görüntü dosya yolu")
    registerParser.add_argument("--id", required=True, help="Hayvan kimliği (ID)")
    registerParser.add_argument("--species", required=True, choices=VALID_SPECIES, help="Hayvan türü")
    registerParser.add_argument("--method", default=METHOD_LBP_GLCM, choices=VALID_FEATURE_METHODS, help="Öznitelik yöntemi")

    # identify
    identifyParser = subparsers.add_parser("identify", help="Görüntüden kimlik doğrula / tanı (1:N)")
    identifyParser.add_argument("--image", required=True, help="Görüntü dosya yolu")
    identifyParser.add_argument("--species", required=True, choices=VALID_SPECIES, help="Hayvan türü")
    identifyParser.add_argument("--method", default=METHOD_LBP_GLCM, choices=VALID_FEATURE_METHODS, help="Öznitelik yöntemi")
    identifyParser.add_argument("--top-k", default=1, type=int, help="En yakın kaç aday listelensin")

    # verify (1:1 Verification)
    verifyParser = subparsers.add_parser("verify", help="1:1 Hayvan kimlik doğrulama")
    verifyParser.add_argument("--image", required=True, help="Sorgu görüntü dosya yolu")
    verifyParser.add_argument("--id", required=True, help="İddia edilen hayvan kimliği (ID/Küpe no)")
    verifyParser.add_argument("--species", required=True, choices=VALID_SPECIES, help="Hayvan türü")
    verifyParser.add_argument("--method", default=METHOD_LBP_GLCM, choices=VALID_FEATURE_METHODS, help="Öznitelik yöntemi")
    verifyParser.add_argument("--threshold", default=0.08, type=float, help="Doğrulama kabul eşiği")

    # web (Mobile Phone UI)
    webParser = subparsers.add_parser("web", help="Mobil telefon simülasyonlu web arayüzünü başlat")
    webParser.add_argument("--port", default=5000, type=int, help="Sunucu port numarası (varsayılan: 5000)")
    webParser.add_argument("--host", default="127.0.0.1", help="Sunucu adresi (varsayılan: 127.0.0.1)")

    # split
    splitParser = subparsers.add_parser("split", help="Kapalı-küme train/test ayrımı üret")
    splitParser.add_argument("--species", required=True, choices=VALID_SPECIES, help="Hayvan türü")
    splitParser.add_argument("--seed", default=42, type=int, help="Rastgele tohum değeri")
    splitParser.add_argument("--train-ratio", default=DEFAULT_TRAIN_RATIO, type=float, help="Galeri oranı")

    # convert
    convertParser = subparsers.add_parser("convert", help="Ham veri setini standart formata dönüştür")
    convertParser.add_argument("--source", required=True, help="Kaynak klasör")
    convertParser.add_argument("--species", required=True, choices=VALID_SPECIES, help="Hayvan türü")

    # ablation
    ablationParser = subparsers.add_parser("ablation", help="Yöntem karşılaştırma deneyi yürüt")
    ablationParser.add_argument("--split-file", required=True, help="Ayrım JSON dosyası")

    return parser


def Main() -> int:
    """CLI giriş noktası."""
    argumentParser = BuildCommandLineParser()
    parsedArguments = argumentParser.parse_args()

    if not parsedArguments.command:
        argumentParser.print_help()
        return 0

    if parsedArguments.command == "register":
        return HandleRegisterCommand(parsedArguments)
    elif parsedArguments.command == "identify":
        return HandleIdentifyCommand(parsedArguments)
    elif parsedArguments.command == "verify":
        return HandleVerifyCommand(parsedArguments)
    elif parsedArguments.command == "web":
        return HandleWebCommand(parsedArguments)
    elif parsedArguments.command == "split":
        return HandleSplitCommand(parsedArguments)
    elif parsedArguments.command == "convert":
        return HandleConvertCommand(parsedArguments)
    elif parsedArguments.command == "ablation":
        return HandleAblationCommand(parsedArguments)
    else:
        argumentParser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(Main())
