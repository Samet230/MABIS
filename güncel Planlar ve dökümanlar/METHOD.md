# Algoritma / Yöntem Dokümanı
## ZooID (MABIS) — Çoklu Tür Hayvan Biyometrik Kimlik Tespit Sistemi

**İlişkili dokümanlar:** PRD.md, ARCHITECTURE.md, DATASET.md
**Versiyon:** 0.2 (taslak)

---

## 1. Genel Yaklaşım

Öznitelik çıkarımı için üç klasik yöntem paralel olarak denenecek, Hafta
3'teki küçük ölçekli deneyle en iyi performans gösteren yöntem/kombinasyon
seçilecek. Bu, "tek bir yöntemi baştan seçip kilitlenmek" yerine, veriye dayalı bir karar sürecidir.

## 2. Öznitelik Çıkarımı Yöntemleri

### 2.1 LBP (Local Binary Pattern) — Doku

| Parametre | Değer | Not |
|---|---|---|
| Yarıçap (R) | 1 (temel), 3 (genişletilmiş — karşılaştırılacak) | |
| Komşu nokta sayısı (P) | 8 (R=1 için), 24 (R=3 için) | |
| Yöntem | `uniform` | Dönme değişmezliği (rotation invariance) sağlar |
| Çıktı | Normalize edilmiş histogram | scikit-image `local_binary_pattern` |

**Neden:** LBP doku analizinde hesaplama açısından hafif ve gürültüye
görece dayanıklı — burun/yüz derisindeki ince desen farklarını yakalamada
literatürde en yaygın kullanılan yöntemlerden biri.

### 2.2 GLCM (Gray-Level Co-occurrence Matrix) — Doku İstatistikleri

| Parametre | Değer |
|---|---|
| Mesafeler | [1, 2, 3] piksel |
| Açılar | [0°, 45°, 90°, 135°] |
| Gri seviye kuantalama | 16 seviye (hesaplama maliyetini düşürmek için) |
| Çıkarılan özellikler | contrast, dissimilarity, homogeneity, energy, correlation, ASM |

**Neden:** GLCM, LBP'nin yakalayamadığı yönlü (directional) doku
ilişkilerini ölçer — ikisi birbirini tamamlayıcı niteliktedir.

### 2.3 SIFT / ORB — Anahtar Nokta Tabanlı

| Parametre | SIFT | ORB |
|---|---|---|
| Tanımlayıcı boyutu | 128 boyut | 32 bayt (ikili) |
| Kullanım amacı | Yüksek doğruluk, yavaş | Hızlı, hafif alternatif |
| Eşleştirme | FLANN veya Brute-Force + Lowe's ratio test (eşik ≈ 0,75) | Brute-Force (Hamming mesafesi) |

**Neden:** Doku histogramlarının aksine, anahtar nokta yöntemleri
görüntüdeki belirgin yapısal noktaları (burun oluklarının kesişimleri gibi)
doğrudan eşleştirir — insan parmak izi tanımada minutiae noktası
eşleştirmesine kavramsal olarak en yakın yöntem budur.

## 3. Öznitelik Birleştirme Stratejisi (Fusion)

İki seviyede birleştirme denenecek, hangisinin daha iyi sonuç verdiği
deneysel olarak belirlenecek:

- **Öznitelik seviyesinde (feature-level):** LBP histogramı + GLCM
  özellikleri tek bir vektörde birleştirilip (concat) normalize edilir,
  KNN/kosinüs benzerliğiyle eşleştirilir
- **Skor seviyesinde (score-level):** SIFT/ORB eşleşme sayısı ile doku
  histogramı benzerlik skoru ağırlıklı ortalamayla birleştirilir

## 4. Eşleştirme Algoritması

### 4.1 Histogram tabanlı öznitelikler (LBP, GLCM, kombinasyon)
- **Yöntem:** KNN (k=1, Rank-1 için) veya kosinüs benzerliği
- **Mesafe metriği:** Ki-kare (Chi-square) veya Öklid mesafesi
  karşılaştırılacak — histogram karşılaştırmada literatürde ki-kare
  genelde daha iyi sonuç verir

### 4.2 Anahtar nokta tabanlı (SIFT/ORB)
- İyi eşleşme (good match) sayısı hesaplanır (ratio test sonrası kalanlar)
- Bir eşik değerinin üzerindeki eşleşme sayısı "aynı birey" kararı için
  kullanılır; en yüksek eşleşme sayısına sahip veritabanı kaydı Rank-1
  sonucu olarak döndürülür

