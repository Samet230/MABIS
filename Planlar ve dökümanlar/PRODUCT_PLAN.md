# Ürün Seviyesi Gereksinimler Planı
## ZooID (MABIS) — Sığır Odaklı Biyometrik Kimlik Doğrulama Sistemi

**Versiyon:** 0.2 (taslak)  
**Durum:** PRD.md'nin Bölüm 4–10'unun yerine geçer (kapsam, gereksinimler, metrikler). PRD.md'nin geri kalanı (problem tanımı, vizyon) geçerli.

---

## 1. Ürün Tanımı ve Konumlanma

**Ürün:** Sığırın burun deseninden (muzzle) kimlik kaydı ve doğrulaması yapan, telefon kamerasıyla çalışabilecek bir sistem.

**Ana odak:** Sığır. **İkincil:** köpek (burun), kedi (yüz).

**Konumlanma (önemli):** Türkiye'de sığırlar için küpe zorunlu ve Bakanlık elektronik küpe sistemine geçiyor. Bu yüzden ürün "küpenin yerine" değil, şu durumlar için **ikinci bir doğrulama katmanı** olarak tanımlanır:
- Küpe kaybolduğunda / şüpheli göründüğünde hayvanın kimliğini doğrulama
- Hırsızlık şüphesinde hayvanı kayıtlı kimliğiyle eşleştirme
- Sigorta/alım-satım doğrulaması

> Not: Küpe/TÜRKVET/PETVET düzenlemeleri için kaynaklar REFERENCES.md'ye eklenecek (Bakanlık duyuruları, bianet PETVET haberi, tarimorman.gov.tr yönetmelik değişiklikleri sayfası).

## 2. Kullanım Senaryoları

| # | Senaryo | Tür |
|---|---|---|
| S1 | **Kayıt (enrollment):** Hayvanın birkaç burun fotoğrafı çekilir, kimlik olarak kaydedilir | Sığır |
| S2 | **Doğrulama (1:1):** "Bu hayvan, kayıtlı X hayvanı mı?" (küpe no + burun fotoğrafı) | Sığır |
| S3 | **Tanıma (1:N):** Kayıtlı hayvanlar arasından kimliği bulma | Sığır |
| S4 | **Bilinmeyen reddi:** Kayıtlı olmayan hayvanı "kayıtsız" olarak işaretleme | Sığır |
| S5 | **Kayıt yönetimi:** Kayıt ekleme, güncelleme, silme, işlem geçmişi | Tümü |

## 3. Fonksiyonel Gereksinimler

Öncelik: **P0** = ürün çekirdeği, **P1** = önemli, **P2** = zaman kalırsa.

| ID | Gereksinim | Öncelik |
|---|---|---|
| FR-01 | **Kalite kapısı:** Çekilen görüntüde bulanıklık (Laplacian varyansı), pozlama/parlaklık, burun bölgesinin kadraja tam girmesi ve minimum çözünürlük kontrol edilir; yetersiz görüntü reddedilip yeniden çekim istenir | P0 |
| FR-02 | **Burun ROI segmentasyonu:** Hem kırpılmış burun görüntülerinden hem de **tüm yüz fotoğraflarından** (Pakistan seti) burun bölgesi otomatik ayrılır | P0 |
| FR-03 | **Ön işleme:** Gri seviye/HSV, CLAHE, gürültü giderme, boyut normalizasyonu | P0 |
| FR-04 | **Çoklu kareyle kayıt:** Kayıtta bir hayvan için en az N (başlangıç önerisi: 5) kaliteli görüntü alınır ve galeriye eklenir | P0 |
| FR-05 | **Öznitelik çıkarımı:** Klasik yöntemler (LBP, GLCM, SIFT/ORB). *Varyant B'de* bunlara ek olarak öğrenilmiş öznitelik (embedding) — bkz. Bölüm 9 | P0 |
| FR-06 | **1:N tanıma + güven skoru** | P0 |
| FR-07 | **1:1 doğrulama** (kabul/red kararı, eşik ayarlı) | P0 |
| FR-08 | **Bilinmeyen reddi (open-set):** Skor eşiğinin altında kalan sorgular "kayıtsız" döner; eşik veriyle kalibre edilir | P0 |
| FR-09 | **Kirli/ıslak burun dayanıklılığı:** Pakistan setindeki kirli burun örnekleriyle test edilir, kötü durumlar raporlanır | P1 |
| FR-10 | **Kayıt yönetimi ve işlem günlüğü** (kim, ne zaman kaydetti/sorguladı) | P1 |
| FR-11 | **Kullanım arayüzü:** CLI + basit web arayüzü (telefon tarayıcısından çekim/yükleme yapılabilecek şekilde, mobile geçişe uygun REST API tabanlı) | P1 |
| FR-12 | **Köpek desteği** (burun) | P1 |
| FR-13 | **Kedi desteği** (yüz) | P2 |
| FR-14 | Yerel çekim setiyle telefon üzerinde saha doğrulaması | P1 (bonus, veri erişimine bağlı) |

