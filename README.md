# 🐾 MABIS — Biyometrik Hayvan Tanıma ve Pasaport Takip Sistemi

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Tests: Pytest](https://img.shields.io/badge/tests-61%2F61%20passing-brightgreen.svg)](tests/)
[![Architecture: Classical CV](https://img.shields.io/badge/architecture-Pure%20CV%20(ORB%2B%20RANSAC)-orange.svg)](src/)
[![Database: Supabase Ready](https://img.shields.io/badge/database-Supabase%20Ready-cyan.svg)](src/database/)

MABIS (Mobil Biyometrik Hayvan Tanıma Sistemi), sığır burun izi deseni, köpek burun ucu morfolojisi ve kedi yüz biyometrisini kullanarak **klasik bilgisayarlı görü (Classical Computer Vision)** tabanlı 1:N kimliklendirme ve pasaport yönetimi sunan ürün seviyesinde bir sistemdir.

---

## 🚀 Temel Özellikler

### 1. 🐄 Büyükbaş Hayvan Modu (Özel Ahır Depolama)
- **Burun İzi Deseni Biyometrisi:** ORB öznitelik çıkarımı ve RANSAC homografi doğrulama ile yüksek güvenilirlikte kimliklendirme.
- **İzole Ahır Depolama (`cattle_private`):** Her çiftlik sahibi sadece kendi sürüsünü görür; 1:N arama sadece ilgili ahırdaki hayvanlar arasında yapılır.
- **Çalışan Erişim Kodu (`AHIR-XXXX`):** Ahır sahibi çalışanları için erişim kodu üretebilir veya yenileyebilir. Çalışanlar kod ile katılarak ekleme ve kayıt düzenleme yetkisi kazanır.
- **TÜRKVET Küpe Doğrulama:** Küpe no ve pasaport bilgileriyle çift aşamalı doğrulama.

### 2. 🐕🐈 Sokak & Evcil Hayvan Modu (Ortak Depolama & Harita)
- **Köpek Burun & Kedi Yüz Biyometrisi:** Tür anatomisine göre uyarlanmış ROI segmentasyonu ve kalite kapısı denetimi.
- **Bölgesel Ortak Depo (`stray_public`):** Erişim koduna gerek olmadan açık havuz; kullanıcının GPS konumuna göre en yakın mahalle depoları (Kadıköy, Beşiktaş vb.) otomatik sıralanır.
- **Yaşam Alanı & Dolaşım Haritası:** Leaflet / OpenStreetMap tabanlı tespit zaman çizelgesi, merkez üssü (centroid) ve tahmini yaşam alanı çapı hesaplama.
- **Kayıp Hayvan Alarmı:** Sistem kayıp statüsündeki bir hayvanla eşleştiğinde anında görsel ve dinamik alarm tetikler.

### 3. ⚡ Supabase Cloud Hazır Veritabanı Mimarisi
- `src/database/supabase_schema.sql` üzerinden PostgreSQL DDL, çok kiracılı (multi-tenant) `repo_id` yapısı ve Row-Level Security (RLS) politikaları hazırdır.
- `.env` üzerinden `STORAGE_BACKEND=supabase` yapılandırmasıyla bulut veritabanına kesintisiz geçiş desteklenir.

### 4. 📱 Dokunmatik Mobil Web Arayüzü (Flask)
- Mobil cihaz çerçevesi veya tam ekran mobil modunda çalışan, koyu tema odaklı, dokunmatik duyarlı arayüz.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimler
- Python 3.10+
- Virtualenv

### 2. Depoyu Klonlayın ve Bağımlılıkları Yükleyin
```bash
git clone https://github.com/Samet230/MABIS.git
cd MABIS

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Çevre Değişkenleri
```bash
cp .env.example .env
```

### 4. Web Arayüzünü Başlatın
```bash
python -m src.web.app
```
Tarayıcınızda `http://127.0.0.1:5000` adresine giderek uygulamayı kullanabilirsiniz.

---

## 🧪 Testleri Çalıştırma

Tüm birim ve entegrasyon testlerini çalıştırmak için:
```bash
pytest tests/ -v
```
> **Not:** 61/61 test sentetik biyometrik matrisler kullanarak fiziksel veri setine ihtiyaç duymadan %100 oranında başarıyla geçer.

---

## 📂 Proje Dizin Yapısı

```
MABIS/
├── src/
│   ├── database/         # Depolama yöneticisi & Supabase şeması
│   ├── evaluation/       # Metrik hesaplama (Rank-1, F1, CMC, FAR/FRR)
│   ├── features/         # ORB, SIFT, LBP, GLCM öznitelik çıkarıcılar
│   ├── matching/         # RANSAC homografi eşleştirme motoru
│   ├── preprocessing/    # CLAHE, gürültü azaltma, hizalama
│   ├── segmentation/     # Burun ve yüz ROI segmentasyonu
│   ├── utils/            # Konfigürasyon, geo mesafe, görsel I/O
│   └── web/              # Flask web sunucusu ve HTML şablonları
├── tests/                # 61 kapsamlı test senaryosu
├── main.py               # Komut satırı (CLI) arayüzü
├── requirements.txt      # Python bağımlılıkları
├── ROADMAP.md            # Geliştirme yol haritası
└── .env.example          # Örnek çevre değişkenleri konfigürasyonu
```

---

## 📄 Lisans
Bu proje MIT lisansı ile korunmaktadır.
