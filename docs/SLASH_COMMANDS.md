# (E) SLASH KOMUTLARI LİSTESİ

## GOVERNANCE KATEGORİSİ

### Owner Komutları (Break-Glass)
| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `/safe-mode enable` | Bot enforcement'ı durdurur, sadece log + ticket | `reason: str` |
| `/safe-mode disable` | Normal enforcement'a döner | - |
| `/safe-mode status` | Mevcut durumu gösterir | - |
| `/owner-override <action>` | Acil durum için manuel aksiyon | `user: Member`, `action: str`, `reason: str` |

### OpsAdmin Komutları (Konfigürasyon)
| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `/governance config` | Governance ayarlarını görüntüle | - |
| `/governance set <key> <value>` | Ayar değiştir | `key: str`, `value: str` |
| `/governance lockdown enable` | Manuel lockdown başlat | `reason: str`, `duration: str` |
| `/governance lockdown disable` | Lockdown kaldır | - |
| `/policy list` | Aktif politikaları listele | `page: int = 1` |
| `/policy view <rule_id>` | Politika detayı | `rule_id: str` |
| `/policy enable <rule_id>` | Politikayı aktifleştir | `rule_id: str` |
| `/policy disable <rule_id>` | Politikayı devre dışı bırak | `rule_id: str`, `reason: str` |
| `/policy import` | JSON'dan politika yükle | `attachment: Attachment` |
| `/policy export <rule_id>` | Politikayı JSON olarak indir | `rule_id: str` |
| `/threshold set <type> <value>` | Eşik değeri ayarla | `type: str`, `value: int` |
| `/roles setup` | Governance rollerini oluştur | - |
| `/channels setup` | Log kanallarını oluştur | - |
| `/weekly-report generate` | Manuel haftalık rapor | - |
| `/metrics dashboard` | Anlık metrikleri göster | - |

### Triage Komutları (Ticket Yönlendirme)
| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `/ticket view <ticket_id>` | Ticket detayı | `ticket_id: str` |
| `/ticket assign <ticket_id>` | Kendine ata | `ticket_id: str` |
| `/ticket transfer <ticket_id> <user>` | Başkasına transfer et | `ticket_id: str`, `user: Member` |
| `/ticket tag <ticket_id> <tag>` | Etiket ekle | `ticket_id: str`, `tag: str` |
| `/ticket priority <ticket_id> <level>` | Öncelik ayarla | `ticket_id: str`, `level: int (1-10)` |
| `/ticket request-info <ticket_id>` | Kullanıcıdan bilgi iste | `ticket_id: str`, `question: str` |
| `/ticket add-note <ticket_id>` | Internal not ekle | `ticket_id: str`, `note: str` |
| `/ticket escalate <ticket_id>` | Reviewer'a yükselt | `ticket_id: str`, `reason: str` |
| `/queue triage` | Bekleyen ticket'ları listele | `status: str = 'opened'` |

### Reviewer Komutları (Karar)
| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `/review queue` | Review bekleyen case/ticket | `type: str = 'all'` |
| `/review case <case_id>` | Case detayı + evidence | `case_id: str` |
| `/review vote <case_id> <decision>` | Karar ver | `case_id: str`, `decision: approve/deny/overturn` |
| `/review context <case_id>` | Bağlam notu ekle | `case_id: str`, `context: str` |
| `/appeal view <ticket_id>` | Appeal detayı | `ticket_id: str` |
| `/appeal decide <ticket_id> <decision>` | Appeal kararı | `ticket_id: str`, `decision: accept/reject`, `reason: str` |

---

## KULLANICI KOMUTLARİ (Herkes)

### Raporlama
| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `/report user <user>` | Kullanıcı rapor et | `user: Member`, `reason: str`, `evidence: Attachment?` |
| `/report message` | Mesaj rapor et (context menu) | - |
| `/complaint` | Şikayet bildir | `subject: str`, `description: str` |
| `/request` | Özellik/etkinlik isteği | `type: feature/event`, `description: str` |
| `/appeal` | Ceza itirazı | `case_id: str?`, `reason: str` |

### Bilgi
| Komut | Açıklama | Parametreler |
|-------|----------|--------------|
| `/my-status` | Kendi risk durumunu gör | - |
| `/my-cases` | Kendi case geçmişi | `page: int = 1` |
| `/my-appeals` | Appeal durumları | - |
| `/rules` | Sunucu kurallarını göster | - |
| `/verify` | Doğrulama başlat (newcomer) | - |

