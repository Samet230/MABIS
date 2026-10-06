# Kaynak Havuzu (Reference Pool)
## ZooID (MABIS) — Çoklu Tür Hayvan Biyometrik Kimlik Tespit Sistemi

**Versiyon:** 0.1 (taslak)

---

> ⚠️ **Önemli not:** Bu doküman, konuşma boyunca web araması ile gerçekten
> doğrulanmış kaynakların ham listesidir — URL/DOI'ler gerçek ve
> kontrol edilmiştir. Ancak makalenin kaynakçasına geçirmeden önce
> **her kaynağı kendi orijinal sayfasından tekrar açıp** tam
> bibliyografik bilgiyi (yazar sırası, cilt/sayı, sayfa aralığı) IEEE/
> APA gibi istenen formatta doğrulaman gerekir. Bu, hem doğruluk hem de
> akademik dürüstlük açısından atlanmaması gereken bir adımdır — yanlış/
> eksik atıf ciddi bir risktir.

---

## 1. Sığır (ve Manda) Burun Deseni ile Kimliklendirme

| Kaynak | Bilgi | Link |
|---|---|---|
| Petersen, W.E. (1922) | "The identification of the bovine by means of nose-prints", J. Dairy Sci. 5, 249–258 — burun desenlerinin kimliklendirmede kullanılmasının **1921'e dayanan** temel/tarihsel referansı | (tarihsel kaynak, doğrudan link bulunamadı, kütüphane veritabanından aranmalı) |
| Xiong, Li, Erickson (2022) | "Beef cattle muzzle/noseprint database for individual identification" — Zenodo veri seti, 268 sığırdan 4.923 görüntü, 26MP kamera ile çekilmiş | https://zenodo.org/record/6324361 (DOI: 10.5281/zenodo.6324361) |
| Andrew, Burghardt, Campbell, Gao (2020) | "Visual Identification of Individual Holstein Friesian Cattle via Deep Metric Learning" — OpenCows2020 veri seti, 46 sığır, 4.736 görüntü — ⚠ burun verisi değil, üstten çekilmiş vücut deseni; bu projede veri olarak kullanılmıyor | https://arxiv.org/abs/2006.09205 · veri: https://data.bris.ac.uk/data/dataset/10m32xl88x2b61zlkkgz3fml17 |
| Gao, Burghardt, Andrew, Dowsey, Campbell (2021) | "Towards Self-Supervision for Video Identification of Individual Holstein-Friesian Cattle: The Cows2021 Dataset" — 10.402 görüntü + 301 video — ⚠ burun verisi değil (vücut deseni/video); bu projede veri olarak kullanılmıyor | https://arxiv.org/abs/2105.01938 |
| Noviyanto & Arymurthy (2013) | "Beef cattle identification based on muzzle pattern using a matching refinement technique in the SIFT method", Computers and Electronics in Agriculture, 99, 77–84 | (Springer/ScienceDirect üzerinden aranmalı — METHOD.md'deki SIFT yaklaşımı için doğrudan ilgili) |
| Awad & Hassaballah (2019) | "Bag-of-visual-words for cattle identification from muzzle print images", Applied Sciences, 9(22), 4914 — SURF ile %75-93, MSER+SURF ile %52-67 doğruluk aralığı raporlanmış | https://agris.fao.org/search/en/records/6759a5190ce2cede71c8ac87 |
| Kaur, Kumar, Jindal (2022) | "Shi-Tomasi corner detector for cattle identification from muzzle print image pattern", Ecological Informatics | DOI: 10.1016/j.ecoinf.2021.101549 |
| Girish, Santhosh, Kartikeya, Palekar, Harikrishna, Rathod (2020) | "Artificial intelligence based muzzle recognition technology for individual identification of animals" (**GoMukh** — Hindistan, ICAR), Indian J. Anim. Sci. 90(7), 1070–1073 — mobil kamerayla derin öğrenme tabanlı tanıma, %98 alan testi başarısı | https://epubs.icar.org.in/index.php/IJAnS/article/view/106684 (DOI: 10.56093/ijans.v90i7.106684) |
| Bara, Das, Singh, Pandey, Gaur, Pandey, Narwal, Tarafdar (2025) | "Deep learning assisted muzzle-based identification of Vrindavani cattle – A crossbred of India", Journal of Dairy Research | https://resolve.cambridge.org/core/journals/journal-of-dairy-research/article/deep-learning-assisted-muzzlebased-identification-of-vrindavani-cattle-a-crossbred-of-india/C1E903C5F48778A6FEF1CFA693D56304 |
| **Ermetin & Kahramanlı Örnek (2025)** | **"Deep-learning-based buffalo identification through muzzle pattern images"**, Arch. Anim. Breed. 68, 473–484 — **Yozgat, Türkiye**'deki bir tesisten 11 mandanın yüz görüntüsü, SqueezeNet ile %99,88 doğruluk. **Bulduğum tek Türkiye kaynaklı çalışma — özgünlük iddiamızın dayanağı** | https://aab.copernicus.org/articles/68/473/2025/ (DOI: 10.5194/aab-68-473-2025) |
| Singh, Khalid, Ahlawat, Azman, Agrawal, Ghorpade, Romle (2024) | "Individual Buffalo Identification Through Muzzle Dermatoglyphics Images using Deep Learning Approaches", J. Adv. Res. Applied Sciences Eng. Tech. 59(2), 178–191 | DOI: 10.37934/araset.59.2.178191 |
| Dataset of cattle biometrics through muzzle images (Pakistan, FAST-NUCES Karaçi) | **D2 veri seti.** ~13,9 GB ZIP; DSLR (Canon D80) ve telefonlarla (OnePlus 9 Pro, Oppo A76) çekilmiş tam yüz görüntüleri, kirli burun örnekleri dahil. Yazarlar/dergi/yıl/cilt bilgisi makaleden doğrulanmalı | Veri: DOI 10.5281/zenodo.8377921 · https://zenodo.org/records/10535934 · Makale: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10869238/ |
| Individual Beef Cattle Identification Using Muzzle Images and Deep Learning Techniques (Animals, 2022, 12(11), 1453) | D1 veri setinin eşlik eden makalesi; 59 derin öğrenme modeli karşılaştırılmış, 268 sığır için en iyi doğruluk %98,7. Yazarlar doğrulanmalı | DOI: 10.3390/ani12111453 · https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9179917/ |
| Lalit BC, Chaudhary D.S., Nepal S. — Open-Set Cattle Muzzle Identification: A Leakage-Controlled Benchmark and Evaluation Protocol | D1 üzerinde open-set protokolü; bölme dosyaları ve **yinelenen kimlik listesi** paylaşılmış (sızıntı kontrolü için). Ön baskı olabilir; künye doğrulanmalı | https://github.com/Dharmendra016/Muzzlenet |

## 2. Ticari Uygulamalar (Sektör Durumu için)

| Kaynak | Bilgi | Link |
|---|---|---|
| Stoktake (Avustralya, Dr. Philip Zada) | Mobil uygulamayla burun deseni tanıma, ~%99,6 doğruluk, 25.000+ sığırlık küresel veritabanı, hırsızlık/küpe kaybı önleme odaklı | https://www.stockandland.com.au/story/8903634/future-of-cattle-sales-scanning-muzzles-with-recognition-tech · https://itbrief.com.au/story/livestock-facial-recognition-tech-stoktake-getting-popular |
| GoMukh (Hindistan, ICAR) | bkz. yukarıdaki Girish vd. (2020) satırı — mobil/web tabanlı, açık kaynak teknolojilerle (PHP, Java, MySQL) geliştirilmiş | https://epubs.icar.org.in/index.php/IJAnS/article/download/106684/41933/342963 |

## 3. Köpek Burun Deseni

| Kaynak | Bilgi | Link |
|---|---|---|
| Jang, Kwon, Kim, Yang, Kim (2020) | "Dog Identification Method Based on Muzzle Pattern Image", Applied Sciences, 10(24), 8994 | (Springer/MDPI üzerinden aranmalı) |
| Dog Face Dataset | "A Deep Learning Approach for Dog Face Verification and Recognition" — 1.393 köpek, 8.363 görüntü (DogFaceNet olarak da anılıyor) | Kaynak listesi: https://github.com/DariaKern/IndividualAnimalRe-IDDatasets |

## 4. Kedi Yüz Tanıma

| Kaynak | Bilgi | Link |
|---|---|---|
| Cat Individual Images | "Cat face recognition using deep learning" (2018) — 518 kedi, 13.536 görüntü | Kaynak listesi: https://github.com/DariaKern/IndividualAnimalRe-IDDatasets |

## 5. Çoklu Tür Veri Seti

| Kaynak | Bilgi | Link |
|---|---|---|
| **Shinoda & Shiohara (2024)** | **"PetFace: A Large-Scale Dataset and Benchmark for Animal Identification"**, ECCV 2024 — 13 tür, 257.484 birey, 319 ırk, 1.012.934 görüntü. **Projenin çoklu-tür mimarisi için en güçlü referans** | https://arxiv.org/abs/2407.13555 (DOI: 10.1007/978-3-031-72649-1_2) · Proje sayfası: https://dahlian00.github.io/PetFacePage/ |
| DariaKern (GitHub) | "IndividualAnimalRe-IDDatasets" — hayvan bireysel tanıma alanındaki tüm açık veri setlerinin güncel, kürate edilmiş listesi (kaynakça olarak değil, veri seti keşfi için kullanışlı) | https://github.com/DariaKern/IndividualAnimalRe-IDDatasets |

## 6. Kamera/Çözünürlük İstatistikleri (Mobil Uygulama Bölümü için)

| Kaynak | Bilgi | Link |
|---|---|---|
| Omdia, Smartphone Model Market Tracker 2Q25 (Jusy Hong, Ağustos 2025) | 2Q25'te akıllı telefonların %58'i 50MP sınıfı kamera, %12'si 15MP altı (5 yıl önce bu oran %54'tü) | https://omdia.tech.informa.com/pr/2025/aug/smartphones-now-shipping-with-fewer-cameras |

