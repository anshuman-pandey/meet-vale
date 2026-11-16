# Meet Vale

### Find a time without the timezone guesswork.

Propose meeting times, collect yes/maybe/no responses, and export the final choice to a calendar. A focused, self-hosted alternative to Doodle for group availability polls.

[![CI](https://github.com/anshuman-pandey/meet-vale/actions/workflows/test.yml/badge.svg)](https://github.com/anshuman-pandey/meet-vale/actions/workflows/test.yml) · [MIT license](LICENSE) · Python + SQLite · Self-hosted

![Meet Vale: actual application workspace](docs/assets/workspace.png)

**Public source preview.** The local workflow and container recovery have been tested. There is no hosted demo or tagged product release yet; public HTTPS acceptance remains pending.

## How it works

1. Create a poll with future slots in an IANA timezone and an explicit UTC offset.
2. Share the poll. Guests respond yes, maybe or no and keep a private link to update their answers.
3. Choose one final slot to freeze responses, then download an ICS calendar event.

## Try it locally

Requires Git, Python 3 and Docker with the Compose plugin.

```sh
git clone https://github.com/anshuman-pandey/meet-vale.git
cd meet-vale
python3 scripts/setup.py
docker compose up --build -d
```

Open **http://127.0.0.1:8102**. Read the generated private `.env` file locally and use its `MEET_OWNER_KEY` value to unlock the owner workspace. Setup retains any existing `.env`; do not commit or share this file.

The app binds to localhost and stores data in a persistent Docker volume. Links pointing to localhost work only on your computer. For remote sharing, follow the [HTTPS deployment and backup guide](docs/DEPLOYMENT.md). Avoid `docker compose down -v` unless you intend to delete the stored data.

## Included

- Daylight-saving gaps are rejected; repeated hours require an explicit offset.
- Aggregate availability counts and separate private response-update credentials.
- Calendar export with stable event identifiers and UTC times.

**Interface languages:** English and Spanish. German, Japanese, Simplified Chinese and Traditional Chinese are planned. User-authored content is never translated.

## Know the boundaries

Up to 200 polls, 20 slots per poll and 100 participant records. Slots must be within 366 days, with durations from five minutes to 12 hours. Names are self-reported and one person can submit multiple responses. Calendar import was checked with Khal 0.14.1; other clients remain unverified. No calendar synchronization, email notifications, recurring meetings or account system.

Private links and reviewer keys grant access to whoever holds them. Keep the owner key separate from participant credentials. This project covers the workflow above, not the full feature set of its commercial reference.

## Development and checks

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The published baseline passed **20 Python tests**. Recorded browser acceptance covers: poll creation, timezone/dst validation, guest responses, finalization and ics export/import. Container restart and clean-volume backup/restore were also checked. See the [validation record](artifacts/validation.json) for the exact evidence and remaining acceptance gates.

Bug reports should include reproduction steps and browser/runtime versions, with private keys and client data removed. Focused fixes and improvements are welcome through [issues](https://github.com/anshuman-pandey/meet-vale/issues) and pull requests.

## Documentation

[Deployment & backups](docs/DEPLOYMENT.md) · [Calendar guide](docs/CALENDAR.md) · [Api guide](docs/API.md) · [Scope & comparison](docs/SCOPE.md) · [Validation evidence](artifacts/validation.json) · [License](LICENSE)
