# Meet Vale · development core

An open-source alternative for Doodle's group scheduling workflow, in preparation.

Implemented locally: immutable proposed slots, guest yes/maybe/no responses, private participant update credentials, aggregate counts, one final choice and UTC iCalendar export. No HTTP API, browser UI, hosted demo or public release yet.

```sh
python3 -m unittest discover -s tests -v
```

Use Python 3.12 on Linux with system timezone data. No third-party runtime packages are needed for the core. Proposed times require explicit offsets matching an IANA timezone. Nonexistent daylight-saving times are rejected; repeated local times are disambiguated by their offset. Slots must begin within 366 days and last 5 minutes to 12 hours.

Limits: 200 polls, 20 slots per poll, 100 participant records per poll. The invite secret grants poll viewing and participation; each participant gets a separate secret for updating only their own response. Secrets are hashed at rest. Display names are not verified identities, and people holding the invite can create multiple responses. Counts describe records, not verified unique people. Participant names are not exposed in the shared aggregate view.

Finalization freezes responses and selects one future slot; calendar exports use stable event IDs, UTC times, escaped text and UTF-8 line folding. Calendar import into actual calendar clients remains unverified. No email, calendar connection, notifications, recurring meetings, file attachments or Doodle feature parity is promised.

Owner methods currently rely on the calling code to authorize access. Do not expose this library directly as a public service. The next steps are an authenticated API, owner/guest browser workflow, six interface languages and persistent deployment/recovery acceptance.

[Scope and primary references](docs/SCOPE.md) · [MIT license](LICENSE)
