from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Tuple
import cv2
import numpy as np

from src.utils.logger import GetLogger

loggerInstance = GetLogger("SpeciesValidator")

# Sabitler
CASCADE_CAT_DEFAULT: Final[Path] = (
    Path(__file__).resolve().parent.parent / "segmentation" / "cascades" / "haarcascade_frontalcatface.xml"
)
MIN_CAT_FACE_AREA_RATIO: Final[float] = 0.045
MIN_CAT_CASCADE_NEIGHBORS: Final[int] = 5

MIN_NOSTRIL_CONTOUR_AREA: Final[float] = 250.0
CATTLE_MUZZLE_MIN_ASPECT_RATIO: Final[float] = 1.25


class SpeciesValidator:
    """Klasik bilgisayarlı görü yöntemleriyle görüntüdeki türün seçilen kategoriyle uyuşup uyuşmadığını denetler."""

    def __init__(
        self,
        catCascadePath: Path = CASCADE_CAT_DEFAULT,
    ) -> None:
        """Tür doğrulayıcı nesnesini başlatır."""
        self.catCascadeClassifier: Optional[cv2.CascadeClassifier] = None

        resolvedCascade = Path(catCascadePath).resolve()
        if hasattr(cv2, "CascadeClassifier") and resolvedCascade.is_file():
            try:
                classifier = cv2.CascadeClassifier(str(resolvedCascade))
                if not classifier.empty():
                    self.catCascadeClassifier = classifier
                else:
                    loggerInstance.warning(f"Kedi Haar cascade yüklenemedi: {resolvedCascade}")
            except Exception as cascadeException:
                loggerInstance.warning(f"Cascade başlatma hatası: {cascadeException}")
        elif hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            # OpenCV dahili cascade yedeği
            fallbackPath = Path(cv2.data.haarcascades) / "haarcascade_frontalcatface.xml"
            if fallbackPath.is_file():
                self.catCascadeClassifier = cv2.CascadeClassifier(str(fallbackPath))

    def DetectCatFace(self, imageMatrix: np.ndarray) -> Tuple[bool, float, Optional[Tuple[int, int, int, int]]]:
        """Görüntüde kedi yüzü olup olmadığını Haar cascade ile doğrular.

        Returns:
            Tuple[bool, float, box]: (kedi_var_mi, guven_orani, bounding_box)
        """
        if self.catCascadeClassifier is None or imageMatrix is None:
            return False, 0.0, None

        imageHeight, imageWidth = imageMatrix.shape[:2]
        totalImageArea = float(imageHeight * imageWidth)

        grayImage = (
            imageMatrix
            if imageMatrix.ndim == 2
            else cv2.cvtColor(imageMatrix, cv2.COLOR_BGR2GRAY)
        )
        equalizedGray = cv2.equalizeHist(grayImage)

        try:
            detectedFaces = self.catCascadeClassifier.detectMultiScale(
                equalizedGray,
                scaleFactor=1.1,
                minNeighbors=MIN_CAT_CASCADE_NEIGHBORS,
                minSize=(int(imageWidth * 0.15), int(imageHeight * 0.15)),
            )

            if len(detectedFaces) > 0:
                # En büyük tespit kutusunu seç
                bestFaceBox = max(detectedFaces, key=lambda box: box[2] * box[3])
                faceX, faceY, faceWidth, faceHeight = bestFaceBox
                faceAreaRatio = float((faceWidth * faceHeight) / totalImageArea)

                if faceAreaRatio >= MIN_CAT_FACE_AREA_RATIO:
                    confidenceScore = min(1.0, 0.6 + faceAreaRatio)
                    loggerInstance.debug(f"Kedi yüzü tespit edildi: alan oranı={faceAreaRatio:.2f}")
                    return True, confidenceScore, (faceX, faceY, faceWidth, faceHeight)

        except Exception as detectionException:
            loggerInstance.debug(f"Kedi yüz tespiti sırasında hata: {detectionException}")

        return False, 0.0, None

    def AnalyzeMuzzleAnatomy(self, imageMatrix: np.ndarray) -> Dict[str, Any]:
        """Burun deseni anatomisini (büyükbaş yatay çift delik vs köpek merkezi burun pedi) analiz eder."""
        if imageMatrix is None or imageMatrix.size == 0:
            return {
                "hasDualHorizontalNostrils": False,
                "nostrilSeparationDistance": 0.0,
                "isDogNosePadCandidate": False,
                "significantContourCount": 0,
                "contrastDifference": 0.0,
            }

        try:
            canonicalSize = 320
            resizedMatrix = cv2.resize(imageMatrix, (canonicalSize, canonicalSize))
            grayImage = (
                resizedMatrix
                if resizedMatrix.ndim == 2
                else cv2.cvtColor(resizedMatrix, cv2.COLOR_BGR2GRAY)
            )

            blurredGray = cv2.GaussianBlur(grayImage, (5, 5), 0)

            # 1. Koyu alanları (burun delikleri / burun pedi) segmente et
            meanIntensity = float(np.mean(blurredGray))
            intensityStd = float(np.std(blurredGray))
            darkThreshold = max(15.0, meanIntensity - 0.45 * intensityStd)

            binaryMask = (blurredGray < darkThreshold).astype(np.uint8) * 255
            morphologyKernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            cleanedMask = cv2.morphologyEx(binaryMask, cv2.MORPH_OPEN, morphologyKernel)

            contoursList, _ = cv2.findContours(
                cleanedMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            significantContours: List[Dict[str, Any]] = []
            minContourArea = float((canonicalSize * canonicalSize) * 0.0015)  # ~150 px

            for contourItem in contoursList:
                contourArea = cv2.contourArea(contourItem)
                if contourArea >= minContourArea:
                    boxX, boxY, boxW, boxH = cv2.boundingRect(contourItem)
                    aspectRatio = float(boxW / max(1, boxH))
                    significantContours.append({
                        "contour": contourItem,
                        "area": contourArea,
                        "box": (boxX, boxY, boxW, boxH),
                        "aspectRatio": aspectRatio,
                        "centerX": float((boxX + boxW / 2.0) / canonicalSize),
                        "centerY": float((boxY + boxH / 2.0) / canonicalSize),
                        "relW": float(boxW / canonicalSize),
                        "relH": float(boxH / canonicalSize),
                        "boxY": boxY,
                    })

            # 2. Fotometrik Kontrast (Merkez vs Yanaklar) ve Doku Varyansı
            boxTop = int(canonicalSize * 0.30)
            boxBottom = int(canonicalSize * 0.70)
            centerRegion = grayImage[boxTop:boxBottom, int(canonicalSize * 0.35):int(canonicalSize * 0.65)]
            leftCheekRegion = grayImage[boxTop:boxBottom, int(canonicalSize * 0.05):int(canonicalSize * 0.30)]
            rightCheekRegion = grayImage[boxTop:boxBottom, int(canonicalSize * 0.70):int(canonicalSize * 0.95)]

            meanCenterIntensity = float(np.mean(centerRegion))
            meanCheekIntensity = float((np.mean(leftCheekRegion) + np.mean(rightCheekRegion)) / 2.0)
            contrastDifference = float(meanCheekIntensity - meanCenterIntensity)
            laplacianVariance = float(np.var(cv2.Laplacian(centerRegion, cv2.CV_64F)))

            # 3. Yatay simetrik iki büyükbaş burun deliği tespiti
            hasDualHorizontalNostrils = False
            nostrilSeparationDistance = 0.0

            # Gerçek burun deliği adayları (kulak/arka plan gölgeleri elenir)
            nostrilCandidates = [
                item for item in significantContours
                if (item["boxY"] > 8)
                and (0.15 <= item["centerY"] <= 0.70)
                and (item["relW"] <= 0.48)
                and (item["relH"] <= 0.75)
            ]

            leftCandidates = [
                candidateItem for candidateItem in nostrilCandidates
                if candidateItem["centerX"] <= 0.35
            ]
            rightCandidates = [
                candidateItem for candidateItem in nostrilCandidates
                if candidateItem["centerX"] >= 0.65
            ]

            if leftCandidates and rightCandidates:
                for leftCandidate in leftCandidates:
                    for rightCandidate in rightCandidates:
                        horizontalDifference = float(rightCandidate["centerX"] - leftCandidate["centerX"])
                        verticalDifference = float(abs(rightCandidate["centerY"] - leftCandidate["centerY"]))
                        areaRatio = float(
                            max(leftCandidate["area"], rightCandidate["area"])
                            / max(1.0, min(leftCandidate["area"], rightCandidate["area"]))
                        )

                        # Sığır delikleri yatayda geniş ayrık (horizontalDifference >= 0.38), dikeyde hizada ve benzer boyuttadır
                        if horizontalDifference >= 0.38 and verticalDifference <= 0.20 and areaRatio <= 6.0:
                            hasDualHorizontalNostrils = True
                            nostrilSeparationDistance = horizontalDifference
                            break
                    if hasDualHorizontalNostrils:
                        break

            hasSingleLateralNostril = len(leftCandidates) > 0 or len(rightCandidates) > 0

            # 4. Köpek merkezi burun pedi adayları (merkezde belirgin koyu leke)
            centerDarkBlobs = [
                item for item in significantContours
                if (0.35 <= item["centerX"] <= 0.65)
                and (0.20 <= item["centerY"] <= 0.75)
                and (item["relW"] <= 0.50)
                and (item["relH"] <= 0.45)
            ]
            hasCenterDarkBlob = len(centerDarkBlobs) > 0

            # 1. Sığır burun deseni belirteçleri (çoklu biyometrik imza)
            isCattleCandidate = False
            if hasDualHorizontalNostrils:
                isCattleCandidate = True
            elif contrastDifference <= 20.0 and (
                laplacianVariance >= 400.0
                or hasSingleLateralNostril
                or contrastDifference < -5.0
            ):
                isCattleCandidate = True

            # 2. Köpek burun pedi belirteçleri
            isDogNosePadCandidate = False
            if not hasDualHorizontalNostrils:
                if contrastDifference > 25.0:
                    isDogNosePadCandidate = True
                elif hasCenterDarkBlob and contrastDifference > 18.0 and not hasSingleLateralNostril:
                    isDogNosePadCandidate = True
                elif hasCenterDarkBlob and laplacianVariance < 200.0 and not hasSingleLateralNostril:
                    isDogNosePadCandidate = True

            # 3. Kesin öncelik: Çift yatay burun deliği varsa KÖPEK OLAMAZ
            if hasDualHorizontalNostrils:
                isDogNosePadCandidate = False
                isCattleCandidate = True

            return {
                "hasDualHorizontalNostrils": hasDualHorizontalNostrils,
                "nostrilSeparationDistance": nostrilSeparationDistance,
                "isDogNosePadCandidate": isDogNosePadCandidate,
                "isCattleCandidate": isCattleCandidate,
                "hasSingleLateralNostril": hasSingleLateralNostril,
                "hasCenterDarkBlob": hasCenterDarkBlob,
                "significantContourCount": len(significantContours),
                "contrastDifference": contrastDifference,
                "laplacianVariance": laplacianVariance,
            }

        except Exception as analysisException:
            loggerInstance.warning(f"Anatomi analizi sırasında hata: {analysisException}")
            return {
                "hasDualHorizontalNostrils": False,
                "nostrilSeparationDistance": 0.0,
                "isDogNosePadCandidate": False,
                "isCattleCandidate": False,
                "hasSingleLateralNostril": False,
                "hasCenterDarkBlob": False,
                "significantContourCount": 0,
                "contrastDifference": 0.0,
                "laplacianVariance": 0.0,
            }

    def ValidateCategory(
        self,
        imageMatrix: np.ndarray,
        selectedCategory: str,
        selectedSubType: str = "dog",
    ) -> Tuple[bool, str, Optional[str]]:
        """Görüntüyü analiz ederek seçilen kategori ve türe uygunluğunu denetler.

        Args:
            imageMatrix: Girdi görüntüsü.
            selectedCategory: 'cattle' | 'stray'.
            selectedSubType: 'dog' | 'cat'.

        Returns:
            Tuple[bool, str, Optional[str]]:
                - isValid: Görüntü seçilen kategoriye uygun mu?
                - message: Açıklama veya ret gerekçesi.
                - detectedSpecies: Tespit edilen tür ('cat', 'cattle', 'dog', None).
        """
        if imageMatrix is None or imageMatrix.size == 0:
            return False, "Görüntü verisi boş veya geçersiz.", None

        normalizedCategory = selectedCategory.strip().lower()
        normalizedSubType = selectedSubType.strip().lower()

        # 1. Kedi yüzü denetimi
        isCatFace, catConfidence, catBox = self.DetectCatFace(imageMatrix)
        muzzleAnatomy = self.AnalyzeMuzzleAnatomy(imageMatrix)

        isCattleCandidate = muzzleAnatomy["isCattleCandidate"]
        isDogCandidate = muzzleAnatomy["isDogNosePadCandidate"]
        hasCenterDarkBlob = muzzleAnatomy["hasCenterDarkBlob"]
        laplacianVariance = muzzleAnatomy["laplacianVariance"]
        contrastDifference = muzzleAnatomy["contrastDifference"]
        hasDualHorizontalNostrils = muzzleAnatomy["hasDualHorizontalNostrils"]
        hasSingleLateralNostril = muzzleAnatomy["hasSingleLateralNostril"]

        # Tür belirleme motoru
        detectedSpecies: Optional[str] = None
        isCat = isCatFace and not isCattleCandidate and not isDogCandidate
        isDog = isDogCandidate and not isCattleCandidate
        isCattle = isCattleCandidate and not isDogCandidate

        if isDogCandidate and isCattleCandidate:
            # Çakışma durumunda çözücü (tie-breaker)
            if hasDualHorizontalNostrils:
                isCattle = True
                isDog = False
            elif contrastDifference > 20.0:
                isDog = True
                isCattle = False
            else:
                isCattle = True
                isDog = False

        if not isCat and not isCattle and not isDog:
            if hasDualHorizontalNostrils:
                isCattle = True
            elif contrastDifference > 20.0 or (hasCenterDarkBlob and not hasSingleLateralNostril):
                isDog = True
            elif (
                contrastDifference <= 20.0 and laplacianVariance >= 350.0
            ) or hasSingleLateralNostril or contrastDifference < -5.0:
                isCattle = True
            else:
                # Belirsizlik durumunda seçilen kategoriye tolerans tanı
                if normalizedCategory == "cattle" or "büyükbaş" in normalizedCategory:
                    isCattle = True
                else:
                    isDog = True

        detectedSpecies = "cat" if isCat else ("cattle" if isCattle else "dog")

        # Durum 1: Büyükbaş seçildiğinde kedi veya köpek yüklenmesi
        if normalizedCategory == "cattle" or "büyükbaş" in normalizedCategory:
            if isCat:
                return (
                    False,
                    "⚠️ Tür Uyuşmazlığı: 'Büyükbaş' kategorisinde KEDİ yüzü tespit edildi! "
                    "Lütfen 'Sokak Hayvanları -> Kedi' kategorisini seçiniz.",
                    "cat",
                )
            if detectedSpecies == "dog":
                return (
                    False,
                    "⚠️ Tür Uyuşmazlığı: 'Büyükbaş' kategorisinde KÖPEK burnu tespit edildi! "
                    "Lütfen 'Sokak Hayvanları -> Köpek' kategorisini seçiniz.",
                    "dog",
                )
            return True, "Büyükbaş burun deseni onaylandı.", "cattle"

        # Durum 2: Sokak Hayvanı -> Köpek seçildiğinde kedi veya büyükbaş yüklenmesi
        if normalizedCategory == "stray" and "dog" in normalizedSubType:
            if detectedSpecies == "cat":
                return (
                    False,
                    "⚠️ Tür Uyuşmazlığı: 'Köpek' kategorisinde KEDİ yüzü tespit edildi! "
                    "Lütfen 'Sokak Hayvanları' altındaki 'Kedi (Yüz)' seçeneğini işaretleyiniz.",
                    "cat",
                )
            if detectedSpecies == "cattle":
                return (
                    False,
                    "⚠️ Tür Uyuşmazlığı: 'Köpek' kategorisinde BÜYÜKBAŞ (sığır) burun deseni tespit edildi! "
                    "Lütfen 'Büyükbaş' kategorisini seçiniz.",
                    "cattle",
                )
            return True, "Köpek burun/yüz bölgesi onaylandı.", "dog"

        # Durum 3: Sokak Hayvanı -> Kedi seçildiğinde köpek veya büyükbaş yüklenmesi
        if normalizedCategory == "stray" and "cat" in normalizedSubType:
            if detectedSpecies == "cattle":
                return (
                    False,
                    "⚠️ Tür Uyuşmazlığı: 'Kedi' kategorisinde BÜYÜKBAŞ burun deseni tespit edildi! "
                    "Lütfen 'Büyükbaş' kategorisini seçiniz.",
                    "cattle",
                )
            if detectedSpecies == "dog":
                return (
                    False,
                    "⚠️ Tür Uyuşmazlığı: 'Kedi' kategorisinde KÖPEK burnu/yüzü tespit edildi! "
                    "Lütfen 'Sokak Hayvanları -> Köpek' seçeneğini işaretleyiniz.",
                    "dog",
                )
            return True, "Kedi yüz bölgesi onaylandı.", "cat"

        return True, "Tür doğrulaması tamamlandı.", detectedSpecies
