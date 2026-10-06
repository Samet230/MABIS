from typing import Dict, Final, List, Optional, Tuple
import cv2
import numpy as np

from src.database.db_manager import DatabaseManager, _defaultDatabaseManager
from src.utils.config import LOWE_RATIO_THRESHOLD, VALID_SPECIES
from src.utils.image_io import ValidateSpecies
from src.utils.logger import GetLogger

loggerInstance = GetLogger("Matcher")

DEFAULT_EPSILON: Final[float] = 1e-10
DEFAULT_RANSAC_REPROJECTION_THRESHOLD: Final[float] = 5.0
MINIMUM_RANSAC_MATCHES: Final[int] = 4
ORB_PACKED_DIMENSION: Final[int] = 34
SIFT_PACKED_DIMENSION: Final[int] = 130
ORB_RAW_DIMENSION: Final[int] = 32
SIFT_RAW_DIMENSION: Final[int] = 128
ORB_LOWE_RATIO_THRESHOLD: Final[float] = 0.80
SIFT_LOWE_RATIO_THRESHOLD: Final[float] = 0.75
NORMALIZATION_INLIER_COUNT: Final[float] = 30.0
NORMALIZATION_GOOD_MATCH_COUNT: Final[float] = 40.0
DEFAULT_VERIFICATION_THRESHOLD: Final[float] = 0.08
DEFAULT_OPEN_SET_REJECTION_THRESHOLD: Final[float] = 0.05
UNKNOWN_ANIMAL_LABEL: Final[str] = "unknown"


