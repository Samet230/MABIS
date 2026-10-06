# ZooID (MABIS) — Ürün Seviyesi Yol Haritası ve Görev Listesi (Roadmap)

**Proje:** ZooID (MABIS — Multi-species Animal Biometric Identification System)  
**Odak:** Sığır burun deseni biyometrisi (Öncelikli), Köpek burun, Kedi yüz  
**Mevcut Durum:** Klasik öznitelikler (LBP, GLCM, SIFT, ORB + RANSAC) ve uçtan uca kapalı-küme pipeline tamamlandı (%100 sentetik doğruluk, 30/30 test geçiyor).  
**Yeni Hedef:** Ürün Seviyesi Gereksinimler Planı v0.2 doğrultusunda sistemi açık-küme (open-set), 1:1 doğrulama, kalite kapısı, tam yüz segmentasyonu, D1/D2 gerçek veri değerlendirmesi ve web arayüzü ile donatmak.

---

## 1. Çift Hatlı Geliştirme Takvimi (Akademik Hat & Ürün Hattı)

```
Hafta 1: Literatür + D1/D2 İndirme & Hazırlık [GÜNCEL] ───► Ortam Kurulumu & Kalite Kapısı (FR-01)
Hafta 2: Ön İşleme + Tam Yüz ROI Segmentasyonu (FR-02) ───► Kalite Kapısı Prototipi & Entegrasyonu
Hafta 3: Klasik Öznitelikler & RANSAC (Tamamlandı)    ───► Çoklu Kareyle Kayıt Akışı (FR-04)
Hafta 4: Veritabanı & Eşleştirme Motoru (Tamamlandı) ───► 1:N Tanıma & Güven Skoru
Hafta 5: D1 Gerçek Veri E1 Değerlendirmesi            ───► 1:1 Doğrulama & Açık-Küme Eşiği (FR-07/08)
Hafta 6: E2 Çapraz Veri Seti & E3 Açık-Küme Testi     ───► Basit Web & Mobil Arayüzü (FR-11)
Hafta 7: Hata Analizi (Kirli Burun, Çevre - E4/FR-09) ───► Kayıt Yönetimi & Denetim Günlüğü (FR-10)
Hafta 8: Makale Finali & Sunum                        ───► Canlı Demo, Dağıtım & Dokümantasyon
```

---

## 2. Aşamalı Görev Listesi (TODO)

### Faz 1: Planlama, Dokümantasyon & Veri İndirme (Hafta 1)
- [x] **Task 1.1: Ürün Seviyesi Planlama ve Doküman Senkronizasyonu**
  - `PRODUCT_PLAN.md` oluşturuldu.
  - `PRD.md`, `DATASET.md`, `EVALUATION.md`, `METHOD.md`, `AGENTS.md`, `REFERENCES.md` senkronize edildi.
- [x] **Task 1.2: D1 (Zenodo Beef Cattle) Veri Seti İndirme ve Doğrulama**
  - 613.92 MB arşiv indirildi ve bütünlüğü doğrulandı.
- [ ] **Task 1.3: D2 (Pakistan Cattle Biometrics, ~13.9 GB) Arka Plan İndirmesi**
  - `src/data/download_pakistan_dataset.py` başlatıldı (arka planda devam ediyor).
- [ ] **Task 1.4: D1 Veri Setini Standart Formata Çıkarma ve Çözme**
  - `BeefCattle_Muzzle_database.zip` açılacak ve `data/raw/cattle/` dizinine dönüştürülecek.

---

### Faz 2: Kalite Kapısı ve Çoklu Kare Kayıt (Hafta 2 - 3)
- [ ] **Task 2.1: Gelişmiş Kalite Kapısı Modülü (FR-01)**
  - `src/preprocessing/quality_gate.py`: Laplacian varyansı, aşırı/yetersiz pozlama, parlaklık histogramı ve kadraj kontrolü.
  - Birim testleri: `tests/test_quality_gate.py`.
- [ ] **Task 2.2: Çoklu Kare Kayıt Yöneticisi (FR-04)**
  - `src/enrollment/enrollment_manager.py`: En az $N=5$ kaliteli görüntü toplayıp galeri kaydı oluşturan mekanizma.
  - CLI `register` komutunun çoklu dosya ve klasör kabul edecek şekilde genişletilmesi.