### 4.3 Doğrulama (1:1) ve Bilinmeyen Reddi

- Aynı skor/mesafe hem 1:N tanıma, hem 1:1 doğrulama, hem bilinmeyen reddi için kullanılır: en iyi eşleşmenin skoru eşiğin altındaysa sonuç "kayıtsız" döner.
- Eşik, validation alt kümesinde sabit bir FAR hedefiyle (ör. %1) belirlenir; test sorguları eşik ayarı için kullanılmaz.
- Çoklu kareyle kayıt: bir hayvanın galerideki birden çok görüntüsü ayrı kayıt olarak tutulur; hayvan skoru, o hayvanın görüntüleri arasındaki en iyi skordur (alternatif: ortalama; deneyle karşılaştırılır).
- Farklı yöntemlerin skorları birleştirilecekse (score-level fusion) skorlar min-max ile [0,1] aralığına normalize edilir.

## 5. Deneysel Karşılaştırma Planı (Hafta 3)

Küçük bir alt küme (ör. her türden 10-15 birey, birey başına 4-6 görüntü)
üzerinde aşağıdaki kombinasyonlar test edilip Rank-1 doğruluğu
karşılaştırılacak:

1. Yalnızca LBP
2. Yalnızca GLCM
3. LBP + GLCM (feature-level birleşim)
4. Yalnızca SIFT/ORB
5. En iyi doku yöntemi + SIFT/ORB (score-level birleşim)

En yüksek Rank-1 doğruluğu veren kombinasyon, tüm veri seti üzerindeki asıl
değerlendirme için seçilecek. Bu karşılaştırma tablosu doğrudan makalenin
"Deneyler" bölümüne (ablation study olarak) girecek.

## 6. Algoritma Akışı (Pseudocode)

```
FONKSIYON kayit_et(görüntü, animal_id, species):
    roi = on_isle_ve_segmentle(görüntü, species)
    öznitelik = öznitelik_çıkar(roi, seçilen_yöntem)
    veritabanina_ekle(animal_id, species, öznitelik)

FONKSIYON tani(görüntü, species):
    roi = on_isle_ve_segmentle(görüntü, species)
    sorgu_öznitelik = öznitelik_çıkar(roi, seçilen_yöntem)
    adaylar = veritabanindan_getir(species)
    en_yakin, skor = en_yakin_komsuyu_bul(sorgu_öznitelik, adaylar)
    DÖNDÜR en_yakin, skor
```

## 7. Hesaplama Karmaşıklığı Notları

- LBP ve GLCM hesaplama maliyeti düşük — gerçek zamanlı olmasa da
  saniyeler mertebesinde çalışması beklenir
- SIFT nispeten daha maliyetli; ORB bu nedenle "hızlı alternatif" olarak
  ayrıca test edilir
- Veritabanı boyutu (MVP'de birkaç yüz kayıt) için doğrusal arama (linear
  search) yeterli — endeksleme (ör. KD-tree/FLANN indeksleme) gerekmez

## 8. Yöntem Varyantları (A / B)

Ders şartnamesinin hazır (pretrained) model kullanımına izin verip vermediği henüz netleşmemiştir (REQUIREMENTS.md, Bölüm 9).

- **Varyant A (varsayılan) — yalnızca klasik:** Bu dokümandaki tüm yöntemler. Geliştirme buna göre yapılır.
- **Varyant B (izne bağlı) — hibrit:** Ön işleme, segmentasyon ve kalite kapısı klasik kalır; eşleştirme için hazır bir modelden çıkarılan embedding eklenir. Yalnızca kullanıcı ders sorumlusundan onay alarak açıkça onaylarsa uygulanır.

Geçişi ucuz tutmak için ortak kurallar:
- Öznitelik çıkarımı `extract_features(roi, method)` arayüzünün arkasındadır; yeni yöntem eklemek diğer modülleri etkilemez.
- Galeri kaydına yöntem adı ve sürümü yazılır. Farklı yöntemlerin öznitelikleri birbiriyle karşılaştırılamaz; yöntem değişince galeri yeniden çıkarılmalıdır.
- Ham (ön işlenmemiş) görüntüler saklanır; yöntem değişiminde hayvanların yeniden çekilmesi gerekmez.

## 9. Sonraki Doküman

Bir sonraki adım: **Test & Değerlendirme Planı** — deney tasarımı, hangi
verinin ayrılacağı ve sonuçların nasıl raporlanacağının detaylandığı
doküman (DATASET.md'deki train/test ayrımıyla birlikte kullanılacak).
