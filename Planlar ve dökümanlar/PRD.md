# PRD — Ürün Gereksinim Dokümanı
## ZooID (MABIS) — Sığır Odaklı Çoklu Tür Biyometrik Kimlik Doğrulama Sistemi

**Ders:** Sayısal Görüntü İşleme  
**Doküman türü:** Proje Gereksinim Dokümanı (Product Requirements Document)  
**Versiyon:** 0.2 (Ürün Seviyesi Güncellemesi)  

---

## 1. Proje Özeti

ZooID (akademik açık isim: MABIS — *Multi-species Animal Biometric Identification System*), büyükbaş hayvanlarda (sığır) ve köpeklerde burun deseni (muzzle), kedilerde ise yüz özelliklerini kullanarak; sayısal görüntü işleme teknikleriyle her hayvanı benzersiz biçimde tanıyan, kayıt altına alan, doğrulayan ve telefon kamerasıyla çalışabilen türe göre uyarlanabilir bir biyometrik kimlik sistemidir.

## 2. Problem Tanımı

Hayvan kimliklendirmede kullanılan geleneksel yöntemlerin (küpe, dövme, mikroçip, kulak çentiği) üç temel sorunu vardır:

- **Kaybolma/tahrip edilebilme** — küpe düşebilir, dövme silinebilir, bu da hırsızlık ve sahiplik anlaşmazlıklarına zemin hazırlar.
- **Hayvan refahı** — çoğu yöntem invaziv, hayvana acı veya rahatsızlık verir.
- **Maliyet** — özellikle küçük/orta ölçekli işletmeler için mikroçip/RFID altyapısı maliyetli olabilir.

Burun deseni (sığır/köpek) ve yüz geometrisi (kedi), insan parmak izine benzer biçimde her bireyde benzersizdir ve bu sorunların hiçbirine sahip olmayan, temassız bir alternatif sunar.

## 3. Amaç, Vizyon ve Konumlanma

**Amaç (teknik hedef):** Hayvan görüntülerinden görüntü işleme teknikleriyle (kalite kapısı → segmentasyon → ön işleme → doku/öznitelik çıkarımı → eşleştirme/doğrulama) her birey için benzersiz bir dijital imza çıkarıp, yeni bir görüntüyü veritabanındaki kayıtlarla doğru eşleştiren veya kimliğini doğrulayan bir sistem geliştirmek.

**Vizyon (büyük resim):** Küpe/mikroçip gibi yöntemlere tamamlayıcı, düşük maliyetli, temassız ve hayvan refahını gözeten bir biyometrik kimlik doğrulama çözümü sunmak; hayvan hırsızlığı, sigorta dolandırıcılığı ve sahiplik ihtilaflarının önlenmesine katkı sağlamak.

**Konumlanma (önemli):** Türkiye'de sığırlar için küpe zorunlu ve Tarım ve Orman Bakanlığı elektronik küpe sistemine geçmektedir. Bu yüzden ürün "küpenin yerine" değil, şu durumlar için **ikinci bir doğrulama katmanı** olarak konumlandırılır:
- Küpe kaybolduğunda veya şüpheli göründüğünde hayvanın kimliğini doğrulama (1:1 doğrulama)
- Hırsızlık şüphesinde hayvanı kayıtlı kimliğiyle eşleştirme (1:N tanıma)
- Sigorta ve alım-satım işlemlerinde kimlik teyidi

---

## 4. Kullanım Senaryoları

| # | Senaryo | Tür | Açıklama |
|---|---|---|---|
| S1 | **Kayıt (Enrollment)** | Sığır (Öncelikli), Köpek, Kedi | Hayvanın birden fazla (en az 5) kaliteli fotoğrafı çekilir, kalite kapısından geçer, şablon veritabanına kaydedilir |
| S2 | **Doğrulama (1:1 Verification)** | Sığır | "Bu hayvan, kayıtlı X hayvanı mı?" (küpe no/ID + burun fotoğrafı ile ikili kabul/ret kararı) |
| S3 | **Tanıma (1:N Identification)** | Sığır, Köpek, Kedi | Bilinmeyen bir fotoğraf girildiğinde kayıtlı galeri içerisinden en olası eşleşmeyi ve güven skorunu bulma |
| S4 | **Bilinmeyen Reddi (Open-Set)** | Sığır | Sistemde kayıtlı olmayan hayvan sorgulandığında, benzerlik skoru eşiğin altındaysa "kayıtsız / yabancı" olarak reddetme |
| S5 | **Kayıt Yönetimi ve Denetim** | Tümü | Hayvan kaydı ekleme, güncelleme, silme ve tüm işlem geçmişini (audit log) tutma |

