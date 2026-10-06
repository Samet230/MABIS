import base64
from datetime import datetime
import io
import math
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple
import cv2
from flask import Flask, jsonify, render_template, request
import numpy as np

from src.features.feature_extractor import extract_features
from src.matching.matcher import MatchingEngine
from src.preprocessing.preprocessor import preprocess
from src.preprocessing.quality_gate import QualityGate
from src.preprocessing.species_validator import SpeciesValidator
from src.segmentation.router import segment_roi
from src.utils.config import METHOD_ORB
from src.utils.logger import GetLogger

loggerInstance = GetLogger("WebApp")

WEB_MODULE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_MODULE_DIR / "templates"
STATIC_DIR = WEB_MODULE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
)

# Kategori ve tür eşleme sabitleri
CATEGORY_CATTLE: Final[str] = "cattle"
CATEGORY_STRAY: Final[str] = "stray"
VALID_CATEGORIES: Final[Tuple[str, ...]] = (CATEGORY_CATTLE, CATEGORY_STRAY)

DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.08
MAX_IMAGE_UPLOAD_BYTES: Final[int] = 16 * 1024 * 1024  # 16 MB

from src.database.repository_manager import (
    DEFAULT_BARN_REPO_ID,
    DEFAULT_STRAY_REPO_ID,
    REPO_TYPE_PRIVATE,
    REPO_TYPE_PUBLIC,
    RepositoryManager,
    repositoryManagerInstance,
)
from src.utils.geo import (
    CalculateHaversineDistanceMeters,
    CalculateTerritoryStats,
    DEFAULT_TERRITORY_DEFAULT_RADIUS_METERS,
    DEFAULT_TERRITORY_MIN_RADIUS_METERS,
    EARTH_RADIUS_METERS,
)

qualityGateInstance = QualityGate(blurThreshold=45.0)  # Telefon çekimleri için makul eşik
speciesValidatorInstance = SpeciesValidator()
matchingEngineInstance = MatchingEngine()

# Bellek içi geçici hayvan kaydı veri yapısı (veritabanı olmaksızın oturum kaydı)
# Format: { animalId: { "animalId": str, "repoId": str, "category": str, "species": str, ... } }
IN_MEMORY_ANIMAL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def GetCurrentRequestUser() -> str:
    """İstek başlıklarından, parametrelerinden veya formundan kullanıcı kimliğini döndürür."""
    authHeader = request.headers.get("X-User-Id") or request.headers.get("X-User-Email")
    if authHeader:
        return authHeader.strip()

    jsonData = request.get_json(silent=True) if request.is_json else None
    if jsonData and isinstance(jsonData, dict):
        for candidateKey in ("userId", "username", "ownerId"):
            if jsonData.get(candidateKey):
                return str(jsonData[candidateKey]).strip()

    userParam = (
        request.args.get("userId")
        or request.args.get("username")
        or request.form.get("userId")
        or request.form.get("username")
    )
    if userParam:
        return userParam.strip()
    return "demo_veteriner"



def ConvertImageMatrixToBase64(imageMatrix: np.ndarray, formatExtension: str = ".jpg") -> str:
    """OpenCV görüntü matrisini webde gösterilebilir base64 veri URI dizgisine dönüştürür."""
    encodeSuccess, bufferArray = cv2.imencode(formatExtension, imageMatrix)
    if not encodeSuccess:
        return ""
    base64EncodedString = base64.b64encode(bufferArray).decode("utf-8")
    mimeType = "image/jpeg" if formatExtension.lower() in (".jpg", ".jpeg") else "image/png"
    return f"data:{mimeType};base64,{base64EncodedString}"


def DecodeUploadedImageFile(uploadedFile) -> Optional[np.ndarray]:
    """Flask request dosyasını OpenCV BGR formatında numpy matrisine çözer."""
    try:
        rawFileBytes = uploadedFile.read()
        if len(rawFileBytes) == 0:
            return None
        numpyArray = np.frombuffer(rawFileBytes, dtype=np.uint8)
        decodedImage = cv2.imdecode(numpyArray, cv2.IMREAD_COLOR)
        return decodedImage
    except Exception as decodeException:
        loggerInstance.error(f"Görüntü çözme hatası: {decodeException}")
        return None


def MapCategoryToSpecies(categoryName: str, subType: Optional[str] = None) -> str:
    """Kullanıcı arayüzündeki kategoriyi çekirdek model türüne ('cattle', 'dog', 'cat') eşler."""
    normalizedCategory = categoryName.strip().lower()
    if normalizedCategory == CATEGORY_CATTLE or "büyükbaş" in normalizedCategory:
        return "cattle"

    # Sokak hayvanları için varsayılan köpek veya kedi
    if subType:
        normalizedSubtype = subType.strip().lower()
        if "kedi" in normalizedSubtype or normalizedSubtype == "cat":
            return "cat"
        return "dog"
    return "dog"


@app.route("/")
def IndexRoute():
    """Mobil telefon simülatör arayüzünü sunar."""
    return render_template("index.html")


@app.route("/api/quality_check", methods=["POST"])
def QualityCheckEndpoint():
    """Yüklenen görüntüyü kalite kapısından ve tür uyuşmazlığı kontrolünden geçirip anlık teşhis döndürür."""
    if "image" not in request.files:
        return jsonify({"success": False, "message": "Görüntü dosyası bulunamadı."}), 400

    inputImage = DecodeUploadedImageFile(request.files["image"])
    if inputImage is None:
        return jsonify({"success": False, "message": "Görüntü okunamadı veya bozuk."}), 400

    categoryName = request.form.get("category", CATEGORY_CATTLE).strip()
    subType = request.form.get("subType", "dog").strip()

    # Tür Uyuşmazlığı Denetimi (Örn: Köpek seçiliyken kedi veya sığır yüklenmesi)
    isSpeciesValid, speciesMessage, detectedSpecies = speciesValidatorInstance.ValidateCategory(
        imageMatrix=inputImage,
        selectedCategory=categoryName,
        selectedSubType=subType,
    )

    assessment = qualityGateInstance.AssessQuality(inputImage)
    return jsonify({
        "success": True,
        "isPassed": assessment.isPassed and isSpeciesValid,
        "speciesValid": isSpeciesValid,
        "speciesMessage": speciesMessage,
        "detectedSpecies": detectedSpecies,
        "reasons": (
            assessment.rejectionReasons
            if isSpeciesValid
            else [speciesMessage] + assessment.rejectionReasons
        ),
        "metrics": assessment.ToDictionary(),
    })


