# Veri Seti & Ön İşleme Dokümanı
## ZooID (MABIS) — Sığır Odaklı Biyometrik Kimlik Doğrulama Sistemi

**İlişkili dokümanlar:** PRD.md, ARCHITECTURE.md, METHOD.md, EVALUATION.md, PRODUCT_PLAN.md  
**Versiyon:** 0.2 (Ürün Seviyesi Güncellemesi)  

---

## 1. Veri Seti Envanteri

| ID | Tür | Veri Seti | Birey Sayısı | Görüntü Sayısı | Boyut | Durum / Rol |
|---|---|---|---|---|---|---|
| **D1** | Sığır | **Zenodo Beef Cattle Muzzle Database** | 268 | 4.923 | ~644 MB | **İndirildi & Doğrulandı** ✅ — Ana geliştirme, kalibrasyon ve E1 içi test seti. Doğrudan kırpılmış burun görüntüleri. |
| **D2** | Sığır | **Pakistan Cattle Biometrics Dataset** ("Cows Frontal Face", Zenodo 10535934) | 460 | 8.000+ | ~13.9 GB | **İndiriliyor** ⏳ — E2 çapraz veri seti testi, FR-02 tam yüz segmentasyonu, FR-09 kirlilik ve aydınlatma stres testleri. DSLR ve akıllı telefonlarla çekilmiş tam yüz fotoğrafları. |
| **D3** | Sığır | **Yerel Çekim Seti** (Elazığ) | 20–30 | $\ge 200$ | — | **Saha / Bonus** (P1) — Türkiye yerel ırkları, Redmi 10 akıllı telefon kamerası ile gerçek saha koşullarında kayıt ve doğrulama. |
| **D4** | Köpek | **DogFaceNet_224resized** | 1.393 | 8.363 | ~75.6 MB | **İndirildi & Doğrulandı** ✅ — P1 köpek burun desteği. |
| **D5** | Kedi | **Cat Individual Images** | 518 | 13.536 | — | **P2 (Kaggle)** — Kedi yüz tanıma. |

> ⚠️ **Kapsam Dışı Bırakılan Veri Seti:**  
> **OpenCows2020:** Üstten ve yandan çekilmiş gövde/ten deseni içerdiği, burun biyometrisi barındırmadığı için proje kapsamından tamamen çıkarılmıştır.

---

## 2. D1 (Zenodo Beef Cattle) İçin Kritik Not: Yinelenen Kimlik Kontrolü

Literatürdeki son çalışmalar, Zenodo Beef Cattle veri setinde bazı hayvanların birden fazla klasörde farklı ID'ler altında yinelenmiş olabileceğini göstermiştir. Bu durum, train/test ayrımında veri sızıntısına (data leakage) yol açabilir.
- Dönüştürme ve bölme aşamasında bu yinelenen kimlik şüphesi taşıyan örnekler taranır ve filtrelenir.
- Birey-içi (per-individual) ayrımda her hayvanın görüntüleri kronolojik veya homojen biçimde %75 galeri - %25 test olarak bölünür.

---

## 3. D2 (Pakistan Cattle) Özellikleri ve Stratejisi

Pakistan veri seti, sistemin ürün seviyesine taşınmasında kritik bir rol oynar:
1. **Tam Yüz Girişi:** Görüntüler buruna kırpılmamış, tüm kafa ve vücut parçalarını içermektedir. Bu sebeple **FR-02 (Burun ROI Segmentasyonu)** modülünün geliştirilmesini zorunlu kılar.
2. **Kirli / Islak Burun Örnekleri:** Çiftlik ortamından gelen çamurlu, ıslak ve kirli burun desenleri içerir; bu da **FR-09 dayanıklılık analizinin** temelini oluşturur.
3. **Çoklu Kamera Cihazları:** Canon D80 DSLR, OnePlus 9 Pro ve Oppo A76 akıllı telefon kameralarıyla çekilmiştir; cihazlar arası genelleme yeteneğini test eder.

