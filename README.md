# Meet Vale · local API preview

An open-source alternative for Doodle's group scheduling workflow, in preparation.

Implemented locally: immutable proposed slots, guest yes/maybe/no responses, private participant update credentials, aggregate counts, one final choice and UTC iCalendar export. Authenticated HTTP API included; no browser UI, hosted demo or public release yet.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Use Python 3.12 on Linux with system timezone data. The domain core uses the standard library; the HTTP service uses Flask. Proposed times require explicit offsets matching an IANA timezone. Nonexistent daylight-saving times are rejected; repeated local times are disambiguated by their offset. Slots must begin within 366 days and last 5 minutes to 12 hours.

Limits: 200 polls, 20 slots per poll, 100 participant records per poll. The invite secret grants poll viewing and participation; each participant gets a separate secret for updating only their own response. Secrets are hashed at rest. Display names are not verified identities, and people holding the invite can create multiple responses. Counts describe records, not verified unique people. Participant names are not exposed in the shared aggregate view.

Finalization freezes responses and selects one future slot; calendar exports use stable event IDs, UTC times, escaped text and UTF-8 line folding. Calendar import into actual calendar clients remains unverified. No email, calendar connection, notifications, recurring meetings, file attachments or Doodle feature parity is promised.

The included HTTP service authenticates owner operations and separates invite and participant credentials. [Run the local API](docs/API.md). Twenty domain/HTTP tests pass. The next steps are the owner/guest browser workflow, six interface languages, actual calendar-client import and persistent deployment/recovery acceptance.

[Scope and primary references](docs/SCOPE.md) · [MIT license](LICENSE)
