"""
main.py
-------
CSS Ticket Management Tool — CLI entrypoint.

Usage:
    python main.py submit
    python main.py list
    python main.py submit --non-interactive  (reads JSON from stdin)

Commands:
    submit   Interactively submit a new ticket and receive a ticket ID
    list     Display all tickets in priority-sorted order

Examples:
    python main.py submit
    python main.py list
    echo '{"category":"Record Update","priority":"High","timeline":"2026-06-20",
           "description":"Test.","poc":""}' | python main.py submit --non-interactive
"""

from __future__ import annotations

import json
import sys

from models import TicketForm
from service.classifier import CSSClassifier
from service.id_generator import CSSIDGenerator
from service.queue_store import append_ticket, load_queue
from service.redactor import DoDRedactor
from service.sequence_counter import FileSequenceCounter
from service.ticket_id import CSSTicketIDService

# ============================================================
# Shared service instances
# ============================================================

_classifier = CSSClassifier()
_id_service = CSSTicketIDService(
    generator = CSSIDGenerator(),
    counter   = FileSequenceCounter(),
    redactor  = DoDRedactor(),
)

CATEGORY_OPTIONS = [
    "SEL/Commander's Signature",
    "Record Update",
    "Dissemination Info",
]

PRIORITY_OPTIONS = [
    "Critical",
    "High",
    "Low",
]

# ============================================================
# Formatting helpers
# ============================================================

PRIORITY_LABEL = {1: "🔴 CRITICAL", 2: "🟡 HIGH", 3: "🟢 LOW"}
CATEGORY_LABEL = {
    1: "SEL/Commander's Signature",
    2: "Record Update",
    3: "Dissemination Info",
}

DIVIDER    = "─" * 60
DIVIDER_SM = "─" * 40


def print_banner() -> None:
    print(f"\n{'═'*60}")
    print("  CSS Ticket Management Tool")
    print(f"{'═'*60}\n")


def print_ticket(ticket, index: int | None = None) -> None:
    prefix = f"[{index}] " if index is not None else ""
    pocs   = ticket.pocs

    print(f"\n{DIVIDER}")
    print(f"{prefix}Ticket ID : {ticket.id}")
    print(f"{DIVIDER_SM}")
    print(f"  Category  : {CATEGORY_LABEL.get(ticket.category.value, ticket.category.name)}")
    print(f"  Priority  : {PRIORITY_LABEL.get(ticket.priority.value, ticket.priority.name)}")
    print(f"  Need By   : {ticket.timeline.strftime('%Y-%m-%d')}")
    print(f"  Created   : {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Description:")
    print(f"    {ticket.description or '(none)'}")
    if pocs:
        print(f"  POC(s):")
        for poc in pocs:
            parts = [p for p in [poc.name, poc.email, poc.phone] if p]
            print(f"    · {' | '.join(parts)}")
    else:
        print(f"  POC(s)    : (none)")
    print(f"{DIVIDER}")


# ============================================================
# Submit command
# ============================================================

def prompt_choice(prompt: str, options: list[str]) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input("  Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  ⚠  Please enter a number between 1 and {len(options)}.")


def cmd_submit(non_interactive: bool = False) -> None:
    if non_interactive:
        raw = sys.stdin.read().strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"\n❌  Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)

        form = TicketForm(
            raw_category    = data.get("category", ""),
            raw_priority    = data.get("priority", ""),
            raw_timeline    = data.get("timeline", ""),
            raw_description = data.get("description", ""),
            raw_poc         = data.get("poc", ""),
        )
    else:
        print_banner()
        print("  Submit a New Ticket\n")

        category = prompt_choice("Category:", CATEGORY_OPTIONS)
        priority = prompt_choice("Priority:", PRIORITY_OPTIONS)

        timeline = ""
        while not timeline:
            timeline = input("\nNeed By Date (YYYY-MM-DD): ").strip()
            if not timeline:
                print("  ⚠  Need By Date is required.")

        print("\nDescription (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        description = "\n".join(lines).strip()

        print("\nPOC (format: Name: ... | Email: ... | Phone: ...)")
        print("Leave blank if not applicable.")
        poc = input("POC: ").strip()

        form = TicketForm(
            raw_category    = category,
            raw_priority    = priority,
            raw_timeline    = timeline,
            raw_description = description,
            raw_poc         = poc,
        )

    try:
        ticket = _classifier.classify(form)
        ticket = _id_service.assign(ticket)
        append_ticket(ticket)           # persist to ~/.css_ticket/queue.json
    except Exception as e:
        print(f"\n❌  Ticket creation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n✅  Ticket created successfully:")
    print_ticket(ticket)


# ============================================================
# List command
# ============================================================

def cmd_list() -> None:
    print_banner()
    tickets = sorted(
        load_queue(),
        key=lambda t: (t.priority.value, t.timeline),
    )

    if not tickets:
        print("  No tickets in queue.\n")
        return

    print(f"  {len(tickets)} ticket(s) — sorted by priority and Need By Date\n")
    for i, ticket in enumerate(tickets, 1):
        print_ticket(ticket, index=i)
    print()


# ============================================================
# Entry point
# ============================================================

def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    command         = args[0].lower()
    non_interactive = "--non-interactive" in args

    if command == "submit":
        cmd_submit(non_interactive=non_interactive)
    elif command == "list":
        cmd_list()
    else:
        print(f"\n❌  Unknown command: '{command}'", file=sys.stderr)
        print("    Usage: python main.py [submit|list]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
