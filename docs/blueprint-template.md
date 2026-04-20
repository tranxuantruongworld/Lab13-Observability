# Day 13 Observability Lab Report

## 1. Team Metadata
- GROUP_NAME: D5-2
- REPO_URL: https://github.com/tranxuantruongworld/C401-D5-2-Day13
- MEMBERS:
  - Member A: Trường | Role: Logging & PII
  - Member B: Trường | Role: Tracing & Enrichment
  - Member C: Công | Role: SLO & Alerts
  - Member D: Minh Hà | Role: Load Test & Dashboard
  - Member E: Hải Đặng | Role: Dashboard & Evidence
  - Member F: Công | Role: Blueprint & Demo Lead
---

## 2. Group Performance (Auto-Verified)
- VALIDATE_LOGS_FINAL_SCORE: 100/100
- TOTAL_TRACES_COUNT: 215
- PII_LEAKS_FOUND: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- *Evidence 1: Correlation ID propagation*
{
  "service": "api",
  "event": "request_received",
  "correlation_id": "req-aee8be88",
  "user_id_hash": "97ce842ec69d",
  "level": "info",
  "ts": "2026-04-20T14:57:46.412037Z"
}

- *Evidence 2: PII Redaction*
{
  "message_preview": "What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?",
  "event": "request_received",
  "correlation_id": "req-279c5499"
}

- *Evidence 3: Incident Alerting*
{
  "alert_name": "high_latency_p95",
  "condition": "latency_p95_ms > 5000 for 30m",
  "actual_value": 2665.0,
  "event": "alert_triggered",
  "correlation_id": "req-aa05cdf5",
  "level": "warning",
  "ts": "2026-04-20T15:11:20.813624Z"
}

- TRACE_WATERFALL_EXPLANATION: We successfully implemented structured logging with correlation IDs. In the incident trace, we can see the alert_triggered event firing when latency exceeds the threshold.

### 3.2 Dashboard & SLOs
- DASHBOARD_6_PANELS_SCREENSHOT: ../evidence/dashboard-1.jpeg
- SLO_TABLE:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 5000ms | 28d | 1500ms |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $2.5/day | 1d | $0.0 |

---

## 4. Incident Response (Group)
- SCENARIO_NAME: rag_slow
- SYMPTOMS_OBSERVED: P95 Latency spiked to ~2600ms-3000ms. Alerts triggered for 'slo_breach_latency'.
- ROOT_CAUSE_PROVED_BY: Trace ID req-77ec6a76 showing rag_lookup span taking > 2s.
- FIX_ACTION: Disabled 'rag_slow' incident toggle via API.
- PREVENTIVE_MEASURE: Implement caching for RAG retrieval and set timeout for vector database queries.
---

## 5. Individual Contributions & Evidence

### Trần Xuân Trường - 2A202600321
- TASKS_COMPLETED: A + B : Implemented JSON logging with structlog, configured correlation ID middleware, and set up PII scrubbing patterns using regex. Integrated Langfuse for tracing and enriched logs with user/session metadata.

### Minh Hà - 2A202600060
- TASKS_COMPLETED: D : Developed and executed load testing scripts using Python to simulate concurrent user traffic. Configured the initial layout of the dashboard to track real-time metrics.

### Hải Đặng - 2A202600020
- TASKS_COMPLETED: E : Finalized the Dashboard visualization, ensuring all SLO thresholds were clearly marked. Collected and curated technical evidence screenshots for the final report.


### Đào Văn Công - 2A202600031
- TASKS_COMPLETED: C + F : Defined SLOs and SLIs based on business requirements. Configured alert rules and wrote the runbook. Led the blueprint orchestration, demo coordination, and evidence reporting.

---

## 6. Bonus Items (Optional)
- BONUS_CUSTOM_METRIC: Business metrics such as spam email detection and escalation rate.
