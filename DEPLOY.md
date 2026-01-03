# Lithium Bot Deployment Guide

Bu rehber, Lithium Bot ve Web Kontrol Panelini bir Linux VPS (Ubuntu/Debian) üzerinde canlıya almak için gerekli adımları içerir.

## Ön Gereksinimler

*   **Linux VPS** (Ubuntu 22.04+ önerilir)
*   **Domain Adresi** (API ve Web için DNS A kaydı VPS IP adresine yönlendirilmiş olmalı)
*   **Docker & Docker Compose** yüklü olmalı

## Hızlı Kurulum (Otomatik)

Projede sizin için hazırlanmış `deploy.sh` betiğini kullanarak hızlıca kurulum yapabilirsiniz.

1.  **Projeyi Sunucuya Çekin:**
    ```bash
    git clone https://github.com/onurtamer/lithium_bot.git
    cd lithium_bot
    ```

2.  **Kurulum Betiğini Çalıştırın:**
    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```

3.  **Konfigürasyon:**
    Script ilk çalıştırıldığında `.env` dosyası bulamazsa oluşturur ve düzenlemenizi ister.
    Aşağıdaki değerleri **mutlaka** canlı ortam verileriyle doldurun:
    *   `POSTGRES_PASSWORD`: Güçlü bir şifre belirleyin.
    *   `DISCORD_TOKEN`: Bot tokeniniz.
    *   `DISCORD_CLIENT_SECRET`: Developer portalından alacağınız secret.
    *   `DOMAIN_NAME`: Domain adresi (örn: `lithiumbot.xyz`).
    *   `EMAIL`: SSL sertifikası için e-posta adresi.

4.  **Bitir:**
    Bilgileri kaydettikten sonra `./deploy.sh` komutunu tekrar çalıştırın. Sistem otomatik olarak build alacak, servisleri başlatacak ve veritabanı tablolarını oluşturacaktır.

## Manuel Kurulum

Eğer script kullanmak istemezseniz:

1.  **Environment Dosyasını Hazırlayın:**
    ```bash
    cp .env.example .env
    nano .env
    ```

2.  **Servisleri Başlatın:**
    ```bash
    docker compose -f docker-compose.prod.yml up -d --build
    ```

3.  **Migrasyonları Çalıştırın:**
    Veritabanı tablolarının oluşması için:
    ```bash
    docker compose -f docker-compose.prod.yml exec bot alembic upgrade head
    ```

## Güncelleme (Update)

Yeni bir özellik eklediğinizde veya bug düzelttiğinizde sunucuyu güncellemek için sadece:

```bash
./deploy.sh
```

komutunu çalıştırmanız yeterlidir. Script:
1.  Git'ten son değişiklikleri çeker.
2.  Container'ları yeniden build eder.
3.  Migrasyonları uygular.

## Troubleshooting (Sorun Giderme)

*   **Logs:** Logları izlemek için:
    ```bash
    docker compose -f docker-compose.prod.yml logs -f
    ```
*   **Bot Bağlanamıyor:** `DISCORD_TOKEN`'ın doğru olduğundan emin olun. Türkiye lokasyonlu sunucularda Discord erişim engeli olabilir, sunucunun yurt dışında olduğundan emin olun.
*   **Web Sitesi Açılmıyor:** 80 ve 443 portlarının sunucu güvenlik duvarında (UFW) açık olduğundan emin olun: `ufw allow 80`, `ufw allow 443`.