## 4. Fonksiyonel Olmayan Gereksinimler

- **Doğruluk:** İki ayrı hedef seviyesi (Bölüm 7). Ticari referans noktaları %98–99,6 civarı; bizim hedefimiz ölçüm sonrası kalibre edilir.
- **Süre:** Tek sorgunun işlenmesi dizüstü bilgisayarda birkaç saniye içinde (kesin sınır ilk profillemeden sonra belirlenecek).
- **Donanım varsayımı (telefon):** 8 MP+ ana kamera, otomatik odaklama (autofocus), yakın mesafe odaklama kabiliyeti. Redmi 10 gibi orta segment telefonlar yeterli kabul edilir.
- **Tekrarlanabilirlik:** Sabit seed, kayıtlı split dosyaları, sürümlenmiş konfigürasyon.
- **Veri güvenliği/gizlilik:** Hayvan görüntüleri kişisel veri değil, ancak **sahip bilgisiyle eşleştirilirse** kişisel veri işlenmiş olur; ürün aşamasında KVKK açısından ayrıca değerlendirilmelidir (hukuki danışmanlık gerektirir, bu doküman hukuki görüş değildir).
- **Genişletilebilirlik:** Yeni bir tür veya yeni bir öznitelik yöntemi mimariyi bozmadan eklenebilmeli.

## 5. Veri Gereksinimleri

| ID | Veri Seti | Rol | Boyut / İçerik | Not |
|---|---|---|---|---|
| D1 | **Zenodo Beef Cattle Muzzle/Noseprint** | Ana geliştirme ve kalibrasyon seti | ~644 MB, 268 hayvan, 4.923 kırpılmış burun görüntüsü, hayvan başına ortalama 12+ | Tek çiftlik, 3 et sığırı ırkı; çeşitlilik sınırlı. Yayımlanmış bir çalışma, bu sette **yinelenen kimlik listesi** paylaşmış — aynı hayvanın birden fazla ID ile kayıtlı olma ihtimaline karşı bu liste kontrol edilmeli, aksi halde train/test sızıntısı (leakage) olabilir |
| D2 | **Pakistan Cattle Biometrics Dataset** (Zenodo, "Cows Frontal Face Dataset") | İkinci set: çapraz veri seti testi, segmentasyon, gerçekçi kalite | ~13,9 GB; DSLR (Canon D80) ve telefonlarla (OnePlus 9 Pro, Oppo A76) çekilmiş; **tam yüz** görüntüleri, bir kısmında **kirli burun** | 460 sınıf/birey. Burun ROI segmentasyonu gerektirir (FR-02) — bu, projeye ek görüntü işleme içeriği katar |
| D3 | **Yerel çekim seti** (Elazığ) | Türkiye/telefon saha doğrulaması | Hedef: 20–30 hayvan, hayvan başına ≥8 fotoğraf, Redmi 10 | Çiftlik erişimi ve sahibinin izni gerekir. Garanti değil, bonus |
| D4 | DogFaceNet | Köpek (P1) | Zenodo kaydı toplam 3,9 GB; hizalı set 1.393 köpek / 8.363 görüntü (indirilmiş alt küme ~75.6 MB) | Görüntüler 224×224 hizalı yüz |
| D5 | Cat Individual Images | Kedi (P2) | 518 kedi, 13.536 görüntü | Boyut doğrulanmadı |

**Çıkarılan:** OpenCows2020 — üstten çekilmiş vücut/ten deseni verisi, burun verisi değil; bu projede kullanılmayacak.

**Toplam indirme (D1+D2):** yaklaşık 14,5 GB.

## 6. Değerlendirme Protokolleri

| Protokol | Tanım | Amaç |
|---|---|---|
| E1 — Veri seti içi | D1 içinde galeri/sorgu ayrımı (~%75/%25, birey-içi), 3 farklı seed | Klasik literatürle kıyas |
| E2 — Çapraz veri seti | D1 ile galeri kur → D2'den sorgula (ve tersi) | Genelleme; ürün iddiasının asıl testi |
| E3 — Open-set | Bazı hayvanlar galeriden tamamen çıkarılır ("bilinmeyen"); sızıntı kontrollü ayrım | FR-08 doğrulaması |
| E4 — Kalite dayanıklılığı | D2'deki kirli burun / farklı kamera alt kümeleri | FR-09 |
| E5 — Saha (bonus) | D3 ile telefon çekimi | FR-14 |

**Metrikler:** Rank-1 doğruluk, precision/recall/F1, confusion matrix, **FAR / FRR / EER** (doğrulama), open-set için sabit FAR altında doğru tanıma oranı ve ROC/AUC. Süre: ms/sorgu.

