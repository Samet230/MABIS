# Test & Değerlendirme Planı
## ZooID (MABIS) — Sığır Odaklı Biyometrik Kimlik Doğrulama Sistemi

**İlişkili dokümanlar:** PRD.md, DATASET.md, METHOD.md, PRODUCT_PLAN.md  
**Versiyon:** 0.2 (Ürün Seviyesi Güncellemesi)  

---

## 1. Değerlendirme Protokolleri (E1 – E5)

Sistemin başarısı tek bir sentetik veya izole testle değil, biyometrik sistem standartlarına uygun 5 kademeli protokol ile ölçülür:

### E1 — Veri Seti İçi Kapalı-Küme Değerlendirme (In-Dataset Closed-Set)
- **Veri Seti:** D1 (Zenodo Beef Cattle Muzzle).
- **Prosedür:** Her bireyin görüntüleri %75 galeri (kayıt), %25 sorgu (test) olarak ayrılır.
- **Tekrarlanabilirlik:** 3 bağımsız rastgele tohum (`seed=42, 100, 2024`).
- **Amaç:** Klasik literatürdeki kapalı-küme çalışmalarla doğrudan karşılaştırılabilir temel başarı seviyesini belirlemek.
- **Hedef:** Rank-1 Doğruluk $\ge \%90$.

### E2 — Çapraz Veri Seti Değerlendirme (Cross-Dataset Generalization)
- **Veri Seti:** D1 (Zenodo Beef Cattle) $\longleftrightarrow$ D2 (Pakistan Cattle Biometrics).
- **Prosedür:** D1 ile referans veritabanı kurulup D2'den sorgular yapılır (ve tersi).
- **Amaç:** Sistemin farklı kamera sensörleri (DSLR vs telefon), farklı çiftlik ortamları ve farklı ırklar arasındaki genelleme başarısını test etmek. Ürün iddiasının en kritik sınavıdır.

### E3 — Açık-Küme ve Bilinmeyen Reddi (Open-Set Evaluation)
- **Prosedür:** Veri setindeki bireylerin bir kısmı (%20) galeriden tamamen hariç tutulur. Bu "yabancı/kayıtsız" hayvanlar test aşamasında sorgulanır.
- **Amaç:** FR-08 gereksiniminin doğrulanması. Sistemin kayıtsız bir hayvanı yanlışlıkla kayıtlı birine benzetmek yerine "Kayıtsız / Yabancı" olarak reddetme başarısını ölçmek.
- **Metrik:** FAR, FRR, EER ve EER operasyonel eşik kalibrasyonu.

### E4 — Kalite ve Çevre Dayanıklılığı (Environmental Stress Test)
- **Veri Seti:** D2 içerisindeki kirli, ıslak ve çamurlu burun fotoğrafları ile farklı ışıklandırma koşulları.
- **Amaç:** Algoritmanın zorlu çevre faktörleri altındaki performans sınırlarını ve hata modlarını tespit etmek.

### E5 — Saha Doğrulaması (Field Bonus)
- **Veri Seti:** D3 (Elazığ yerel çiftlik çekimleri, Redmi 10).
- **Amaç:** Telefon kamerasıyla gerçek çiftlik ortamında uçtan uca çalışabilirliği göstermek.

---

## 2. Değerlendirme Metrikleri ve Matematiksel Tanımları

### A. Tanıma (1:N Identification) Metrikleri
1. **Rank-1 Doğruluk (Rank-1 Accuracy):**
   $$ \text{Rank-1} = \frac{\sum_{i=1}^{N_q} \mathbb{I}(\hat{y}_i^{(1)} = y_i)}{N_q} $$
   Burada $\hat{y}_i^{(1)}$ sorgu $i$ için en yüksek benzerlik skoru alan adayın ID'sidir, $y_i$ gerçek ID'dir.
2. **Precision, Recall ve F1-Score:** Macro ve Weighted ortalamalarla sınıf dengesizlikleri gözlemlenir.
3. **Confusion Matrix (Hata Matrisi):** Karışan bireylerin analizi için $N \times N$ matris.

