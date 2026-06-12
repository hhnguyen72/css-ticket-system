"""
mocks/mock_router.py
--------------------
Mock implementation of the Router boundary interface.

Purpose:
    Allows the ID Generation team to develop and test ticket enqueue
    and queue ordering logic — including Priority 1 pinning and
    Need By Date tie-breaking — without blocking on the Router team.

Scope:
    Test and development use only. Must not be used in production.

Behavior:
    - enqueue(): Inserts a Ticket into an in-memory queue.
    - list(): Returns tickets sorted by Priority ascending, then
              Timeline ascending within the same tier.
    - Priority 1 tickets always appear before Priority 2 and 3
      tickets regardless of Timeline value — per REQ-08.
    - Raises TicketError if ticket has no ID assigned.
    - Error simulation: Force read failure via constructor flag.
"""

from __future__ import annotations

from src.protocols import Router
from src.models import Ticket, TicketError, TicketErrorCode

class MockRouter(Router):
    """
    In-memory mock Router for use in ID Generation team tests.

    Args:
        force_queue_read_failure: If True, list() raises COUNTER_UNAVAILABLE.
    """

    def __init__(self, force_queue_read_failure: bool = False) -> None:
        self._queue: list[Ticket]        = []
        self._force_queue_read_failure   = force_queue_read_failure

    def enqueue(self, ticket: Ticket) -> None:
        """
        Insert a fully assigned Ticket into the in-memory queue.

        Raises:
            TicketError: INVALID_SEQUENCE if ticket.id is empty —
                         ID must be assigned before enqueue.
        """
        if not ticket.id:
            raise TicketError(
                TicketErrorCode.INVALID_SEQUENCE,
                f"MockRouter: ticket cannot be enqueued without an assigned ID. "
                f"Call TicketIDService.assign() before enqueue().",
            )
        self._queue.append(ticket)

    def list(self) -> list[Ticket]:
        """
        Return all tickets in sorted order.

        Sort contract (per REQ-05, REQ-08):
          1. Priority ascending (1 → 3) — Priority 1 always first.
          2. Timeline ascending within the same Priority tier.
          3. No ticket omitted from output.

        Raises:
            TicketError: COUNTER_UNAVAILABLE if force_queue_read_failure is set.
        """
        if self._force_queue_read_failure:
            raise TicketError(
                TicketErrorCode.COUNTER_UNAVAILABLE,
                "MockRouter: simulated queue read failure.",
            )

        return sorted(
            self._queue,
            key=lambda t: (t.priority.value, t.timeline),
        )

    # --------------------------------------------------------
    # Test helpers — not part of Router interface contract
    # --------------------------------------------------------

    def clear(self) -> None:
        """Reset the in-memory queue. Use between test cases."""
        self._queue = []

    def count(self) -> int:
        """Return the number of tickets currently in the queue."""
        return len(self._queue)

    def find_by_id(self, ticket_id: str) -> Ticket | None:
        """
        Return the ticket matching the given ID, or None if not found.
        Used in tests to assert ID stability after re-ranking.
        """
        return next((t for t in self._queue if t.id == ticket_id), None)
