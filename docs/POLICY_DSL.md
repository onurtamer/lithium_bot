# (C) POLICY DSL ŞEMASI + 12 HAZIR KURAL

## Policy DSL JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Lithium Bot Policy",
  "type": "object",
  "required": ["rule_id", "name", "version", "enabled", "trigger", "conditions", "actions"],
  "properties": {
    "rule_id": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$",
      "description": "Unique identifier for the rule"
    },
    "name": {
      "type": "string",
      "description": "Human-readable name"
    },
    "description": {
      "type": "string"
    },
    "version": {
      "type": "integer",
      "minimum": 1
    },
    "enabled": {
      "type": "boolean"
    },
    "priority": {
      "type": "integer",
      "minimum": 0,
      "maximum": 1000,
      "default": 500
    },
    "trigger": {
      "type": "object",
      "required": ["event_types"],
      "properties": {
        "event_types": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["message", "member_join", "member_leave", "reaction", "voice_state", "invite_create"]
          }
        },
        "channels": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Channel IDs (empty = all)"
        },
        "exclude_channels": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "conditions": {
      "type": "object",
      "properties": {
        "content_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": {"enum": ["regex", "keyword", "fuzzy", "domain", "tld"]},
              "value": {"type": "string"},
              "case_sensitive": {"type": "boolean", "default": false}
            }
          }
        },
        "rate_limit": {
          "type": "object",
          "properties": {
            "count": {"type": "integer"},
            "window_seconds": {"type": "integer"},
            "scope": {"enum": ["user", "channel", "guild"]}
          }
        },
        "user_criteria": {
          "type": "object",
          "properties": {
            "account_age_days_lt": {"type": "integer"},
            "server_age_hours_lt": {"type": "integer"},
            "has_avatar": {"type": "boolean"},
            "is_newcomer": {"type": "boolean"},
            "risk_score_gt": {"type": "number"}
          }
        },
        "content_criteria": {
          "type": "object",
          "properties": {
            "mention_count_gt": {"type": "integer"},
            "link_count_gt": {"type": "integer"},
            "attachment_count_gt": {"type": "integer"},
            "caps_percentage_gt": {"type": "integer"},
            "zalgo_detected": {"type": "boolean"},
            "emoji_flood_gt": {"type": "integer"}
          }
        },
        "coordination": {
          "type": "object",
          "properties": {
            "similar_messages_count": {"type": "integer"},
            "similar_messages_window_seconds": {"type": "integer"},
            "similarity_threshold": {"type": "number"}
          }
        }
      }
    },
    "risk_weight": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Weight contribution to risk score"
    },
    "threshold": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Score threshold to trigger action"
    },
    "actions": {
      "type": "object",
      "properties": {
        "immediate": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": {"enum": ["delete", "nudge", "warn", "timeout", "kick", "ban", "tempban", "add_role", "remove_role", "lockdown", "slowmode"]},
              "duration_seconds": {"type": "integer"},
              "role_id": {"type": "string"},
              "message": {"type": "string"},
              "dm_user": {"type": "boolean"}
            }
          }
        },
        "escalation": {
          "type": "object",
          "properties": {
            "after_violations": {"type": "integer"},
            "within_hours": {"type": "integer"},
            "escalate_to": {"type": "string", "description": "Next action type"}
          }
        },
        "review_queue": {
          "type": "boolean",
          "description": "Send to human review instead of immediate action"
        }
      }
    },
    "exceptions": {
      "type": "object",
      "properties": {
        "roles": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Role IDs exempt from this rule"
        },
        "users": {
          "type": "array",
          "items": {"type": "string"}
        },
        "channels": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "cooldown": {
      "type": "object",
      "properties": {
        "user_seconds": {"type": "integer"},
        "global_seconds": {"type": "integer"}
      }
    },
    "evidence_capture": {
      "type": "object",
      "properties": {
        "capture_message": {"type": "boolean"},
        "capture_attachments": {"type": "boolean"},
        "capture_context_messages": {"type": "integer"},
        "retention_days": {"type": "integer"}
      }
    }
  }
}
```

---

## 12 HAZIR KURAL ÖRNEĞİ

### 1. spam_flood - Mesaj Flood Koruması
```json
{
  "rule_id": "spam_flood",
  "name": "Message Flood Protection",
  "description": "Detects users sending too many messages in short time",
  "version": 1,
  "enabled": true,
  "priority": 900,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "rate_limit": {
      "count": 7,
      "window_seconds": 5,
      "scope": "user"
    }
  },
  "risk_weight": 0.8,
  "threshold": 0.6,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "timeout", "duration_seconds": 60, "dm_user": true, "message": "Çok hızlı mesaj attığınız için 1 dakika susturuldunuz."}
    ],
    "escalation": {
      "after_violations": 3,
      "within_hours": 1,
      "escalate_to": "timeout_600"
    }
  },
  "exceptions": {
    "roles": ["OpsAdmin", "Triage", "Reviewer"]
  },
  "cooldown": {
    "user_seconds": 60
  },
  "evidence_capture": {
    "capture_message": true,
    "capture_context_messages": 3,
    "retention_days": 30
  }
}
```

### 2. mention_spam - Mention Flood
```json
{
  "rule_id": "mention_spam",
  "name": "Mention Spam Protection",
  "description": "Detects excessive mentions in a single message",
  "version": 1,
  "enabled": true,
  "priority": 850,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_criteria": {
      "mention_count_gt": 5
    }
  },
  "risk_weight": 0.9,
  "threshold": 0.5,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "warn", "message": "Toplu mention yasaktır."}
    ],
    "escalation": {
      "after_violations": 2,
      "within_hours": 24,
      "escalate_to": "timeout_3600"
    }
  },
  "cooldown": {
    "user_seconds": 30
  },
  "evidence_capture": {
    "capture_message": true,
    "retention_days": 30
  }
}
```

### 3. phishing_link - Phishing Tespiti
```json
{
  "rule_id": "phishing_link",
  "name": "Phishing Link Detection",
  "description": "Detects known phishing domains and patterns",
  "version": 1,
  "enabled": true,
  "priority": 1000,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_patterns": [
      {"type": "domain", "value": "discord.gift"},
      {"type": "domain", "value": "discordgift.com"},
      {"type": "domain", "value": "discord.gg.scam"},
      {"type": "domain", "value": "steamcommunity.ru"},
      {"type": "regex", "value": "disc[o0]rd[^.]*\\.(gift|click|gg)"},
      {"type": "regex", "value": "(?:free|nitro|steam)[^\\s]*\\.(com|gift|gg)"}
    ]
  },
  "risk_weight": 1.0,
  "threshold": 0.3,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "tempban", "duration_seconds": 86400, "dm_user": true, "message": "Phishing linki paylaştığınız için 24 saat yasaklandınız."}
    ]
  },
  "evidence_capture": {
    "capture_message": true,
    "capture_attachments": true,
    "retention_days": 90
  }
}
```

### 4. toxicity_keywords - Küfür/Hakaret
```json
{
  "rule_id": "toxicity_keywords",
  "name": "Toxicity Keyword Filter",
  "description": "Detects toxic language and slurs",
  "version": 1,
  "enabled": true,
  "priority": 800,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_patterns": [
      {"type": "keyword", "value": "orospu", "case_sensitive": false},
      {"type": "keyword", "value": "piç", "case_sensitive": false},
      {"type": "keyword", "value": "amk", "case_sensitive": false},
      {"type": "keyword", "value": "sikik", "case_sensitive": false},
      {"type": "regex", "value": "\\b(amcık|yarrak|göt|pezevenk)\\b"}
    ]
  },
  "risk_weight": 0.7,
  "threshold": 0.5,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "warn", "message": "Küfür/hakaret yasaktır."}
    ],
    "escalation": {
      "after_violations": 3,
      "within_hours": 24,
      "escalate_to": "timeout_3600"
    }
  },
  "cooldown": {
    "user_seconds": 10
  },
  "evidence_capture": {
    "capture_message": true,
    "retention_days": 30
  }
}
```

### 5. raid_join_flood - Raid Koruma
```json
{
  "rule_id": "raid_join_flood",
  "name": "Raid Join Flood Detection",
  "description": "Detects mass joins indicating a raid",
  "version": 1,
  "enabled": true,
  "priority": 950,
  "trigger": {
    "event_types": ["member_join"]
  },
  "conditions": {
    "rate_limit": {
      "count": 15,
      "window_seconds": 60,
      "scope": "guild"
    }
  },
  "risk_weight": 1.0,
  "threshold": 0.8,
  "actions": {
    "immediate": [
      {"type": "lockdown"},
      {"type": "add_role", "role_id": "NEWCOMER_ROLE"}
    ]
  },
  "evidence_capture": {
    "capture_message": false,
    "retention_days": 90
  }
}
```

### 6. newcomer_link - Yeni Üye Link Koruması
```json
{
  "rule_id": "newcomer_link",
  "name": "Newcomer Link Restriction",
  "description": "Prevents new users from posting links",
  "version": 1,
  "enabled": true,
  "priority": 700,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "user_criteria": {
      "is_newcomer": true
    },
    "content_criteria": {
      "link_count_gt": 0
    }
  },
  "risk_weight": 0.6,
  "threshold": 0.4,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "nudge", "message": "Yeni üyeler henüz link paylaşamaz. Verified statüsü kazandıktan sonra paylaşabilirsiniz."}
    ]
  },
  "evidence_capture": {
    "capture_message": true,
    "retention_days": 7
  }
}
```

### 7. caps_abuse - Büyük Harf Spamı
```json
{
  "rule_id": "caps_abuse",
  "name": "Caps Lock Abuse",
  "description": "Detects excessive use of capital letters",
  "version": 1,
  "enabled": true,
  "priority": 400,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_criteria": {
      "caps_percentage_gt": 70
    }
  },
  "risk_weight": 0.3,
  "threshold": 0.5,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "nudge", "message": "Lütfen büyük harf flood yapmayın."}
    ]
  },
  "cooldown": {
    "user_seconds": 60
  }
}
```

### 8. invite_spam - Davet Linki Spam
```json
{
  "rule_id": "invite_spam",
  "name": "Discord Invite Spam",
  "description": "Prevents unauthorized Discord invites",
  "version": 1,
  "enabled": true,
  "priority": 750,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_patterns": [
      {"type": "regex", "value": "discord\\.gg\\/[a-zA-Z0-9]+"},
      {"type": "regex", "value": "discord\\.com\\/invite\\/[a-zA-Z0-9]+"}
    ]
  },
  "risk_weight": 0.6,
  "threshold": 0.5,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "warn", "message": "İzinsiz sunucu reklamı yasaktır."}
    ],
    "escalation": {
      "after_violations": 2,
      "within_hours": 24,
      "escalate_to": "kick"
    }
  },
  "exceptions": {
    "channels": ["REKLAM_CHANNEL_ID"]
  },
  "evidence_capture": {
    "capture_message": true,
    "retention_days": 30
  }
}
```

### 9. new_account_suspicious - Şüpheli Yeni Hesap
```json
{
  "rule_id": "new_account_suspicious",
  "name": "Suspicious New Account",
  "description": "Flags very new accounts with no avatar",
  "version": 1,
  "enabled": true,
  "priority": 600,
  "trigger": {
    "event_types": ["member_join"]
  },
  "conditions": {
    "user_criteria": {
      "account_age_days_lt": 7,
      "has_avatar": false
    }
  },
  "risk_weight": 0.5,
  "threshold": 0.7,
  "actions": {
    "immediate": [
      {"type": "add_role", "role_id": "QUARANTINE_ROLE"}
    ],
    "review_queue": true
  },
  "evidence_capture": {
    "retention_days": 30
  }
}
```

### 10. emoji_flood - Emoji Spamı
```json
{
  "rule_id": "emoji_flood",
  "name": "Emoji Flood Detection",
  "description": "Detects messages with excessive emojis",
  "version": 1,
  "enabled": true,
  "priority": 350,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_criteria": {
      "emoji_flood_gt": 15
    }
  },
  "risk_weight": 0.3,
  "threshold": 0.5,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "nudge", "message": "Emoji spam yapmayın."}
    ]
  },
  "cooldown": {
    "user_seconds": 30
  }
}
```

### 11. coordinated_message - Koordineli Saldırı
```json
{
  "rule_id": "coordinated_message",
  "name": "Coordinated Message Attack",
  "description": "Detects multiple users posting similar messages",
  "version": 1,
  "enabled": true,
  "priority": 900,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "coordination": {
      "similar_messages_count": 5,
      "similar_messages_window_seconds": 30,
      "similarity_threshold": 0.85
    }
  },
  "risk_weight": 0.95,
  "threshold": 0.6,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "timeout", "duration_seconds": 600}
    ]
  },
  "evidence_capture": {
    "capture_message": true,
    "capture_context_messages": 10,
    "retention_days": 90
  }
}
```

### 12. zalgo_abuse - Zalgo/Unicode Bozulması
```json
{
  "rule_id": "zalgo_abuse",
  "name": "Zalgo Text Abuse",
  "description": "Detects zalgo and unicode abuse for visual disruption",
  "version": 1,
  "enabled": true,
  "priority": 500,
  "trigger": {
    "event_types": ["message"]
  },
  "conditions": {
    "content_criteria": {
      "zalgo_detected": true
    }
  },
  "risk_weight": 0.5,
  "threshold": 0.5,
  "actions": {
    "immediate": [
      {"type": "delete"},
      {"type": "warn", "message": "Zalgo/bozuk metin kullanımı yasaktır."}
    ]
  },
  "evidence_capture": {
    "capture_message": true,
    "retention_days": 14
  }
}
```

---

## POLICY LOADING EXAMPLE

```python
import json
from pathlib import Path

def load_policies(policy_dir: Path) -> list:
    """Load all policy JSON files from directory"""
    policies = []
    for policy_file in policy_dir.glob("*.json"):
        with open(policy_file) as f:
            policy = json.load(f)
            if policy.get("enabled", False):
                policies.append(policy)
    
    # Sort by priority (higher first)
    policies.sort(key=lambda p: p.get("priority", 500), reverse=True)
    return policies
```
