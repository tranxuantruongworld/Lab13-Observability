from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    'email': r'[\w\.-]+@[\w\.-]+\.\w+',
    'phone_vn': r'(?:\+84|0)[ \.-]?\d{3}[ \.-]?\d{3}[ \.-]?\d{3,4}',  # Matches 090 123 4567, 090.123.4567, etc.
    'cccd': r'\b\d{12}\b',
    'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    'passport_vn': r'\b[A-Z]\d{7,8}\b',
    'tax_id_vn': r'\b\d{10}(?:-\d{3})?\b',
    'address_vn': r'(?i)\b(?:số|đường|phố|ngõ|ngách|quận|huyện|thành phố|tỉnh|phường|xã|thôn|xóm|ấp)\b',
    'ipv4': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}


def scrub_text(data: object, **_: object) -> object:
    if isinstance(data, str):
        safe = data
        for name, pattern in PII_PATTERNS.items():
            safe = re.sub(pattern, f'[REDACTED_{name.upper()}]', safe)
        return safe

    if isinstance(data, dict):
        return {k: scrub_text(v) for k, v in data.items()}
    if isinstance(data, list):
        return [scrub_text(item) for item in data]

    return data


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace('\n', ' ')
    return safe[:max_len] + ('...' if len(safe) > max_len else '')


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:12]
