"""
services/sequence_counter.py
-----------------------------
SL-03 / SL-04: SequenceCounter with file-based persistence.

Maintains a per-day sequence number that:
  - Increments on every call to next()
  - Resets to SEQUENCE_FLOOR at the start of a new calendar day
  - Persists across service restarts via a JSON file
  - Is safe for single-process concurrent use via file locking
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from models import SEQUENCE_FLOOR, TicketError, TicketErrorCode
from protocols import SequenceCounter


class FileSequenceCounter(SequenceCounter):
    """
    File-backed sequence counter. State is stored as JSON at `store_path`.

    File format:
        {"date": "20260612", "sequence": 4}

    Args:
        store_path: Path to the JSON persistence file.
                    Defaults to ~/.css_ticket/sequence.json
    """

    DEFAULT_STORE = Path.home() / ".css_ticket" / "sequence.json"

    def __init__(self, store_path: Path | None = None) -> None:
        self._path  = Path(store_path) if store_path else self.DEFAULT_STORE
        self._lock  = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Public interface
    # --------------------------------------------------------

    def next(self, date: str) -> int:
        with self._lock:
            state = self._read()
            if state.get("date") != date:
                # New calendar day — reset sequence
                state = {"date": date, "sequence": SEQUENCE_FLOOR}
            else:
                state["sequence"] += 1
            self._write(state)
            return state["sequence"]

    def current(self, date: str) -> int:
        with self._lock:
            state = self._read()
            if state.get("date") != date:
                return SEQUENCE_FLOOR
            return state.get("sequence", SEQUENCE_FLOOR)

    # --------------------------------------------------------
    # Private helpers
    # --------------------------------------------------------

    def _read(self) -> dict:
        try:
            if self._path.exists():
                return json.loads(self._path.read_text())
            return {}
        except Exception as e:
            raise TicketError(
                TicketErrorCode.COUNTER_UNAVAILABLE,
                f"SequenceCounter: failed to read state from {self._path}: {e}",
            )

    def _write(self, state: dict) -> None:
        try:
            self._path.write_text(json.dumps(state))
        except Exception as e:
            raise TicketError(
                TicketErrorCode.COUNTER_UNAVAILABLE,
                f"SequenceCounter: failed to write state to {self._path}: {e}",
            )
