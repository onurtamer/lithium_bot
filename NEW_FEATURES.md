# 🚀 Lithium Bot - Yeni Özellikler

Bu dokümantasyon, Lithium Bot'a eklenen tüm yeni özellikleri açıklamaktadır.

## 📁 Yeni Dosyalar

### Modeller (lithium_core/models/)
- `fun.py` - Eğlence özellikleri modelleri (Giveaway, Birthday, Suggestion, DuelStats)
- `security.py` - Güvenlik modelleri (JailConfig, BadWordFilter, AutoModConfig, TempMute)

### Cog'lar (apps/bot/cogs/)
- `audit_logging.py` - Gelişmiş loglama sistemi
- `advanced_automod.py` - Gelişmiş automod (küfür, caps, link, spam koruması)
- `jail.py` - Jail ve mute sistemi
- `fun.py` - Eğlence ve oyunlar
- `suggestions.py` - Öneri sistemi
- `extended_utility.py` - Genişletilmiş utility komutları
- `reaction_roles.py` - Tepki rolleri

---

## 🛡️ Moderasyon ve Güvenlik Özellikleri

### 1. Gelişmiş Loglama (Audit Logs)
**Komutlar:**
- `/log_setup <module> <channel>` - Log kanalı ayarla
- `/log_list` - Aktif log kanallarını göster

**Log Türleri:**
- `MESSAGES` - Silinen/düzenlenen mesajlar
- `VOICE` - Sesli kanal giriş-çıkışları
- `MEMBERS` - Rol değişiklikleri, takma ad değişiklikleri
- `MODERATION` - Ban/unban logları
- `SERVER` - Sunucu değişiklikleri

### 2. Küfür ve Argo Engelleyici
**Komutlar:**
- `/badword_add <word> <severity>` - Yasaklı kelime ekle
- `/badword_remove <word>` - Yasaklı kelime kaldır
- `/badword_list` - Yasaklı kelimeleri listele

**Özellikler:**
- Varsayılan Türkçe küfür listesi
- Özelleştirilebilir kelime listesi
- Otomatik mesaj silme ve uyarı

### 3. Link Engelleyici (Anti-Link)
**Komutlar:**
- `/link_whitelist <domain>` - İzin verilen domain ekle
- `/link_allow_role <role>` - Role link atma izni ver

**Özellikler:**
- Yetkisiz link paylaşımını engelleme
- Whitelist sistemi
- Rol bazlı izinler
- Kanal bazlı izinler

### 4. Caps Lock Koruması
**Ayarlar:**
- Eşik: %70 (ayarlanabilir)
- Minimum mesaj uzunluğu: 10 karakter

### 5. Spam/Flood Koruması
**Özellikler:**
- 5 saniyede 5+ mesaj spam sayılır
- Otomatik timeout (mute)
- Ayarlanabilir eşik ve süre

### 6. Jail (Hapis) Sistemi
**Komutlar:**
- `/jail_setup <role> <channel>` - Jail sistemini kur
- `/jail <member> <reason> [duration]` - Üyeyi hapse at
- `/unjail <member>` - Üyeyi hapisten çıkar
- `/jaillist` - Hapisteki üyeleri listele

**Özellikler:**
- Tüm rolleri alıp jail rolü verir
- Sadece jail kanalını görebilir
- Süreli veya süresiz hapis
- Otomatik rol geri verme

### 7. Süreli Susturma (Temp Mute)
**Komutlar:**
- `/mute <member> <duration> [reason]` - Üyeyi sustur
- `/unmute <member>` - Susturmayı kaldır

**Süre Formatı:** `10m`, `1h`, `1d`

### 8. Sesli Kanal Koruması (Mic Spam)
**Özellikler:**
- Hızlı gir-çık tespiti
- Otomatik disconnect
- Kısa süreli mute

### 9. AutoMod Ayarları
**Komut:** `/automod_config`
- Caps koruması açık/kapalı
- Spam koruması açık/kapalı
- Link koruması açık/kapalı
- Küfür filtresi açık/kapalı

---

## 🤝 Kullanıcı Etkileşimi ve Eğlence

### 1. Çekiliş (Giveaway) Sistemi
**Komutlar:**
- `/giveaway <duration> <prize> [winners] [required_role]` - Çekiliş başlat
- `/giveaway_reroll <message_id>` - Kazananı yeniden çek

**Özellikler:**
- 🎉 emoji ile katılım
- Çoklu kazanan desteği
- Rol gereksinimi
- Otomatik sonlandırma

### 2. Doğum Günü Kutlayıcı
**Komutlar:**
- `/birthday_set <day> <month>` - Doğum gününüzü kaydedin
- `/birthday_setup <channel> [role]` - Doğum günü kanalı ayarla

