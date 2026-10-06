# Ürün Seviyesi Gereksinimler Planı
## ZooID (MABIS) — Sığır Odaklı Biyometrik Kimlik Doğrulama Sistemi

**Versiyon:** 0.3 (taslak) — mobil uygulama ders teslimi kapsamına alındı
**Durum:** PRD.md'nin Bölüm 4–10'unun yerine geçer (kapsam, gereksinimler, metrikler). PRD.md'nin geri kalanı (problem tanımı, vizyon) geçerli.

---

## 1. Ürün Tanımı ve Konumlanma

**Ürün:** Sığırın burun deseninden (muzzle) kimlik kaydı ve doğrulaması yapan, telefon kamerasıyla çalışabilecek bir sistem.

**Ana odak:** Sığır. **İkincil:** köpek (burun), kedi (yüz).

**Teslim biçimi (karar verildi):** Ders teslimine (8 hafta) kadar **Android'de çalışan mobil uygulama** (ince istemci) + arka uç API + makale. Uygulama APK olarak veya Play Console'un dahili/kapalı test kanalıyla dağıtılır; **herkese açık mağaza yayını teslim kapsamı dışındadır** (bkz. Bölüm 8 ve 11).

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
| FR-11 | **Mobil uygulama (Android, ince istemci):** rehberli kamera ekranı (burun çerçeve kılavuzu, odak kilidi), kayıt, tanıma ve doğrulama akışları, sonuç ekranı (kimlik + güven skoru veya "kayıtsız") | P0 |
| FR-12 | **Köpek desteği** (burun) | P1 |
| FR-13 | **Kedi desteği** (yüz) | P2 |
| FR-14 | Yerel çekim setiyle telefon üzerinde saha doğrulaması | P1 (bonus, veri erişimine bağlı) |
| FR-15 | **Arka uç API (FastAPI):** kayıt, tanıma, doğrulama ve kalite kontrolü uç noktaları; tüm istemciler aynı API'yi çağırır | P0 |
| FR-16 | **Yeniden çekim akışı:** Kalite kapısı (FR-01) reddederse uygulama nedeni gösterir (bulanık / karanlık / burun kadraj dışı) ve yeniden çekim ister. İlk sürümde kalite kontrolü sunucuda çalışır; cihaz üstü kontrol sonraki aşamaya kalır | P0 |
| FR-17 | **Web demo (yedek istemci):** Aynı API'yi çağıran, telefon tarayıcısından çekim/yükleme yapan basit sayfa; mobil uygulama gecikirse demo bununla yapılır | P1 |
| FR-18 | **Çevrimdışı kuyruk:** Bağlantı yokken çekilen görüntüler saklanıp bağlantı gelince gönderilir | P2 |

## 4. Fonksiyonel Olmayan Gereksinimler

- **Doğruluk:** İki ayrı hedef seviyesi (Bölüm 7). Ticari referans noktaları %98–99,6 civarı; bizim hedefimiz ölçüm sonrası kalibre edilir.
- **Süre:** Tek sorgunun işlenmesi dizüstü bilgisayarda birkaç saniye içinde (kesin sınır ilk profillemeden sonra belirlenecek).
- **Donanım varsayımı (telefon):** 8 MP+ ana kamera, otomatik odaklama (autofocus), yakın mesafe odaklama kabiliyeti. Redmi 10 gibi orta segment telefonlar yeterli kabul edilir.
- **Platform:** Önce Android; iOS kapsam dışı. İstemci çerçevesi (React Native/Expo veya Flutter) Hafta 1'de seçilir.
- **Ağ / barındırma:** İlk sürüm çevrimiçi çalışır. Demo için API dizüstü bilgisayarda çalışır, telefon aynı ağdan (veya tünelle) erişir; bulut barındırma sonraki aşamadır.
- **Tekrarlanabilirlik:** Sabit seed, kayıtlı split dosyaları, sürümlenmiş konfigürasyon.
- **Veri güvenliği/gizlilik:** Hayvan görüntüleri kişisel veri değil, ancak **sahip bilgisiyle eşleştirilirse** kişisel veri işlenmiş olur; ürün aşamasında KVKK açısından ayrıca değerlendirilmelidir (hukuki danışmanlık gerektirir, bu doküman hukuki görüş değildir).
- **Genişletilebilirlik:** Yeni bir tür veya yeni bir öznitelik yöntemi mimariyi bozmadan eklenebilmeli.

## 5. Veri Gereksinimleri

