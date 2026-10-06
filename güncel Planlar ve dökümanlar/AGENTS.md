# AGENTS.md — AI Kod Asistanı için Proje Bağlamı

> Bu dosya, Antigravity/Codex gibi AI destekli kod asistanlarının bu
> projede tutarlı kod üretmesi için referans alınır. Kod yazmadan önce
> bu dosyayı, ardından ilgili modülün bağlı olduğu dokümanı (PRD.md,
> ARCHITECTURE.md, DATASET.md, METHOD.md, EVALUATION.md) oku.

## 1. Proje Özeti

ZooID (MABIS) — sığırlarda burun deseni (ikincil: köpekte burun, kedide yüz) ile biyometrik kimlik kaydı, tanıma ve doğrulama yapan sistem. Üniversite Sayısal Görüntü İşleme dersi projesi olarak başlar; hedef ürün seviyesinde bir sistemdir: Python çekirdek + FastAPI arka uç + Android mobil istemci (8 hafta sonunda çalışan prototip) ve akademik makale. Ayrıntılar: REQUIREMENTS.md (v0.3).

## 2. Kesin Kısıtlar — ASLA İHLAL ETME

- **Varsayılan yöntem klasik görüntü işlemedir (Varyant A):** segmentasyon, morfolojik işlemler, LBP/GLCM/SIFT/ORB doku ve öznitelik analizi. Derin öğrenme kütüphaneleri (`tensorflow`, `torch`, `onnxruntime` vb.) ve hazır CNN/embedding modelleri, **kullanıcı Varyant B'yi açıkça onaylamadan eklenmez.** Bu kısıt ders kuralı olarak doğrulanmış değildir, bir varsayımdır; kullanıcı ders sorumlusundan izin alırsa Varyant B açılabilir. Varyant kararı kullanıcıya aittir, sessizce değiştirme.
- **Onaysız yeni bağımlılık ekleme.** Yalnızca Bölüm 4'teki listeyi kullan; farklı bir kütüphane gerekiyorsa önce sor.
- **Var olan modül arayüzlerini (fonksiyon imzalarını, API uç noktalarını) tek taraflı değiştirme.** Değişiklik gerekiyorsa önce kullanıcıya sor.
- **Sahte/rastgele sonuç üretme.** Metrikler her zaman gerçek veri üzerinden hesaplanır; test edilmemiş bir sayıyı "örnek" olarak bile rapor dosyalarına yazma.
- **Test setini eşik veya parametre ayarı için kullanma.** Ayar yalnızca validation alt kümesinde yapılır (bkz. DATASET.md, Bölüm 4).
- **Ham veriyi (`data/raw/`) değiştirme veya üzerine yazma.**

## 3. Klasör Yapısı

```
zooid/
├── data/
│   ├── raw/                # DATASET.md standardına göre
│   └── processed/
├── src/
│   ├── preprocessing/
│   ├── segmentation/
│   ├── features/
│   ├── matching/
│   ├── database/
│   └── evaluation/
├── api/                    # FastAPI arka uç (görüntü işleme mantığı içermez)
├── mobile/                 # Android istemci (çerçeve Hafta 1'de seçilir)
├── notebooks/
├── tests/
├── results/
├── main.py
└── requirements.txt
```

Yeni dosyalar ilgili modül klasörünün dışına konulmaz. Deneysel/tek seferlik kodlar `notebooks/` altında kalır; `src/` yalnızca yeniden kullanılabilir, test edilmiş modülleri barındırır.

## 4. İzin Verilen Kütüphaneler

Python: `opencv-python`, `scikit-image`, `scikit-learn`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pandas`, `pytest`, `fastapi`, `uvicorn`, `python-multipart`. Standart kütüphane (`sqlite3`, `json`, `pathlib` vb.) serbest.

Mobil istemcinin bağımlılıkları `mobile/` içinde ayrı yönetilir (çerçeve seçimi kullanıcıdan gelir).

## 5. Modül Arayüzleri (referans)

```python
# src/preprocessing/
def preprocess(image: np.ndarray) -> np.ndarray: ...

# src/segmentation/
def segment_roi(image: np.ndarray, species: str) -> np.ndarray: ...

# src/features/
def extract_features(roi: np.ndarray, method: str = "lbp") -> np.ndarray: ...

# src/database/
def register(animal_id: str, species: str, feature_vector: np.ndarray, method: str) -> None: ...

# src/matching/
def identify(feature_vector: np.ndarray, species: str, k: int = 1) -> list[tuple[str, float]]: ...

# src/evaluation/
def evaluate(predictions: list, ground_truth: list) -> dict: ...
```

`species` her zaman `"cattle" | "dog" | "cat"` değerlerinden biridir (`cattle` yalnızca sığırdır, manda kapsam dışı). Galeri kaydına yöntem adı ve sürümü yazılır.

API uç noktaları (REQUIREMENTS.md, FR-15/16):

```
POST /quality   -> {"ok": bool, "reasons": [str]}
POST /register  -> {"registered": int}                 # animal_id, species, images[]
POST /identify  -> {"match": str|null, "score": float, "known": bool}   # species, image
POST /verify    -> {"same": bool, "score": float}       # animal_id, species, image
```

API katmanı yalnızca `src/` modüllerini çağırır; görüntü işleme mantığı `api/` içine yazılmaz.

## 6. Kodlama Standartları

- **PEP8** uyumlu, `black` formatlaması varsayılır
- Tüm fonksiyonlarda **type hints** kullanılır
- Her fonksiyon **tek sorumluluk** taşır (ör. `preprocess` içinde
  segmentasyon yapılmaz)
- Docstring formatı: Google style, kısa açıklama + `Args`/`Returns`
- Değişken/fonksiyon isimleri **İngilizce**, yorum satırları ve
  docstring açıklamaları **Türkçe** olabilir (rapor/makale ile tutarlılık
  için) — ama kod tarafında karışıklık yaratmamak adına isimlendirme
  İngilizce kalmalı

## 7. Veri Kuralları

- Ham veri `data/raw/<species>/<animal_id>/img_NNN.jpg` yapısında
  (bkz. DATASET.md Bölüm 2)
- İşlenmiş/segmentlenmiş veri `data/processed/` altında aynı yapıda
- Veri setine yazma/silme işlemi yapan kod, her zaman `data/raw/`'ı
  değil `data/processed/`'ı hedeflemeli — ham veri asla üzerine
  yazılarak değiştirilmez

## 8. Test Beklentisi

- Her modül (`preprocessing`, `segmentation`, `features`, `matching`,
  `evaluation`) için `tests/` altında en az bir birim testi
- Testler küçük, sentetik veya örnek 2-3 görüntüyle çalışmalı — tüm veri
  setini test sırasında işlemeye çalışmamalı (yavaş olur)

## 9. Bir Şey Belirsizse

Varsayım yapıp sessizce ilerlemek yerine, karar PRD.md/ARCHITECTURE.md/
METHOD.md dokümanlarından biriyle çelişiyorsa veya bu dosyada
karşılığı yoksa, kullanıcıya kısaca sor.