---

## BOT İÇ KOMUTLARI (Otomatik)

### Event Handler Tetiklemeleri
| Event | Handler | Açıklama |
|-------|---------|----------|
| `on_message` | Pipeline.ingest | Mesaj analizi |
| `on_member_join` | Pipeline.ingest | Yeni üye analizi |
| `on_member_remove` | Audit.log | Ayrılma kaydı |
| `on_voice_state_update` | VoiceMonitor.check | Ses durumu |
| `on_raw_reaction_add` | VerifyHandler | Doğrulama |
| `on_guild_join` | Setup.initialize | Yeni sunucu kurulumu |

### Background Tasks
| Task | Interval | Açıklama |
|------|----------|----------|
| `risk_decay` | 1 hour | Risk score azalması |
| `heat_calculation` | 5 min | Kanal sıcaklık hesabı |
| `mute_expiry` | 1 min | Timeout süresi kontrolü |
| `lockdown_check` | 1 min | Lockdown süresi kontrolü |
| `evidence_cleanup` | 1 day | Eski evidence silme |
| `weekly_report` | Sunday 00:00 | Haftalık rapor oluşturma |
| `newcomer_promotion` | 1 hour | Newcomer → Verified kontrolü |

---

## KOMUT DETAYLARI

### /report user
```
Kullanım: /report user <user> <reason> [evidence]

Parametreler:
  user: @mention veya User ID (zorunlu)
  reason: Rapor sebebi (zorunlu, 10-1000 karakter)
  evidence: Ekran görüntüsü veya dosya (opsiyonel)

Çalışma:
  1. Ticket oluşturulur (type: report)
  2. Evidence varsa snapshot alınır
  3. Triage kuyruğuna eklenir
  4. Kullanıcıya ticket ID verilir

Kısıtlamalar:
  - Aynı kullanıcıyı 24h içinde max 3 kez raporlayabilir
  - Spam rapor tespit edilirse uyarı verilir
```

### /safe-mode enable
```
Kullanım: /safe-mode enable <reason>

Yetki: Owner only

Çalışma:
  1. governance_config.safe_mode_active = True
  2. Tüm auto-enforcement durdurulur
  3. Sadece logging ve ticket sistemi çalışır
  4. #alerts kanalına bildirim gider
  5. Audit event oluşturulur

Kullanım Senaryoları:
  - Yanlış pozitif kriz (çok fazla false positive)
  - Bot davranışı şüpheli
  - Acil maintenance
```

### /governance lockdown enable
```
Kullanım: /governance lockdown enable <reason> [duration]

Parametreler:
  reason: Lockdown sebebi (zorunlu)
  duration: Süre (opsiyonel, default: 1h, max: 24h)

Çalışma:
  1. governance_config.lockdown_active = True
  2. Tüm yeni üyelere NEWCOMER rol verilir
  3. Link/mention/attachment izinleri kısıtlanır
  4. #new-members dışında yazma engeli
  5. Doğrulama zorunlu hale gelir
  6. Heat threshold düşürülür

Auto-Trigger:
  - raid_join_threshold aşılırsa otomatik başlar
```

### /policy import
```
Kullanım: /policy import (JSON dosyası eklenerek)

Yetki: OpsAdmin

Çalışma:
  1. JSON schema validation
  2. rule_id benzersizlik kontrolü
  3. policy_versions'a eski versiyon kaydedilir
  4. policies tablosuna yeni versiyon yazılır
  5. Cache invalidate edilir
  6. Audit event oluşturulur

Güvenlik:
  - actions.immediate içinde ban/kick varsa warning gösterilir
  - Yüksek priority kurallar için onay istenir
```

### /review vote
```
Kullanım: /review vote <case_id> <decision> [reason]

Parametreler:
  case_id: Case ID (zorunlu)
  decision: approve | deny | overturn (zorunlu)
  reason: Karar gerekçesi (overturn için zorunlu)

Kararlar:
  - approve: Bot kararı onaylanır, case kapatılır
  - deny: Case reddedilir, aksiyon uygulanmaz
  - overturn: Uygulanan aksiyon geri alınır

overturn için:
  1. Uygulanan aksiyon geri alınır (unban, role restore, vb)
  2. User risk score düşürülür
  3. Kullanıcıya özür DM gönderilir
  4. Haftalık rapora "false positive" olarak eklenir
```
