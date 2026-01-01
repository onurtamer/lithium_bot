# (G) LOAD TEST VE RAID SİMÜLASYON SENARYOLARI

## 1. LOAD TEST SENARYOLARI

### 1.1 Normal Trafik Baseline
```yaml
scenario: normal_traffic
description: "Normal gün içi trafiği simüle et"
duration: 30m
users: 100

patterns:
  - type: message
    rate: 10/second
    content_types:
      - text: 80%
      - link: 10%
      - image: 8%
      - mention: 2%
    
  - type: member_join
    rate: 1/minute
    account_age: random(30, 365) days
    
  - type: reaction
    rate: 5/second

expected_results:
  pipeline_latency_p99: < 100ms
  action_dispatch_p99: < 500ms
  false_positive_rate: < 1%
  memory_usage: < 512MB per shard
```

### 1.2 Yoğun Trafik (Peak Hours)
```yaml
scenario: peak_traffic
description: "Prime time yoğunluğu simüle et (3x normal)"
duration: 1h
users: 500

patterns:
  - type: message
    rate: 30/second
    burst_probability: 10%
    burst_multiplier: 5x
    
  - type: member_join
    rate: 5/minute
    
  - type: voice_state_update
    rate: 2/second

expected_results:
  pipeline_latency_p99: < 200ms
  action_dispatch_p99: < 1000ms
  backpressure_triggers: < 5
  dropped_events: 0
```

### 1.3 Stress Test (Limits)
```yaml
scenario: stress_test
description: "Sistem limitlerini test et"
duration: 15m
users: 1000

patterns:
  - type: message
    rate: 100/second
    
  - type: member_join
    rate: 30/minute

expected_results:
  graceful_degradation: true
  backpressure_activates: true
  no_crashes: true
  recovery_time: < 5min after load drops
```

### 1.4 Shard Failover
```yaml
scenario: shard_failover
description: "Bir shard'ın çökmesi durumunu test et"
duration: 10m

actions:
  - at: 2min
    action: kill_shard
    shard_id: 0
    
  - at: 5min
    action: verify_recovery
    expected:
      - shard_0_reconnected: true
      - events_not_lost: true
      - no_duplicate_processing: true
```

---

## 2. RAID SİMÜLASYON SENARYOLARI

### 2.1 Basic Spam Raid
```yaml
scenario: basic_spam_raid
description: "Basit spam raid - aynı mesajı tekrar eden botlar"
severity: LOW
duration: 5m

attack_pattern:
  join_rate: 10/minute
  accounts:
    count: 30
    age: 1-3 days
    avatar: none
    name_pattern: "user{random_digits}"
  
  messages:
    delay_after_join: 10-30 seconds
    content: "Free Discord Nitro! Click here: {malicious_link}"
    channels: all_accessible
    rate: 3/second per bot

expected_detection:
  - raid_join_flood: within 1 minute
  - phishing_link: immediate
  
expected_actions:
  - lockdown: activated
  - newcomer_quarantine: all 30 accounts
  - message_delete: all spam messages
  - auto_tempban: accounts with phishing links
  
success_criteria:
  detection_time: < 60s
  spam_visible_duration: < 30s
  false_positives: 0
```

### 2.2 Slow Burn Raid
```yaml
scenario: slow_burn_raid
description: "Yavaş sızma - tespitten kaçınmaya çalışan raid"
severity: MEDIUM
duration: 2h

attack_pattern:
  join_rate: 2-3/10 minutes (under threshold)
  accounts:
    count: 50
    age: 7-14 days (older accounts)
    avatar: generic
    name_pattern: realistic names
  
  behavior:
    wait_before_spam: 30-60 minutes
    initial_messages: normal looking messages
    escalation:
      - phase_1: normal chat (30min)
      - phase_2: subtle promo (20min)
      - phase_3: coordinated spam burst
  
  messages:
    phase_3_content: "JOIN OUR SERVER {invite_link}"
    phase_3_rate: all accounts, same time

expected_detection:
  - coordinated_message: within 30s of phase_3
  - user_risk_score: gradual increase during phase_2
  
expected_actions:
  - lockdown: triggered at phase_3
  - review_queue: suspicious accounts from phase_2
  - ban: phase_3 spammers
  
success_criteria:
  phase_3_detection: < 30s
  pre_emptive_flags: some accounts flagged in phase_2
```