---

## 5. Fonksiyonel Gereksinimler

Öncelik: **P0** = ürün çekirdeği, **P1** = önemli, **P2** = zaman kalırsa / bonus.

| ID | Gereksinim | Öncelik | Açıklama |
|---|---|---|---|
| **FR-01** | **Kalite Kapısı (Quality Gate)** | **P0** | Görüntüde bulanıklık (Laplacian varyansı), aşırı/yetersiz pozlama, parlaklık histogramı, burun bölgesinin kadraja tam girmesi ve minimum çözünürlük kontrol edilir; standart dışı görüntü kullanıcıya sebebiyle bildirilip reddedilir. |
| **FR-02** | **Burun ROI Segmentasyonu** | **P0** | Hem doğrudan kırpılmış burun görüntülerinden (D1) hem de serbest açıdan çekilmiş **tam yüz fotoğraflarından** (D2 Pakistan veri seti) burun bölgesini otomatik tespit edip 300×300 piksele normalize eder. |
| **FR-03** | **Ön İşleme Hattı** | **P0** | Gri seviye/HSV dönüşümü, CLAHE ile adaptif kontrast iyileştirme, medyan/Gauss gürültü giderme ve boyut normalizasyonu. |
| **FR-04** | **Çoklu Kareyle Kayıt** | **P0** | Kayıtta tek görüntü yerine en az $N=5$ kaliteli görüntü alınarak galeri şablonu oluşturulur. |
| **FR-05** | **Öznitelik Çıkarımı** | **P0** | Klasik öznitelikler (LBP, GLCM, SIFT, ORB). Varyant B onaylandığı takdirde öğrenilmiş öznitelik (embedding) ekleme imkânı. |
| **FR-06** | **1:N Tanıma + Güven Skoru** | **P0** | Galeri ile sorgu karşılaştırması; Rank-1 eşleşme ve güven skoru çıktısı. |
| **FR-07** | **1:1 Doğrulama (Verification)** | **P0** | İddia edilen hayvan ID'si ve sorgu görüntüsü eşleştirilerek kalibre edilmiş eşik üzerinden kabul/ret ikili kararı üretilir. |
| **FR-08** | **Bilinmeyen Reddi (Open-Set)** | **P0** | Kalibre edilmiş güven eşiğinin altında kalan sorgularda "Kayıtsız Hayvan" kararı verilir. |
| **FR-09** | **Kirli/Islak Burun Dayanıklılığı** | **P1** | Pakistan veri setindeki çamurlu, ıslak ve kirli burun örneklerinde algoritma performansı stres testine tabi tutulur ve hata sınırları raporlanır. |
| **FR-10** | **Kayıt Yönetimi & İşlem Günlüğü** | **P1** | Kayıt silme, güncelleme, sorgu tarihi ve kullanıcı bilgisi içeren SQLite denetim kaydı (audit log). |
| **FR-11** | **Kullanıcı Arayüzü** | **P1** | CLI ve telefon tarayıcısından fotoğraf yüklemeye ve kameradan çekim yapmaya uygun, mobil geçişe hazır REST API tabanlı web arayüzü. |
| **FR-12** | **Köpek Desteği** (Burun) | **P1** | DogFaceNet veri setiyle burun odaklı tanıma desteği. |
| **FR-13** | **Kedi Desteği** (Yüz) | **P2** | Haar Cascade yüz tespiti ile kedi yüz tanıma desteği. |
| **FR-14** | **Saha Doğrulaması** | **P1 (Bonus)** | Elazığ yerel çiftliklerinden Redmi 10 / telefon kamerasıyla çekilmiş 20–30 hayvanlık set üzerinde saha doğrulaması. |

---

## 6. Fonksiyonel Olmayan Gereksinimler

- **Doğruluk:** 
  - Akademik hedef: Kapalı-küme (E1) Rank-1 $\ge \%90$.
  - Ürün prototipi hedefi: Çapraz veri seti (E2) ve açık-küme (E3) sonuçlarının titizlikle ölçülüp raporlanması.
  - Ürün ideali: Ticari referanslara (%98–99.6) yaklaşmak.
