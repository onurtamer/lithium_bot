# 🤖 Bot-Otokrasi: Mimari ve Tasarım Belgesi

## (A) MODÜL/MİMARİ DİYAGRAMI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DISCORD GATEWAY (Sharded)                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                    │
│  │ Shard 0 │ │ Shard 1 │ │ Shard 2 │ │ Shard N │ │   ...   │                    │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘                    │
└───────┼──────────┼──────────┼──────────┼──────────┼─────────────────────────────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EVENT INGRESS PIPELINE                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│  │   Ingress    │──▶│  Normalize   │──▶│ Idempotency  │──▶│  Rate Check  │      │
│  │  (Raw Event) │   │  + Enrich    │   │    Guard     │   │   (Noise)    │      │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘      │
│                                                                  │               │
│                                                                  ▼               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         FAST PATH (Low Latency)                           │   │
│  │  • Anti-Spam Rules          • Rate Limit Violations                       │   │
│  │  • Phishing Detection       • Raid Pattern Match                          │   │
│  │  • Mention Flood            • Known Bad Actors                            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                              │ (pass)              │ (violation)                │
│                              ▼                     ▼                            │
│  ┌──────────────────────────────────┐   ┌──────────────────────────────────┐   │
│  │      RISK SCORING ENGINE         │   │     IMMEDIATE ACTION QUEUE       │   │
│  │  • User Profile Score            │   │  • Delete Message                │   │
│  │  • Message Content Score         │   │  • Timeout User                  │   │
│  │  • Temporal Pattern Score        │   │  • Lockdown Trigger              │   │
│  │  • Coordination Score            │   └──────────────────────────────────┘   │
│  └──────────────────────────────────┘                                           │
│                              │                                                   │
│                              ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                       POLICY EVALUATION ENGINE                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐          │   │
│  │  │  Policy 1  │  │  Policy 2  │  │  Policy N  │  │ Exception  │          │   │
│  │  │  (Spam)    │  │  (Toxic)   │  │  (Custom)  │  │   Rules    │          │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                   │
│                 ┌────────────┴────────────┐                                     │
│                 ▼                         ▼                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                    │
│  │   CLEAR VIOLATION         │  │   UNCERTAIN (Grey Zone)   │                   │
│  │   → Action Dispatch       │  │   → Review Queue          │                   │
│  └──────────────────────────┘  └──────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                              │                         │
                              ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ACTION DISPATCH LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                    PROGRESSIVE DISCIPLINE LADDER                          │   │
