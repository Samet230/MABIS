# Veri Seti & Ön İşleme Notu
## ZooID (MABIS) — Çoklu Tür Hayvan Biyometrik Kimlik Tespit Sistemi

**İlişkili dokümanlar:** PRD.md, REQUIREMENTS.md, ARCHITECTURE.md
**Versiyon:** 0.2 (taslak)

---

## 1. Veri Seti Envanteri

| ID | Tür | Veri Seti | Birey | Görüntü | Boyut | Rol |
|---|---|---|---|---|---|---|
| D1 | Sığır | Zenodo Beef Cattle Muzzle/Noseprint | 268 | 4.923 | ~644 MB | Ana geliştirme ve kalibrasyon; kırpılmış burun görüntüleri |
| D2 | Sığır | Pakistan Cattle Biometrics ("Cows Frontal Face Dataset") | doğrulanacak | doğrulanacak (8.000+ olarak bildirilmiş) | ~13,9 GB | Aktarım testi (E2), burun segmentasyonu (tam yüz), kirli burun; DSLR + telefon |
| D3 | Sığır | Yerel çekim (Elazığ) | hedef 20–30 | hayvan başına ≥8 | — | Türkiye/telefon saha doğrulaması (bonus) |
| D4 | Köpek | DogFaceNet (hizalı, 224×224) | 1.393 | 8.363 | Zenodo kaydı toplam 3,9 GB | Köpek (P1) — düşük çözünürlük riski |
| D5 | Kedi | Cat Individual Images | 518 | 13.536 | doğrulanmadı | Kedi (P2) |

**Kullanılmayacak:** OpenCows2020 ve Cows2021 — üstten çekilmiş Holstein-Friesian vücut/ten deseni verisidir, burun verisi değildir. PetFace (1M+ görüntü) MVP dışıdır; gerekirse yalnızca alt kümesi.

**Öncelik:** D1 ana set (P0). D2 Hafta 1'de indirilir; önce küçük alt kümeyle çalışılır. D3 bonus. Köpek (P1) ve kedi (P2) süre yetiyorsa.

**D1 uyarısı (sızıntı riski):** D1'i kullanan yayımlanmış bir açık-küme çalışması, yinelenen kimlik listesi paylaşmıştır. Bölme yapmadan önce bu liste indirilip kontrol edilir (aynı hayvanın birden fazla ID ile kayıtlı olma ihtimali); bölme dosyaları kaydedilir.

**D2 kontrol listesi (indirince):**
- Zenodo'dan indir (DOI 10.5281/zenodo.8377921; kayıt: https://zenodo.org/records/10535934), md5 kontrolü yap
- Klasör yapısı, hayvan sayısı, görüntü sayısı ve kamera dağılımı (DSLR/telefon) sayılıp bu dokümana yazılır
- Lisans/atıf şartı kontrol edilir
- Kirli burun örneklerinin nasıl etiketlendiği (ayrı klasör mü, sınıf içinde mi) kontrol edilir

**D4 uyarısı:** Görüntüler 224×224 hizalı yüzlerdir; burun bölgesi çok az piksele düşer ve LBP/GLCM gibi ince doku yöntemleri için yetersiz kalabilir. Hafta 1'de burun kırpmasına bakılıp karar verilir; yetersizse aynı Zenodo kaydındaki ham "large" set denenir.

## 2. Klasör ve Format Standardı

```
data/raw/
├── cattle/
│   ├── animal_001/
│   │   ├── img_001.jpg
│   │   └── img_002.jpg
│   └── animal_002/
├── dog/
│   └── ...
└── cat/
    └── ...
```

- Her birey kendi klasöründe, görüntüler `img_NNN.jpg` formatında
- Orijinal veri setlerinin klasör/etiketleme yapısı bu standarda
  dönüştürülecek (dönüştürme betiği `src/data/convert_dataset.py` altında
  yazılacak)
- `processed/` altında da aynı yapı korunur, yalnızca görüntüler ön işlenmiş
  ve ROI'ye kırpılmış halde bulunur

## 3. Veri Temizleme Kriterleri

Aşağıdaki kriterlere uymayan görüntüler veri setinden çıkarılır:

- **Bulanıklık kontrolü:** Laplacian varyansı belirlenen eşiğin altındaki
  görüntüler elenir (net eşik değeri Hafta 1'de küçük bir örneklemle
  kalibre edilecek)
- **Minimum çözünürlük:** Belirli bir piksel boyutunun altındaki görüntüler
  elenir (bkz. daha önce konuşulan minimum çözünürlük gereksinimleri)