---

## 4. Klasör ve Format Standardı

Projede kullanılan tüm veri setleri, ham kaynaktan bağımsız olarak standart hiyerarşiye dönüştürülür (`src/data/convert_dataset.py`):

```
data/
├── downloads/                     # Orijinal indirilen zip arşivleri
│   ├── BeefCattle_Muzzle_database.zip
│   ├── DogFaceNet_224resized.zip
│   └── INDIVIDUAL_SUBJECTS_Data.zip
├── raw/                           # Standart klasör yapısı
│   ├── cattle/
│   │   ├── animal_0001/
│   │   │   ├── img_001.jpg
│   │   │   └── img_002.jpg
│   │   └── animal_0002/
│   ├── dog/
│   └── cat/
├── processed/                     # Kalite filtresinden geçmiş, ROI segmente ve normalize
│   └── <species>/<animal_id>/roi_001.png
└── splits/                        # Tekrarlanabilir train/test split JSON dosyaları
    ├── split_cattle_seed_42.json
    ├── split_cattle_seed_100.json
    └── split_cattle_seed_2024.json
```

---

## 5. Veri Kalite Kapısı Kriterleri (FR-01)

Sisteme kaydedilmek veya sorgulanmak istenen her görüntü, aşağıdaki kalite kontrollerinden geçirilir:

1. **Bulanıklık Kontrolü (Blur Filter):** Gri seviyeye dönüştürülen görüntü üzerinde Laplacian operatörünün varyansı ($Var(\nabla^2 I)$) hesaplanır. Eşik: $\ge 80.0$.
2. **Pozlama ve Parlaklık (Illumination Check):** Ortalama piksel yoğunluğu $40 \le \mu \le 220$ aralığında olmalıdır. Aşırı karanlık veya aşırı parlamış görüntüler elenir.
3. **Kadraj ve Çözünürlük Kontrolü:** Görüntü boyutları en az $120 \times 120$ piksel olmalıdır. Tespit edilen burun ROI alanı, girdi görüntüsünün en az %15'ini kapsamalıdır.
4. **Birey Başına Minimum Görüntü Sayısı:** Bir hayvanın galeri/test ayrımına girebilmesi için veri setinde en az 4 kaliteli görüntüsü bulunmalıdır.

---

## 6. Train / Test Ayrım Protokolü

- **Kapalı-Küme (Closed-Set) Ayrımı (E1):** Her bireyin görüntüleri %75 galeri, %25 test olarak ayrılır. 3 farklı rastgele tohum (42, 100, 2024) ile tekrarlanır.
- **Açık-Küme (Open-Set) Ayrımı (E3):** Veri setindeki bireylerin %80'i "bilinen" (galeri + sorgu), %20'si ise "bilinmeyen / yabancı" (yalnızca sorgu) olarak ayrılır. Veritabanında kaydı olmayan bu %20'lik grubun sistem tarafından doğru reddedilme oranı (True Rejection Rate) test edilir.
- **Çapraz Veri Seti Ayrımı (E2):** D1'deki tüm bireyler galeriye eklenir; D2'deki bireyler sorgulanır (ve tersi).

---

## 7. Ön İşleme Hattı

Standart ön işleme modülü (`src/preprocessing/preprocessor.py`):
1. **Renk Uzayı:** BGR $\rightarrow$ Gri seviye (öznitelik çıkarımı için) ve HSV (renk tabanlı maskeleme için).
2. **Kontrast Zenginleştirme:** CLAHE (Contrast Limited Adaptive Histogram Equalization) — `clipLimit=2.5`, `tileGridSize=(8, 8)`.
3. **Gürültü Giderme:** $3 \times 3$ Medyan Filtre.
4. **Geometrik Boyut:** Çıkarılan ROI $300 \times 300$ piksel kare matrise normalize edilir.