# ==============================================================================
# DEPOLAMA ALANI / REPO YÖNETİMİ UÇ NOKTALARI (ÖZEL AHIR & ORTAK SOKAK DEPOLARI)
# ==============================================================================
@app.route("/api/repositories", methods=["GET"])
def ListRepositoriesEndpoint():
    """Kullanıcının erişebildiği özel ahır depolarını veya konuma göre ortak sokak depolarını listeler."""
    category = request.args.get("category", "").strip().lower()
    userLatitudeRaw = request.args.get("latitude")
    userLongitudeRaw = request.args.get("longitude")
    currentUser = GetCurrentRequestUser()

    userLatitude: Optional[float] = None
    userLongitude: Optional[float] = None
    if userLatitudeRaw is not None and userLongitudeRaw is not None:
        try:
            userLatitude = float(userLatitudeRaw)
            userLongitude = float(userLongitudeRaw)
        except (ValueError, TypeError):
            userLatitude = None
            userLongitude = None

    cattleRepos = repositoryManagerInstance.ListUserRepositories(
        userIdentifier=currentUser,
        category="cattle",
        userLatitude=userLatitude,
        userLongitude=userLongitude,
    )
    strayRepos = repositoryManagerInstance.ListPublicRepositories(
        userLatitude=userLatitude, userLongitude=userLongitude
    )
    nearestStray = next((repoItem for repoItem in strayRepos if repoItem.get("isNearest")), strayRepos[0] if strayRepos else None)

    if category == CATEGORY_STRAY or "sokak" in category:
        selectedList = strayRepos
        currentCategory = "stray"
        repoType = "public"
        requiresCode = False
        message = "Konumunuza göre bölgesel ortak sokak depoları listelendi."
    else:
        selectedList = cattleRepos
        currentCategory = "cattle"
        repoType = "private"
        requiresCode = True
        message = "Erişebildiğiniz ahır depoları listelendi."

    return jsonify({
        "success": True,
        "category": currentCategory,
        "repoType": repoType,
        "requiresCode": requiresCode,
        "message": message,
        "count": len(selectedList),
        "repositories": selectedList,
        "cattleRepositories": cattleRepos,
        "strayRepositories": strayRepos,
        "userRepositories": cattleRepos,
        "nearestStrayRepo": nearestStray,
        "defaultRepoId": DEFAULT_BARN_REPO_ID if currentCategory == "cattle" else DEFAULT_STRAY_REPO_ID,
    })


@app.route("/api/repositories/create", methods=["POST"])
def CreateRepositoryEndpoint():
    """Büyükbaş hayvan yetiştiricisi için yeni bir özel ahır deposu ve erişim kodu oluşturur."""
    data = request.get_json(silent=True) or request.form
    repoName = str(data.get("name") or data.get("repoName") or "").strip()
    category = str(data.get("category", CATEGORY_CATTLE)).strip().lower()
    locationName = str(data.get("locationName") or data.get("location") or "").strip()
    latitudeRaw = data.get("latitude")
    longitudeRaw = data.get("longitude")
    currentUser = str(data.get("ownerId") or data.get("userId") or GetCurrentRequestUser()).strip()

    if not repoName:
        return jsonify({"success": False, "message": "Ahır / Depo adı zorunludur."}), 400

    parsedLatitude: Optional[float] = None
    parsedLongitude: Optional[float] = None
    if latitudeRaw is not None and longitudeRaw is not None:
        try:
            parsedLatitude = float(latitudeRaw)
            parsedLongitude = float(longitudeRaw)
        except (ValueError, TypeError):
            parsedLatitude = None
            parsedLongitude = None

    try:
        newRepo = repositoryManagerInstance.CreateRepository(
            repoName=repoName,
            repoType=REPO_TYPE_PRIVATE,
            category=category,
            ownerUsername=currentUser,
            locationName=locationName,
            latitude=parsedLatitude,
            longitude=parsedLongitude,
        )
        return jsonify({
            "success": True,
            "message": f"'{repoName}' ahır deposu başarıyla oluşturuldu. Çalışanlarınızla paylaşabileceğiniz erişim kodu üretildi.",
            "repository": newRepo,
        }), 200
    except Exception as createException:
        loggerInstance.error(f"Depo oluşturma hatası: {createException}")
        return jsonify({"success": False, "message": f"Depo oluşturulamadı: {str(createException)}"}), 500


@app.route("/api/repositories/join", methods=["POST"])
def JoinRepositoryEndpoint():
    """Çalışanın veya yetkili kullanıcının erişim kodu ile özel ahır deposuna bağlanmasını sağlar."""
    data = request.get_json(silent=True) or request.form
    accessCode = str(data.get("accessCode", "")).strip().upper()
    currentUser = GetCurrentRequestUser()

    if not accessCode:
        return jsonify({"success": False, "message": "Lütfen bir depo erişim kodu giriniz."}), 400

    isSuccess, statusMessage, repoDict = repositoryManagerInstance.JoinRepositoryWithCode(
        accessCode=accessCode, userIdentifier=currentUser
    )

    if not isSuccess or not repoDict:
        return jsonify({"success": False, "message": statusMessage}), 404

    return jsonify({
        "success": True,
        "message": statusMessage,
        "repository": repoDict,
    })


@app.route("/api/repositories/regenerate_code", methods=["POST"])
def RegenerateAccessCodeEndpoint():
    """Ahır sahibinin depo erişim kodunu yenilemesini sağlar."""
    data = request.get_json(silent=True) or request.form
    repoId = str(data.get("repoId", "")).strip()
    currentUser = GetCurrentRequestUser()

    if not repoId:
        return jsonify({"success": False, "message": "Depo kimliği (repoId) zorunludur."}), 400

    isSuccess, statusMessage, newCode = repositoryManagerInstance.RegenerateAccessCode(
        repoId=repoId, requesterUsername=currentUser
    )

    if not isSuccess:
        return jsonify({"success": False, "message": statusMessage}), 403

    return jsonify({
        "success": True,
        "message": statusMessage,
        "repoId": repoId,
        "accessCode": newCode,
    })


