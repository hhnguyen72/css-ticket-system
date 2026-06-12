"""
mocks/mock_classifier.py
------------------------
Mock implementation of the Classifier boundary interface.

Purpose:
    Allows the ID Generation team to develop and test the full ticket
    creation flow — including ID assignment and redaction — without
    blocking on the Classifier team's implementation.

Scope:
    Test and development use only. Must not be used in production.

Behavior:
    - Happy path: Returns a pre-classified Ticket from a TicketForm.
    - Error simulation: Force specific TicketErrors via constructor flags.
    - Category mapping: Maps raw string values to canonical Category enum.
    - Does not perform real NLP or AI classification.
"""

from __future__ import annotations

from datetime import datetime

from src.protocols import Classifier
from src.models import (
    Category,
    POC,
    Priority,
    Ticket,
    TicketError,
    TicketErrorCode,
    TicketForm,
)

# ============================================================
# CATEGORY STRING MAP
# Simulates the Classifier team's label normalization logic.
# Covers realistic varied phrasings per TDD-02.
# ============================================================

_CATEGORY_MAP: dict[str, Category] = {
    # SEL / Commander's Signature
    "sel/commander's signature":    Category.SEL_COMMANDER_SIGNATURE,
    "commander signature needed":   Category.SEL_COMMANDER_SIGNATURE,
    "sig request":                  Category.SEL_COMMANDER_SIGNATURE,
    "sel sig":                      Category.SEL_COMMANDER_SIGNATURE,
    "commander's signature":        Category.SEL_COMMANDER_SIGNATURE,

    # Record Update
    "record update":                Category.RECORD_UPDATE,
    "update personnel record":      Category.RECORD_UPDATE,
    "update record":                Category.RECORD_UPDATE,

    # Dissemination Info
    "dissemination info":           Category.DISSEMINATION_INFO,
    "push to distribution list":    Category.DISSEMINATION_INFO,
    "dissemination":                Category.DISSEMINATION_INFO,
}

_PRIORITY_MAP: dict[str, Priority] = {
    "critical": Priority.CRITICAL,
    "high":     Priority.HIGH,
    "low":      Priority.LOW,
}


class MockClassifier(Classifier):
    """
    Mock Classifier for use in ID Generation team tests.

    Args:
        force_invalid_category: If True, raises INVALID_CATEGORY on classify().
        force_missing_timeline: If True, raises MISSING_TIMELINE on classify().
        default_priority:       Priority assigned when raw_priority is unrecognized.
    """

    def __init__(
        self,
        force_invalid_category: bool = False,
        force_missing_timeline: bool = False,
        default_priority: Priority = Priority.HIGH,
    ) -> None:
        self._force_invalid_category = force_invalid_category
        self._force_missing_timeline = force_missing_timeline
        self._default_priority       = default_priority

    def classify(self, form: TicketForm) -> Ticket:
        """
        Map a raw TicketForm to a classified Ticket.

        Raises TicketError per interface contract if error flags are set
        or if required fields cannot be resolved.
        """
        # --- Simulate forced error paths ---
        if self._force_invalid_category:
            raise TicketError(
                TicketErrorCode.INVALID_CATEGORY,
                f"MockClassifier: category '{form.raw_category}' does not map "
                "to a canonical Category value.",
            )

        if self._force_missing_timeline:
            raise TicketError(
                TicketErrorCode.MISSING_TIMELINE,
                f"MockClassifier: timeline '{form.raw_timeline}' is absent "
                "or cannot be parsed to a valid date.",
            )

        # --- Resolve Category ---
        category = _CATEGORY_MAP.get(form.raw_category.strip().lower())
        if category is None:
            raise TicketError(
                TicketErrorCode.INVALID_CATEGORY,
                f"MockClassifier: unrecognized category '{form.raw_category}'. "
                f"Must be one of: {list(_CATEGORY_MAP.keys())}",
            )

        # --- Resolve Priority ---
        priority = _PRIORITY_MAP.get(
            form.raw_priority.strip().lower(), self._default_priority
        )

        # --- Resolve Timeline ---
        timeline = self._parse_timeline(form.raw_timeline)

        # --- Resolve POCs ---
        pocs = self._parse_pocs(form.raw_poc)

        return Ticket(
            id          = "",                  # Not yet assigned — ID Generation team assigns
            category    = category,
            priority    = priority,
            timeline    = timeline,
            description = form.raw_description,  # Redaction applied by Redactor, not here
            pocs        = pocs,
            created_at  = datetime.now(),
        )

    # --------------------------------------------------------
    # Private helpers — mock parsing only, not production logic
    # --------------------------------------------------------

    def _parse_timeline(self, raw: str) -> datetime:
        """
        Attempt to parse the raw timeline string.
        Supports ISO format (YYYY-MM-DD) only in this mock.
        Raises MISSING_TIMELINE if parsing fails.
        """
        if not raw.strip():
            raise TicketError(
                TicketErrorCode.MISSING_TIMELINE,
                "MockClassifier: Need By Date is empty.",
            )
        try:
            return datetime.strptime(raw.strip(), "%Y-%m-%d")
        except ValueError:
            raise TicketError(
                TicketErrorCode.MISSING_TIMELINE,
                f"MockClassifier: cannot parse timeline '{raw}'. "
                "Expected format: YYYY-MM-DD.",
            )

    def _parse_pocs(self, raw: str) -> list[POC]:
        """
        Parse raw POC string into a list of POC objects.
        In this mock, parses a single POC block delimited by pipe (|).

        Expected format:
            "Name: SSgt Jane Doe | Email: jane.doe@mail.mil | Phone: 555-123-4567"

        Returns an empty list if raw is blank — does not raise.
        """
        if not raw.strip():
            return []

        poc = POC()
        for segment in raw.split("|"):
            segment = segment.strip()
            if segment.lower().startswith("name:"):
                poc.name = segment[5:].strip()
            elif segment.lower().startswith("email:"):
                poc.email = segment[6:].strip()
            elif segment.lower().startswith("phone:"):
                poc.phone = segment[6:].strip()

        return [poc] if any([poc.name, poc.email, poc.phone]) else []
