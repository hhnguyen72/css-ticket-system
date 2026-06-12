"""
services/id_generator.py
------------------------
SL-02: Concrete implementation of IDGenerator.

Generates a formatted TicketID from a date string and sequence number.
Format: CSS-YYYYMMDD-NNNN
"""

from __future__ import annotations

from models import (
    SEQUENCE_FLOOR,
    TICKET_ID_DELIMITER,
    TICKET_ID_PREFIX,
    TicketError,
    TicketErrorCode,
    TicketID,
)
from protocols import IDGenerator


class CSSIDGenerator(IDGenerator):
    """
    Generates CSS ticket IDs in the format CSS-YYYYMMDD-NNNN.

    Rules:
      - date must be exactly 8 numeric characters (YYYYMMDD)
      - sequence must be >= SEQUENCE_FLOOR (1)
      - sequence is zero-padded to 4 digits minimum, no upper cap
    """

    def generate(self, date: str, sequence: int) -> TicketID:
        if not date.isdigit() or len(date) != 8:
            raise TicketError(
                TicketErrorCode.INVALID_DATE,
                f"IDGenerator: date '{date}' must be exactly 8 numeric characters (YYYYMMDD).",
            )

        if sequence < SEQUENCE_FLOOR:
            raise TicketError(
                TicketErrorCode.INVALID_SEQUENCE,
                f"IDGenerator: sequence {sequence} is below floor {SEQUENCE_FLOOR}.",
            )

        padded = f"{sequence:04d}"
        return TicketID(
            f"{TICKET_ID_PREFIX}{TICKET_ID_DELIMITER}{date}{TICKET_ID_DELIMITER}{padded}"
        )