@app.route("/api/repositories/<repo_id>", methods=["GET"])
def GetRepositoryDetailEndpoint(repo_id: str):
    """Belirtilen deponun detaylarını, erişim durumunu ve istatistiklerini döndürür."""
    cleanRepoId = repo_id.strip()
    repo = repositoryManagerInstance.GetRepository(cleanRepoId)
    if not repo:
        return jsonify({"success": False, "message": f"'{cleanRepoId}' kimlikli depo bulunamadı."}), 404

    currentUser = GetCurrentRequestUser()
    hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(cleanRepoId, currentUser, "view")
    animalCount = sum(
        1 for item in IN_MEMORY_ANIMAL_REGISTRY.values()
        if item.get("repoId", DEFAULT_BARN_REPO_ID if item.get("category") == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID) == cleanRepoId
    )

    return jsonify({
        "success": True,
        "repository": repo,
        "hasAccess": hasAccess,
        "accessMessage": accessMessage,
        "animalCount": animalCount,
    })


@app.route("/api/register", methods=["POST"])
def RegisterAnimalEndpoint():
    """Görüntüyü kalite kapısından geçirir, ROI'yi segmente eder, öznitelik çıkarıp belleğe kaydeder."""
    try:
        animalId = request.form.get("animalId", "").strip()
        animalName = request.form.get("animalName", "").strip() or animalId
        categoryName = request.form.get("category", CATEGORY_CATTLE).strip()
        subType = request.form.get("subType", "dog").strip()
        bypassQuality = request.form.get("bypassQuality", "false").lower() == "true"

        # Yeni Biyometrik Pasaport Alanları
        birthDate = request.form.get("birthDate", "").strip()
        vaccinations = request.form.get("vaccinations", "").strip()
        distinctiveFeatures = request.form.get("distinctiveFeatures", "").strip()
        temperament = request.form.get("temperament", "").strip()
        favoriteFood = request.form.get("favoriteFood", "").strip()
        breed = request.form.get("breed", "").strip()
        gender = request.form.get("gender", "Belirtilmedi").strip()
        neutered = request.form.get("neutered", "Belirtilmedi").strip()
        healthStatus = request.form.get("healthStatus", "healthy").strip().lower()
        if healthStatus not in ("healthy", "sick", "lost"):
            healthStatus = "healthy"

        # Coğrafi Konum (Sokak Hayvanı ve Saha Kayıtları İçin)
        latitudeRaw = request.form.get("latitude")
        longitudeRaw = request.form.get("longitude")
        locationName = request.form.get("locationName", "").strip()
        locationAccuracyRaw = request.form.get("locationAccuracy")

        parsedLatitude: Optional[float] = None
        parsedLongitude: Optional[float] = None
        parsedAccuracy: float = 15.0

        if latitudeRaw is not None and longitudeRaw is not None:
            try:
                parsedLatitude = float(latitudeRaw)
                parsedLongitude = float(longitudeRaw)
                if locationAccuracyRaw:
                    parsedAccuracy = float(locationAccuracyRaw)
            except (ValueError, TypeError):
                parsedLatitude = None
                parsedLongitude = None

        # Depo Seçimi ve Erişim Yetkisi Denetimi
        targetRepoId = request.form.get("repoId", "").strip()
        if not targetRepoId:
            targetRepoId = (
                DEFAULT_BARN_REPO_ID
                if (categoryName == CATEGORY_CATTLE or "büyükbaş" in categoryName)
                else DEFAULT_STRAY_REPO_ID
            )

        currentUser = GetCurrentRequestUser()
        hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(
            repoId=targetRepoId, userIdentifier=currentUser, requiredPermission="add"
        )
        if not hasAccess:
            return jsonify({"success": False, "message": f"Depo erişim engeli: {accessMessage}"}), 403

        if not animalId:
            return jsonify({"success": False, "message": "Hayvan Kimlik Numarası / Küpe No zorunludur."}), 400

        if "image" not in request.files:
            return jsonify({"success": False, "message": "Lütfen bir hayvan fotoğrafı yükleyin veya çekin."}), 400

        inputImage = DecodeUploadedImageFile(request.files["image"])
        if inputImage is None:
            return jsonify({"success": False, "message": "Görüntü dosyası okunamadı."}), 400

        # 1. Tür Uyuşmazlığı Denetimi (Cross-Species Rejection) - Kesinlikle atlanamaz!
        isSpeciesValid, speciesMessage, detectedSpecies = speciesValidatorInstance.ValidateCategory(
            imageMatrix=inputImage,
            selectedCategory=categoryName,
            selectedSubType=subType,
        )
        if not isSpeciesValid:
            loggerInstance.warning(f"Kayıtta tür uyuşmazlığı: {speciesMessage}")
            return jsonify({
                "success": False,
                "speciesMismatch": True,
                "detectedSpecies": detectedSpecies,
                "message": speciesMessage,
            }), 422

        # 2. Kalite Kapısı Denetimi (FR-01)
        qualityAssessment = qualityGateInstance.AssessQuality(inputImage)
        if not qualityAssessment.isPassed and not bypassQuality:
            reasonsJoined = " | ".join(qualityAssessment.rejectionReasons)
            return jsonify({
                "success": False,
                "qualityFailed": True,
                "message": f"Kalite Kapısı Reddi: {reasonsJoined}",
                "qualityReport": qualityAssessment.ToDictionary(),
            }), 422

        # 3. Tür Belirleme ve Ön İşleme (FR-02 & FR-03)
        resolvedSpecies = MapCategoryToSpecies(categoryName, subType)
        preprocessedImage = preprocess(inputImage)
        segmentedRoi = segment_roi(preprocessedImage, resolvedSpecies)

        # 3. Öznitelik Çıkarımı (FR-05) - ORB + RANSAC mimarisi
        extractedFeatures = extract_features(segmentedRoi, method=METHOD_ORB)
        if extractedFeatures is None or extractedFeatures.size == 0:
            return jsonify({
                "success": False,
                "message": "Görüntüden biyometrik öznitelik çıkarılamadı. Lütfen burun bölgesini daha net çekiniz.",
            }), 422

        # 4. Bellek İçi Detaylı Kayıt Oluşturma
        roiBase64Uri = ConvertImageMatrixToBase64(segmentedRoi, ".jpg")
        rawThumbnailBase64Uri = ConvertImageMatrixToBase64(cv2.resize(inputImage, (160, 160)), ".jpg")
        registrationTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        initialSightingsList: List[Dict[str, Any]] = []
        if parsedLatitude is not None and parsedLongitude is not None:
            initialSightingsList.append({
                "sightingId": "sig_0",
                "latitude": round(parsedLatitude, 6),
                "longitude": round(parsedLongitude, 6),
                "accuracy": round(parsedAccuracy, 1),
                "locationName": locationName or "İlk Kayıt Noktası",
                "timestamp": registrationTimestamp,
                "type": "registration",
                "confidence": 100.0,
            })

        IN_MEMORY_ANIMAL_REGISTRY[animalId] = {
            "animalId": animalId,
            "repoId": targetRepoId,
            "animalName": animalName,
            "category": categoryName,
            "species": resolvedSpecies,
            "breed": breed,
            "gender": gender,
            "neutered": neutered,
            "birthDate": birthDate,
            "vaccinations": vaccinations,
            "distinctiveFeatures": distinctiveFeatures,
            "temperament": temperament,
            "favoriteFood": favoriteFood,
            "healthStatus": healthStatus,
            "features": extractedFeatures,
            "roiBase64": roiBase64Uri,
            "rawThumbnailBase64": rawThumbnailBase64Uri,
            "keypointCount": int(extractedFeatures.shape[0]),
            "registeredAt": registrationTimestamp,
            "sightings": initialSightingsList,
        }

        territoryStats = CalculateTerritoryStats(initialSightingsList)

        loggerInstance.info(
            f"Yeni hayvan başarıyla kaydedildi: ID='{animalId}', İsim='{animalName}', Depo='{targetRepoId}', "
            f"Durum='{healthStatus}', Anahtar Nokta={extractedFeatures.shape[0]}, "
            f"Konum={parsedLatitude}, {parsedLongitude}"
        )

        return jsonify({
            "success": True,
            "message": f"'{animalName}' ({animalId}) başarıyla sisteme kaydedildi.",
            "animalId": animalId,
            "repoId": targetRepoId,
            "animalName": animalName,
            "species": resolvedSpecies,
            "category": categoryName,
            "healthStatus": healthStatus,
            "keypointCount": int(extractedFeatures.shape[0]),
            "roiThumbnail": roiBase64Uri,
            "qualityReport": qualityAssessment.ToDictionary(),
            "sightings": initialSightingsList,
            "territory": territoryStats,
        })

    except Exception as registrationException:
        loggerInstance.error(f"Kayıt uç noktasında beklenmeyen hata: {registrationException}")
        return jsonify({"success": False, "message": f"Sunucu hatası: {str(registrationException)}"}), 500


