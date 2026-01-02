# 🧪 Lithium Bot - The Ultimate Discord Management Solution

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Discord.py](https://img.shields.io/badge/Discord.py-5865F2?style=for-the-badge&logo=discord)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

Lithium is a powerful, production-ready Discord bot suite designed for high-performance server management. It features a modern **FastAPI** backend, a high-concurrency **Discord.py** bot client, and a stunning **HTMX-powered Django dashboard**.

---

## 🌟 Önemli Özellikler (Current Features)

Lithium Bot, sunucunuzu yönetmek, korumak ve eğlendirmek için 40'tan fazla yeni ve gelişmiş komutla donatılmıştır.

### 🛡️ Güvenlik ve Moderasyon
*   **Gelişmiş Denetim Kaydı (Audit Logs):** Mesaj düzenlemeleri, silinmeler, ses kanalı hareketleri ve üye değişikliklerini anlık olarak izleyin.
*   **Akıllı AutoMod:**
    *   🔇 **Küfür & Argo Filtresi:** Özelleştirilebilir yasaklı kelime listesi.
    *   🔗 **Link Engelleyici:** Beyaz liste (whitelist) destekli bağlantı koruması.
    *   🔡 **Caps Lock Koruması:** Mesajlardaki büyük harf yoğunluğunu kontrol eder.
    *   🚫 **Spam & Flood Koruması:** Hızlı mesaj gönderimini otomatik engeller.
*   **Jail (Hapis) Sistemi:** Kural ihlali yapan kullanıcıları süreli veya süresiz olarak tüm yetkilerinden arındırıp özel bir odaya hapseder.
*   **Süreli Susturma (Temp Mute):** `10m`, `1h`, `1d` gibi esnek sürelerle susturma desteği.

### 🤝 Topluluk ve Eğlence
*   **Çekiliş (Giveaway) Sistemi:** Rol gereksinimli, çoklu kazanan destekli ve otomatik sonuçlanan gelişmiş çekilişler.
*   **Doğum Günü Kutlayıcı:** Üyelerin doğum günlerini otomatik rol ve mesajlarla kutlar.
*   **Düello & Oyunlar:** Taş-Kağıt-Makas ve Yazı-Tura düelloları ile sunucu içi etkileşimi artırın.
*   **Tepki Rolleri (Reaction Roles):** Kullanıcıların emoji ile rol almasını sağlayan kolay kurulumlu mesajlar.
*   **Aşk Ölçer & Diğerleri:** `/love`, `/ship`, `/8ball`, `/roll` gibi eğlence komutları.

### 🛠️ Gelişmiş Araçlar
*   **Öneri Sistemi:** Kullanıcı geri bildirimlerini oylama ve moderatör onayı ile yönetin.
*   **Detaylı Kullanıcı Bilgisi:** Badge'ler, aktivite durumu, hesap yaşı ve özel bilgiler içeren şık kartlar.
*   **Finans & Hava Durumu:** Canlı döviz kurları (`/dolar`, `/euro`) ve anlık hava durumu bilgisi.
*   **Çeviri & Anket:** Anlık metin çevirisi ve interaktif anket oluşturma.

### 📊 Mevcut Temel Sistemler
*   ✅ **Leveling & XP:** Aktifliğe göre seviye atlama sistemi.
*   ✅ **Gelişmiş Ekonomi:** Sunucu içi ticaret ve bakiye yönetimi.
*   ✅ **Ticket Sistemi:** Destek talepleri için özel kanal yönetimi.
*   ✅ **Anti-Raid & Raid Koruması:** Sunucuyu bot saldırılarından korur.
*   ✅ **Starboard:** En çok beğenilen mesajları özel kanalda sergiler.

---

## 🖥️ Kontrol Paneli (Dashboard)

Lithium, sunucunuzu web üzerinden yönetmenize olanak tanıyan modern bir panel sunar:
- **Discord OAuth2 Entegrasyonu:** Güvenli giriş ve yetkilendirme.
- **Canlı Ayar Yönetimi:** Bot ayarlarını (leveling, moderasyon, loglama) panel üzerinden anlık güncelleyin.
- **İstatistikler:** Sunucu aktivitesini ve bot kullanımını takip edin.

---

## 🚀 Quick Start (Development)

1. **Environment Kurulumu**:
   ```bash
   cp .env.example .env
   # Discord Bot Token ve OAuth2 bilgilerini doldurun
   ```

2. **Servisleri Başlat**:
   ```bash
   make up
   ```

3. **Veritabanını Hazırla**:
   ```bash
   make init
   ```

4. **Erişim**:
   - Panel: [http://localhost:5173](http://localhost:5173)
   - API Dokümantasyonu: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🏗️ Production Deployment

Production ortamı için Nginx revers-proxy ve SSL yapılandırması önerilir.

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📁 Repository Structure

```text
.
├── apps/
│   ├── api/           # FastAPI Backend
│   ├── bot/           # Discord.py Bot Client
│   └── dashboard/     # Django Dashboard (HTMX Powered)
├── lithium_core/      # Shared Models, DB Schemas, and Utils
├── tests/             # Comprehensive Test Suite
├── docker-compose.yml # Docker Configuration
└── Makefile           # Automation Scripts
```

---

## 🛡️ Security & RBAC
Lithium, `RBAC.md` ve `PERMISSIONS.md` dosyalarında detaylandırılan güçlü bir Rol Bazlı Erişim Kontrolü (RBAC) sistemi kullanır.

## ❓ Troubleshooting
- **Bot çevrimdışı mı?**: Intents'lerin Discord Developer Portal üzerinden etkinleştirildiğinden emin olun.
- **Veritabanı hatası mı?**: `make init` komutuyla migration'ların uygulandığını kontrol edin.
- **Giriş yapılamıyor mu?**: `DISCORD_REDIRECT_URI` bilgisinin Dev Portal ile eşleştiğini doğrula.