## 7. Ürün Konumlanması ve Platform Kaynakları

| Kaynak | Bilgi | Link |
|---|---|---|
| T.C. Tarım ve Orman Bakanlığı, Hayvancılık Genel Müdürlüğü — Yönetmelik Değişiklikleri (11.09.2025) | Sığır cinsi hayvanların tanımlanması, tescili ve izlenmesi yönetmeliğinde değişiklik duyurusu | https://www.tarimorman.gov.tr/HAYGEM/Haber/381/Yonetmelik-Degisiklikleri |
| Bigpara/Hürriyet — "Her hayvanın dijital bir kimliği olacak" | Güvenli Elektronik Küpe İzleme Sistemi; Bakan'ın sahte ve kayıp küpe sorununa dair açıklaması (tarih/künye doğrulanmalı) | https://bigpara.hurriyet.com.tr/haberler/ekonomi-haberleri/her-hayvanin-dijital-bir-kimligi-olacak_ID102225681/ |
| Ekonomi Gazetesi (köşe yazısı) | Aselsan'ın geliştirdiği yerli dijital küpe; ikincil/yorum niteliğinde kaynak | https://www.ekonomigazetesi.com/kose-yazisi/hayvancilikta-yeni-uygulama-her-hayvanin-dijital-kimligi-olacak-85190 |
| FAOLEX — Kesimhanelerin Genel ve Özel Hijyen Kurallarına Dair Yönetmelik | "Küpe" tanımının Sığır Cinsi Hayvanların Tanımlanması, Tescili ve İzlenmesi Yönetmeliği'ne atıfı | https://faolex.fao.org/docs/pdf/tur222905.pdf |
| Hürriyet — Kurbanlıkların kimlikleri cepten öğrenilebilecek | TÜRKVET/HaySag: küpe numarası/barkodla hayvan sorgulama | https://www.hurriyet.com.tr/ekonomi/kurbanliklarin-kimlikleri-cepten-ogrenilebilecek-40908169 |
| bianet — Tarım ve Orman Bakanlığı: Hayvanları 31 Aralık'a kadar kimliklendirin | Kedi/köpek mikroçip ve PETVET kayıt zorunluluğu (2022) | https://bianet.org/haber/tarim-ve-orman-bakanligi-hayvanlari-31-aralik-a-kadar-kimliklendirin-271833 |
| Google Play Console Yardım — Yeni kişisel hesaplar için test şartları | 13 Kasım 2023 sonrası açılan kişisel hesaplarda üretim erişimi için en az 12 testerle 14 gün kesintisiz kapalı test (kurumsal hesaplar muaf). Şartlar değişebilir, başvurudan önce tekrar kontrol edilmeli | https://support.google.com/googleplay/android-developer/answer/14151465 |

> Bu kaynaklar ürün konumlanmasını (küpe zorunlu; ürün ikinci doğrulama katmanıdır) ve yayın planını destekler; makalenin bilimsel kaynakçası değil, giriş/tartışma bölümü ve proje dokümantasyonu içindir.

## 8. Kapsam Dışı Bırakılan Konu Alanları (Referans Amaçlı Not)

Proje seçim sürecinde araştırılan ama son kararla ilgisi kalmayan alanlar
(deri lezyonu/PASI, ekimoz yaş tahmini, kumaş kusuru, orman yangını dumanı,
manga panel tespiti) için toplanan kaynaklar bu dokümana dahil edilmedi —
makalenin doğrudan konusuyla ilgisizler. Gerekirse (ör. "Giriş" bölümünde
alternatif konuların neden elendiğini kısaca anmak istersen) bu kaynaklar
ayrıca toplanabilir.

## 9. Sonraki Adım

Bu ham listeyi, makale yazım aşamasında METHOD.md'deki iddialarla
(SURF için %75–93 aralığı; kaynağı doğrulanmayan başka rakamlar kullanılmayacak) eşleştirip doğru IEEE/APA formatına
çevirmek gerekecek — bu adımı makale taslağı yazılırken birlikte yapalım.
