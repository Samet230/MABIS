# Algoritma & Yöntem Dokümanı
## ZooID (MABIS) — Sığır Odaklı Biyometrik Kimlik Doğrulama Sistemi

**İlişkili dokümanlar:** PRD.md, ARCHITECTURE.md, EVALUATION.md, PRODUCT_PLAN.md  
**Versiyon:** 0.2 (Ürün Seviyesi Güncellemesi)  

---

## 1. Yöntem Varyantları: A (Klasik) ve B (Hibrit)

Sistem mimarisi, öznitelik çıkarıcı ve eşleştirme katmanlarını soyutlayarak iki varyantı da destekleyecek şekilde tasarlanmıştır:

### Varyant A — Saf Klasik Çözüm (Mevcut Temel Hat)
- **Tüm işlem adımları klasik görüntü işleme teknikleriyle yürütülür:**
  - Kalite Kapısı: Laplacian varyansı + parlaklık histogramı
  - Segmentasyon: Otsu eşikleme + morfolojik filtreleme + kontur analizi
  - Ön İşleme: CLAHE + medyan filtre
  - Öznitelik Çıkarımı: LBP, GLCM, SIFT ve ORB
  - Eşleştirme & Doğrulama: RANSAC homografi geometrik doğrulama + Ki-Kare / Kosinüs mesafesi
- **Durum:** Ders kısıtlarına %100 uygundur. Akademik makale için temel oluşturur.

### Varyant B — Hibrit Çözüm (Gelecek Genişletme / Ürün Seviyesi)
- Ön işleme, kalite kapısı ve segmentasyon klasik olarak korunur (görüntü işleme katkısı burada yer alır).
- Eşleştirme aşamasında klasik özniteliklere ek olarak hafif bir derin öğrenme omurgasından çıkarılan öznitelik vektörü (embedding) eklenir.
- **Durum:** Ders şartnamesi izin verdiği takdirde veya ticari ürün aşamasında devreye alınacaktır.

---

## 2. Kalite Kapısı Algoritması (FR-01)

Sisteme giren görüntü $I$ için:
1. **Bulanıklık Puanı:**
   $$ S_{\text{blur}} = \text{Var}(\nabla^2 I_{\text{gray}}) = \frac{1}{M N} \sum (L_{x,y} - \bar{L})^2 $$
   $S_{\text{blur}} < 80.0$ ise "Bulanık Görüntü" uyarısıyla reddedilir.
2. **Pozlama Kontrolü:**
   Piksel ortalaması $\mu = \frac{1}{M N} \sum I_{\text{gray}}(x, y)$. Eğer $\mu < 40$ ("Karanlık") veya $\mu > 220$ ("Aşırı Parlak / Patlamış") ise reddedilir.
3. **Kadraj Kontrolü:** Burun bölgesinin bounding box alanı görüntünün en az %15'ini kaplamalıdır.

---

## 3. Segmentasyon Hattı (FR-02)

- **Doğrudan Kırpılmış Görüntüler (D1):**
  - Merkez odaklı adaptif eşikleme ve kare $300 \times 300$ ROI çıkarımı.
- **Tam Yüz Fotoğrafları (D2 - Pakistan):**
  - Yüzün alt bölgesine odaklanan oransal maskeleme.
  - Burun deliklerinin koyu tonlarını yakalamak için adaptif Otsu eşikleme.
  - En büyük dışbükey gövde (convex hull) ile burun bölgesinin izole edilip $300 \times 300$ piksele kırpılması.
  - Fallback: Burun tespit edilemezse yüzün alt-orta üçte birlik bölümü merkez kırpma ile alınır.

---

## 4. Öznitelik Çıkarımı

Sistemde 4 farklı klasik öznitelik yöntemi mevcuttur:

1. **LBP (Local Binary Patterns):**
   - $4 \times 4$ ızgara hücreli uniform LBP ($P=8, R=1$).
   - Her hücre için 10 kutulu histogram $\rightarrow 16 \times 10 = 160$ boyutlu $L_2$ normalize vektör.
2. **GLCM (Gray-Level Co-occurrence Matrix):**
   - 16 gri seviye kuantalama, 3 mesafe (1, 2, 3), 4 yön ($0^\circ, 45^\circ, 90^\circ, 135^\circ$).
   - 6 istatistiksel özellik (contrast, dissimilarity, homogeneity, energy, correlation, ASM) $\rightarrow 3 \times 4 \times 6 = 72$ boyutlu vektör.
3. **LBP + GLCM Birleşimi:** 232 boyutlu birleşik doku vektörü.
4. **SIFT / ORB Anahtar Nokta ve Tanımlayıcılar (Geometrik Paketleme):**
   - **Taranan Noktalar:** SIFT (kontrast eşiği 0.02, kenar eşiği 15.0) veya ORB (FAST eşiği 7, kenar eşiği 12).
   - **Koordinat Paketleme Mimarisi:** Her anahtar noktanın $(x, y)$ koordinatları tanımlayıcı matrisinin ilk iki sütununa eklenir:
     - ORB: $(N, 34)$ boyutlu matris (2 koordinat + 32 bayt tanımlayıcı)
     - SIFT: $(N, 130)$ boyutlu matris (2 koordinat + 128 boyutlu float tanımlayıcı)
   - Bu paketleme, eşleştirme aşamasında harici koordinat taşımaya gerek kalmadan doğrudan RANSAC geometrik doğrulamasına imkân tanır.

---

## 5. Eşleştirme, Geometrik Doğrulama ve Karar Motoru

### A. 1D Vektörler (LBP / GLCM)
- Ki-Kare ($\chi^2$) mesafesi:
  $$ D_{\chi^2}(p, q) = \frac{1}{2} \sum \frac{(p_i - q_i)^2}{p_i + q_i + \epsilon}, \quad S = \frac{1}{1 + D_{\chi^2}} $$

### B. 2D Tanımlayıcılar (SIFT / ORB) ve RANSAC Doğrulaması
1. **Lowe's Ratio Test:** ORB için $0.80$, SIFT için $0.75$ oranı ile en iyi iki eşleşme filtrelenir ($d_1 < \alpha \cdot d_2$).
2. **RANSAC Homografi Doğrulaması:**
   Eşleşen noktalar arasından $4 \times 4$ homografi matrisi $H$ RANSAC ile aranır (yeniden izdüşüm hata eşiği: 5.0 piksel).
3. **Güven Skoru (Inlier Ratio):**
   Rastgele doku benzerliklerinden kaynaklanan sahte eşleşmeleri filtrelemek için güven skoru inlier oranına göre hesaplanır:
   $$ \text{Score} = \frac{\text{İnlier Eşleşme Sayısı}}{\max(1, \text{Sorgu Anahtar Nokta Sayısı})} $$

### C. 1:1 Doğrulama (FR-07)
- Sorgu görüntüsü $I_q$ ve iddia edilen kimlik $ID_{\text{claim}}$ girilir.
- Veritabanındaki $ID_{\text{claim}}$ şablonu ile eşleştirme skoru hesaplanır.
- $\text{Score} \ge \theta_{\text{verify}}$ ise **KABUL**, aksi halde **RET** kararı üretilir.

### D. Açık-Küme Bilinmeyen Reddi (FR-08)
- 1:N sorguda elde edilen en yüksek benzerlik skoru $S_{\text{max}}$ incelenir.
- Eğer $S_{\text{max}} < \theta_{\text{unknown}}$ ise sistem "Bilinmeyen / Kayıtsız Hayvan" çıktısı verir.
- $\theta_{\text{unknown}}$ eşiği, EER veya hedef FAR seviyesine göre kalibre edilir.
