"""
services/router.py
-------------------
Production Router implementation.

Manages the CSS ticket queue with priority-ordered output.
Sorts by Priority ascending (1→3), ties broken by Timeline ascending.
Priority 1 tickets always appear before Priority 2 and 3.
"""

from __future__ import annotations

import threading

from models import Ticket, TicketError, TicketErrorCode
from protocols import Router


class CSSRouter(Router):
    """
    In-memory priority queue for CSS tickets.
    Thread-safe for single-service use.
    """

    def __init__(self) -> None:
        self._queue: list[Ticket] = []
        self._lock  = threading.Lock()

    def enqueue(self, ticket: Ticket) -> None:
        if not ticket.id:
            raise TicketError(
                TicketErrorCode.INVALID_SEQUENCE,
                "Router: ticket must have an assigned ID before enqueue. "
                "Call TicketIDService.assign() first.",
            )
        with self._lock:
            self._queue.append(ticket)

    def list(self) -> list[Ticket]:
        with self._lock:
            return sorted(
                self._queue,
                key=lambda t: (t.priority.value, t.timeline),
            )