| ID | Veri Seti | Rol | Boyut / İçerik | Not |
|---|---|---|---|---|
| D1 | **Zenodo Beef Cattle Muzzle/Noseprint** | Ana geliştirme ve kalibrasyon seti | ~644 MB, 268 hayvan, 4.923 kırpılmış burun görüntüsü, hayvan başına ortalama 12+ | Tek çiftlik, 3 et sığırı ırkı; çeşitlilik sınırlı. Yayımlanmış bir çalışma, bu sette **yinelenen kimlik listesi** paylaşmış — aynı hayvanın birden fazla ID ile kayıtlı olma ihtimaline karşı bu liste kontrol edilmeli, aksi halde train/test sızıntısı (leakage) olabilir |
| D2 | **Pakistan Cattle Biometrics Dataset** (Zenodo, "Cows Frontal Face Dataset") | İkinci set: çapraz veri seti testi, segmentasyon, gerçekçi kalite | ~13,9 GB; DSLR (Canon D80) ve telefonlarla (OnePlus 9 Pro, Oppo A76) çekilmiş; **tam yüz** görüntüleri, bir kısmında **kirli burun** | Görüntü/hayvan sayısı ve klasör yapısı indirildikten sonra doğrulanmalı. Burun ROI segmentasyonu gerektirir (FR-02) — bu, projeye ek görüntü işleme içeriği katar |
| D3 | **Yerel çekim seti** (Elazığ) | Türkiye/telefon saha doğrulaması | Hedef: 20–30 hayvan, hayvan başına ≥8 fotoğraf, Redmi 10 | Çiftlik erişimi ve sahibinin izni gerekir. Garanti değil, bonus |
| D4 | DogFaceNet | Köpek (P1) | Zenodo kaydı toplam 3,9 GB; hizalı set 1.393 köpek / 8.363 görüntü | Görüntüler 224×224 hizalı yüz: burun bölgesi çok az piksel, doku yöntemleri için zayıf kalabilir → Hafta 1'de kontrol |
| D5 | Cat Individual Images | Kedi (P2) | 518 kedi, 13.536 görüntü | Boyut doğrulanmadı |

**Çıkarılan:** OpenCows2020 — üstten çekilmiş vücut/ten deseni verisi, burun verisi değil; bu projede kullanılmayacak.

**Toplam indirme (D1+D2):** yaklaşık 14,5 GB. D4 ve D5 dahil edilirse ek birkaç GB.

## 6. Değerlendirme Protokolleri

| Protokol | Tanım | Amaç |
|---|---|---|
| E1 — Veri seti içi | D1 içinde galeri/sorgu ayrımı (~%75/%25, birey-içi), 3 farklı seed | Klasik literatürle kıyas |
| E2 — Veri seti aktarımı | Yöntem parametreleri ve doğrulama eşiği D1'de belirlenir; D2'de **hiçbir ayar değiştirilmeden**, D2'nin kendi galeri/sorgu ayrımıyla test edilir (iki sette aynı hayvanlar olmadığı için galeri test edilen setin içinden kurulur). Ters yön (D2→D1) de yapılır | Kamera/ırk/ortam değişimine genelleme; ürün iddiasının asıl testi |
| E3 — Open-set | Bazı hayvanlar galeriden tamamen çıkarılır ("bilinmeyen"); sızıntı kontrollü ayrım | FR-08 doğrulaması |
| E4 — Kalite dayanıklılığı | D2'deki kirli burun / farklı kamera alt kümeleri | FR-09 |
| E5 — Saha (bonus) | D3 ile telefon çekimi | FR-14 |

**Metrikler:** Rank-1 doğruluk, precision/recall/F1, confusion matrix, **FAR / FRR / EER** (doğrulama), open-set için sabit FAR altında doğru tanıma oranı ve ROC/AUC. Süre: ms/sorgu.

## 7. Kabul Kriterleri (kademeli)

| Seviye | Kriter | Not |
|---|---|---|
| **Makale (klasik)** | E1'de Rank-1 ≥ %90 (galeri oranı %75) | Klasik literatürde eğitim verisi oranına göre %75–93 aralığı raporlanmıştır; %90 hedefi üst banda yakındır, tutmazsa sonuç dürüstçe raporlanır |
| **Ürün prototipi** | E2 (çapraz set) ve E3 (open-set) sonuçları **ölçülüp raporlanmış** olmalı | Sayısal hedef, ilk ölçümden sonra belirlenecek — ölçmeden hedef yazmıyoruz |
| **Ürün ideali** | Ticari referanslara (%98+) yaklaşmak | Klasik yöntemlerle beklenmiyor; Varyant B (hibrit) ile denenir |
| **Mobil teslim** | Android telefonda (Redmi 10 sınıfı) API üzerinden uçtan uca çalışır: kayıt → tanıma → doğrulama → "kayıtsız" sonucu | Herkese açık yayın değil; APK veya dahili/kapalı test |

## 8. Kapsam Dışı (bilinçli)

- Manda (açık veri yok; "gelecek çalışma")
- At, eşek, deve ve küçükbaş hayvanlar
- Sahte girdi tespiti (fotoğrafın fotoğrafı / liveness)
- Gerçek zamanlı video akışı
- Google Play'de **herkese açık yayın** (yeni kişisel hesaplar için kapalı test şartı var, bkz. Bölüm 11) ve iOS uygulaması
- Cihaz üstü (offline) çalışma; çevrimdışı kuyruk yalnızca P2
- TÜRKVET / elektronik küpe sistemiyle entegrasyon (yalnızca gelecek çalışma olarak tartışılır)

## 9. Açık Karar: Yöntem Varyantı