### B. Doğrulama (1:1 Verification) ve Açık-Küme Metrikleri
1. **False Acceptance Rate (FAR - Yanlış Kabul Oranı):**
   Farklı iki hayvana ait (impostor) bir çiftin benzerlik skorunun eşik değerini ($\theta$) aşarak sistem tarafından "aynı hayvan" kabul edilme oranı:
   $$ \text{FAR}(\theta) = \frac{\text{Yanlış Kabul Edilen Impostor Sayısı}}{\text{Toplam Impostor Çift Sayısı}} $$
2. **False Rejection Rate (FRR - Yanlış Ret Oranı):**
   Aynı hayvana ait (genuine) bir çiftin benzerlik skorunun eşiğin ($\theta$) altında kalarak sistem tarafından reddedilme oranı:
   $$ \text{FRR}(\theta) = \frac{\text{Yanlış Reddedilen Genuine Sayısı}}{\text{Toplam Genuine Çift Sayısı}} $$
3. **Equal Error Rate (EER - Eşit Hata Oranı):**
   $\text{FAR}(\theta) = \text{FRR}(\theta)$ olduğu noktadaki hata oranı. Biyometrik sistemin genel kalitesini gösteren standart metriktir; EER ne kadar düşükse sistem o kadar kararlıdır.
4. **Decidability Index ($d'$ - Ayırt Edilebilirlik İndeksi):**
   $$ d' = \frac{|\mu_{\text{genuine}} - \mu_{\text{impostor}}|}{\sqrt{\frac{1}{2}(\sigma_{\text{genuine}}^2 + \sigma_{\text{impostor}}^2)}} $$
   $d' > 3.0$ mükemmel ayrışmayı, $d' < 1.5$ ise dağılımların çakıştığını gösterir.
5. **ROC Eğrisi ve AUC (Area Under Curve):** Farklı eşik değerleri için $\text{TAR} = 1 - \text{FRR}$ ile $\text{FAR}$ arasındaki ilişkiyi gösterir.

---

## 3. Kabul Kriterleri (Kademeli)

| Seviye | Kriter | Literatür Referansı & Not |
|---|---|---|
| **Akademik Çizgi (Klasik)** | E1'de Rank-1 $\ge \%90$ (%75 galeri oranı) | Klasik literatürde (Awad 2019, Noviyanto 2013) eğitim verisine göre %75–93 arası başarı raporlanmıştır. %90 hedefi klasik yöntemler için üst sınırdır. |
| **Ürün Prototipi** | E2 (çapraz) ve E3 (açık-küme) sonuçlarının ölçülüp kalibre edilmesi | Gerçek dünya şartlarında düşüş beklenir; dürüstçe belgelenecektir. |
| **Ürün İdeali** | Ticari seviye (%98+ Rank-1, $\text{EER} < \%1$) | Saf klasik yöntemlerle beklenmez; Varyant B (hibrit) ile hedeflenebilir. |

---

## 4. Hata Analizi Prosedürü

1. **Hatalı Örneklerin İzolasyonu:** Yanlış eşleşen veya yanlış reddedilen tüm sorgular otomatik olarak `results/failures/` dizinine kaydedilir.
2. **Kök Neden Sınıflandırması:** Her hata 4 ana kategoriden birine atanır:
   - *Segmentasyon Hatası:* Burun bölgesi kadraj dışı veya hatalı kırpılmış.
   - *Görüntü Kalitesi / Bulanıklık:* Hareket veya odak bulanıklığı.
   - *Aşırı Aydınlatma / Yansıma:* Nemli burun yüzeyindeki aşırı flaş/güneş parlaması.
   - *Yabancı Madde / Kirlilik:* Burun üzerinde çamur, yem veya su damlası.
3. **İstatistiksel Raporlama:** Hata kategorilerinin yüzdeleri makalenin "Sınırlamalar ve Tartışma" bölümüne eklenir.
