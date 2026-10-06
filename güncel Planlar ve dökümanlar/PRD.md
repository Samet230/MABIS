# PRD — Ürün Gereksinim Dokümanı
## ZooID (MABIS) — Çoklu Tür Hayvan Biyometrik Kimlik Tespit Sistemi

**Ders:** Sayısal Görüntü İşleme
**Doküman türü:** Proje Gereksinim Dokümanı (Product Requirements Document)
**Versiyon:** 0.3 (taslak) — üst düzey özet; ayrıntılı gereksinimler REQUIREMENTS.md'de

---

## 1. Proje Özeti

ZooID (akademik açık isim: MABIS — *Multi-species Animal Biometric Identification System*),
büyükbaş hayvanlarda (sığır) ve köpeklerde burun deseni, kedilerde ise yüz
özelliklerini kullanarak; klasik sayısal görüntü işleme teknikleriyle her hayvanı
benzersiz biçimde tanıyan, kayıt altına alan ve doğrulayan, türe göre uyarlanabilir
bir biyometrik kimlik sistemidir.

## 2. Problem Tanımı

Hayvan kimliklendirmede kullanılan geleneksel yöntemlerin (küpe, dövme, mikroçip,
kulak çentiği) üç temel sorunu vardır:

- **Kaybolma/tahrip edilebilme** — küpe düşebilir, dövme silinebilir, bu da
  hırsızlık ve sahiplik anlaşmazlıklarına zemin hazırlar.
- **Hayvan refahı** — çoğu yöntem invaziv, hayvana acı veya rahatsızlık verir.
- **Maliyet** — özellikle küçük/orta ölçekli işletmeler için mikroçip/RFID
  altyapısı maliyetli olabilir.

Burun deseni (sığır/köpek) ve yüz geometrisi (kedi), insan parmak izine
benzer biçimde her bireyde benzersizdir ve bu sorunların hiçbirine sahip
olmayan, temassız bir alternatif sunar.

## 3. Amaç ve Vizyon

**Amaç (teknik hedef):** Hayvan görüntülerinden klasik görüntü işleme
teknikleriyle (segmentasyon → doku/öznitelik çıkarımı → eşleştirme) her birey
için benzersiz bir dijital imza çıkarıp, yeni bir görüntüyü veritabanındaki
kayıtlarla doğru eşleştiren bir sistem geliştirmek.

**Vizyon (büyük resim):** Küpe/mikroçip gibi yöntemlere alternatif, düşük
maliyetli, temassız ve hayvan refahını gözeten bir biyometrik kimlik doğrulama
çözümü sunarak; hayvan hırsızlığı, sigorta dolandırıcılığı ve sahiplik
ihtilaflarının önlenmesine katkı sağlamak.

## 4. Kapsam ve Gereksinimler (özet)

Ayrıntılı kapsam, fonksiyonel/fonksiyonel olmayan gereksinimler, veri planı, değerlendirme protokolleri, kabul kriterleri, takvim ve riskler **REQUIREMENTS.md (v0.3)** dokümanında tutulur. Bu doküman yalnızca üst düzey özettir; çelişki halinde REQUIREMENTS.md geçerlidir.

- **Tür kapsamı:** Ana odak sığır (burun deseni). İkincil: köpek (burun), kedi (yüz). Manda için açık veri bulunmadığından kapsam dışıdır (gelecek çalışma).
- **Teslim:** 8 hafta sonunda Android'de çalışan mobil uygulama (ince istemci) + FastAPI arka uç + akademik makale. Google Play'de herkese açık yayın kapsam dışıdır.
- **Veri:** D1 Zenodo Beef Cattle Muzzle (ana), D2 Pakistan Cattle Biometrics (aktarım testi, tam yüz/kirli burun), D3 yerel çekim (bonus), köpek/kedi için P1/P2 setler. OpenCows2020 kullanılmaz (burun verisi değil, üstten çekilmiş vücut deseni).
- **Yöntem:** Varsayılan Varyant A (yalnızca klasik). Varyant B (hazır modelden öznitelik) yalnızca ders sorumlusundan izin alınırsa.
- **Metrikler:** Rank-1, precision/recall/F1, confusion matrix, FAR/FRR/EER, open-set ölçümü.

## 5. Hedef Doğruluk

- **Makale hedefi:** Veri seti içi (E1) Rank-1 ≥ %90 (galeri oranı %75). Klasik yöntem literatüründe (Awad & Hassaballah, 2019) eğitim verisi oranına bağlı olarak %75–93 aralığı raporlanmıştır; hedef bu aralığın üst bandındadır.
- **Ürün:** Aktarım (E2) ve open-set (E3) sonuçları önce ölçülür; sayısal hedef ölçümden sonra belirlenir. Ticari/saha referansları %98–99,6 civarındadır ve klasik yöntemlerden beklenmez.
- Bu literatür rakamları makalede kullanılmadan önce kaynaklarının kendi sayfalarından doğrulanacaktır (bkz. REFERENCES.md).

## 6. Çözülmüş Kararlar

- Dil/kütüphane: Python + OpenCV + scikit-image + scikit-learn; arka uç FastAPI
- Mobil: Android öncelikli, ince istemci; çekirdek istemci-bağımsız API arkasında (mobil geçişi kolay olsun diye)
- Pakistan veri seti (D2) Hafta 1'de indirilir
- Eşleştirme: KNN/kosinüs benzerliği tabanlı; kesin seçim METHOD.md deneyleriyle

## 7. Açık Kararlar

- [ ] Varyant A/B: ders sorumlusundan hazır (pretrained) model kullanımı için izin alınacak (Hafta 1)
- [ ] Mobil istemci çerçevesi: React Native (Expo) veya Flutter (Hafta 1)
- [ ] Makale dili (Türkçe/İngilizce) ve şablonu