- **Bozuk/okunamayan dosyalar:** Otomatik kontrolle elenir
- **Minimum görüntü sayısı:** Bir bireyin train/test ayrımına dahil
  edilebilmesi için en az 4 görüntüsü olmalı; daha azına sahip bireyler
  MVP değerlendirmesinden çıkarılır (ileride genişletme notu olarak
  raporda belirtilir)

## 4. Train / Test Ayrımı ve Protokol Bölmeleri

**E1 — Veri seti içi (kapalı-küme):** Her bireyin görüntülerinin ~%75'i galeriye, ~%25'i sorguya ayrılır. Ayrım görüntü bazında rastgele ve birey-içidir (aynı hayvanın görüntüleri hem galeride hem sorguda bulunmalıdır; Rank-1 ölçümü bunu gerektirir). Sabit `random_state`, 3 farklı seed.

**Validation alt kümesi:** Parametre ayarı ve eşik kalibrasyonu için galeriden küçük bir kısım (ör. her bireyden 1 görüntü) ayrılır. Test sorguları hiçbir ayar için kullanılmaz.

**E2 — Veri seti aktarımı (D1 ↔ D2):** İki sette farklı hayvanlar bulunduğu için "D1 galerisi, D2 sorgusu" kurulamaz. Bunun yerine yöntem parametreleri ve doğrulama eşiği D1'de belirlenir; D2'de hiçbir ayar değiştirilmeden, D2'nin kendi galeri/sorgu ayrımıyla test edilir. Ters yön (D2 → D1) de yapılır. Varyant B uygulanırsa model D1'de eğitilip D2'de görülmemiş bireylerle test edilir.

**E3 — Open-set:** Bireylerin ~%20'si tamamen "bilinmeyen" olarak ayrılır ve galeriye hiç girmez. Sorgular: bilinen bireylerin test görüntüleri + bilinmeyen bireylerin tüm görüntüleri. Ayrım birey bazındadır (sızıntı kontrolü). Eşik validation alt kümesinde kalibre edilir.

**Neden bu tasarım:** Ürün senaryosunda kayıtsız hayvan ve farklı kamera/ortam mutlaka gelir; kapalı-küme tek başına ürün iddiası için yetmez.

## 5. Ön İşleme Hattı (Detay)

ARCHITECTURE.md'deki Ön İşleme modülünün somut adımları:

1. **Renk uzayı dönüşümü:** BGR → Gri seviye (doku analizi için) ve/veya
   HSV (segmentasyonda renk tabanlı ayrıştırma gerekirse)
2. **Kontrast iyileştirme:** CLAHE (clipLimit ve tileGridSize değerleri
   deneysel olarak ayarlanacak)
3. **Gürültü giderme:** Medyan filtre (çekirdek boyutu görüntü
   çözünürlüğüne göre ayarlanır)
4. **Boyut normalize etme:** ROI kırpıldıktan sonra sabit boyuta
   (ör. 300×300) yeniden boyutlandırma

## 6. Segmentasyon Notları (Tür Bazında)

- **Sığır burnu (D1):** Görüntüler zaten kırpılmış burun bölgesidir; segmentasyon çoğunlukla doğrulama/normalizasyon adımıdır.
- **Sığır burnu (D2):** Tam yüz fotoğraflarıdır; burun bölgesi önce bulunmalıdır. Eşikleme + kontur tabanlı yaklaşım denenir; gerekirse basit bir Haar cascade eğitimi değerlendirilir. Kirli burun örneklerinde başarısızlık oranı ayrıca raporlanır (E4).
- **Köpek burnu:** DogFaceNet hizalı yüz olduğundan burun yüzün alt-orta kısmından oransal kırpmayla çıkarılabilir; çözünürlük yetersizse bkz. D4 uyarısı.
- **Kedi yüzü:** OpenCV'nin hazır Haar cascade yüz/göz dedektörleri ilk denemede kullanılır; veri setine göre ince ayar yapılabilir.

## 7. Kalite Güvencesi

- Ön işleme hattından geçen her görüntü için önce-sonra karşılaştırması
  küçük bir örneklemde (ör. 20 görüntü/tür) manuel olarak görsel kontrol
  edilecek (Hafta 2 sonunda)
- Segmentasyon başarısız olan (ROI'nin doğru bölgeyi yakalamadığı)
  görüntüler ayrı bir "başarısız" klasörüne loglanacak — bu oran, makalenin
  sınırlamalar bölümünde raporlanabilir

## 8. Sonraki Doküman

Bir sonraki adım: **Algoritma/Yöntem Dokümanı** — öznitelik çıkarımı
(LBP/GLCM/SIFT) ve eşleştirme algoritmasının kesin parametreleriyle
detaylandırıldığı doküman.
