# Test & Değerlendirme Planı
## ZooID (MABIS) — Çoklu Tür Hayvan Biyometrik Kimlik Tespit Sistemi

**İlişkili dokümanlar:** PRD.md, DATASET.md, METHOD.md
**Versiyon:** 0.2 (taslak)

---

## 1. Değerlendirme Protokolü

Değerlendirme, DATASET.md'de tanımlanan kapalı-küme (closed-set) senaryosu
üzerinden yürütülecek: her bireyin görüntülerinin ~%75'i galeri
(veritabanı), ~%25'i sorgu (test) seti olarak ayrılmıştı. Her sorgu
görüntüsü, galerideki tüm kayıtlarla karşılaştırılır ve en yakın eşleşme
Rank-1 tahmini olarak alınır.

**Tekrarlanabilirlik:** Train/test ayrımı sabit bir `random_state` ile 3
farklı tohum (seed) değeriyle tekrarlanacak, sonuçlar ortalama ±
standart sapma olarak raporlanacak — tek seferlik bir ayrımın şans eseri
iyi/kötü çıkmasının önüne geçer.

## 2. Değerlendirme Metrikleri (hesaplama detayı)

| Metrik | Hesaplama | Amaç |
|---|---|---|
| Rank-1 Doğruluk | Doğru eşleşen sorgu sayısı / toplam sorgu sayısı | Temel başarı göstergesi (1:N tanıma) |
| Precision / Recall / F1 | scikit-learn `classification_report`, tür bazında ayrı | Sınıf bazlı dengesizliği görmek |
| Confusion Matrix | Gerçek vs tahmin edilen birey ID'leri | Hangi bireylerin karıştığını görmek |
| FAR / FRR / EER | 1:1 doğrulama: "bu görüntü X'e mi ait" | Biyometrik literatürle doğrudan kıyas; FR-07 doğrulaması (artık zorunlu) |
| DIR @ sabit FAR + AUROC | Open-set: bilinen-doğru-tanıma oranı, sabit FAR (%1 ve %0,1) altında; bilinen/bilinmeyen ayrımı için AUROC | FR-08 doğrulaması |
| İşlem süresi | ms/sorgu (sunucu tarafı, ayrıca uçtan uca telefon-sunucu) | Ürün kullanılabilirliği |

## 3. Deney Senaryoları

Tüm senaryolarda sabit seed'lerle (3 tekrar) çalışılır; sonuçlar ortalama ± standart sapma olarak raporlanır. Eşik ve parametre ayarı yalnızca validation alt kümesinde yapılır (bkz. DATASET.md, Bölüm 4).

### Senaryo A — Tür Bazlı Değerlendirme (E1)
Sığır (ana), köpek ve kedi için ayrı ayrı Rank-1, precision/recall/F1. Türler arası fark tartışmada yorumlanır.

### Senaryo B — Yöntem Karşılaştırması (Ablation)
METHOD.md Bölüm 5'teki 5 kombinasyon (LBP, GLCM, LBP+GLCM, SIFT/ORB, en iyi doku + SIFT/ORB). Varyant B onaylanırsa embedding tabanlı yöntem de tabloya eklenir.

### Senaryo C — Veri Seti Aktarımı (E2)
Parametreler ve eşik D1'de belirlenir, D2'de değiştirilmeden test edilir (ve ters yön). İki sette aynı hayvanlar bulunmadığı için galeri, test edilen setin kendi içinden kurulur. Amaç: kamera, ırk ve ortam değişimine genelleme.

### Senaryo D — Open-set (E3)
Bireylerin ~%20'si bilinmeyen olarak ayrılır. DIR@FAR ve AUROC raporlanır.

### Senaryo E — Kalite Dayanıklılığı (E4)
D2 alt kümeleri: DSLR vs telefon, temiz vs kirli burun. ROI segmentasyon başarısızlık oranı ayrıca raporlanır.

### Senaryo F — Galeri Boyutu Duyarlılığı (opsiyonel)
Galeri kayıt sayısı kademeli artırılır (ör. 20, 50, 100, tümü).

### Senaryo G — Saha (bonus, D3)
Telefonla çekilen yerel setle uçtan uca (uygulama → API) test.

## 4. Başarı Kriterleri (REQUIREMENTS.md Bölüm 7 ile tutarlı)

- **Makale (klasik):** E1'de Rank-1 ≥ %90 (galeri oranı %75). Klasik yöntem literatüründe (Awad & Hassaballah, 2019) eğitim verisi oranına bağlı olarak %75–93 aralığı raporlanmıştır; hedef üst banda yakındır.
- **Ürün prototipi:** E2 ve E3 sonuçları ölçülüp raporlanmış olmalıdır; sayısal hedef ilk ölçümden sonra belirlenir.
- **Referans:** Ticari/saha sonuçları (%98–99,6) doğrudan kıyas hedefi değildir; makalede klasik yöntem literatürüyle kıyaslama yapılır.
- Hedefin altında kalınsa dahi metodolojinin doğru uygulanması ve sonuçların dürüstçe raporlanması akademik olarak yeterlidir; nedenler hata analiziyle tartışılır.

## 5. Sonuçların Raporlanma Formatı

- **Tablo 1:** Tür bazında Rank-1, precision, recall, F1 (E1)
- **Tablo 2:** Yöntem karşılaştırması (ablation)
- **Tablo 3:** Veri seti aktarımı (D1→D2, D2→D1)
- **Tablo 4:** Open-set (DIR@FAR, AUROC)
- **Şekil 1:** Confusion matrix ısı haritası
- **Şekil 2:** Yöntem karşılaştırması çubuk grafiği
- **Şekil 3:** ROC / DET eğrisi (doğrulama)
- **Örnek görseller:** Doğru ve yanlış eşleşen görüntü çiftleri

## 6. Hata Analizi Prosedürü (Hafta 7 ile bağlantılı)

1. Yanlış sınıflandırılan tüm sorgu görüntüleri listelenir
2. Bunlar görsel olarak incelenir: ışık, açı, bulanıklık, segmentasyon
   hatası gibi ortak nedenler aranır
3. Bulgular kategorize edilip bir tabloya dökülür (ör. "%40'ı segmentasyon
   hatasından, %30'u düşük çözünürlükten...")
4. Bu tablo doğrudan makalenin "Sınırlamalar" bölümüne girer

## 7. Sınırlamalar (baştan kabul edilen)

- D1 tek çiftlikten, üç et sığırı ırkından oluşur; D2 farklı bölgeden olsa da ırk çeşitliliği sınırlıdır. Sonuçlar "bu setlerde" geçerlidir, her sığır için değil.
- Klasik yöntemlerin doğruluğu literatürde %75–93 bandındadır; ticari seviye beklenmez.
- Sahte girdi (fotoğrafın fotoğrafı/liveness) değerlendirilmemiştir.
- Manda kapsam dışıdır (açık veri yok).
- Bir bireyin en az 4 görüntüsü olması kriteri nedeniyle bazı hayvanlar dışarıda kalmıştır.
- Saha verisi (D3) garanti değildir; yoksa saha doğrulaması yapılamaz.

## 8. Sonraki Doküman

Bir sonraki adım: **AI-Ajan Bağlam Dosyası** (AGENTS.md) — Antigravity/
Codex'in kod yazarken tutarlı kalması için proje standartlarının,
klasör yapısının ve kısıtların (klasik yöntem, deep learning yok vb.)
özetlendiği doküman.