### 2.3 Mention Flood
```yaml
scenario: mention_flood
description: "@everyone ve @here spam"
severity: HIGH
duration: 2m

attack_pattern:
  accounts: 5 (compromised or newly joined)
  messages:
    content: "@everyone FREE NITRO @here CLICK NOW"
    rate: max possible
    target_channels: announcement channels

expected_detection:
  - mention_spam: immediate
  
expected_actions:
  - message_delete: immediate
  - timeout: immediate (1h)
  - escalation: kick after 2nd offense
  
success_criteria:
  mention_visibility: < 1 message seen by general users
  response_time: < 1s
```

### 2.4 Token/Account Compromise Raid
```yaml
scenario: compromised_accounts
description: "Mevcut üyelerin hesapları ele geçirildi"
severity: CRITICAL
duration: 10m

attack_pattern:
  accounts: 10 existing verified members
  behavioral_change:
    - sudden_activity_spike
    - unusual_message_content
    - rapid_channel_hopping
  messages:
    content: phishing_link
    rate: 1/min per account (staying under spam threshold)

expected_detection:
  - anomaly_detection: behavioral change
  - phishing_link: immediate
  - coordination: similar messages from trusted accounts
  
expected_actions:
  - message_delete: phishing content
  - timeout: compromised accounts
  - review_queue: manual verification needed
  - dm_to_user: "Hesabınız ele geçirilmiş olabilir"
  
success_criteria:
  detection_time: < 5min
  false_flags_of_real_users: 0
```

### 2.5 DM Spam Raid
```yaml
scenario: dm_spam  
description: "Toplu DM spam (sunucu üyelerine)"
severity: MEDIUM
duration: 30m

attack_pattern:
  accounts: 5 new members
  behavior:
    - join server
    - scrape member list
    - send DM to all members
  dm_content: "Free gift! {scam_link}"

expected_detection:
  - high outgoing DM rate (if trackable)
  - user reports
  - similar content reports

expected_actions:
  - quarantine: accounts with reports
  - ban: after verification
  
notes: |
  DM'ler bot tarafından doğrudan görülmez.
  Tespit kullanıcı raporlarına bağlı.
  /report komutuyla toplanan veriler analiz edilmeli.
```

### 2.6 Distributed Attack
```yaml
scenario: distributed_attack
description: "Farklı kaynaklardan, farklı içeriklerle koordineli saldırı"
severity: CRITICAL
duration: 1h

attack_pattern:
  groups:
    - name: spam_bots
      count: 20
      content: generic spam
      
    - name: phishing_bots
      count: 10
      content: scam links
      
    - name: toxicity_bots  
      count: 15
      content: hate speech
      
    - name: distraction_bots
      count: 10
      content: innocent-looking messages (to dilute detection)
  
  coordination:
    - wave_1: phishing_bots (probe defenses)
    - wave_2: spam_bots + toxicity_bots (overwhelm)
    - wave_3: distraction_bots (confusion)

expected_detection:
  - multiple_rules_triggered
  - coordination_detection
  
expected_actions:
  - lockdown: immediate
  - multi_rule_enforcement
  - prioritization: phishing > toxicity > spam
  
success_criteria:
  phishing_removed: < 10s
  toxicity_removed: < 30s
  lockdown_time: < 2min
```

---

## 3. TEST INFRASTRUCTURE

### 3.1 Test Bot Setup
```python
# tests/load/raid_bot.py
import discord
import asyncio
import random

class RaidBotSimulator:
    def __init__(self, token: str, guild_id: int):
        self.token = token
        self.guild_id = guild_id
        self.client = discord.Client(intents=discord.Intents.all())
    
    async def spam_messages(self, channel_id: int, content: str, count: int, delay: float):
        """Spam mesaj gönder"""
        channel = self.client.get_channel(channel_id)
        for _ in range(count):
            try:
                await channel.send(content)
                await asyncio.sleep(delay)
            except discord.HTTPException:
                break
    
    async def simulate_raid_join(self, bots: list, join_delay: float):
        """Koordineli join simüle et"""
        for bot in bots:
            await bot.connect()
            await asyncio.sleep(join_delay)
```

