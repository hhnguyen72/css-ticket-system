# ADR-002: Command-Line Interface

**Status:** Accepted  
**Date:** 2026-06-12  
**Deciders:** Jacob Kosswig, Hung Nguyen, Neharika Bhandari

---

## Context

The system needs a user interface and a data persistence layer. A web front end requires hosting infrastructure, firewall exceptions, and expanded ATO surface area — none of which are viable on a government network without significant approval overhead. A CLI runs locally within existing network boundaries with no additional infrastructure. On storage, the current user base is small enough that local shared file storage is sufficient; PostgreSQL becomes necessary as request volume and concurrent access grow.

This decision sets the interface and persistence approach for initial deployment and defines when each should be revisited.

---

## Options Considered

## Options Considered

| | CLI + Local File Storage | Web UI + PostgreSQL |
|---|---|---|
| Network access | Works within gov network constraints | Requires hosting, firewall rules, ATO expansion |
| Deployment complexity | Low — runs locally | High — server, TLS, auth layer required |
| Token efficiency | Higher — local spec bundles, fewer round-trips | Lower — remote storage adds API calls |
| Scalability | Degrades under concurrent load | Handles concurrency natively |
| User accessibility | Requires terminal familiarity | Lower barrier for non-technical users |
| Operational overhead | Minimal | Database + hosting require ongoing ops |

---

## Decision

**CLI interface with local shared file storage. PostgreSQL via Docker scoped as the migration target when volume justifies it.**

---

## Rationale

- CLI is the only interface that clears government network constraints without new approvals.
- Local storage eliminates round-trip latency and reduces token consumption per session.
- PostgreSQL overhead isn't justified at current scale — but the migration path is already defined, not deferred.

---

## Consequences

**Positive:**
- No hosting infrastructure required
- Reduced ATO surface area. Faster deployment
- Lower token cost per session
- Migration path pre-scoped

**Negative:**
 - CLI requires terminal familiarity — not viable for all users
 - File storage doesn't scale under concurrent load
 - No dashboard or real-time visibility without additional tooling
 - Direct API calls would be faster; multi-step flows compound latency.

---

## Revisit Triggers

Re-evaluate this decision if:

- File storage causes locking or consistency errors as request volume grows → migrate to PostgreSQL.
- Leadership requests a web-accessible interface for reporting or broader access.
- CLI friction blocks user adoption, particularly for non-technical personnel.
- Latency in multi-step flows becomes measurable and impactful.
- Users cannot reliably obtain or run the CLI (availability/distribution problem).