## 7. Kabul Kriterleri (kademeli)

| Seviye | Kriter | Not |
|---|---|---|
| **Makale (klasik)** | E1'de Rank-1 ≥ %90 (galeri oranı %75) | Klasik literatürde eğitim verisi oranına göre %75–93 aralığı raporlanmıştır; %90 hedefi üst banda yakındır |
| **Ürün prototipi** | E2 (çapraz set) ve E3 (open-set) sonuçları **ölçülüp raporlanmış** olmalı | Sayısal hedef, ilk ölçümden sonra belirlenecek |
| **Ürün ideali** | Ticari referanslara (%98+) yaklaşmak | Klasik yöntemlerle beklenmiyor; Varyant B (hibrit) ile denenir |

## 8. Kapsam Dışı (bilinçli)

- Manda (açık veri yok; "gelecek çalışma")
- At, eşek, deve ve küçükbaş hayvanlar
- Sahte girdi tespiti (fotoğrafın fotoğrafı / liveness)
- Gerçek zamanlı video akışı
- Native mobil uygulama yayınlama (yalnızca tarayıcı tabanlı prototip ve mobile uygun REST API)
- TÜRKVET / elektronik küpe sistemiyle entegrasyon (yalnızca gelecek çalışma olarak tartışılır)

## 9. Açık Karar: Yöntem Varyantı

Ders şartnamesinin derin öğrenme / hazır (pretrained) model kullanımına izin verip vermediği netleşene kadar iki varyant hazır tutulur:

- **Varyant A — Yalnızca klasik:** Tüm hat klasik görüntü işleme. Makale ve ders kuralları için uygun; ürün doğruluğu literatürdeki klasik aralıkla sınırlı kalır (%75–93).
- **Varyant B — Hibrit:** Ön işleme, segmentasyon ve kalite kapısı klasik kalır; eşleştirme için hazır bir modelden çıkarılan öznitelik (embedding) eklenir. Ürün doğruluğuna daha yakın. Kod mimarisi öznitelik çıkarımını yöntemden bağımsız tuttuğu için iki varyant aynı iskelete oturur.

## 10. Güncellenmiş 8 Haftalık Takvim

| Hafta | Makale hattı | Ürün hattı |
|---|---|---|
| 1 | Literatür + D1/D2 indirme, yapı standardı, yinelenen kimlik kontrolü; Varyant A/B kararı | Ortam kurulumu, kalite kapısı (FR-01) tasarımı |
| 2 | Ön işleme + ROI segmentasyonu (D1 kırpılmış, D2 tam yüz) | Kalite kapısı prototipi |
| 3 | LBP / GLCM / SIFT-ORB karşılaştırması (küçük alt küme) | Kayıt akışı (FR-04) |
| 4 | Veritabanı + eşleştirme, D1'de ilk uçtan uca test | 1:N tanıma + güven skoru |
| 5 | E1 tam değerlendirme; (P1) köpek hattı | 1:1 doğrulama + open-set eşiği (FR-07/08) |
| 6 | **E2 çapraz veri seti** + E3 open-set | Basit web arayüzü (FR-11) |
| 7 | Hata analizi (kirli burun, kamera farkı — E4); varsa D3 saha testi | Kayıt yönetimi/günlük (FR-10) |
| 8 | Makale finali + sunum | Demo, kurulum kılavuzu |

## 11. Riskler

| Risk | Etki | Önlem |
|---|---|---|
| D2 (13,9 GB) indirme/işleme yükü | Zaman kaybı | Hafta 1'de indir, önce küçük alt kümeyle çalış |
| D2'de burun segmentasyonu zor çıkabilir | FR-02 gecikir | Hafta 2'ye tam süre ayrıldı; başarısızlık oranı makalede raporlanır |
| Klasik yöntemler çapraz sette düşük çıkabilir | Ürün iddiası zayıflar | Bu beklenen ve raporlanacak bir bulgu; Varyant B ile karşılaştırılabilir |
| Yerel veri toplanamaz | FR-14 düşer | Bonus olarak tanımlandı, ana hedefi etkilemez |
| İki hat (makale + ürün) 8 haftaya sığmaz | Kapsam kayması | P2 maddeleri (kedi, saha) ilk kesilecekler |

## 12. Bu Dokümanla Senkron Edilecek Dosyalar

PRD.md (Bölüm 4–10), DATASET.md (veri envanteri, OpenCows2020'nin çıkarılması, D2 stratejisi), EVALUATION.md (E2–E4 protokolleri, SURF aralığı düzeltmesi), METHOD.md (Varyant A/B), AGENTS.md (izin verilen kütüphaneler Varyant kararına göre), REFERENCES.md (küpe/TÜRKVET/PETVET kaynakları).