@app.route("/api/identify", methods=["POST"])
def IdentifyAnimalEndpoint():
    """Girdi görüntüsünden hayvan kimliğini bellek içi kayıtlardan 1:N eşleştirerek tespit eder."""
    try:
        categoryName = request.form.get("category", CATEGORY_CATTLE).strip()
        subType = request.form.get("subType", "dog").strip()
        bypassQuality = request.form.get("bypassQuality", "false").lower() == "true"

        # Kullanıcının mevcut coğrafi konumu (Arama anında tespit edilen yer)
        queryLatitudeRaw = request.form.get("latitude")
        queryLongitudeRaw = request.form.get("longitude")
        queryLocationName = request.form.get("locationName", "").strip()
        queryAccuracyRaw = request.form.get("locationAccuracy")

        parsedQueryLatitude: Optional[float] = None
        parsedQueryLongitude: Optional[float] = None
        parsedQueryAccuracy: float = 15.0

        if queryLatitudeRaw is not None and queryLongitudeRaw is not None:
            try:
                parsedQueryLatitude = float(queryLatitudeRaw)
                parsedQueryLongitude = float(queryLongitudeRaw)
                if queryAccuracyRaw:
                    parsedQueryAccuracy = float(queryAccuracyRaw)
            except (ValueError, TypeError):
                parsedQueryLatitude = None
                parsedQueryLongitude = None

        if "image" not in request.files:
            return jsonify({"success": False, "message": "Lütfen arama için bir fotoğraf yükleyin veya çekin."}), 400

        inputImage = DecodeUploadedImageFile(request.files["image"])
        if inputImage is None:
            return jsonify({"success": False, "message": "Görüntü dosyası okunamadı."}), 400

        # 1. Tür Uyuşmazlığı Denetimi (Cross-Species Rejection) - Kesinlikle atlanamaz!
        isSpeciesValid, speciesMessage, detectedSpecies = speciesValidatorInstance.ValidateCategory(
            imageMatrix=inputImage,
            selectedCategory=categoryName,
            selectedSubType=subType,
        )
        if not isSpeciesValid:
            loggerInstance.warning(f"Aramada tür uyuşmazlığı: {speciesMessage}")
            return jsonify({
                "success": False,
                "speciesMismatch": True,
                "detectedSpecies": detectedSpecies,
                "message": speciesMessage,
            }), 422

        # 2. Kalite Kapısı Denetimi
        qualityAssessment = qualityGateInstance.AssessQuality(inputImage)
        if not qualityAssessment.isPassed and not bypassQuality:
            reasonsJoined = " | ".join(qualityAssessment.rejectionReasons)
            return jsonify({
                "success": False,
                "qualityFailed": True,
                "message": f"Kalite Kapısı Reddi: {reasonsJoined}",
                "qualityReport": qualityAssessment.ToDictionary(),
            }), 422

        # 3. Ön İşleme ve Segmentasyon
        resolvedSpecies = MapCategoryToSpecies(categoryName, subType)
        preprocessedImage = preprocess(inputImage)
        segmentedRoi = segment_roi(preprocessedImage, resolvedSpecies)

        # 3. Öznitelik Çıkarımı
        extractedQueryFeatures = extract_features(segmentedRoi, method=METHOD_ORB)
        if extractedQueryFeatures is None or extractedQueryFeatures.size == 0:
            return jsonify({
                "success": False,
                "message": "Görüntüden biyometrik öznitelik çıkarılamadı. Lütfen net bir fotoğraf çekiniz.",
            }), 422

        queryRepoId = request.form.get("repoId", "").strip()

        # 4. İlgili türdeki adayları bellek içi kayıttan filtrele (Depo İzolasyonu)
        eligibleCandidates: List[Tuple[str, np.ndarray, dict]] = [
            (recordData["animalId"], recordData["features"], {})
            for recordData in IN_MEMORY_ANIMAL_REGISTRY.values()
            if (recordData["species"] == resolvedSpecies or recordData["category"] == categoryName)
            and (
                not queryRepoId
                or recordData.get(
                    "repoId",
                    DEFAULT_BARN_REPO_ID if categoryName == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID,
                )
                == queryRepoId
            )
        ]

        queryRoiBase64 = ConvertImageMatrixToBase64(segmentedRoi, ".jpg")

        if not eligibleCandidates:
            return jsonify({
                "success": True,
                "status": "no_candidates",
                "message": (
                    f"Seçilen depoda ({queryRepoId or categoryName}) henüz kayıtlı hayvan bulunmuyor. "
                    "Önce 'Kayıt' sekmesinden bu depoya bir hayvan kaydedin."
                ),
                "queryRoi": queryRoiBase64,
                "matchedAnimalId": None,
                "confidenceScore": 0.0,
            })

        # 5. RANSAC Destekli Eşleştirme Motoru ile Arama
        matchedResults = matchingEngineInstance.MatchDescriptors(
            queryDescriptors=extractedQueryFeatures,
            candidateRecords=eligibleCandidates,
            topK=1,
        )

        if not matchedResults:
            return jsonify({
                "success": True,
                "status": "unknown",
                "message": "Eşleşme bulunamadı: Kayıtsız / Yabancı Hayvan.",
                "queryRoi": queryRoiBase64,
                "matchedAnimalId": None,
                "confidenceScore": 0.0,
            })

        topCandidateId, topConfidenceScore = matchedResults[0]
        registeredAnimalData = IN_MEMORY_ANIMAL_REGISTRY.get(topCandidateId, {})
        matchedTemplateRoi = registeredAnimalData.get("roiBase64", "")

        isConfidenceSufficient = topConfidenceScore >= DEFAULT_CONFIDENCE_THRESHOLD

        # Eşleşen hayvanın pasaport bilgilerini hazırla
        matchedProfile = None
        isLostAlert = False
        territoryResponse: Optional[Dict[str, Any]] = None

        if isConfidenceSufficient and registeredAnimalData:
            animalSightingsList = registeredAnimalData.setdefault("sightings", [])

            # Kullanıcı konum sağladıysa yeni görülme (sighting) noktasını kaydet
            if parsedQueryLatitude is not None and parsedQueryLongitude is not None:
                newSightingRecord = {
                    "sightingId": f"sig_{len(animalSightingsList)}",
                    "latitude": round(parsedQueryLatitude, 6),
                    "longitude": round(parsedQueryLongitude, 6),
                    "accuracy": round(parsedQueryAccuracy, 1),
                    "locationName": queryLocationName or "Saha Tespiti (Canlı Arama)",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "sighting",
                    "confidence": round(float(topConfidenceScore) * 100.0, 1),
                }
                animalSightingsList.append(newSightingRecord)

            territoryStats = CalculateTerritoryStats(animalSightingsList)

            # Kullanıcının anlık konumuna göre mesafe hesaplama
            distanceToCentroidMeters: Optional[float] = None
            distanceToLatestMeters: Optional[float] = None

            if parsedQueryLatitude is not None and parsedQueryLongitude is not None:
                if territoryStats.get("centroid"):
                    distanceToCentroidMeters = CalculateHaversineDistanceMeters(
                        parsedQueryLatitude,
                        parsedQueryLongitude,
                        territoryStats["centroid"]["latitude"],
                        territoryStats["centroid"]["longitude"],
                    )
                if animalSightingsList:
                    latestPoint = animalSightingsList[-1]
                    if latestPoint.get("latitude") is not None and latestPoint.get("longitude") is not None:
                        distanceToLatestMeters = CalculateHaversineDistanceMeters(
                            parsedQueryLatitude,
                            parsedQueryLongitude,
                            latestPoint["latitude"],
                            latestPoint["longitude"],
                        )

            territoryResponse = {
                "centroid": territoryStats.get("centroid"),
                "territoryRadiusMeters": territoryStats.get("territoryRadiusMeters", 0.0),
                "sightingsCount": territoryStats.get("sightingsCount", 0),
                "primaryZone": territoryStats.get("primaryZone", ""),
                "distanceToCentroidMeters": round(distanceToCentroidMeters, 1) if distanceToCentroidMeters is not None else None,
                "distanceToLatestMeters": round(distanceToLatestMeters, 1) if distanceToLatestMeters is not None else None,
                "sightings": animalSightingsList,
            }

            matchedProfile = {
                "animalId": registeredAnimalData.get("animalId", topCandidateId),
                "animalName": registeredAnimalData.get("animalName", topCandidateId),
                "category": registeredAnimalData.get("category", categoryName),
                "species": registeredAnimalData.get("species", resolvedSpecies),
                "breed": registeredAnimalData.get("breed", ""),
                "gender": registeredAnimalData.get("gender", "Belirtilmedi"),
                "neutered": registeredAnimalData.get("neutered", "Belirtilmedi"),
                "birthDate": registeredAnimalData.get("birthDate", ""),
                "vaccinations": registeredAnimalData.get("vaccinations", ""),
                "distinctiveFeatures": registeredAnimalData.get("distinctiveFeatures", ""),
                "temperament": registeredAnimalData.get("temperament", ""),
                "favoriteFood": registeredAnimalData.get("favoriteFood", ""),
                "healthStatus": registeredAnimalData.get("healthStatus", "healthy"),
                "registeredAt": registeredAnimalData.get("registeredAt", ""),
                "sightingsCount": territoryStats.get("sightingsCount", 0),
                "primaryZone": territoryStats.get("primaryZone", ""),
                "lastSeen": animalSightingsList[-1] if animalSightingsList else None,
            }
            if matchedProfile["healthStatus"] == "lost":
                isLostAlert = True

        return jsonify({
            "success": True,
            "status": "matched" if isConfidenceSufficient else "unknown",
            "isMatch": isConfidenceSufficient,
            "matchedAnimalId": topCandidateId if isConfidenceSufficient else "Bilinmeyen / Kayıtsız",
            "matchedAnimalName": registeredAnimalData.get("animalName", topCandidateId) if isConfidenceSufficient else "Bilinmeyen",
            "confidenceScore": round(float(topConfidenceScore) * 100.0, 1),
            "rawConfidence": float(topConfidenceScore),
            "threshold": round(float(DEFAULT_CONFIDENCE_THRESHOLD) * 100.0, 1),
            "queryRoi": queryRoiBase64,
            "templateRoi": matchedTemplateRoi if isConfidenceSufficient else None,
            "animalProfile": matchedProfile,
            "territory": territoryResponse,
            "isLostAlert": isLostAlert,
            "message": (
                f"Eşleşme Başarılı! {registeredAnimalData.get('animalName', topCandidateId)} ({topCandidateId}) (%{topConfidenceScore * 100:.1f} Güven)"
                if isConfidenceSufficient
                else f"Güven skoru yetersiz (%{topConfidenceScore * 100:.1f} < %{DEFAULT_CONFIDENCE_THRESHOLD * 100:.1f}). Hayvan kayıtsız görünüyor."
            ),
        })

    except Exception as identificationException:
        loggerInstance.error(f"Tanıma uç noktasında hata: {identificationException}")
        return jsonify({"success": False, "message": f"Sunucu hatası: {str(identificationException)}"}), 500


