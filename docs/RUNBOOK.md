# (F) OPERASYON RUNBOOK

## İÇİNDEKİLER
1. [Normal Operasyon](#1-normal-operasyon)
2. [Lockdown Prosedürü](#2-lockdown-prosedürü)
3. [Raid Müdahale](#3-raid-müdahale)
4. [False Positive Krizi](#4-false-positive-krizi)
5. [Safe Mode Prosedürü](#5-safe-mode-prosedürü)
6. [Incident Response](#6-incident-response)
7. [Bot Kesinti Prosedürü](#7-bot-kesinti-prosedürü)
8. [Günlük / Haftalık İşlemler](#8-günlük-haftalık-i̇şlemler)

---

## 1. NORMAL OPERASYON

### 1.1 Günlük Kontrol Listesi (OpsAdmin)
```
□ #mod-log kanalını kontrol et (son 24h)
□ #alerts kanalını kontrol et
□ Review queue'da bekleyen item var mı?
□ Heat map'te kızaran kanal var mı?
□ Sistem metrikleri normal mi? (latency, error rate)
```

### 1.2 Haftalık Kontrol Listesi (OpsAdmin)
```
□ Haftalık raporu incele
□ False positive oranını kontrol et (hedef: <%5)
□ En çok tetiklenen kuralları incele
□ Appeal kabul oranını kontrol et
□ Yeni kural/ayar gereksinimi var mı?
□ Triage/Reviewer performansını değerlendir
```

### 1.3 Triage Görevleri
```
□ Yeni ticket'ları 2 saat içinde triage et
□ Öncelik ve etiket ata
□ Eksik bilgi varsa kullanıcıdan iste
□ Gerekirse reviewer'a yükselt
□ Spam/invalid ticket'ları kapat
```

### 1.4 Reviewer Görevleri
```
□ Review queue'yu günlük kontrol et
□ Grey zone case'lere karar ver
□ Appeal'ları 48 saat içinde değerlendir
□ Bağlam notları ekle
□ Overturn kararlarını gerekçelendir
```

---

## 2. LOCKDOWN PROSEDÜRÜ

### 2.1 Otomatik Lockdown Tetiklendi
**Belirtiler:**
- #alerts'te "🔒 LOCKDOWN ACTIVATED" mesajı
- governance_config.lockdown_active = True

**Yapılacaklar:**
```
1. [OpsAdmin] Durumu değerlendir
   /governance config
   
2. Gerçek raid mi yoksa yanlış alarm mı?
   - Son 10 dakikada kaç yeni üye katıldı?
   - Yeni üyeler benzer pattern gösteriyor mu?
   - Koordinasyon belirtisi var mı?
   
3a. Gerçek Raid ise:
   - Lockdown'ı sürdür
   - Şüpheli hesapları incele
   - Gerekirse tempban uygulat
   
3b. Yanlış Alarm ise:
   /governance lockdown disable
   - Neden tetiklendiğini araştır
   - Threshold'u ayarla
```

### 2.2 Manuel Lockdown Başlatma
**Ne Zaman:**
- Planlı event öncesi (büyük duyuru, vs.)
- Dış tehdit istihbaratı
- Koordineli saldırı belirtileri

**Komut:**
```
/governance lockdown enable reason:"Event güvenliği" duration:2h
```

### 2.3 Lockdown Sırasında İzin Verilenler
```
✓ Mevcut verified üyeler normal yazabilir
✓ Triage/Reviewer/OpsAdmin tam yetki
✓ Bot enforcement aktif
✓ Ticket sistemi çalışır
✓ #new-members kanalı açık (kısıtlı)

✗ Newcomer dışarı yazamaz
✗ Link/mention/attachment yasak (newcomer için)
✗ Yeni davetler oluşturulamaz
```

---

## 3. RAID MÜDAHALE

### 3.1 Raid Tespit Göstergeleri
| Gösterge | Eşik | Açıklama |
|----------|------|----------|
| Join rate | >15/dakika | Anormal katılım hızı |
| Account age | <7 gün | Çok yeni hesaplar |
| No avatar | >%50 | Avatarsız hesap oranı |
| Similar names | >5 | Benzer kullanıcı adları |
| Coordinated messages | >3 aynı mesaj | Koordineli spam |

### 3.2 Raid Müdahale Aşamaları

#### Aşama 1: Tespit (Otomatik)
```
Bot otomatik olarak:
1. Lockdown aktive eder
2. Yeni üyelere NEWCOMER rol verir
3. #alerts'e bildirim gönderir
4. Şüpheli hesapları quarantine eder
```

#### Aşama 2: Değerlendirme (OpsAdmin - 5 dakika)
```
1. #alerts'i kontrol et
2. Raid ölçeğini değerlendir:
   /metrics raid-stats
   
3. Koordinasyon seviyesini belirle:
   - Düşük: Birkaç spam hesap
   - Orta: Organize grup (10-50 hesap)
   - Yüksek: Büyük ölçekli saldırı (50+ hesap)
```

#### Aşama 3: Müdahale (Seviyeye Göre)

**Düşük Seviye:**
```
1. Lockdown sürdür (30 dakika)
2. Şüpheli hesapları incele
3. Net ihlal varsa bot tempban uygular
4. Lockdown kaldır
```

**Orta Seviye:**
```
1. Lockdown sürdür (1-2 saat)
2. Tüm yeni katılımları incele
3. Pattern analizi yap
4. Toplu tempban (bot uygular)
5. Discord Trust & Safety'e rapor
6. Lockdown kaldır
```

**Yüksek Seviye:**
```
1. Lockdown sürdür (24+ saat)
2. Safe mode değerlendir
3. Owner bilgilendir
4. Tüm davetleri devre dışı bırak
5. Verification zorunlu yap
6. Discord Trust & Safety acil rapor
7. Durum güncellemesi yayınla
```

### 3.3 Raid Sonrası
```
□ Lockdown kaldır
□ Karantina listesini temizle
□ False positive varsa appeal işle
□ Incident raporu hazırla
□ Threshold'ları gözden geçir
□ Haftalık rapora ekle
```

---

## 4. FALSE POSITIVE KRİZİ

### 4.1 Kriz Tespit Göstergeleri
- Kısa sürede çok sayıda appeal
- Sosyal medyada şikayetler
- Masum kullanıcıların timeout/ban'ı
- Tek bir kural çok tetikleniyor

### 4.2 Acil Müdahale
```
1. [OpsAdmin] Sorunu tespit et
   /metrics rule-stats last:1h
   
2. Sorumlu kuralı belirle
   
3. Kuralı devre dışı bırak
   /policy disable <rule_id> reason:"False positive krizi"
   
4. Etkilenen kullanıcıları belirle
   /cases list rule:<rule_id> since:1h
   
5. Toplu geri alma başlat
   /review bulk-overturn rule:<rule_id> since:1h
```

### 4.3 Kullanıcı İletişimi
```
1. #announcements'a açıklama yaz:
   "Teknik bir hata nedeniyle bazı kullanıcılar 
    yanlışlıkla zaman aşımına uğradı. 
    Özür dileriz, düzeltiliyor."

2. Etkilenen kullanıcılara DM:
   "Size uygulanan işlem hatalıydı. 
    Özür dileriz. İşlem geri alındı."

3. Ticket açmış olanları bilgilendir
```

### 4.4 Kök Neden Analizi
```
□ Hangi kural sorunlu?
□ Kural mantığı mı hatalı?
□ Threshold çok mu düşük?
□ Exception eksik mi?
□ Yeni bir pattern mi ortaya çıktı?
```

### 4.5 Düzeltme
```
1. Kuralı düzelt
   /policy import (düzeltilmiş JSON)

2. Küçük ölçekte test et
   - Sadece 1 kanalda aktif et
   - 24 saat monitor et
   
3. Tam aktive et
   /policy enable <rule_id>

4. Incident raporu hazırla
```

---

## 5. SAFE MODE PROSEDÜRÜ

### 5.1 Safe Mode Nedir?
- Tüm **otomatik enforcement** durdurulur
- Bot sadece **log tutar** ve **ticket işler**
- İnsan müdahalesi gerektiğinde kullanılır

### 5.2 Safe Mode Başlatma
**Ne Zaman:**
- Büyük çaplı false positive
- Bot davranışı şüpheli
- Kritik bug tespit edildi
- Acil maintenance gerekli

**Komut (Owner Only):**
```
/safe-mode enable reason:"False positive krizi araştırılıyor"
```

### 5.3 Safe Mode Sırasında
```
✓ Loglama çalışır
✓ Ticket sistemi çalışır
✓ Metrics toplanır
✓ Risk scoring hesaplanır (uygulanmaz)

✗ Otomatik delete yok
✗ Otomatik timeout/kick/ban yok
✗ Otomatik lockdown yok
✗ Slowmode otomasyonu yok
```

### 5.4 Manuel Müdahale (Safe Mode'da)
```
Owner gerekirse manuel aksiyon alabilir:
/owner-override ban user:@spammer reason:"Manuel raid müdahale"

Bu aksiyon:
- Audit log'a yazılır
- Case oluşturur (decided_by = owner_id)
- Normal akış takip eder
```

### 5.5 Safe Mode Sonlandırma
```
1. Sorun çözüldüğünden emin ol
2. Kuralları gözden geçir
3. Test et (dry-run)
4. Safe mode kapat:
   /safe-mode disable
   
5. Gradual rollout:
   - İlk 1 saat yakın monitor
   - Anormallik yok ise normal operasyon
```

---

## 6. INCIDENT RESPONSE

### 6.1 Incident Seviyeleri

| Seviye | Açıklama | Response Time | Escalation |
|--------|----------|---------------|------------|
| P1 | Bot tamamen down | 15 dakika | Owner + Tüm ekip |
| P2 | Kritik fonksiyon bozuk | 1 saat | OpsAdmin |
| P3 | Minör sorun | 4 saat | Triage |
| P4 | Kozmetik/iyileştirme | Sonraki sprint | - |

### 6.2 P1 Incident Prosedürü
```
1. [İlk Tespit Eden] 
   #incident-response kanalına yaz
   @Owner @OpsAdmin "P1: Bot yanıt vermiyor"
   
2. [OpsAdmin - 5 dakika]
   Bot health check:
   - Discord API durumu kontrol
   - Container logs kontrol
   - Database bağlantı kontrol
   
3. [OpsAdmin - 15 dakika]
   İlk müdahale:
   - Container restart
   - Shard restart
   - Database failover
   
4. [Owner - Gerekirse]
   Safe mode aktive
   Manuel müdahale başlat
   
5. [Post-Incident]
   RCA (Root Cause Analysis) hazırla
   Önlem listesi oluştur
```

### 6.3 Incident Kaydı
```
Her incident için:
- Incident ID
- Başlangıç zamanı
- Tespit zamanı
- Çözüm zamanı
- Etki (kaç kullanıcı?)
- Kök neden
- Düzeltici aksiyonlar
- Tekrar önleme planı
```

---

## 7. BOT KESİNTİ PROSEDÜRÜ

### 7.1 Planlı Kesinti
```
1. 24 saat önce duyuru:
   #announcements: "Bot bakımı: [tarih] [saat] - [süre]"
   
2. 1 saat önce hatırlatma
   
3. Kesinti öncesi:
   - Aktif ticket'ları bilgilendir
   - Lockdown KALDIR (manuel olarak yönetilemez)
   - Son durum kaydet
   
4. Kesinti sırasında:
   - Owner sunucuda olmalı
   - Kritik durum için Discord moderasyonu kullan
   
5. Kesinti sonrası:
   - Health check
   - Sync commands
   - Backlog işle
```

### 7.2 Plansız Kesinti
```
1. Tespit:
   - Monitoring alertleri
   - Kullanıcı raporları
   
2. Değerlendirme:
   - Sebep: Kod hatası? Infra? Discord API?
   - Tahmini çözüm süresi
   
3. İletişim:
   #announcements: "Bot geçici olarak devre dışı. Üzerinde çalışıyoruz."
   
4. Çözüm:
   - Restart dene
   - Rollback gerekli mi?
   - Discord support gerekli mi?
   
5. Dönüş:
   - Health check
   - Backlog işle
   - Post-mortem yaz
```

---

## 8. GÜNLÜK / HAFTALIK İŞLEMLER

### 8.1 Günlük Rutin (OpsAdmin)
```
Sabah (09:00):
□ Gece boyunca tetiklenen alertleri incele
□ Review queue kontrolü
□ Aktif lockdown var mı?

Öğlen (13:00):
□ Heat map kontrolü
□ Yüksek riskli kullanıcı listesi

Akşam (18:00):
□ Günlük özet raporu
□ Bekleyen ticket'lar
□ Ertesi gün planlaması
```

### 8.2 Haftalık Rutin (OpsAdmin)
```
Pazartesi:
□ Geçen hafta raporu incele
□ Policy değişiklikleri planla

Çarşamba:
□ Triage/Reviewer performans kontrolü
□ Backlog temizliği

Cuma:
□ Güncellenecek policy'ler deploy
□ Hafta sonu planı (coverage)

Pazar (otomatik):
□ Haftalık rapor oluşturulur
□ Evidence cleanup çalışır
□ Risk score decay uygulanır
```

### 8.3 Aylık Rutin
```
□ Full policy review
□ Threshold optimization
□ False positive analizi
□ Abuse pattern analizi
□ Team retrospective
□ Yol haritası güncelleme
```

---

## HIZLI REFERANS

### Acil Durum Komutları
```
# Lockdown
/governance lockdown enable reason:"<sebep>"
/governance lockdown disable

# Safe Mode
/safe-mode enable reason:"<sebep>"
/safe-mode disable

# Policy Acil
/policy disable <rule_id> reason:"<sebep>"

# Bulk Overturn
/review bulk-overturn rule:<rule_id> since:1h
```

### İletişim Şablonları

**Lockdown Duyurusu:**
```
🔒 **GÜVENLİK MODU AKTİF**

Sunucumuz şu anda yükseltilmiş güvenlik modunda.
Yeni üyeler geçici olarak kısıtlı erişime sahip.

Normal operasyonlara en kısa sürede döneceğiz.
Anlayışınız için teşekkürler.
```

**False Positive Özrü:**
```
⚠️ **Teknik Hata Bildirimi**

Sistemimizde yaşanan bir hata nedeniyle bazı 
kullanıcılarımız yanlışlıkla kısıtlamaya uğradı.

Etkilenen tüm kullanıcıların kısıtlamaları kaldırıldı.
Özür diler, anlayışınız için teşekkür ederiz.
```

**Maintenance Duyurusu:**
```
🔧 **Planlı Bakım**

📅 Tarih: [tarih]
⏰ Saat: [saat] - [saat]
⏱️ Tahmini Süre: [süre]

Bu süre zarfında bot geçici olarak devre dışı olacaktır.
Sorun için: [destek kanalı]
```
