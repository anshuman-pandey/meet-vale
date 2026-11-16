# Authenticated local API preview

Use Python 3.12 on Linux with system timezone data:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export MEET_OWNER_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export MEET_DATABASE=meet.sqlite3
python server.py
```

The development service listens only on `127.0.0.1:8102`. No browser workspace or production deployment is included yet. Keep the owner key private. All credentials must be sent as `Authorization: Bearer <key>`; query-string keys are not accepted. The database stores hashed invite and participant secrets, never the owner key.

| Route | Credential | Behavior |
| --- | --- | --- |
| GET /api/polls | Owner | List poll metadata without secrets |
| POST /api/polls | Owner | Create title, IANA zone and slots; returns invite token once |
| GET /api/polls/{id} | Owner | Aggregate counts and final choice |
| POST /api/polls/{id}/finalize | Owner | JSON `index`, zero-based slot index; freezes responses |
| GET /api/shared/{id} | Invite | Shared metadata and aggregate counts; no participant names |
| POST /api/shared/{id}/participants | Invite | JSON `name`, `votes`; returns participant ID and update token once |
| PUT /api/shared/{id}/participants/{guest} | Participant | JSON `votes`; updates only that participant in that poll |
| GET /api/shared/{id}/calendar.ics | Invite | Finalized event attachment; no automatic invitation or notification |

Example create body (choose future dates):

```json
{"title":"Team review","zone":"Europe/London","slots":[{"start":"2027-01-20T10:00:00+00:00","end":"2027-01-20T11:00:00+00:00"}]}
```

Each vote list must contain one `yes`, `maybe` or `no` for every slot. Proposed slots are immutable. Save both invitation and participant update credentials when returned: they cannot be retrieved later. Display names do not establish identity; one person can submit multiple participant records.

Requests are limited to 64 KiB. Missing/wrong owner or invitation credentials return 401. Domain validation (including rejected participant updates, finalized polls and missing records) returns 400. Invalid content types return 415; oversized requests 413; storage unavailability 503. Errors are JSON. Responses disable caching, framing and referrer disclosure; no CORS is enabled.

Tests cover the HTTP workflow using Flask's test client. Actual browser acceptance, calendar-client import, six-language UI, persistent deployment/restore and public HTTPS remain pending. No remote access or public publication is configured.
