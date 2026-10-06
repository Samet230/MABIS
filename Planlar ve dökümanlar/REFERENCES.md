# Kaynak Havuzu (Reference Pool)
## ZooID (MABIS) — Sığır Odaklı Çoklu Tür Biyometrik Kimlik Doğrulama Sistemi

**Versiyon:** 0.2 (Ürün Seviyesi Güncellemesi)  

---

> ⚠️ **Önemli Not:** Bu doküman, doğrulanmış akademik yayınların, açık veri setlerinin ve Türkiye'deki yasal mevzuat kaynaklarının listesidir. Makalede kullanılmadan önce ilgili standartlara (IEEE/APA) göre biçimlendirilmelidir.

---

## 1. Sığır / Manda Biyometrisi ve Burun Deseni Kaynakları

| Kaynak | Tanım / Bilgi | Bağlantı / DOI |
|---|---|---|
| Petersen, W.E. (1922) | "The identification of the bovine by means of nose-prints", J. Dairy Sci. 5, 249–258 — Burun deseninin biyometrik olarak kullanılmasının 1920'lere dayanan ilk tarihsel referansı. | Tarihsel Referans |
| Xiong, Li, Erickson (2022) | "Beef cattle muzzle/noseprint database for individual identification" — **D1 Ana Veri Seti**: 268 sığır, 4.923 kırpılmış burun fotoğrafı. | [Zenodo: 6324361](https://zenodo.org/record/6324361) · DOI: 10.5281/zenodo.6324361 |
| Ahmed, S. U. et al. (2024) | "Cows Frontal Face Dataset" — **D2 Pakistan Veri Seti**: 460 sınıf/birey, 8.000+ görüntü, Canon D80 DSLR ve akıllı telefonlarla çekilmiş tam yüz fotoğrafları, çamurlu/kirli burun örnekleri. | [Zenodo: 10535934](https://zenodo.org/record/10535934) · DOI: 10.5281/zenodo.10535934 |
| **Ermetin & Kahramanlı Örnek (2025)** | **"Deep-learning-based buffalo identification through muzzle pattern images"**, Arch. Anim. Breed. 68, 473–484 — **Yozgat, Türkiye** manda tesisi çalışması. Literatürdeki tek Türkiye odaklı manda burun deseni çalışmasıdır. | [Copernicus AAB](https://aab.copernicus.org/articles/68/473/2025/) · DOI: 10.5194/aab-68-473-2025 |
| Noviyanto & Arymurthy (2013) | "Beef cattle identification based on muzzle pattern using a matching refinement technique in the SIFT method", Computers and Electronics in Agriculture, 99, 77–84 — SIFT ve anahtar nokta eşleştirme temel referansı. | ScienceDirect · DOI: 10.1016/j.compag.2013.08.023 |
| Awad & Hassaballah (2019) | "Bag-of-visual-words for cattle identification from muzzle print images", Applied Sciences, 9(22), 4914 — Klasik yöntemlerle %75–93 başarı aralığı raporu. | [FAO Agris Kaydı](https://agris.fao.org/search/en/records/6759a5190ce2cede71c8ac87) |
| Kaur, Kumar, Jindal (2022) | "Shi-Tomasi corner detector for cattle identification from muzzle print image pattern", Ecological Informatics | DOI: 10.1016/j.ecoinf.2021.101549 |
| Girish et al. (2020) | "Artificial intelligence based muzzle recognition technology for individual identification of animals" (**GoMukh** — Hindistan ICAR), Indian J. Anim. Sci. 90(7), 1070–1073. | [ICAR ePubs](https://epubs.icar.org.in/index.php/IJAnS/article/view/106684) |
| Bara et al. (2025) | "Deep learning assisted muzzle-based identification of Vrindavani cattle – A crossbred of India", Journal of Dairy Research | [Cambridge Core](https://resolve.cambridge.org/core/journals/journal-of-dairy-research/article/deep-learning-assisted-muzzlebased-identification-of-vrindavani-cattle-a-crossbred-of-india/C1E903C5F48778A6FEF1CFA693D56304) |

---

## 2. Türkiye Mevzuatı ve Düzenlemeleri (TÜRKVET / PETVET ve Küpe Sistemi)

Ürünün konumlanması (ikinci bir doğrulama katmanı) aşağıdaki yasal düzenlemelere dayanmaktadır:

| Düzenleme / Kurum | Kapsam ve Önemi | Bağlantı / Kaynak |
|---|---|---|
| **T.C. Tarım ve Orman Bakanlığı** | **Sığır Cinsi Hayvanların Tanımlanması, Tescili ve İzlenmesi Yönetmeliği** — Sığırlarda her iki kulağa resmi küpe takılması zorunludur. Küpenin düşmesi veya tahrif edilmesi durumunda kimlik kaybı riski doğar. | [Mevzuat Bilgi Sistemi](https://www.mevzuat.gov.tr/) · [tarimorman.gov.tr Yönetmelikler](https://www.tarimorman.gov.tr/) |
| **Tarım ve Orman Bakanlığı** | **Elektronik Küpe (RFID) Sistemi Uygulaması** — Bakanlığın büyükbaş hayvanlarda elektronik kulak küpesi ile kayıt ve izleme sistemine kademeli geçiş duyuruları ve tebliğleri. | [Bakanlık Duyuruları](https://www.tarimorman.gov.tr/Duyurular) |
| **TÜRKVET** | **Hayvan Kayıt Sistemi** — Türkiye genelindeki tüm büyükbaş ve küçükbaş hayvanların hareket, aşılama ve sahiplik kayıtlarının tutulduğu merkezi veritabanı. | [TÜRKVET Bilgi Sistemi](https://turkvet.tarim.gov.tr/) |
| **PETVET & 5199 Sayılı Kanun** | **Kedi, Köpek ve Gelinciklerin Kimliklendirilmesi ve Kayıt Altına Alınmasına Dair Yönetmelik** — Evcil hayvanlara mikroçip takılması ve PETVET sistemine kayıt zorunluluğu (2022 sonu itibarıyla yürürlüğe girdi). | [Resmî Gazete Sayı: 30344](https://www.resmigazete.gov.tr/) · [bianet PETVET Raporu](https://bianet.org/) |

---

## 3. Ticari ve Sektörel Uygulamalar

| Şirket / Girişim | Çözüm ve Doğruluk | Bilgi / Link |
|---|---|---|
| **Stoktake** (Avustralya) | Akıllı telefon kamerası ile burun deseni tarama, %99.6 doğruluk iddiası, 25.000+ sığırlık veritabanı; hırsızlık ve küpe kaybına karşı biyometrik sigorta. | [Stock & Land Haberi](https://www.stockandland.com.au/story/8903634/future-of-cattle-sales-scanning-muzzles-with-recognition-tech) |
| **GoMukh** (Hindistan) | ICAR destekli mobil ve web tabanlı burun tanıma sistemi, açık kaynak PHP/Java/MySQL altyapısı. | [ICAR Raporu](https://epubs.icar.org.in/index.php/IJAnS/article/download/106684/41933/342963) |

---

## 4. Köpek ve Kedi Biyometrisi Kaynakları

| Kaynak | Bilgi | Bağlantı |
|---|---|---|
| Jang et al. (2020) | "Dog Identification Method Based on Muzzle Pattern Image", Applied Sciences, 10(24), 8994 — Köpek burun deseni ile kimlik tanıma. | MDPI Applied Sciences · DOI: 10.3390/app10248994 |
| DogFaceNet | 1.393 köpek, 8.363 görüntü. Yüz ve burun odaklı açık veri seti. | [Zenodo: 12578449](https://zenodo.org/api/records/12578449) |
| Cat Individual Images | 518 kedi, 13.536 görüntü. Kedi yüz tanıma veri seti. | Kaggle `timost1234/cat-individuals` |
| **Shinoda & Shiohara (2024)** | **"PetFace: A Large-Scale Dataset and Benchmark for Animal Identification"**, ECCV 2024 — Çoklu tür mimarimizin en güçlü teorik referansı (13 tür, 257 bin birey). | [arXiv: 2407.13555](https://arxiv.org/abs/2407.13555) |
