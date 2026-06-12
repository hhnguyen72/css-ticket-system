"""
types/models.py
---------------
Core domain types and enumerations for the CSS Ticket Management Tool.

Scope: Type definitions only. No business logic or implementation bodies.
Boundary: Shared across ID Generation, Classifier, and Router teams.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import NewType

# ============================================================
# CONSTANTS
# ============================================================

TICKET_ID_PREFIX: str = "CSS"
TICKET_ID_DELIMITER: str = "-"
SEQUENCE_FLOOR: int = 1
REDACTED_DOD_ID: str = "[DOD_ID_REDACTED]"
DOD_ID_PATTERN: str = r"\b\d{10}\b"

# ============================================================
# CUSTOM TYPES
# ============================================================

# Fully formatted ticket ID string.
# Format: CSS-YYYYMMDD-NNNN
# Example: CSS-20260612-0001
# Date segment uses local server time (EST/EDT).
# Sequence is zero-padded to 4 digits minimum — no upper cap.
TicketID = NewType("TicketID", str)

# ============================================================
# ENUMERATIONS
# ============================================================


class Category(IntEnum):
    """
    The three canonical ticket categories.
    No ticket may be created without exactly one Category assigned.
    Attempts to assign a value outside this enum must be rejected
    with ErrInvalidCategory.
    """
    SEL_COMMANDER_SIGNATURE = 1  # SEL / Commander's Signature — highest routing priority
    RECORD_UPDATE           = 2  # Record Update
    DISSEMINATION_INFO      = 3  # Dissemination Info


class Priority(IntEnum):
    """
    Urgency tier assigned to a ticket.
    Priority 1 (CRITICAL) tickets are always surfaced above
    lower-tier tickets in the queue, regardless of Need By Date.
    """
    CRITICAL = 1
    HIGH     = 2
    LOW      = 3


class TicketErrorCode(IntEnum):
    """
    Enumerated domain error conditions for ticket creation,
    ID assignment, classification, and routing operations.
    """
    INVALID_DATE         = 1  # Date segment is malformed or not exactly 8 numeric chars
    INVALID_SEQUENCE     = 2  # Sequence number is below SEQUENCE_FLOOR
    DUPLICATE_ID         = 3  # Generated ID already exists in storage
    UNRESOLVABLE_DATE    = 4  # Server clock failure — creation must be rejected
    INVALID_CATEGORY     = 5  # Category value does not map to a canonical Category
    MISSING_TIMELINE     = 6  # Need By Date is absent or cannot be parsed
    COUNTER_UNAVAILABLE  = 7  # Sequence counter read/write failure

# ============================================================
# DOMAIN MODELS
# ============================================================


@dataclass
class POC:
    """
    A single point of contact extracted from a structured form submission.

    Phone numbers are US-format only (e.g., 555-867-5309).
    Missing subfields are represented as empty string — never omitted.
    DSN and international formats are not extracted.
    """
    name:  str = ""  # Full name of the POC
    email: str = ""  # Email address — .mil or civilian
    phone: str = ""  # US-format only — empty string if not present or non-US format


@dataclass
class TicketForm:
    """
    Raw structured form submission received from a CSS team member.

    All fields are raw strings at ingestion. Validation, typing, and
    classification are performed downstream by the Classifier team.
    DoD ID redaction is applied before any field is stored or displayed.
    """
    raw_category:    str = ""
    raw_priority:    str = ""
    raw_timeline:    str = ""  # Need By Date as submitted — e.g. "2026-06-20"
    raw_description: str = ""
    raw_poc:         str = ""


@dataclass
class Ticket:
    """
    Fully processed ticket record produced after field extraction,
    classification, ID assignment, and DoD ID redaction.

    This is the canonical type passed to storage and queue output.
    ID is assigned at creation and is immutable thereafter.
    Description is redacted — all DoD IDs replaced with REDACTED_DOD_ID.
    """
    id:          TicketID         = TicketID("")   # Assigned at creation — immutable
    category:    Category         = Category.SEL_COMMANDER_SIGNATURE
    priority:    Priority         = Priority.CRITICAL
    timeline:    datetime         = field(default_factory=datetime.now)  # Need By Date
    description: str              = ""             # Redacted before storage
    pocs:        list[POC]        = field(default_factory=list)
    created_at:  datetime         = field(default_factory=datetime.now)  # Local EST/EDT


# ============================================================
# DOMAIN EXCEPTION
# ============================================================


class TicketError(Exception):
    """
    Domain-specific exception raised during ticket creation,
    ID assignment, classification, or routing.
    """

    def __init__(self, code: TicketErrorCode, message: str) -> None:
        self.code    = code
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        return f"TicketError(code={self.code.name}, message={self.message!r})"