@app.route("/api/animals", methods=["GET"])
def ListAnimalsEndpoint():
    """Bellek içi kayıtlı hayvanların özet listesini depoya göre filtreleyerek döndürür."""
    selectedRepoId = request.args.get("repoId", "").strip()
    categoryFilter = request.args.get("category", "").strip().lower()
    currentUser = GetCurrentRequestUser()

    if selectedRepoId:
        hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(
            repoId=selectedRepoId, userIdentifier=currentUser, requiredPermission="view"
        )
        if not hasAccess:
            return jsonify({
                "success": False,
                "message": f"Depo erişim yetkisi yok: {accessMessage}",
                "count": 0,
                "animals": [],
            }), 403

    animalSummaryList = []
    for itemData in IN_MEMORY_ANIMAL_REGISTRY.values():
        itemRepoId = itemData.get(
            "repoId",
            DEFAULT_BARN_REPO_ID if itemData.get("category") == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID,
        )
        if selectedRepoId and itemRepoId != selectedRepoId:
            continue
        if categoryFilter and itemData.get("category") != categoryFilter:
            continue

        sightingsList = itemData.get("sightings", [])
        territoryStats = CalculateTerritoryStats(sightingsList)
        animalSummaryList.append({
            "animalId": itemData["animalId"],
            "repoId": itemRepoId,
            "animalName": itemData.get("animalName", itemData["animalId"]),
            "category": itemData["category"],
            "species": itemData["species"],
            "breed": itemData.get("breed", ""),
            "healthStatus": itemData.get("healthStatus", "healthy"),
            "birthDate": itemData.get("birthDate", ""),
            "keypointCount": itemData["keypointCount"],
            "registeredAt": itemData["registeredAt"],
            "thumbnail": itemData["rawThumbnailBase64"],
            "roiThumbnail": itemData["roiBase64"],
            "sightingsCount": len(sightingsList),
            "primaryZone": territoryStats.get("primaryZone", ""),
            "latestSighting": sightingsList[-1] if sightingsList else None,
        })
    # En yeniden eskiye sırala
    animalSummaryList.reverse()
    return jsonify({
        "success": True,
        "count": len(animalSummaryList),
        "repoId": selectedRepoId or None,
        "animals": animalSummaryList,
    })