### 3.2 Metrics Collection
```python
# tests/load/metrics_collector.py
import time
from prometheus_client import Counter, Histogram

class LoadTestMetrics:
    events_sent = Counter('loadtest_events_sent', 'Events sent', ['type'])
    events_processed = Counter('loadtest_events_processed', 'Events processed')
    detection_latency = Histogram('loadtest_detection_latency_seconds', 'Detection latency')
    action_latency = Histogram('loadtest_action_latency_seconds', 'Action latency')
    
    def record_event_sent(self, event_type: str):
        self.events_sent.labels(type=event_type).inc()
    
    def record_detection(self, sent_at: float):
        self.detection_latency.observe(time.time() - sent_at)
```

### 3.3 Test Environment
```yaml
# docker-compose.loadtest.yml
version: '3.8'

services:
  lithium-bot:
    build: .
    environment:
      - LOAD_TEST_MODE=true
      - LOG_LEVEL=DEBUG
    deploy:
      resources:
        limits:
          memory: 1G
  
  raid-simulator:
    build: ./tests/load
    depends_on:
      - lithium-bot
    environment:
      - TARGET_GUILD_ID=${TEST_GUILD_ID}
      - SCENARIO=${SCENARIO:-basic_spam_raid}
  
  prometheus:
    image: prom/prometheus
    volumes:
      - ./tests/load/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./tests/load/dashboards:/var/lib/grafana/dashboards
```

---

## 4. TEST EXECUTION PLAYBOOK

### 4.1 Pre-Test Checklist
```
□ Test sunucusu oluşturuldu
□ Bot test sunucusuna eklendi
□ Test hesapları hazır (10+ bot account)
□ Governance config test modunda
□ Metrics collection aktif
□ Baseline metrics alındı
□ Backup alındı (config)
```

### 4.2 Test Execution
```bash
# 1. Start monitoring
docker-compose -f docker-compose.loadtest.yml up -d prometheus grafana

# 2. Run specific scenario
SCENARIO=basic_spam_raid docker-compose -f docker-compose.loadtest.yml up raid-simulator

# 3. Monitor in real-time
# Grafana: http://localhost:3000

# 4. Collect results
./scripts/collect_test_results.sh
```

### 4.3 Post-Test Analysis
```
□ Detection time karşılaştır (vs. expected)
□ False positive oranı
□ Action latency
□ Resource usage (CPU, Memory)
□ Error logs
□ Missed events
□ Backpressure aktivasyonları
```

### 4.4 Test Report Template
```markdown
# Raid Simulation Report

## Summary
- Scenario: {scenario_name}
- Date: {date}
- Duration: {duration}

## Results
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Detection Time | < 60s | 45s | ✅ |
| False Positives | 0 | 0 | ✅ |
| Action Latency p99 | < 500ms | 320ms | ✅ |

## Observations
- [findings]

## Recommendations
- [improvements]
```

---

## 5. CHAOS ENGINEERING

### 5.1 Failure Injection Scenarios
```yaml
# Database connection loss
- name: db_connection_lost
  inject_at: 5min
  duration: 30s
  expected: graceful degradation, events queued

# Redis connection loss  
- name: redis_unavailable
  inject_at: 3min
  duration: 1min
  expected: fallback to memory, no data loss

# High latency
- name: discord_api_slow
  inject_at: 2min
  latency: 2000ms
  expected: backpressure, no timeout errors

# Memory pressure
- name: memory_pressure
  inject_at: 10min
  limit: 256MB
  expected: graceful performance degradation
```

### 5.2 Recovery Verification
```
Her chaos senaryosu sonrası:
□ Sistem normal operasyona döndü
□ Queued events işlendi
□ Data integrity korundu
□ No duplicate actions
□ Audit log complete
```
