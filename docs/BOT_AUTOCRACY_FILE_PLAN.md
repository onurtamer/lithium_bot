# (B) DOSYA/FOLDER PLANLAMAASI

## Mevcut Yapı (KORUNACAK)
```
lithium_bot/
├── apps/
│   ├── api/              # FastAPI Backend
│   ├── bot/              # Discord.py Bot
│   └── dashboard/        # Django+HTMX Dashboard
├── lithium_core/         # Shared Core
│   ├── database/
│   └── models/
├── alembic/              # Migrations
├── docker-compose.yml
└── docker-compose.prod.yml
```

## Yeni Eklenen Modüller

```
lithium_bot/
├── apps/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── policies.py        # [NEW] Policy CRUD endpoints
│   │   │   ├── cases.py           # [NEW] Case management
│   │   │   ├── tickets.py         # [UPDATE] Enhanced ticket endpoints
│   │   │   ├── governance.py      # [NEW] Governance config endpoints
│   │   │   ├── metrics.py         # [NEW] Reports & metrics
│   │   │   └── review_queue.py    # [NEW] Review queue management
│   │   └── middleware/
│   │       └── governance_rbac.py # [NEW] Role-based access
│   │
│   ├── bot/
│   │   ├── main.py                # [UPDATE] AutoShardedClient
│   │   ├── sharding.py            # [NEW] Shard manager
│   │   ├── cogs/
│   │   │   ├── governance/        # [NEW] Governance module
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pipeline.py    # Event pipeline
│   │   │   │   ├── risk_scoring.py
│   │   │   │   ├── policy_engine.py
│   │   │   │   ├── action_dispatch.py
│   │   │   │   ├── progressive_discipline.py
│   │   │   │   └── safe_mode.py
│   │   │   ├── noise_governor.py  # [NEW] Rate limiting
│   │   │   ├── newcomer_gate.py   # [NEW] Newcomer flow
│   │   │   ├── social_temp.py     # [NEW] Channel heat
│   │   │   ├── raid_protection.py # [NEW] Enhanced raid
│   │   │   ├── coordinated_spam.py# [NEW] Cluster detection
│   │   │   └── tickets_v2.py      # [NEW] Enhanced tickets
│   │   ├── services/
│   │   │   ├── idempotency.py     # [NEW] Event dedup
│   │   │   ├── case_service.py    # [NEW] Case management
│   │   │   ├── audit_service.py   # [NEW] Audit logging
│   │   │   └── queue_service.py   # [NEW] Task queue
│   │   └── utils/
│   │       ├── backpressure.py    # [NEW] Load management
│   │       └── evidence.py        # [NEW] Evidence capture
│   │
│   └── dashboard/
│       ├── governance/            # [NEW] Governance app
│       │   ├── views/
│       │   │   ├── review_queue.py
│       │   │   ├── ticket_board.py
│       │   │   ├── policy_editor.py
│       │   │   ├── heat_map.py
│       │   │   └── weekly_report.py
│       │   └── templates/
│       │       └── governance/
│       └── static/
│           └── js/
│               └── governance.js
│
├── lithium_core/
│   ├── database/
│   │   └── session.py             # [EXISTS]
│   ├── models/
│   │   ├── __init__.py            # [UPDATE]
│   │   ├── governance.py          # [NEW] Governance models
│   │   ├── policies.py            # [NEW] Policy models
│   │   ├── risk.py                # [NEW] Risk scoring models
│   │   ├── cases.py               # [NEW] Case models
│   │   ├── tickets_v2.py          # [NEW] Enhanced tickets
│   │   ├── audit.py               # [NEW] Audit models
│   │   └── events.py              # [NEW] Event ingestion
│   └── services/
│       ├── __init__.py
│       ├── policy_service.py      # [NEW] Policy evaluation
│       ├── risk_service.py        # [NEW] Risk calculation
│       ├── case_service.py        # [NEW] Case management
│       └── governance_service.py  # [NEW] Governance config
│
├── alembic/
│   └── versions/
│       └── xxx_bot_autocracy.py   # [NEW] Migration
│
├── config/
│   ├── policies/                  # [NEW] Default policies
│   │   ├── spam.json
│   │   ├── toxicity.json
│   │   ├── phishing.json
│   │   └── raid.json
│   └── governance.yaml            # [NEW] Default config
│
├── docs/
│   ├── BOT_AUTOCRACY_ARCHITECTURE.md    # [NEW]
│   ├── BOT_AUTOCRACY_FILE_PLAN.md       # [NEW] This file
│   ├── POLICY_DSL.md                    # [NEW]
│   ├── RUNBOOK.md                       # [NEW]
│   └── LOAD_TEST.md                     # [NEW]
│
└── tests/
    ├── governance/
    │   ├── test_pipeline.py
    │   ├── test_risk_scoring.py
    │   ├── test_policy_engine.py
    │   └── test_raid_sim.py
    └── load/
        └── raid_simulation.py
```

## Modül Bağımlılıkları

```
┌─────────────────────────────────────────────────────────────┐
│                      DEPENDENCY GRAPH                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  lithium_core/models/governance.py                          │
│       ↑                                                      │
│  lithium_core/services/policy_service.py                    │
│       ↑                                                      │
│  apps/bot/cogs/governance/policy_engine.py                  │
│       ↑                                                      │
│  apps/bot/cogs/governance/pipeline.py                       │
│       ↑                                                      │
│  apps/bot/main.py (AutoShardedClient)                       │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  lithium_core/models/risk.py                                │
│       ↑                                                      │
│  lithium_core/services/risk_service.py                      │
│       ↑                                                      │
│  apps/bot/cogs/governance/risk_scoring.py                   │
│       ↑                                                      │
│  apps/bot/cogs/governance/policy_engine.py                  │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  lithium_core/models/cases.py                               │
│       ↑                                                      │
│  lithium_core/services/case_service.py                      │
│       ↑                                                      │
│  apps/bot/cogs/governance/action_dispatch.py                │
│       ↑                                                      │
│  apps/api/routers/cases.py                                  │
│       ↑                                                      │
│  apps/dashboard/governance/views/review_queue.py            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Konfigürasyon Dosyaları

### config/governance.yaml
```yaml
sharding:
  enabled: true
  shard_count: auto  # veya sayı
  
rate_limits:
  user_message_per_minute: 30
  user_mention_per_minute: 10
  channel_message_burst: 50
  
newcomer:
  duration_hours: 24
  min_messages: 10
  restricted_channels: ["new-members"]
  
lockdown:
  join_threshold_per_minute: 20
  auto_verify: true
  
progressive_discipline:
  levels:
    - action: nudge
      threshold: 0.3
    - action: warn
      threshold: 0.5
    - action: delete
      threshold: 0.6
    - action: timeout_1m
      threshold: 0.7
    - action: timeout_10m
      threshold: 0.75
    - action: timeout_1h
      threshold: 0.8
    - action: kick
      threshold: 0.85
    - action: tempban_1d
      threshold: 0.9
    - action: ban
      threshold: 0.95

evidence:
  retention_days: 90
  snippet_max_length: 500
  hash_algorithm: sha256
```
