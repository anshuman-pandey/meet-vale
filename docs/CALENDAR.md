# Calendar import acceptance

Meet Vale exports one finalized event as an iCalendar attachment. It uses UTC DTSTART/DTEND, a stable random UID per poll, CRLF line endings, escaped text and UTF-8 folding at 75 octets. It does not send invitations, synchronize accounts, verify attendance or update calendar copies automatically.

## Verified client

Khal 0.14.1 imported actual exported files into a disposable local calendar on 16 November 2026. Acceptance verified:

- Long Unicode titles and comma, semicolon and backslash characters survive import.
- New York's repeated 01:00–01:30 hour on 1 November 2026 is distinguishable by explicit offsets: -04:00 imports at 05:00–05:30 UTC; -05:00 imports at 06:00–06:30 UTC.
- Re-importing the same export updates the same UID instead of creating a third event.
- Exactly two distinct events remain in the isolated calendar after three imports.

No connected or personal calendar is touched. The test creates and removes its own configuration, calendar files and cache. This proves compatibility with the tested Khal version only; Apple Calendar, Google Calendar, Outlook and other clients remain unverified.

## Reproduce

```sh
python3 -m venv /tmp/meet-calendar-venv
/tmp/meet-calendar-venv/bin/pip install khal==0.14.1
KHAL=/tmp/meet-calendar-venv/bin/khal python3 scripts/calendar_acceptance.py
```

The fixture uses an injected historical clock to keep the repeated-hour acceptance deterministic. This does not change production validation: users may finalize only future slots. Inspect the event's date, timezone and duration in your chosen calendar before relying on it.
