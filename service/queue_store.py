"""
services/queue_store.py
------------------------
File-backed persistence for the CSS ticket queue.

Serializes and deserializes Ticket objects to/from a JSON file so that
tickets survive across CLI invocations (each `python main.py` is a new process).

Storage: ~/.css_ticket/queue.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from models import Category, POC, Priority, Ticket, TicketID

QUEUE_PATH = Path.home() / ".css_ticket" / "queue.json"


def _ticket_to_dict(ticket: Ticket) -> dict:
    return {
        "id":          str(ticket.id),
        "category":    ticket.category.value,
        "priority":    ticket.priority.value,
        "timeline":    ticket.timeline.isoformat(),
        "description": ticket.description,
        "created_at":  ticket.created_at.isoformat(),
        "pocs": [
            {"name": p.name, "email": p.email, "phone": p.phone}
            for p in ticket.pocs
        ],
    }


def _dict_to_ticket(d: dict) -> Ticket:
    return Ticket(
        id          = TicketID(d["id"]),
        category    = Category(d["category"]),
        priority    = Priority(d["priority"]),
        timeline    = datetime.fromisoformat(d["timeline"]),
        description = d["description"],
        created_at  = datetime.fromisoformat(d["created_at"]),
        pocs        = [
            POC(name=p["name"], email=p["email"], phone=p["phone"])
            for p in d.get("pocs", [])
        ],
    )


def load_queue() -> list[Ticket]:
    """Load all tickets from the queue file. Returns empty list if none exist."""
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_PATH.exists():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text())
        return [_dict_to_ticket(d) for d in data]
    except Exception:
        return []


def save_queue(tickets: list[Ticket]) -> None:
    """Persist all tickets to the queue file."""
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps([_ticket_to_dict(t) for t in tickets], indent=2))


def append_ticket(ticket: Ticket) -> None:
    """Load existing queue, append new ticket, save back."""
    tickets = load_queue()
    tickets.append(ticket)
    save_queue(tickets)
