"""
/protocols.py
-----------------------
Abstract interface contracts for the CSS Ticket Management Tool.

Scope: Protocol definitions only. No implementation bodies.

Boundary ownership:
    IDGenerator, SequenceCounter, TicketIDService, Redactor
        → owned and implemented by: ID Generation team

    Classifier
        → boundary interface only; implemented by: Classifier team

    Router
        → boundary interface only; implemented by: Router team
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from models import Category, Ticket, TicketForm, TicketID

# ============================================================
# ID GENERATION INTERFACES
# Owned by: ID Generation team
# ============================================================


class IDGenerator(ABC):
    """
    Contract for generating a formatted TicketID from a date string
    and a sequence number.

    Implementations must guarantee:
      - Returned ID matches format CSS-YYYYMMDD-NNNN
      - date must be exactly 8 numeric characters (YYYYMMDD)
      - sequence must be >= SEQUENCE_FLOOR (1)
      - Raises TicketError(INVALID_DATE) for malformed date
      - Raises TicketError(INVALID_SEQUENCE) for sequence < 1
    """

    @abstractmethod
    def generate(self, date: str, sequence: int) -> TicketID:
        """
        Return a formatted TicketID for the given date and sequence.

        Args:
            date:     Date string in YYYYMMDD format — local EST/EDT.
            sequence: Integer sequence number >= SEQUENCE_FLOOR.

        Returns:
            TicketID: Formatted ID string e.g. CSS-20260612-0001.

        Raises:
            TicketError: INVALID_DATE if date is not 8 numeric chars.
            TicketError: INVALID_SEQUENCE if sequence < SEQUENCE_FLOOR.
        """
        ...


class SequenceCounter(ABC):
    """
    Contract for managing the per-day sequence counter.

    Implementations must:
      - Persist state across service restarts (database or flat file)
      - Be safe for concurrent use (no duplicate sequence numbers)
      - Reset to SEQUENCE_FLOOR at 00:00:00 local server time daily
      - Raise TicketError(COUNTER_UNAVAILABLE) on read/write failure
    """

    @abstractmethod
    def next(self, date: str) -> int:
        """
        Return and increment the next sequence number for the given date.
        Resets to SEQUENCE_FLOOR when the date changes.

        Args:
            date: Date string in YYYYMMDD format.

        Returns:
            int: Next sequence number for the given date.

        Raises:
            TicketError: COUNTER_UNAVAILABLE if counter cannot be incremented.
        """
        ...

    @abstractmethod
    def current(self, date: str) -> int:
        """
        Return the current sequence number for the given date
        without incrementing it.

        Args:
            date: Date string in YYYYMMDD format.

        Returns:
            int: Current sequence number — SEQUENCE_FLOOR if no tickets today.

        Raises:
            TicketError: COUNTER_UNAVAILABLE if counter cannot be read.
        """
        ...


class TicketIDService(ABC):
    """
    Composes IDGenerator and SequenceCounter into a single entry point
    for ticket ID assignment at the moment of ticket creation.

    This is the interface consumed by the ticket creation flow.
    Implementations must:
      - Assign the ID before any field is written to storage
      - Reject creation if the server date cannot be resolved
      - Reject creation if the generated ID is not unique in storage
    """

    @abstractmethod
    def assign(self, ticket: Ticket) -> Ticket:
        """
        Generate and attach a TicketID to the given Ticket.
        The ID is assigned before storage and is immutable after assignment.

        Args:
            ticket: A classified Ticket with no ID assigned yet.

        Returns:
            Ticket: The same ticket with id field populated.

        Raises:
            TicketError: UNRESOLVABLE_DATE if server clock cannot be read.
            TicketError: COUNTER_UNAVAILABLE if sequence counter fails.
            TicketError: DUPLICATE_ID if generated ID already exists in storage.
        """
        ...


# ============================================================
# REDACTION INTERFACE
# Owned by: ID Generation team (guardrail)
# ============================================================


class Redactor(ABC):
    """
    Contract for PII redaction applied to all ticket fields
    before storage or display.

    Implementations must:
      - Replace all 10-digit DoD IDs matching \\b\\d{10}\\b
        with REDACTED_DOD_ID token
      - Achieve 100% redaction coverage — zero tolerance for missed IDs
      - Not redact numeric strings that are not DoD IDs
      - Return input string unchanged if no DoD IDs are found
    """

    @abstractmethod
    def redact(self, input: str) -> str:
        """
        Scan input string and replace all DoD ID matches.

        Args:
            input: Raw string that may contain DoD ID numbers.

        Returns:
            str: Redacted string with all DoD IDs replaced by
                 REDACTED_DOD_ID. Unchanged if no matches found.
        """
        ...


# ============================================================
# CLASSIFIER INTERFACE — BOUNDARY
# Owned by: Classifier team
# Do not implement bodies here.
# ============================================================


class Classifier(ABC):
    """
    Boundary interface between the ID Generation team and the
    Classifier team.

    The Classifier team owns all implementation bodies.
    This team (ID Generation) consumes this interface only.

    Contract:
      - Accepts a raw TicketForm and returns a classified Ticket
      - Exactly one Category must be assigned — never empty
      - Timeline must be parseable to a valid future datetime
      - Description and POC fields must not be empty
      - Raises TicketError(INVALID_CATEGORY) for unrecognized category
      - Raises TicketError(MISSING_TIMELINE) for absent or unparseable date
    """

    @abstractmethod
    def classify(self, form: TicketForm) -> Ticket:
        """
        Accept a raw TicketForm and return a classified Ticket.

        Args:
            form: Raw structured form submission from CSS team member.

        Returns:
            Ticket: Classified ticket with Category, Priority, Timeline,
                    Description, and POCs populated. ID not yet assigned.

        Raises:
            TicketError: INVALID_CATEGORY if category cannot be mapped.
            TicketError: MISSING_TIMELINE if Need By Date is absent or invalid.
        """
        ...


# ============================================================
# ROUTER INTERFACE — BOUNDARY
# Owned by: Router team
# Do not implement bodies here.
# ============================================================


class Router(ABC):
    """
    Boundary interface between the ID Generation team and the
    Router team.

    The Router team owns all implementation bodies.
    This team (ID Generation) consumes this interface only.

    Queue ordering contract:
      - Sort by Priority ascending (1 → 3)
      - Break ties within the same Priority tier by Timeline ascending
      - Priority 1 tickets always appear before Priority 2 and 3
        regardless of Timeline value
      - No ticket may be omitted from the sorted output
    """

    @abstractmethod
    def enqueue(self, ticket: Ticket) -> None:
        """
        Insert a fully assigned Ticket into the priority queue.

        Args:
            ticket: Ticket with a valid, assigned ID.

        Raises:
            TicketError: INVALID_SEQUENCE if ticket.id is empty.
        """
        ...

    @abstractmethod
    def list(self) -> list[Ticket]:
        """
        Return all tickets in the queue in sorted order.
        Priority 1 tickets always appear first, ties broken by Timeline.

        Returns:
            list[Ticket]: Sorted list — never empty list on error;
                          raises instead.

        Raises:
            TicketError: COUNTER_UNAVAILABLE if queue cannot be read.
        """
        ...