@app.route("/api/animals/<animal_id>", methods=["GET"])
def GetAnimalDetailEndpoint(animal_id: str):
    """Belirtilen hayvanın tam biyometrik pasaport ve dolaşım haritası bilgilerini döndürür."""
    cleanId = animal_id.strip()
    if cleanId not in IN_MEMORY_ANIMAL_REGISTRY:
        return jsonify({"success": False, "message": f"'{cleanId}' kimlikli hayvan bulunamadı."}), 404

    recordData = IN_MEMORY_ANIMAL_REGISTRY[cleanId]
    itemRepoId = recordData.get(
        "repoId",
        DEFAULT_BARN_REPO_ID if recordData.get("category") == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID,
    )
    currentUser = GetCurrentRequestUser()
    hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(
        repoId=itemRepoId, userIdentifier=currentUser, requiredPermission="view"
    )
    if not hasAccess:
        return jsonify({"success": False, "message": f"Depo erişim yetkisi yok: {accessMessage}"}), 403

    sightingsList = recordData.get("sightings", [])
    territoryStats = CalculateTerritoryStats(sightingsList)

    return jsonify({
        "success": True,
        "animal": {
            "animalId": recordData["animalId"],
            "repoId": itemRepoId,
            "animalName": recordData.get("animalName", recordData["animalId"]),
            "category": recordData["category"],
            "species": recordData["species"],
            "breed": recordData.get("breed", ""),
            "gender": recordData.get("gender", "Belirtilmedi"),
            "neutered": recordData.get("neutered", "Belirtilmedi"),
            "birthDate": recordData.get("birthDate", ""),
            "vaccinations": recordData.get("vaccinations", ""),
            "distinctiveFeatures": recordData.get("distinctiveFeatures", ""),
            "temperament": recordData.get("temperament", ""),
            "favoriteFood": recordData.get("favoriteFood", ""),
            "healthStatus": recordData.get("healthStatus", "healthy"),
            "registeredAt": recordData["registeredAt"],
            "keypointCount": recordData["keypointCount"],
            "thumbnail": recordData["rawThumbnailBase64"],
            "roiThumbnail": recordData["roiBase64"],
            "sightings": sightingsList,
            "territory": territoryStats,
        },
    })