class MatchingEngine:
    """Veritabanındaki kayıtlarla sorgu özniteliğini karşılaştıran eşleştirme motoru."""

    def __init__(
        self,
        databaseManager: DatabaseManager = _defaultDatabaseManager,
        metric: str = "chi_square",
    ) -> None:
        """Eşleştirme motorunu başlatır.

        Args:
            databaseManager: Kayıtların okunacağı veritabanı yöneticisi.
            metric: 1D vektörler için benzerlik metriği ('chi_square' veya 'cosine').
        """
        self.databaseManager = databaseManager
        self.metric = metric
        self.bfMatcherL2 = cv2.BFMatcher(cv2.NORM_L2)
        self.bfMatcherHamming = cv2.BFMatcher(cv2.NORM_HAMMING)

    @staticmethod
    def CalculateChiSquareDistance(
        vectorAlpha: np.ndarray,
        vectorBeta: np.ndarray,
    ) -> float:
        """İki histogram arasındaki Ki-Kare (Chi-Square) mesafesini hesaplar."""
        denominator = vectorAlpha + vectorBeta + DEFAULT_EPSILON
        numerator = (vectorAlpha - vectorBeta) ** 2
        distanceValue = 0.5 * np.sum(numerator / denominator)
        return float(distanceValue)

    @staticmethod
    def CalculateCosineSimilarity(
        vectorAlpha: np.ndarray,
        vectorBeta: np.ndarray,
    ) -> float:
        """İki vektör arasındaki Kosinüs benzerliğini hesaplar [-1, 1] aralığında."""
        dotProduct = np.dot(vectorAlpha, vectorBeta)
        normAlpha = np.linalg.norm(vectorAlpha)
        normBeta = np.linalg.norm(vectorBeta)
        if normAlpha == 0.0 or normBeta == 0.0:
            return 0.0
        return float(dotProduct / (normAlpha * normBeta))

    def MatchHistogramVector(
        self,
        queryVector: np.ndarray,
        candidateRecords: List[Tuple[str, np.ndarray, dict]],
        topK: int = 1,
    ) -> List[Tuple[str, float]]:
        """1D doku histogramı/öznitelik vektörünü veritabanı kayıtlarıyla karşılaştırır."""
        scoredCandidates: List[Tuple[str, float]] = []

        for candidateAnimalId, candidateVector, _ in candidateRecords:
            if candidateVector.ndim != 1 or len(candidateVector) != len(queryVector):
                continue

            if self.metric == "cosine":
                similarityScore = self.CalculateCosineSimilarity(
                    queryVector, candidateVector
                )
                confidenceScore = max(0.0, min(1.0, similarityScore))
            else:
                # Varsayılan: Chi-square mesafesi
                distanceScore = self.CalculateChiSquareDistance(
                    queryVector, candidateVector
                )
                # Mesafeyi [0, 1] aralığında güven skoruna dönüştür
                confidenceScore = 1.0 / (1.0 + distanceScore)

            scoredCandidates.append((candidateAnimalId, confidenceScore))

        # Hayvan ID bazında en yüksek skoru sakla
        bestScorePerAnimal: Dict[str, float] = {}
        for candidateAnimalId, confidenceScore in scoredCandidates:
            if (
                candidateAnimalId not in bestScorePerAnimal
                or confidenceScore > bestScorePerAnimal[candidateAnimalId]
            ):
                bestScorePerAnimal[candidateAnimalId] = confidenceScore

        sortedCandidates = sorted(
            bestScorePerAnimal.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        return sortedCandidates[:topK]

    def MatchDescriptors(
        self,
        queryDescriptors: np.ndarray,
        candidateRecords: List[Tuple[str, np.ndarray, dict]],
        topK: int = 1,
    ) -> List[Tuple[str, float]]:
        """SIFT veya ORB tanımlayıcı matrislerini Lowe's ratio test ve RANSAC geometrik doğrulama ile karşılaştırır."""
        if queryDescriptors is None or queryDescriptors.size == 0 or queryDescriptors.ndim != 2:
            return []

        isPackedQuery = queryDescriptors.shape[1] in (SIFT_PACKED_DIMENSION, ORB_PACKED_DIMENSION)
        isBinaryDescriptor = (
            queryDescriptors.shape[1] == ORB_PACKED_DIMENSION
            or queryDescriptors.shape[1] == ORB_RAW_DIMENSION
            or queryDescriptors.dtype == np.uint8
        )

        if isPackedQuery:
            queryCoordinates = queryDescriptors[:, :2]
            extractedQueryDescriptors = (
                queryDescriptors[:, 2:].astype(np.uint8)
                if isBinaryDescriptor
                else queryDescriptors[:, 2:].astype(np.float32)
            )
        else:
            queryCoordinates = None
            extractedQueryDescriptors = (
                queryDescriptors.astype(np.uint8)
                if isBinaryDescriptor
                else queryDescriptors.astype(np.float32)
            )

        matcherInstance = (
            self.bfMatcherHamming if isBinaryDescriptor else self.bfMatcherL2
        )
        loweRatioThreshold = (
            ORB_LOWE_RATIO_THRESHOLD if isBinaryDescriptor else SIFT_LOWE_RATIO_THRESHOLD
        )

        scoredCandidates: List[Tuple[str, float]] = []

        for candidateAnimalId, candidateDescriptors, _ in candidateRecords:
            if candidateDescriptors.ndim != 2:
                continue
            if candidateDescriptors.shape[0] < 2 or extractedQueryDescriptors.shape[0] < 2:
                continue

            try:
                isPackedCandidate = candidateDescriptors.shape[1] in (
                    SIFT_PACKED_DIMENSION,
                    ORB_PACKED_DIMENSION,
                )
                if isPackedCandidate:
                    candidateCoordinates = candidateDescriptors[:, :2]
                    extractedCandidateDescriptors = (
                        candidateDescriptors[:, 2:].astype(np.uint8)
                        if isBinaryDescriptor
                        else candidateDescriptors[:, 2:].astype(np.float32)
                    )
                else:
                    candidateCoordinates = None
                    extractedCandidateDescriptors = (
                        candidateDescriptors.astype(np.uint8)
                        if isBinaryDescriptor
                        else candidateDescriptors.astype(np.float32)
                    )

                knnMatches = matcherInstance.knnMatch(
                    extractedQueryDescriptors,
                    extractedCandidateDescriptors,
                    k=2,
                )
                goodMatchesList = []
                for matchPair in knnMatches:
                    if len(matchPair) == 2:
                        matchFirst, matchSecond = matchPair
                        if matchFirst.distance < loweRatioThreshold * matchSecond.distance:
                            goodMatchesList.append(matchFirst)

                canRunRansac = (
                    queryCoordinates is not None
                    and candidateCoordinates is not None
                    and len(goodMatchesList) >= MINIMUM_RANSAC_MATCHES
                )

                if canRunRansac:
                    sourcePoints = np.float32(
                        [queryCoordinates[matchItem.queryIdx] for matchItem in goodMatchesList]
                    ).reshape(-1, 1, 2)
                    destinationPoints = np.float32(
                        [candidateCoordinates[matchItem.trainIdx] for matchItem in goodMatchesList]
                    ).reshape(-1, 1, 2)

                    homographyMatrix, inlierMask = cv2.findHomography(
                        sourcePoints,
                        destinationPoints,
                        cv2.RANSAC,
                        DEFAULT_RANSAC_REPROJECTION_THRESHOLD,
                    )
                    inlierCount = int(np.sum(inlierMask)) if inlierMask is not None else 0
                    totalDescriptorsCount = max(1, extractedQueryDescriptors.shape[0])
                    confidenceScore = float(inlierCount) / float(totalDescriptorsCount)
                else:
                    totalDescriptorsCount = max(1, extractedQueryDescriptors.shape[0])
                    confidenceScore = float(len(goodMatchesList)) / float(totalDescriptorsCount * 4.0)

                scoredCandidates.append((candidateAnimalId, confidenceScore))

            except Exception as matchException:
                loggerInstance.debug(f"Tanımlayıcı eşleştirme hatası: {matchException}")
                continue

        # Birey ID bazında en yüksek skoru sakla
        bestScorePerAnimal: Dict[str, float] = {}
        for candidateAnimalId, confidenceScore in scoredCandidates:
            if (
                candidateAnimalId not in bestScorePerAnimal
                or confidenceScore > bestScorePerAnimal[candidateAnimalId]
            ):
                bestScorePerAnimal[candidateAnimalId] = confidenceScore

        sortedCandidates = sorted(
            bestScorePerAnimal.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        return sortedCandidates[:topK]

    def Identify(
        self,
        featureVector: np.ndarray,
        speciesName: str,
        topK: int = 1,
        minConfidenceThreshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """Sorgu özniteliğini veritabanındaki tür kayıtlarıyla eşleştirip en yakın adayları döndürür.

        Args:
            featureVector: Sorgu öznitelik matrisi veya vektörü.
            speciesName: Sorgulanacak tür ('cattle', 'dog', 'cat').
            topK: Döndürülecek en yakın aday sayısı (varsayılan: 1).
            minConfidenceThreshold: Açık-küme (open-set) ret eşiği. Bu eşiğin altındaki adaylar
                                     'unknown' olarak etiketlenir veya elenir.

        Returns:
            List[Tuple[str, float]]: [(animal_id, confidence_score), ...] sıralı listesi.
        """
        if featureVector is None or featureVector.size == 0:
            raise ValueError("Sorgu öznitelik vektörü boş veya geçersiz.")

        if not ValidateSpecies(speciesName):
            raise ValueError(
                f"Geçersiz tür: '{speciesName}'. Desteklenenler: {VALID_SPECIES}"
            )

        candidateRecords = self.databaseManager.GetRecordsBySpecies(speciesName)
        if not candidateRecords:
            loggerInstance.warning(f"'{speciesName}' için veritabanında kayıtlı aday bulunamadı.")
            return []

        try:
            if featureVector.ndim == 1:
                matchedCandidates = self.MatchHistogramVector(
                    queryVector=featureVector,
                    candidateRecords=candidateRecords,
                    topK=topK,
                )
            elif featureVector.ndim == 2:
                matchedCandidates = self.MatchDescriptors(
                    queryDescriptors=featureVector,
                    candidateRecords=candidateRecords,
                    topK=topK,
                )
            else:
                raise ValueError(
                    f"Desteklenmeyen öznitelik boyutu: {featureVector.shape}"
                )

            # Açık-küme (Open-Set) Rejection denetimi (FR-08)
            if minConfidenceThreshold is not None and matchedCandidates:
                topCandidateId, topCandidateScore = matchedCandidates[0]
                if topCandidateScore < minConfidenceThreshold:
                    loggerInstance.info(
                        f"Aday skoru ({topCandidateScore:.3f}) eşiğin ({minConfidenceThreshold:.3f}) altında. "
                        f"'{UNKNOWN_ANIMAL_LABEL}' olarak reddedildi."
                    )
                    return [(UNKNOWN_ANIMAL_LABEL, topCandidateScore)]

            return matchedCandidates

        except Exception as identificationException:
            loggerInstance.error(
                f"Kimliklendirme sırasında hata ({speciesName}): {identificationException}"
            )
            raise

    def Verify(
        self,
        featureVector: np.ndarray,
        claimedAnimalId: str,
        speciesName: str,
        verificationThreshold: Optional[float] = None,
    ) -> Tuple[bool, float]:
        """1:1 Doğrulama (Verification - FR-07): 'Bu hayvan, kayıtlı X hayvanı mı?' sorusunu yanıtlar.

        Args:
            featureVector: Sorgu öznitelik matrisi veya vektörü.
            claimedAnimalId: İddia edilen hedef hayvan kimliği (küpe numarası / ID).
            speciesName: Hayvan türü ('cattle', 'dog', 'cat').
            verificationThreshold: Kabul/ret karar eşiği. None verilirse DEFAULT_VERIFICATION_THRESHOLD kullanılır.

        Returns:
            Tuple[bool, float]: (is_accepted, confidence_score) çifti.
        """
        if featureVector is None or featureVector.size == 0:
            raise ValueError("Sorgu özniteliği boş veya geçersiz.")

        if not ValidateSpecies(speciesName):
            raise ValueError(f"Geçersiz tür: '{speciesName}'.")

        thresholdValue = (
            DEFAULT_VERIFICATION_THRESHOLD
            if verificationThreshold is None
            else verificationThreshold
        )

        # Yalnızca iddia edilen hayvana ait şablon kayıtlarını çek
        allSpeciesRecords = self.databaseManager.GetRecordsBySpecies(speciesName)
        targetAnimalRecords = [
            recordItem
            for recordItem in allSpeciesRecords
            if recordItem[0] == claimedAnimalId
        ]

        if not targetAnimalRecords:
            loggerInstance.warning(
                f"Doğrulama başarısız: '{claimedAnimalId}' kimlikli kayıt veritabanında bulunamadı."
            )
            return False, 0.0

        if featureVector.ndim == 1:
            matchedScores = self.MatchHistogramVector(
                queryVector=featureVector,
                candidateRecords=targetAnimalRecords,
                topK=1,
            )
        elif featureVector.ndim == 2:
            matchedScores = self.MatchDescriptors(
                queryDescriptors=featureVector,
                candidateRecords=targetAnimalRecords,
                topK=1,
            )
        else:
            raise ValueError(f"Desteklenmeyen öznitelik boyutu: {featureVector.shape}")

        if not matchedScores:
            return False, 0.0

        bestConfidenceScore = matchedScores[0][1]
        isAccepted = bestConfidenceScore >= thresholdValue

        loggerInstance.info(
            f"1:1 Doğrulama kararı ({claimedAnimalId}): Skor={bestConfidenceScore:.4f}, "
            f"Eşik={thresholdValue:.4f} -> {'KABUL' if isAccepted else 'RET'}"
        )
        return isAccepted, bestConfidenceScore


# Standart sözleşme için varsayılan motor örneği (AGENTS.md ve ARCHITECTURE.md)
_defaultMatchingEngine = MatchingEngine()


def identify(
    feature_vector: np.ndarray,
    species: str,
    k: int = 1,
    min_confidence: Optional[float] = None,
) -> List[Tuple[str, float]]:
    """ZooID standart modül sözleşmesine uygun kimlik tespit fonksiyonu.

    Args:
        feature_vector: Sorgu öznitelik vektörü.
        species: Tür adı ('cattle' | 'dog' | 'cat').
        k: İstenen en yakın aday sayısı (Rank-k).
        min_confidence: Açık-küme ret eşiği (opsiyonel).

    Returns:
        List[Tuple[str, float]]: [(animal_id, confidence_score)] listesi.
    """
    return _defaultMatchingEngine.Identify(
        featureVector=feature_vector,
        speciesName=species,
        topK=k,
        minConfidenceThreshold=min_confidence,
    )


def verify(
    feature_vector: np.ndarray,
    claimed_animal_id: str,
    species: str,
    threshold: Optional[float] = None,
) -> Tuple[bool, float]:
    """ZooID standart modül sözleşmesine uygun 1:1 kimlik doğrulama fonksiyonu.

    Args:
        feature_vector: Sorgu öznitelik vektörü veya matrisi.
        claimed_animal_id: İddia edilen hedef hayvan kimliği.
        species: Tür adı ('cattle' | 'dog' | 'cat').
        threshold: Kabul/ret karar eşiği.

    Returns:
        Tuple[bool, float]: (kabul_edildi_mi, guven_skoru)
    """
    return _defaultMatchingEngine.Verify(
        featureVector=feature_vector,
        claimedAnimalId=claimed_animal_id,
        speciesName=species,
        verificationThreshold=threshold,
    )