│  │                                                                           │   │
│  │   ┌──────┐   ┌──────┐   ┌──────┐   ┌─────────┐   ┌──────┐   ┌─────────┐  │   │
│  │   │Nudge │──▶│ Warn │──▶│Delete│──▶│Timeout  │──▶│ Kick │──▶│TempBan  │  │   │
│  │   │      │   │      │   │      │   │(1m→1h→1d)│  │      │   │(1d→7d)  │  │   │
│  │   └──────┘   └──────┘   └──────┘   └─────────┘   └──────┘   └─────────┘  │   │
│  │                                                                     │     │   │
│  │                                                              ┌──────▼────┐│   │
│  │                                                              │ Perma Ban ││   │
│  │                                                              └───────────┘│   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       AUDIT & OBSERVABILITY LAYER                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                     │
│  │   Case Log     │  │  Audit Event   │  │   Metrics      │                     │
│  │  (PostgreSQL)  │  │    Stream      │  │  (Prometheus)  │                     │
│  └────────────────┘  └────────────────┘  └────────────────┘                     │
│          │                   │                   │                               │
│          ▼                   ▼                   ▼                               │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                      DISCORD CHANNELS                                   │     │
│  │  #mod-log (summary)  │  #audit-log (detail)  │  #alerts (critical)     │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TICKET SYSTEM (Human-in-Loop)                           │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         TICKET LIFECYCLE                                  │   │
│  │                                                                           │   │
│  │  ┌────────┐   ┌─────────┐   ┌───────────┐   ┌───────────┐   ┌────────┐   │   │
│  │  │ OPENED │──▶│ TRIAGED │──▶│NEEDS_INFO │──▶│ IN_REVIEW │──▶│DECIDED │   │   │
│  │  └────────┘   └─────────┘   └───────────┘   └───────────┘   └────────┘   │   │
│  │       │            │              │               │              │        │   │
│  │       │      (Triage Role)   (Bot asks)    (Reviewer Role)  (Bot acts)   │   │
│  │       │                                                           │        │   │
│  │       └───────────────────────────────────────────────────────────┘        │   │
│  │                               ▼                                            │   │
│  │                          ┌────────┐                                        │   │
│  │                          │ CLOSED │                                        │   │
│  │                          └────────┘                                        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  HUMAN ROLES (No Direct Enforcement):                                           │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐                                        │
│  │ Triage  │  │Reviewer │  │ OpsAdmin │                                        │
│  │ - Tag   │  │ - Vote  │  │ - Config │                                        │
│  │ - Route │  │ - Note  │  │ - Policy │                                        │
│  └─────────┘  └─────────┘  └──────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          API & DASHBOARD LAYER                                   │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐               │
│  │     FastAPI Backend         │  │   Django+HTMX Dashboard     │               │
│  │  • Policy CRUD              │  │  • Review Queue (Kanban)    │               │
│  │  • Case/Ticket Endpoints    │  │  • Ticket Board             │               │
│  │  • Metrics/Reports          │  │  • Policy Editor            │               │
│  │  • Governance Config        │  │  • Heat Map                 │               │
│  │  • RBAC Middleware          │  │  • Weekly Reports           │               │
│  └─────────────────────────────┘  └─────────────────────────────┘               │
│                 │                              │                                 │
│                 └──────────────┬───────────────┘                                 │
│                                ▼                                                 │
│                      ┌─────────────────┐                                        │
│                      │  PostgreSQL     │                                        │
│                      │  (Partitioned)  │                                        │
│                      └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## GOVERNANCE ROLE HIERARCHY

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISCORD SERVER ROLES                          │
├─────────────────────────────────────────────────────────────────┤
│  Position │ Role        │ Discord Perms    │ Bot Capabilities   │
├───────────┼─────────────┼──────────────────┼────────────────────┤
│  HIGHEST  │ Lithium Bot │ Administrator    │ ALL ENFORCEMENT    │
│     ↓     │ Owner       │ Administrator*   │ /safe-mode only    │
│     ↓     │ OpsAdmin    │ View Channels    │ /config, /policy   │
│     ↓     │ Triage      │ View Channels    │ /triage, /tag      │
│     ↓     │ Reviewer    │ View Channels    │ /review, /vote     │
│     ↓     │ Verified    │ Send Messages    │ Full access        │
│     ↓     │ Newcomer    │ Limited Send     │ Restricted         │
│  LOWEST   │ @everyone   │ Read Only        │ None               │
└─────────────────────────────────────────────────────────────────┘
* Owner: break-glass için tutulur, günlük kullanım yok
```

## EVENT PIPELINE DATA FLOW

```
Discord Event
     │
     ▼
┌─────────────────────────────────────────┐
│ 1. INGRESS                               │
│    • Receive raw event                   │
│    • Generate event_id (idempotency)     │
│    • Timestamp enrichment                │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 2. NORMALIZER                            │
│    • Extract: user_id, guild_id,         │
│      channel_id, content, attachments    │
│    • Compute: content_hash, length       │
│    • Tag: event_type                     │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 3. IDEMPOTENCY GUARD                     │
│    • Check event_id in Redis/memory      │
│    • If seen → DROP                      │
│    • If new → Mark as processed          │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 4. RATE CHECK (Noise Governor)           │
│    • User message rate (sliding window)  │
│    • Channel heat score                  │
│    • If OVER_LIMIT → Fast action         │
└─────────────────────────────────────────┘
     │
     ├──────────────────────────────────────┐
     ▼ (pass)                              ▼ (violation)
┌─────────────────────────┐    ┌─────────────────────────┐
│ 5. RISK SCORING          │    │ FAST PATH ACTION        │
│    • user_risk            │    │ • Delete message        │
│    • content_risk         │    │ • Short timeout         │
│    • temporal_risk        │    │ • Rate limit response   │
│    • coordination_risk    │    └─────────────────────────┘
│    → combined_score       │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 6. POLICY EVALUATION                     │
│    • Match against active policies       │
│    • Check exceptions (roles, channels)  │
│    • Check cooldown (user + rule)        │
│    • Determine action or review          │
└─────────────────────────────────────────┘
     │
     ├──────────────────────────────────────┐
     ▼ (clear violation)                   ▼ (uncertain)
┌─────────────────────────┐    ┌─────────────────────────┐
│ 7a. ACTION DISPATCH      │    │ 7b. REVIEW QUEUE        │
│     • Select action       │    │     • Create ticket     │
│     • Apply progressive   │    │     • Attach evidence   │
│     • Create case         │    │     • Notify Triage     │
│     • Log audit event     │    └─────────────────────────┘
└─────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 8. DISCORD API DISPATCH                  │
│    • Execute action (timeout/kick/ban)   │
│    • Send DM to user (if applicable)     │
│    • Post to mod-log channel             │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 9. AUDIT & METRICS                       │
│    • Write to audit_events table         │
│    • Increment Prometheus counters       │
│    • Update user_risk_profile            │
└─────────────────────────────────────────┘
```
