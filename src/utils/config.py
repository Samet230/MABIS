from pathlib import Path
from typing import Final, Tuple

# Proje dizin kökü ve veri yolları
PROJECT_ROOT_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT_DIR / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
SPLITS_DIR: Final[Path] = DATA_DIR / "splits"
RESULTS_DIR: Final[Path] = PROJECT_ROOT_DIR / "results"
FIGURES_DIR: Final[Path] = RESULTS_DIR / "figures"
TABLES_DIR: Final[Path] = RESULTS_DIR / "tables"
LOGS_DIR: Final[Path] = PROJECT_ROOT_DIR / "logs"

# Desteklenen hayvan türleri
VALID_SPECIES: Final[Tuple[str, ...]] = ("cattle", "dog", "cat")

# Görüntü ve ROI boyut standartları
ROI_TARGET_WIDTH: Final[int] = 300
ROI_TARGET_HEIGHT: Final[int] = 300
ROI_TARGET_SIZE: Final[Tuple[int, int]] = (ROI_TARGET_WIDTH, ROI_TARGET_HEIGHT)

# Veri kalite kontrol sabitleri
MIN_IMAGES_PER_ANIMAL: Final[int] = 4
DEFAULT_LAPLACIAN_BLUR_THRESHOLD: Final[float] = 80.0
MIN_IMAGE_WIDTH: Final[int] = 120
MIN_IMAGE_HEIGHT: Final[int] = 120
MIN_IMAGE_DIMENSIONS: Final[Tuple[int, int]] = (MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT)

# Train / Test bölümleme ve değerlendirme sabitleri
DEFAULT_TRAIN_RATIO: Final[float] = 0.75
DEFAULT_TEST_RATIO: Final[float] = 0.25
DEFAULT_RANDOM_SEEDS: Final[Tuple[int, ...]] = (42, 100, 2024)

# Öznitelik çıkarma yöntemleri
METHOD_LBP: Final[str] = "lbp"
METHOD_GLCM: Final[str] = "glcm"
METHOD_LBP_GLCM: Final[str] = "lbp_glcm"
METHOD_SIFT: Final[str] = "sift"
METHOD_ORB: Final[str] = "orb"
VALID_FEATURE_METHODS: Final[Tuple[str, ...]] = (
    METHOD_LBP,
    METHOD_GLCM,
    METHOD_LBP_GLCM,
    METHOD_SIFT,
    METHOD_ORB,
)

# LBP Parametreleri
LBP_DEFAULT_RADIUS: Final[int] = 1
LBP_DEFAULT_POINTS: Final[int] = 8
LBP_EXTENDED_RADIUS: Final[int] = 3
LBP_EXTENDED_POINTS: Final[int] = 24
LBP_METHOD_UNIFORM: Final[str] = "uniform"

# GLCM Parametreleri
GLCM_GRAY_LEVELS: Final[int] = 16
GLCM_DISTANCES: Final[Tuple[int, ...]] = (1, 2, 3)
GLCM_ANGLES: Final[Tuple[float, ...]] = (0.0, 0.785398, 1.570796, 2.356194)  # 0, 45, 90, 135 derece radyan cinsinden
GLCM_PROPERTIES: Final[Tuple[str, ...]] = (
    "contrast",
    "dissimilarity",
    "homogeneity",
    "energy",
    "correlation",
    "ASM",
)

# Eşleştirme parametreleri
LOWE_RATIO_THRESHOLD: Final[float] = 0.75
DEFAULT_KNN_NEIGHBORS: Final[int] = 1

# Depolama ve Supabase Yapılandırması
import os
SUPABASE_URL: Final[str] = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: Final[str] = os.environ.get("SUPABASE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: Final[str] = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BACKEND: Final[str] = os.environ.get("STORAGE_BACKEND", "sqlite").lower()

# Depo ve Erişim Kodu Sabitleri
REPO_TYPE_PRIVATE: Final[str] = "private"
REPO_TYPE_PUBLIC: Final[str] = "public"
VALID_REPO_TYPES: Final[Tuple[str, ...]] = (REPO_TYPE_PRIVATE, REPO_TYPE_PUBLIC)
DEFAULT_STRAY_REPO_ID: Final[str] = "repo_stray_public"
DEFAULT_BARN_REPO_ID: Final[str] = "repo_farm_demo"