@app.route("/api/animals/<animal_id>/sightings", methods=["GET", "POST"])
def AnimalSightingsEndpoint(animal_id: str):
    """Hayvanın görülme geçmişini döndürür veya yeni bir saha görülme bildirimi ekler."""
    cleanId = animal_id.strip()
    if cleanId not in IN_MEMORY_ANIMAL_REGISTRY:
        return jsonify({"success": False, "message": f"'{cleanId}' kimlikli hayvan bulunamadı."}), 404

    recordData = IN_MEMORY_ANIMAL_REGISTRY[cleanId]
    itemRepoId = recordData.get(
        "repoId",
        DEFAULT_BARN_REPO_ID if recordData.get("category") == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID,
    )
    currentUser = GetCurrentRequestUser()
    animalSightingsList = recordData.setdefault("sightings", [])

    if request.method == "POST":
        hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(
            repoId=itemRepoId, userIdentifier=currentUser, requiredPermission="edit"
        )
        if not hasAccess:
            return jsonify({"success": False, "message": f"Konum ekleme yetkisi yok: {accessMessage}"}), 403

        data = request.get_json(silent=True) or request.form
        latitudeRaw = data.get("latitude")
        longitudeRaw = data.get("longitude")
        locationName = str(data.get("locationName", "")).strip() or "Saha Bildirimi"
        accuracyRaw = data.get("accuracy", 15.0)
        reportType = str(data.get("type", "sighting")).strip()
        confidenceScore = float(data.get("confidence", 95.0))

        if latitudeRaw is None or longitudeRaw is None:
            return jsonify({"success": False, "message": "Enlem (latitude) ve Boylam (longitude) zorunludur."}), 400

        try:
            parsedLatitude = float(latitudeRaw)
            parsedLongitude = float(longitudeRaw)
            parsedAccuracy = float(accuracyRaw)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Geçersiz koordinat biçimi."}), 400

        newSightingRecord = {
            "sightingId": f"sig_{len(animalSightingsList)}",
            "latitude": round(parsedLatitude, 6),
            "longitude": round(parsedLongitude, 6),
            "accuracy": round(parsedAccuracy, 1),
            "locationName": locationName,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": reportType,
            "confidence": confidenceScore,
        }
        animalSightingsList.append(newSightingRecord)

        if data.get("healthStatus"):
            newStatus = str(data.get("healthStatus")).strip().lower()
            if newStatus in ("healthy", "sick", "lost"):
                recordData["healthStatus"] = newStatus

        territoryStats = CalculateTerritoryStats(animalSightingsList)
        loggerInstance.info(f"Yeni görülme bildirimi eklendi: ID='{cleanId}', Konum='{locationName}'")

        return jsonify({
            "success": True,
            "message": f"'{recordData.get('animalName', cleanId)}' için yeni konum başarıyla kaydedildi.",
            "sighting": newSightingRecord,
            "territory": territoryStats,
        })

    territoryStats = CalculateTerritoryStats(animalSightingsList)
    return jsonify({
        "success": True,
        "animalId": cleanId,
        "repoId": itemRepoId,
        "animalName": recordData.get("animalName", cleanId),
        "species": recordData.get("species", ""),
        "category": recordData.get("category", ""),
        "healthStatus": recordData.get("healthStatus", "healthy"),
        "sightings": animalSightingsList,
        "territory": territoryStats,
    })


@app.route("/api/stray_map", methods=["GET"])
def GetStrayOverviewMapEndpoint():
    """Tüm sokak ve evcil hayvanların son görüldükleri yerleri ve yaşam alanı merkezlerini döndürür."""
    selectedRepoId = request.args.get("repoId", "").strip()
    straySummariesList = []
    for animalId, recordData in IN_MEMORY_ANIMAL_REGISTRY.items():
        category = recordData.get("category", "")
        species = recordData.get("species", "")
        itemRepoId = recordData.get("repoId", DEFAULT_STRAY_REPO_ID)
        if selectedRepoId and itemRepoId != selectedRepoId:
            continue
        if category == CATEGORY_STRAY or species in ("dog", "cat"):
            sightings = recordData.get("sightings", [])
            territoryStats = CalculateTerritoryStats(sightings)
            latestSighting = sightings[-1] if sightings else None

            straySummariesList.append({
                "animalId": animalId,
                "repoId": itemRepoId,
                "animalName": recordData.get("animalName", animalId),
                "category": category,
                "species": species,
                "breed": recordData.get("breed", ""),
                "healthStatus": recordData.get("healthStatus", "healthy"),
                "thumbnail": recordData.get("rawThumbnailBase64", ""),
                "latestSighting": latestSighting,
                "territory": territoryStats,
            })

    return jsonify({
        "success": True,
        "count": len(straySummariesList),
        "repoId": selectedRepoId or None,
        "animals": straySummariesList,
    })


@app.route("/api/animals/<animal_id>/update", methods=["POST"])
def UpdateAnimalEndpoint(animal_id: str):
    """Hayvanın pasaport bilgilerini ve sağlık/kayıp durumunu günceller."""
    cleanId = animal_id.strip()
    if cleanId not in IN_MEMORY_ANIMAL_REGISTRY:
        return jsonify({"success": False, "message": f"'{cleanId}' kimlikli hayvan bulunamadı."}), 404

    record = IN_MEMORY_ANIMAL_REGISTRY[cleanId]
    itemRepoId = record.get(
        "repoId",
        DEFAULT_BARN_REPO_ID if record.get("category") == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID,
    )
    currentUser = GetCurrentRequestUser()
    hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(
        repoId=itemRepoId, userIdentifier=currentUser, requiredPermission="edit"
    )
    if not hasAccess:
        return jsonify({"success": False, "message": f"Değiştirme yetkisi yok: {accessMessage}"}), 403

    data = request.get_json(silent=True) or request.form

    if "animalName" in data and data["animalName"].strip():
        record["animalName"] = data["animalName"].strip()
    if "breed" in data:
        record["breed"] = data["breed"].strip()
    if "gender" in data:
        record["gender"] = data["gender"].strip()
    if "neutered" in data:
        record["neutered"] = data["neutered"].strip()
    if "birthDate" in data:
        record["birthDate"] = data["birthDate"].strip()
    if "vaccinations" in data:
        record["vaccinations"] = data["vaccinations"].strip()
    if "distinctiveFeatures" in data:
        record["distinctiveFeatures"] = data["distinctiveFeatures"].strip()
    if "temperament" in data:
        record["temperament"] = data["temperament"].strip()
    if "favoriteFood" in data:
        record["favoriteFood"] = data["favoriteFood"].strip()
    if "healthStatus" in data:
        newStatus = data["healthStatus"].strip().lower()
        if newStatus in ("healthy", "sick", "lost"):
            record["healthStatus"] = newStatus

    loggerInstance.info(f"Hayvan kaydı güncellendi: ID='{cleanId}', Depo='{itemRepoId}', Yeni Durum='{record.get('healthStatus')}'")
    return jsonify({
        "success": True,
        "message": f"'{record.get('animalName', cleanId)}' bilgileri güncellendi.",
        "animal": {
            "animalId": record["animalId"],
            "repoId": itemRepoId,
            "animalName": record.get("animalName", record["animalId"]),
            "healthStatus": record.get("healthStatus", "healthy"),
        },
    })


