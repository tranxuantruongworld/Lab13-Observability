# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: D5-2
- [REPO_URL]: https://github.com/tranxuantruongworld/C401-D5-2-Day13
- [MEMBERS]:
  - Member A: Trường | Role: Logging & PII
  - Member B: Trường | Role: Tracing & Enrichment
  - Member C: Công | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Dashboard & Evidence
  - Member F: Công | Role: Blueprint & Demo Lead
---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 20
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- **Evidence 1: Correlation ID propagation**
![Terminal Logs](../evidence/terminal.png)
```json
{
  "service": "api",
  "event": "request_received",
  "correlation_id": "req-aee8be88",
  "user_id_hash": "97ce842ec69d",
  "level": "info",
  "ts": "2026-04-20T14:57:46.412037Z"
}
```

- **Evidence 2: PII Redaction**
![PII Scrubbing](../evidence/user_id_hash.png)
```json
{
  "message_preview": "What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?",
  "event": "request_received",
  "correlation_id": "req-279c5499"
}
```

- **Evidence 3: Incident Alerting**
![Incident Alert](../evidence/incident_evidence_warning.png)
```json
{
  "alert_name": "high_latency_p95",
  "condition": "latency_p95_ms > 5000 for 30m",
  "actual_value": 2665.0,
  "event": "alert_triggered",
  "correlation_id": "req-aa05cdf5",
  "level": "warning",
  "ts": "2026-04-20T15:11:20.813624Z"
}
```

- [TRACE_WATERFALL_EXPLANATION]: We successfully implemented structured logging with correlation IDs. In the incident trace, we can see the `alert_triggered` event firing when latency exceeds the threshold.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 2665ms |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $2.5/day | 1d | $0.03 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: ../evidence/incident_1.png
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#1-high-latency-p95](alerts.md#1-high-latency-p95)

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: P95 Latency spiked to ~2600ms-3000ms. Alerts triggered for 'slo_breach_latency'.
- [ROOT_CAUSE_PROVED_BY]: Trace ID req-77ec6a76 showing rag_lookup span taking > 2s.
- [FIX_ACTION]: Disabled 'rag_slow' incident toggle via API.
- [PREVENTIVE_MEASURE]: Implement caching for RAG retrieval and set timeout for vector database queries.
---

## 5. Individual Contributions & Evidence

### Trần Xuân Trường
- [TASKS_COMPLETED]: A + B
- [EVIDENCE_LINK]: https://github.com/tranxuantruongworld/C401-D5-2-Day13/tree/ca1acbd53774c2361f137fdd0cbcc2bb6bfbe913

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: Dashboard creation & Evidence collection
- [EVIDENCE_LINK]: [Link to PR/Commits]

### Đào Văn Công - 2A202600031
- [TASKS_COMPLETED]: C + F : SLO + Alerts, Blueprint orchestration, Demo coordination, & Evidence reporting
- [EVIDENCE_LINK]: https://github.com/tranxuantruongworld/C401-D5-2-Day13/commit/b4e058b
---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
