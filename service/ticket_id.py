"""
services/ticket_id_service.py
------------------------------
SL-05: TicketIDService — wires IDGenerator, SequenceCounter, and Redactor.

Assigns a unique TicketID to a classified Ticket at the moment of creation.
Applies DoD ID redaction to description and POC fields before returning.
"""

from __future__ import annotations

from datetime import datetime

from models import Ticket, TicketError, TicketErrorCode
from protocols import IDGenerator, Redactor, SequenceCounter, TicketIDService


class CSSTicketIDService(TicketIDService):
    """
    Coordinates ID generation, sequence management, and redaction.

    Args:
        generator: IDGenerator implementation (CSSIDGenerator)
        counter:   SequenceCounter implementation (FileSequenceCounter)
        redactor:  Redactor implementation (DoDRedactor)
    """

    def __init__(
        self,
        generator: IDGenerator,
        counter:   SequenceCounter,
        redactor:  Redactor,
    ) -> None:
        self._generator = generator
        self._counter   = counter
        self._redactor  = redactor

    def assign(self, ticket: Ticket) -> Ticket:
        # Resolve today's date — reject if clock fails
        try:
            today = datetime.now().strftime("%Y%m%d")
        except Exception as e:
            raise TicketError(
                TicketErrorCode.UNRESOLVABLE_DATE,
                f"TicketIDService: cannot resolve server date: {e}",
            )

        # Get next sequence number for today
        sequence = self._counter.next(today)

        # Generate the formatted ID
        ticket.id = self._generator.generate(today, sequence)

        # Apply redaction to description and all POC fields
        ticket.description = self._redactor.redact(ticket.description)
        for poc in ticket.pocs:
            poc.name  = self._redactor.redact(poc.name)
            poc.email = self._redactor.redact(poc.email)
            poc.phone = self._redactor.redact(poc.phone)

        return ticket
