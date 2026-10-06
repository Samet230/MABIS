# AGENTS.md — AI Kod Asistanı için Proje Bağlamı ve Kurallar

> Bu dosya, Antigravity/Codex gibi AI destekli kod asistanlarının bu projede tutarlı ve hatasız kod üretmesi için bağlam referansıdır. Herhangi bir kod yazmadan veya düzenleme yapmadan önce bu dosyayı ve ilgili gereksinim dokümanlarını oku.

---

## 1. Proje Özeti ve Kapsamı

**ZooID (MABIS):** Büyükbaş hayvanlarda (sığır) ve köpeklerde burun deseni (muzzle), kedilerde yüz özellikleri kullanarak sayısal görüntü işleme teknikleriyle hayvan kimliklendirme, kayıt ve doğrulama yapan bir sistemdir.
- **Akademik Hat:** Sayısal Görüntü İşleme ders projesi ve akademik makale.
- **Ürün Hattı:** Telefon kamerasıyla çalışan, mobil geçişe uygun REST API mimarisine sahip ürün prototipi.

---

## 2. Kesin Kısıtlar ve Geliştirici Kuralları

### A. Algoritmik Kısıtlar (Varyant A Önceliği)
- **Derin Öğrenme / CNN Kullanımı:** Ders şartnamesi kesinleşene kadar temel hatta `tensorflow`, `torch` veya önceden eğitilmiş CNN modelleri (ResNet, VGG vb.) kullanılmayacaktır. Klasik yöntemler (segmentasyon, morfolojik işlemler, LBP, GLCM, SIFT, ORB ve RANSAC) temel çizgidir.
- **Varyant B (Gelecek Genişletme):** Kod mimarisi öznitelik çıkarıcı ve eşleştiriciyi soyutlayarak gelecekte embedding modellerinin kolayca takılabilmesini destekler.
- **Sahte / Rastgele Sonuç Üretme Yasağı:** Değerlendirme metrikleri ve raporlar daima gerçek veri ve hesaplamalara dayanmalıdır; placeholder veya uydurma değerler raporlara yazılamaz.

### B. Kodlama ve İsimlendirme Kuralları (ZORUNLU)
- **Dil:** Sınıf, metot, fonksiyon ve değişken isimleri daima **İngilizce** olmalıdır. Yorum satırları ve docstring açıklamaları Türkçe olabilir.
- **Sınıflar (Classes):** Daima `PascalCase` (Örn: `MatchingEngine`, `QualityGate`, `EnrollmentManager`).
- **Metotlar ve Fonksiyonlar (Methods):** Dahili metotlar `PascalCase` (Örn: `CalculateChiSquareDistance`, `MatchDescriptors`); modül sözleşme fonksiyonları `snake_case` (Örn: `segment_roi`, `extract_features`, `identify`, `verify`).
- **Değişkenler (Variables):** Daima `camelCase` (Örn: `confidenceScore`, `queryCoordinates`, `candidateRecords`).
- **Sabitler (Constants):** Tümü BÜYÜK HARF ve alt çizgi ile (`UPPER_CASE_SNAKE`) (Örn: `ROI_TARGET_WIDTH`, `ORB_PACKED_DIMENSION`).
- **Anlamlı İsimler:** Asla `x`, `y`, `d` gibi tek harfli değişken kullanılmaz (döngü indeksleri hariç: `item`, `candidateId` gibi açıklayıcı olmalı).
- **Temiz Kod İlkeleri:**
  - *Single Responsibility:* Bir sınıf/fonksiyon yalnızca tek bir iş yapar.
  - *DRY (Don't Repeat Yourself):* Tekrar eden mantıklar ortak yardımcı fonksiyonlara taşınır.
  - *Magic Numbers:* Sabit değerler mutlaka `config.py` veya sınıf başında adlandırılmış sabit olarak tanımlanır.
  - *Hata Yönetimi ve Güvenlik:* Veritabanı, dosya okuma ve API gibi dış dünya işlemlerinde mutlaka `try-catch` blokları kullanılır. Kullanıcıdan gelen tüm girdiler doğrulanır (`ValidateSpecies` vb.).

---

## 3. İzin Verilen Kütüphaneler

Aşağıdaki kütüphaneler dışında onay almadan yeni bağımlılık eklenemez:
- `opencv-python` (görüntü işleme, SIFT, ORB, RANSAC, Haar cascade)
- `scikit-image` (LBP doku analizi, morfolojik operasyonlar)
- `scikit-learn` (GLCM, sınıflandırma metrikleri, train/test ayrımı)
- `numpy`, `scipy` (matematiksel işlemler, mesafe hesapları)
- `matplotlib`, `seaborn` (grafik ve ısı haritaları görselleştirme)
- `pandas` (tablo ve sonuç raporlama)
- `pytest` (birim ve entegrasyon testleri)
- `Flask` (telefon arayüzü ve mobil geçiş için hafif REST API altyapısı)
- Python Standart Kütüphanesi (`sqlite3`, `pathlib`, `json`, `subprocess`, `urllib` vb.)

---

## 4. Standart Modül Sözleşmeleri (API İmzaları)

```python
# src/preprocessing/
def preprocess(image: np.ndarray) -> np.ndarray: ...
def check_quality(image: np.ndarray) -> Tuple[bool, str, Dict[str, float]]: ...

# src/segmentation/
def segment_roi(image: np.ndarray, species: str) -> np.ndarray: ...

# src/features/
def extract_features(roi: np.ndarray, method: str = "orb") -> np.ndarray: ...

# src/database/
def register(animal_id: str, species: str, feature_vector: np.ndarray) -> None: ...

# src/matching/
def identify(feature_vector: np.ndarray, species: str, k: int = 1) -> List[Tuple[str, float]]: ...
def verify(feature_vector: np.ndarray, claimed_animal_id: str, species: str, threshold: float = 0.15) -> Tuple[bool, float]: ...

# src/evaluation/
def evaluate(predictions: list, ground_truth: list) -> dict: ...
```

---

## 5. Klasör Düzeni

```
zooid/
├── data/
│   ├── downloads/          # İndirilen ham arşivler
│   ├── raw/                # Standart formattaki hayvan görüntüleri
│   ├── processed/          # Segmentasyon ve ön işlemeden geçmiş ROI'ler
│   ├── splits/             # Tekrarlanabilir train/test split JSON'ları
│   └── database/           # SQLite veritabanı dosyaları
├── src/
│   ├── data/               # İndirme, dönüştürme ve split betikleri
│   ├── preprocessing/      # Kalite kapısı ve ön işleme
│   ├── segmentation/       # ROI tespiti ve cascades
│   ├── features/           # LBP, GLCM, SIFT, ORB çıkarıcılar
│   ├── matching/           # Eşleştirme motoru ve RANSAC doğrulaması
│   ├── database/           # SQLite veritabanı yöneticisi
│   ├── evaluation/         # Metrik hesaplayıcı ve görselleştirici
│   ├── experiments/        # Ablation ve parametre ince ayarı
│   └── utils/              # Konfigürasyon, loglama ve dosya I/O
├── tests/                  # Pytest birim ve entegrasyon testleri
├── results/                # Tablolar, grafikler ve rapor çıktıları
├── Planlar ve dökümanlar/  # Proje ve ürün seviyesi şartnameler
├── main.py                 # CLI arayüzü
└── requirements.txt
```