**Özellikler:**
- Otomatik kutlama mesajı
- Doğum günü rolü
- Özelleştirilebilir mesaj

### 3. Düello / Mini Oyunlar
**Komutlar:**
- `/duel <opponent>` - Taş-Kağıt-Makas düellosu
- `/coinflip_duel <opponent>` - Yazı-Tura düellosu
- `/duel_stats [member]` - Düello istatistikleri

### 4. Aşk Ölçer / Uyum Testi
**Komutlar:**
- `/love <user1> [user2]` - İki kişi arasındaki aşk yüzdesi
- `/ship <user1> <user2>` - İsimleri birleştir ve uyum hesapla

### 5. Eğlence Komutları
**Komutlar:**
- `/8ball <question>` - Sihirli 8 topuna sor
- `/roll [dice]` - Zar at (örn: 2d6, 1d20)

### 6. Tepki Rolleri (Reaction Roles)
**Komutlar:**
- `/reactionrole <channel> [title] [description]` - Mesaj oluştur
- `/reactionrole_add <message_id> <emoji> <role>` - Emoji ekle
- `/reactionrole_remove <message_id> <emoji>` - Emoji kaldır
- `/reactionrole_list` - Mesajları listele

---

## 🛠️ Araçlar ve Yardımcı Özellikler

### 1. Öneri Sistemi
**Komutlar:**
- `/suggest <suggestion>` - Öneri gönder
- `/suggest_setup <channel>` - Öneri kanalı ayarla
- `/suggest_respond <message_id> <response>` - Öneriye yanıt ver

**Özellikler:**
- 👍/👎 ile oylama
- Moderatör onay/ret butonları
- Durum takibi

### 2. Kullanıcı Bilgi Kartı
**Komutlar:**
- `/userinfo [member]` - Detaylı kullanıcı bilgisi

**Gösterilen Bilgiler:**
- Hesap açılış tarihi
- Sunucuya katılım tarihi
- Roller
- Badge'ler
- Aktivite (Spotify, oyun vb.)
- Banner (varsa)

### 3. Avatar/Banner Getirici
**Komutlar:**
- `/avatar [member]` - Avatarı getir (tüm formatlar)
- `/banner [member]` - Banner'ı getir

### 4. Sunucu Bilgisi
**Komut:** `/serverinfo`

### 5. Hava Durumu
**Komut:** `/weather <city>`

> ⚠️ `OPENWEATHER_API_KEY` env variable gerekli

### 6. Döviz Kuru
**Komutlar:**
- `/currency <amount> <from> <to>` - Para birimi çevir
- `/dolar` - USD/TRY kuru
- `/euro` - EUR/TRY kuru

### 7. Çeviri
**Komut:** `/translate <text> [to_lang]`

### 8. Anket
**Komut:** `/poll <question> <opt1> <opt2> [opt3] [opt4]`

### 9. Bot Bilgisi
**Komutlar:**
- `/ping` - Gecikme
- `/botinfo` - Bot bilgisi

---

## 🔧 Kurulum

### 1. Database Migration
Yeni tablolar için migration çalıştırın:
```bash
alembic revision --autogenerate -m "Add fun and security features"
alembic upgrade head
```

### 2. Environment Variables (Opsiyonel)
```env
# Hava durumu için
OPENWEATHER_API_KEY=your_api_key
```

### 3. Bot Permissions
Aşağıdaki izinler gerekli:
- Manage Roles
- Manage Channels
- Manage Messages
- Moderate Members
- View Audit Log
- Send Messages
- Embed Links
- Add Reactions

---

## 📊 Mevcut Özellikler (Önceden Var)

Bu özellikler zaten mevcuttu:
- ✅ Raporlama Sistemi (`report.py`)
- ✅ Ticket Sistemi (`tickets.py`)
- ✅ Anti-Raid (`antiraid.py`)
- ✅ AFK Modu (`advanced_utils.py`)
- ✅ Hatırlatıcı (`advanced_utils.py`)
- ✅ Starboard (`advanced_utils.py`)
- ✅ Geçici Ses Kanalları (`advanced_utils.py`)
- ✅ Hoş Geldin/Güle Güle (`welcome.py`)
- ✅ Leveling/XP (`leveling.py`)
- ✅ Ekonomi (`economy.py`)
- ✅ Ban/Kick (`moderation.py`)

---

## 🎯 Komut Listesi Özeti

| Kategori | Komut Sayısı |
|----------|-------------|
| Audit Logging | 2 |
| AutoMod | 5 |
| Jail/Mute | 5 |
| Fun & Games | 9 |
| Suggestions | 3 |
| Utility | 12 |
| Reaction Roles | 4 |
| **TOPLAM** | **40+ yeni komut** |