- [ ] **Task 2.3: Tam Yüzden Burun ROI Segmentasyonu (FR-02)**
  - D2 Pakistan tam yüz fotoğraflarından burun bölgesini otomatik tespit edip kırpan algoritma.
  - `src/segmentation/cattle_segmenter.py` içine `SegmentFullFaceMuzzle()` desteği.

---

### Faz 3: 1:1 Doğrulama ve Açık-Küme Bilinmeyen Reddi (Hafta 4 - 5)
- [ ] **Task 3.1: 1:1 Doğrulama Modülü (FR-07 - 1:1 Verification)**
  - `MatchingEngine.Verify(queryFeature, claimedAnimalId, species, threshold) -> (bool, float)`.
  - CLI `verify` komutunun eklenmesi (`main.py verify ...`).
  - Birim testleri: `tests/test_verification.py`.
- [ ] **Task 3.2: Açık-Küme (Open-Set) Rejection ve Eşik Kalibrasyonu (FR-08)**
  - Bilinmeyen hayvanları "Kayıtsız / Yabancı" olarak reddeden eşik mekanizması.
  - Genuine ve Impostor skor dağılımlarından optimal eşik ($\theta$) ve EER hesaplama.
- [ ] **Task 3.3: Biyometrik Metrikler (FAR, FRR, EER, ROC/AUC) Genişletmesi**
  - `src/evaluation/evaluator.py` içine `CalculateVerificationMetrics()` ve `CalculateEER()`.
  - `src/evaluation/visualizer.py` içine ROC ve DET eğrileri çizimi.
  - Birim testleri: `tests/test_evaluation_biometrics.py`.

---

### Faz 4: Gerçek Veri Değerlendirme Deneyleri (Hafta 5 - 6)
- [ ] **Task 4.1: D1 Üzerinde E1 Kapalı-Küme Değerlendirmesi**
  - Gerçek 268 hayvanlık Zenodo veri setinde 3 tohum ile tam test (`seed=42, 100, 2024`).
  - Rank-1 doğruluk, F1 ve hata matrisi raporları.
- [ ] **Task 4.2: D1 $\longleftrightarrow$ D2 Çapraz Veri Seti Değerlendirmesi (E2)**
  - Çapraz veri seti genelleme başarısının ölçülmesi ve raporlanması.
- [ ] **Task 4.3: Açık-Küme Değerlendirmesi (E3)**
  - %20 bilinmeyen birey ayrımı ile açık-küme başarısı ve FAR/FRR analizi.

---

### Faz 5: Kullanıcı Arayüzü ve Kayıt Yönetimi (Hafta 6 - 7)
- [ ] **Task 5.1: Telefon Uyumlu Web Arayüzü ve REST API (FR-11)**
  - Flask tabanlı hafif web sunucusu: Mobil tarayıcı kamerasıyla çekim, kalite önizlemesi, kayıt ve tanıma.
  - Native mobil geçişe hazır REST API uç noktaları (`/api/register`, `/api/identify`, `/api/verify`, `/api/quality`).
- [ ] **Task 5.2: Kayıt Yönetimi ve Denetim Günlüğü (FR-10)**
  - SQLite denetim tablosu: işlem tarihi, işlem tipi, kullanıcı/cihaz bilgisi, sonuç skoru.
  - Hayvan kaydı silme ve güncelleme operasyonları.

---

### Faz 6: Çevre Dayanıklılığı, Hata Analizi ve Makale Finali (Hafta 7 - 8)
- [ ] **Task 6.1: Kirli/Islak Burun Stres Testi (FR-09 & E4)**
  - Pakistan veri setindeki çamurlu ve ıslak örneklerin başarı oranına etkisinin incelenmesi.
- [ ] **Task 6.2: Hata Analizi ve Görsel Örnekler**
  - Yanlış sınıflandırılan örneklerin görsel incelenmesi ve kök neden tablosu.
- [ ] **Task 6.3: Akademik Makale ve Proje Raporu Finali**
  - Tablo ve grafiklerin akademik formata getirilmesi, sunum slaytları ve dağıtım dokümantasyonu.