- **İşlem Süresi:** Tek bir sorgunun işlenmesi standart bir dizüstü bilgisayarda birkaç saniye içinde tamamlanmalıdır.
- **Donanım Varsayımı:** Orta segment akıllı telefon (ör. Redmi 10, 8 MP+ ana kamera, otofokus, yakın çekim kabiliyeti).
- **Tekrarlanabilirlik:** Sabit rastgele tohumlar (42, 100, 2024), versiyonlanmış JSON split dosyaları, parametrize konfigürasyon.
- **Veri Güvenliği ve KVKK:** Hayvan görüntüleri kişisel veri sayılmamakla birlikte, sahip bilgileri ve TÜRKVET kimlikleriyle eşleştiğinde KVKK kapsamına girecektir; sistem mimarisinde sahip verileri soyutlanmalıdır.
- **Genişletilebilirlik:** Yeni bir hayvan türü veya yeni öznitelik çıkarıcı çekirdek mimariyi bozmadan modüler olarak eklenebilmelidir.

---

## 7. Veri Kaynakları

| ID | Veri Seti | Kapsam | Boyut / Durum | Kullanım Rolü |
|---|---|---|---|---|
| **D1** | **Zenodo Beef Cattle Muzzle** | 268 hayvan, 4.923 kırpılmış burun | ~644 MB (İndirildi ✅) | Temel geliştirme, kalibrasyon ve E1 içi değerlendirme |
| **D2** | **Pakistan Cattle Biometrics** | 460 sınıf, 8.000+ tam yüz fotoğrafı | ~13.9 GB (İndiriliyor ⏳) | E2 çapraz veri seti testi, FR-02 full-face segmentasyonu ve FR-09 kirlilik dayanıklılığı |
| **D3** | **Yerel Çekim Seti** (Elazığ) | 20–30 sığır, hayvan başı $\ge 8$ foto | Bonus / Saha | E5 gerçek saha ve telefon kamerası doğrulaması |
| **D4** | **DogFaceNet_224resized** | 1.393 köpek, 8.363 görüntü | ~75.6 MB (İndirildi ✅) | FR-12 köpek burun tanıma |
| **D5** | **Cat Individual Images** | 518 kedi, 13.536 görüntü | Kaggle / P2 | FR-13 kedi yüz tanıma |

*Not: OpenCows2020 veri seti, gövde/ten deseni içerdiği ve burun biyometrisiyle ilgisiz olduğu için kapsamdan çıkarılmıştır.*

---

## 8. Değerlendirme Protokolleri ve Metrikler

1. **E1 (Veri Seti İçi Tanıma):** D1 üzerinde birey-içi %75 galeri - %25 sorgu ayrımı, 3 tohum (42, 100, 2024). Metrik: Rank-1 Doğruluk, Macro/Weighted F1, Confusion Matrix.
2. **E2 (Çapraz Veri Seti Genelleme):** D1 galerisi üzerinde D2 sorguları (ve tersi). Modelin çekim ortamı ve kamera farklarına direnci ölçülür.
3. **E3 (Açık-Küme / Open-Set):** Galeride yer almayan "bilinmeyen" hayvanların sisteme sorgulanması. Metrik: False Acceptance Rate (FAR), False Rejection Rate (FRR), Equal Error Rate (EER) ve ROC/AUC.
4. **E4 (Kalite ve Çevre Dayanıklılığı):** Kirli/ıslak burun ve farklı aydınlatma koşullarının başarıya etkisi.
5. **E5 (Saha Doğrulaması):** D3 yerel çekimleri ile uçtan uca mobil test.

---

## 9. Yöntem Varyantları (A ve B)

Ders şartnamesinin derin öğrenme kısıtına göre iki varyant kurgulanmıştır:

- **Varyant A (Saf Klasik - Temel Çizgi):** Ön işleme, segmentasyon, LBP/GLCM/SIFT/ORB öznitelik çıkarımı, RANSAC geometrik doğrulama ve Chi2/Hamming eşleştirme. %100 klasik yöntem; ders şartnamesine tam uyumlu.
- **Varyant B (Hibrit - Ürün Seviyesi):** Ön işleme, kalite kapısı ve segmentasyon klasik görüntü işleme olarak korunur; öznitelik vektörü adımında hafif bir derin öğrenme embedding modeli (ör. MobileFaceNet/ResNet omurgası) eklenerek füzyon yapılır. Ders onayına bağlı olarak değerlendirilecektir.

---

## 10. Kapsam Dışı Konular

- Manda (açık veri bulunmadığı için gelecek çalışma olarak bırakılmıştır).
- At, eşek, deve ve küçükbaş hayvanlar.
- Liveness tespiti (canlılık testi / sahte fotoğraf tespiti).
- Gerçek zamanlı video akışı üzerinden takip.
- TÜRKVET merkezi veritabanı doğrudan canlı API entegrasyonu (hukuki ve idari izinler gerektirir).