Ders şartnamesinin derin öğrenme / hazır (pretrained) model kullanımına izin verip vermediği **henüz netleşmedi**. İki varyant hazır tutulur:

- **Varyant A — Yalnızca klasik:** Tüm hat klasik görüntü işleme. Makale için uygun; ürün doğruluğu literatürdeki klasik aralıkla sınırlı kalır (%75–93).
- **Varyant B — Hibrit:** Ön işleme, segmentasyon ve kalite kapısı klasik kalır (görüntü işleme içeriği burada); eşleştirme için hazır bir modelden çıkarılan öznitelik (embedding) eklenir. Ürün doğruluğuna daha yakın; dersin kuralına uygun olması gerekir.

**Bu karar Hafta 1'de verilmeli.** Kod mimarisi öznitelik çıkarımını yöntemden bağımsız tuttuğu için (ARCHITECTURE.md, Bölüm 2.5) iki varyant aynı iskelete oturur.

## 10. Güncellenmiş 8 Haftalık Takvim

| Hafta | Makale + çekirdek hat | API + mobil |
|---|---|---|
| 1 | Literatür; D1/D2 indirme; yapı standardı; yinelenen kimlik kontrolü; **Varyant A/B kararı** (hocaya soru) | FastAPI iskeleti; istemci çerçevesi seçimi (Expo/Flutter); Play Console hesabı gerekiyorsa açılış |
| 2 | Ön işleme + ROI segmentasyonu (D1 kırpılmış, D2 tam yüz) | Kalite kapısı (FR-01) API uç noktası |
| 3 | LBP / GLCM / SIFT-ORB karşılaştırması (küçük alt küme) | Mobil iskelet: kamera ekranı + görüntü yükleme (Redmi 10'da çalışır) |
| 4 | Veritabanı + eşleştirme; D1'de ilk uçtan uca test | Kayıt akışı (çoklu kare) uygulamada |
| 5 | E1 tam değerlendirme | Tanıma + doğrulama + sonuç ekranı |
| 6 | E2 çapraz veri seti + E3 open-set | "Kayıtsız" sonucu, yeniden çekim akışı (FR-16), hata yönetimi |
| 7 | Hata analizi (E4); varsa D3 saha verisi | Telefonda uçtan uca saha benzeri test; APK derleme |
| 8 | Makale finali + sunum | Demo + APK teslimi + kurulum kılavuzu |

**Kesme sırası (süre yetmezse):** kedi (FR-13) → köpek (FR-12) → D3 saha verisi (FR-14) → çevrimdışı kuyruk (FR-18) → kayıt yönetimi ayrıntıları (FR-10). Mobil uygulama gecikirse web demo (FR-17) yedek istemci olarak kullanılır.

## 11. Riskler

| Risk | Etki | Önlem |
|---|---|---|
| Üç hat (makale + çekirdek + mobil) 8 haftaya sığmayabilir | Kapsam kayması | Bölüm 10'daki kesme sırası; web demo yedek |
| Google Play'de herkese açık yayın 8 haftada mümkün değil | Beklenti sapması | Yeni kişisel geliştirici hesaplarında üretim erişimi için en az 12 testerin 14 gün kesintisiz kapalı testte olması gerekiyor (kurumsal hesaplar muaf). Teslim APK veya dahili/kapalı testle yapılır. Şartlar değişebildiği için başvurudan önce Play Console yardım sayfasından doğrulanmalı |
| Uygulamadaki doğruluk klasik aralıkla (%75–93) sınırlı | Yanlış eşleşme; özellikle hırsızlık/sigorta senaryosunda ciddi | Sonuç ekranında güven skoru ve "karar destek" dili; herkese açık yayın öncesi E2/E3 sonuçları + saha pilotu |
| D2 (13,9 GB) indirme/işleme yükü | Zaman kaybı | Hafta 1'de indir, önce küçük alt kümeyle çalış |
| D2'de burun segmentasyonu zor çıkabilir | FR-02 gecikir | Hafta 2'ye tam süre ayrıldı; başarısızlık oranı makalede raporlanır |
| Klasik yöntemler çapraz sette düşük çıkabilir | Ürün iddiası zayıflar | Beklenen ve raporlanacak bulgu; Varyant B ile karşılaştırılabilir |
| Yerel veri toplanamaz | FR-14 düşer | Bonus tanımlı, ana hedefi etkilemez |
| Demo için API dizüstüne bağımlı | Demo günü bağlantı sorunu | Yerel ağ/tünel provası; web demo yedek |

## 12. Bu Dokümanla Senkron Edilecek Dosyalar

PRD.md (Bölüm 4–10), DATASET.md (veri envanteri, OpenCows2020'nin çıkarılması, D2 stratejisi), EVALUATION.md (E2–E4 protokolleri, SURF aralığı düzeltmesi), METHOD.md (Varyant A/B), AGENTS.md (izin verilen kütüphaneler Varyant kararına göre; `fastapi`, `uvicorn`, `python-multipart`; mobil istemci klasörü `mobile/`), REFERENCES.md (küpe/TÜRKVET/PETVET kaynakları).