@app.route("/api/animals/<animal_id>", methods=["DELETE"])
def DeleteAnimalEndpoint(animal_id: str):
    """Belirtilen hayvan kaydını bellekten siler."""
    cleanId = animal_id.strip()
    if cleanId not in IN_MEMORY_ANIMAL_REGISTRY:
        return jsonify({"success": False, "message": f"'{cleanId}' kimlikli hayvan bulunamadı."}), 404

    targetRecord = IN_MEMORY_ANIMAL_REGISTRY[cleanId]
    itemRepoId = targetRecord.get(
        "repoId",
        DEFAULT_BARN_REPO_ID if targetRecord.get("category") == CATEGORY_CATTLE else DEFAULT_STRAY_REPO_ID,
    )
    currentUser = GetCurrentRequestUser()
    hasAccess, accessMessage = repositoryManagerInstance.CheckAccess(
        repoId=itemRepoId, userIdentifier=currentUser, requiredPermission="edit"
    )
    if not hasAccess:
        return jsonify({"success": False, "message": f"Silme yetkisi yok: {accessMessage}"}), 403

    deletedItem = IN_MEMORY_ANIMAL_REGISTRY.pop(cleanId)
    loggerInstance.info(f"Hayvan kaydı silindi: ID='{cleanId}' (Depo: {itemRepoId})")
    return jsonify({
        "success": True,
        "message": f"'{deletedItem.get('animalName', cleanId)}' ({cleanId}) kaydı silindi.",
    })


@app.route("/api/clear", methods=["POST"])
def ClearRegistryEndpoint():
    """Bellek içi kayıtları sıfırlar."""
    totalCleared = len(IN_MEMORY_ANIMAL_REGISTRY)
    IN_MEMORY_ANIMAL_REGISTRY.clear()
    loggerInstance.info(f"Oturum kaydı temizlendi ({totalCleared} kayıt silindi).")
    return jsonify({
        "success": True,
        "message": f"Tüm oturum kayıtları temizlendi ({totalCleared} kayıt silindi).",
    })


@app.route("/api/stats", methods=["GET"])
def GetSystemStatsEndpoint():
    """Sistem, biyometrik motor ve kayıtlı hayvan istatistiklerini döndürür."""
    totalAnimals = len(IN_MEMORY_ANIMAL_REGISTRY)
    cattleCount = sum(1 for a in IN_MEMORY_ANIMAL_REGISTRY.values() if a.get("category") == CATEGORY_CATTLE or a.get("species") == "cattle")
    dogCount = sum(1 for a in IN_MEMORY_ANIMAL_REGISTRY.values() if a.get("species") == "dog")
    catCount = sum(1 for a in IN_MEMORY_ANIMAL_REGISTRY.values() if a.get("species") == "cat")

    healthyCount = sum(1 for a in IN_MEMORY_ANIMAL_REGISTRY.values() if a.get("healthStatus") == "healthy")
    sickCount = sum(1 for a in IN_MEMORY_ANIMAL_REGISTRY.values() if a.get("healthStatus") == "sick")
    lostCount = sum(1 for a in IN_MEMORY_ANIMAL_REGISTRY.values() if a.get("healthStatus") == "lost")

    return jsonify({
        "success": True,
        "totalAnimals": totalAnimals,
        "speciesCounts": {
            "cattle": cattleCount,
            "dog": dogCount,
            "cat": catCount,
        },
        "healthCounts": {
            "healthy": healthyCount,
            "sick": sickCount,
            "lost": lostCount,
        },
        "algorithm": "ORB Descriptors (500 keypoints) + RANSAC Homography Inliers",
        "visionFramework": "OpenCV Classical Computer Vision (Zero CNN / Zero Deep Learning)",
        "datasets": {
            "d1_cattle": "Zenodo Beef Cattle (4.923 görüntü, 268 birey)",
            "d2_cattle": "Pakistan Cattle Biometrics (3.308 görüntü, 459 birey)",
            "d4_dog": "DogFaceNet (8.363 görüntü, 1.393 birey)",
        },
        "qualityThresholds": {
            "blurThreshold": qualityGateInstance.blurThreshold,
            "minBrightness": 40.0,
            "maxBrightness": 240.0,
        },
    })


@app.route("/api/sample_image/<sample_key>", methods=["GET"])
def GetSampleImageEndpoint(sample_key: str):
    """Test için gerçek saha örnek görüntülerini doğrudan sunar."""
    from flask import send_file

    sampleMapping = {
        "cattle_d1": Path("data/downloads/extracted_d1/BeefCattle_Muzzle_Individualized/cattle_0100/cattle_0100_DSCF3856.jpg"),
        "cattle_d2": Path("data/downloads/extracted_d2/INDIVIDUAL SUBJECTS Data/cattle-001/IMG20230723072804.jpg"),
        "dog_d4": Path("data/downloads/extracted_d4/after_4_bis/1/1.0.jpg"),
    }

    targetPath = sampleMapping.get(sample_key.lower())
    if not targetPath or not targetPath.is_file():
        return jsonify({"success": False, "message": f"'{sample_key}' örneği bulunamadı."}), 404

    return send_file(str(targetPath.resolve()), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
