"""
service/redactor.py
---------------------
Concrete implementation of Redactor.

Applies DoD ID redaction to any string field using the canonical
pattern \\b\\d{10}\\b before storage or display.

Guardrail: 100% redaction rate required. Non-DoD numeric strings
must not be altered.
"""

from __future__ import annotations

import re

from models import DOD_ID_PATTERN, REDACTED_DOD_ID
from protocols import Redactor


class DoDRedactor(Redactor):
    """
    Replaces all 10-digit DoD ID numbers in a string with
    [DOD_ID_REDACTED]. Uses word boundaries to avoid false
    positives on longer numeric strings.
    """

    _PATTERN = re.compile(DOD_ID_PATTERN)

    def redact(self, input: str) -> str:
        return self._PATTERN.sub(REDACTED_DOD_ID, input)
