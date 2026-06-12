"""
services/classifier.py
-----------------------
Production Classifier implementation.

Accepts a raw TicketForm and returns a classified Ticket with all
five fields populated. Normalizes category and priority strings,
parses timeline, and extracts US-format POC data.
"""

from __future__ import annotations

import re
from datetime import datetime

from models import (
    Category,
    POC,
    Priority,
    Ticket,
    TicketError,
    TicketErrorCode,
    TicketForm,
    TicketID,
)
from protocols import Classifier

# US phone pattern: 555-867-5309 or (555) 867-5309 or 555.867.5309
_US_PHONE_PATTERN = re.compile(
    r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}"
)

_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

_CATEGORY_MAP: dict[str, Category] = {
    "sel/commander's signature":    Category.SEL_COMMANDER_SIGNATURE,
    "sel/commanders signature":     Category.SEL_COMMANDER_SIGNATURE,
    "commander's signature":        Category.SEL_COMMANDER_SIGNATURE,
    "commanders signature":         Category.SEL_COMMANDER_SIGNATURE,
    "commander signature needed":   Category.SEL_COMMANDER_SIGNATURE,
    "commander signature":          Category.SEL_COMMANDER_SIGNATURE,
    "sig request":                  Category.SEL_COMMANDER_SIGNATURE,
    "sel sig":                      Category.SEL_COMMANDER_SIGNATURE,
    "signature request":            Category.SEL_COMMANDER_SIGNATURE,
    "record update":                Category.RECORD_UPDATE,
    "update personnel record":      Category.RECORD_UPDATE,
    "update record":                Category.RECORD_UPDATE,
    "personnel record update":      Category.RECORD_UPDATE,
    "dissemination info":           Category.DISSEMINATION_INFO,
    "dissemination information":    Category.DISSEMINATION_INFO,
    "dissemination":                Category.DISSEMINATION_INFO,
    "push to distribution list":    Category.DISSEMINATION_INFO,
    "distribution":                 Category.DISSEMINATION_INFO,
}

_PRIORITY_MAP: dict[str, Priority] = {
    "critical": Priority.CRITICAL,
    "1":        Priority.CRITICAL,
    "high":     Priority.HIGH,
    "2":        Priority.HIGH,
    "low":      Priority.LOW,
    "3":        Priority.LOW,
    "normal":   Priority.LOW,
}

_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d %b %Y", "%Y%m%d"]


class CSSClassifier(Classifier):
    """
    Production classifier for CSS ticket form submissions.
    """

    def classify(self, form: TicketForm) -> Ticket:
        category  = self._resolve_category(form.raw_category)
        priority  = self._resolve_priority(form.raw_priority)
        timeline  = self._resolve_timeline(form.raw_timeline)
        pocs      = self._extract_pocs(form.raw_poc)

        return Ticket(
            id          = TicketID(""),   # Assigned by TicketIDService
            category    = category,
            priority    = priority,
            timeline    = timeline,
            description = form.raw_description,  # Redacted by TicketIDService
            pocs        = pocs,
            created_at  = datetime.now(),
        )

    # --------------------------------------------------------
    # Private resolvers
    # --------------------------------------------------------

    def _resolve_category(self, raw: str) -> Category:
        key = raw.strip().lower()
        if not key:
            raise TicketError(
                TicketErrorCode.INVALID_CATEGORY,
                "Classifier: category field is empty — must be one of the three canonical categories.",
            )
        category = _CATEGORY_MAP.get(key)
        if category is None:
            raise TicketError(
                TicketErrorCode.INVALID_CATEGORY,
                f"Classifier: '{raw}' does not map to a canonical category. "
                f"Valid options: SEL/Commander's Signature, Record Update, Dissemination Info.",
            )
        return category

    def _resolve_priority(self, raw: str) -> Priority:
        key = raw.strip().lower()
        # Default to HIGH if unrecognized — never block ticket creation on priority alone
        return _PRIORITY_MAP.get(key, Priority.HIGH)

    def _resolve_timeline(self, raw: str) -> datetime:
        if not raw.strip():
            raise TicketError(
                TicketErrorCode.MISSING_TIMELINE,
                "Classifier: Need By Date is required but was not provided.",
            )
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(raw.strip(), fmt)
            except ValueError:
                continue
        raise TicketError(
            TicketErrorCode.MISSING_TIMELINE,
            f"Classifier: cannot parse Need By Date '{raw}'. "
            f"Accepted formats: YYYY-MM-DD, MM/DD/YYYY, DD Mon YYYY.",
        )

    def _extract_pocs(self, raw: str) -> list[POC]:
        """
        Extract POC entries from the raw POC string.

        Supports pipe-delimited structured format:
            Name: SSgt Jane Doe | Email: jane.doe@mail.mil | Phone: 555-123-4567

        Also falls back to scanning for emails and US phone numbers inline.
        """
        if not raw.strip():
            return []

        poc = POC()

        # Structured pipe-delimited format
        if "|" in raw:
            for segment in raw.split("|"):
                segment = segment.strip()
                lower   = segment.lower()
                if lower.startswith("name:"):
                    poc.name = segment[5:].strip()
                elif lower.startswith("email:"):
                    poc.email = segment[6:].strip()
                elif lower.startswith("phone:"):
                    poc.phone = segment[6:].strip()
        else:
            # Fallback: scan inline for email and US phone
            email_match = _EMAIL_PATTERN.search(raw)
            phone_match = _US_PHONE_PATTERN.search(raw)
            if email_match:
                poc.email = email_match.group()
            if phone_match:
                poc.phone = phone_match.group()
            # Name is whatever remains after stripping matched values
            name_raw = raw
            if email_match:
                name_raw = name_raw.replace(email_match.group(), "")
            if phone_match:
                name_raw = name_raw.replace(phone_match.group(), "")
            poc.name = name_raw.strip().strip(",").strip()

        return [poc] if any([poc.name, poc.email, poc.phone]) else []
