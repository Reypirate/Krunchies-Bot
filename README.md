# Krunchies Bot

Krunchies Bot is a Telegram group-management bot for SMU Ardiente club operations. It supports named sign-ups, custom polls, task tracking, reminders, attendance, pairings, production milestones, announcements, and a Gemini-powered assistant that can answer from current club data.

## Features

- Training, event, competition, and custom poll sign-up cards with live named lists.
- Single-choice sign-ups for training, events, and custom polls.
- Multi-choice competition sign-ups.
- Natural-language date input for tasks, training, events, competitions, and production milestones.
- Task and event reminders at about 24 hours and 1 hour before the stored datetime.
- Attendance check-in for same-day training sessions with `/here`.
- Admin-only workflows for club operations.
- Chat allowlisting and bootstrap admin authorization through environment variables.
- SQLite persistence with a configurable database path.
- Gemini assistant with current bot data injected as context.

## Tech Stack

- Python 3.11+
- `python-telegram-bot` v22
- SQLite
- APScheduler
- Google Gemini API
- `dateparser`
- `python-dotenv`

## Repository Layout

```text
Krunchies-Bot/
|-- src/
|   |-- main.py                  # App bootstrap, handler registration, scheduler startup
|   |-- database/
|   |   |-- connection.py         # SQLite connection and schema initialization
|   |   `-- repos/                # Data-access functions
|   |-- handlers/                 # Telegram command, conversation, and callback handlers
|   |-- services/                 # Scheduler and Gemini service wrappers
|   |-- utils/                    # Formatting, security, and time helpers
|   `-- views/                    # Inline keyboards and message templates
|-- .env.example
|-- Procfile
|-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.11 or newer.
- A Telegram bot token from BotFather.
- A Google AI Studio Gemini API key if you want the AI assistant enabled.
- Optional: inline mode enabled in BotFather if you want poll publishing from inline results.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Fill in `.env`. Never commit real secrets or production database files.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather. |
| `GEMINI_API_KEY` | For AI | Google Gemini API key. The bot still runs without it, but AI replies are disabled. |
| `GEMINI_MODEL` | No | Gemini model name. Defaults to `gemini-1.5-flash`. |
| `BOT_TIMEZONE` | No | IANA timezone for parsing dates and reminders. Defaults to `Asia/Singapore`. |
| `DB_PATH` | No | SQLite database path. Defaults to `club.db`. |
| `ALLOWED_CHAT_IDS` | Recommended | Comma-separated Telegram chat IDs allowed to use the bot. |
| `ADMIN_IDS` | Recommended | Comma-separated Telegram user IDs with admin privileges. |

## Running Locally

```powershell
python -m src.main
```

Only one process can poll Telegram for the same bot token. If you see a `409 Conflict`, stop the deployed worker or any other local process using that token.

## Date Input

Date prompts accept natural language and strict datetime strings. The bot parses dates in `BOT_TIMEZONE`, requires future dates for new records, and stores accepted values as `YYYY-MM-DD HH:MM`.

Examples:

```text
next wednesday 7pm
15 june 6pm
tomorrow 18:00
2026-06-15 18:00
```

This applies to `/addtask`, `/addtraining`, `/addevent`, `/addcomp`, and `/addmilestone Title | date/time`.

## Command Reference

### General

| Command | Access | Description |
| --- | --- | --- |
| `/start` | All | Register the user and show a welcome message. |
| `/help` | All | Show command help. |

### Tasks

| Command | Access | Description |
| --- | --- | --- |
| `/addtask` | All | Create a task with title, description, deadline, and optional assignee. |
| `/tasks` | All | List pending tasks in the current chat. |
| `/mytasks` | All | List tasks assigned to your Telegram username. |
| `/done <id>` | All | Mark a task as done. |
| `/deletetask <id>` | Admin | Delete a task. |

### Training and Events

| Command | Access | Description |
| --- | --- | --- |
| `/addtraining` | Admin | Create a training session and sign-up card. |
| `/training` | All | List scheduled training sessions. |
| `/here` | All | Mark attendance for today's training. |
| `/addevent` | Admin | Create an event and sign-up card. |
| `/events` | All | List upcoming events. |
| `/deleteevent <id>` | Admin | Delete an event and close its linked sign-up sheet. |

### Polls

| Command | Access | Description |
| --- | --- | --- |
| `/newpoll` | All | Create a custom named poll with up to 10 options. |
| `/done` | Poll creation flow | Finish and publish a poll while creating it. |
| `/polls` | Poll creator | List your custom polls. |
| `/viewpoll <id>` | Poll owner or admin | Repost a poll management card. |
| `/headcount <id>` | Chat members | Show a summary for a sign-up sheet or poll. |
| `/deletepoll <id>` | Poll owner or admin | Delete a custom poll. |

### Competitions and Partners

| Command | Access | Description |
| --- | --- | --- |
| `/addcomp` | Admin | Create a competition sign-up card. |
| `/partners` | All | List pairings for the current chat. |
| `/addpair @member1 @member2 [context]` | Admin | Add a pairing. |

### Production and Announcements

| Command | Access | Description |
| --- | --- | --- |
| `/prodstatus` | All | Show production milestones. |
| `/addmilestone Title \| date/time` | Admin | Add a production milestone with a natural-language or strict datetime deadline. |
| `/announce <message>` | Admin | Send a formatted announcement. |

## Sign-up Behavior

- Training, events, and custom polls are single-choice: tapping a new option moves the user from their previous option.
- Competitions are multi-choice: each style option is toggled independently.
- Inline callback data uses option indexes to stay within Telegram's 64-byte callback limit.
- Poll owners and admins can close, reopen, publish, or delete custom polls.

## Custom Poll Workflow

1. Run `/newpoll`.
2. Send the poll title.
3. Send each option as a separate message.
4. Run `/done` to publish.
5. Members tap buttons to add or remove their names.
6. The poll owner or an admin can close, reopen, publish, or delete the poll.

For inline publishing, enable inline mode in BotFather. Then use the `Publish poll` button or type the bot username in another chat and choose the poll result.

## Deployment

The included `Procfile` starts the bot as a worker:

```text
worker: python -m src.main
```

SQLite persistence depends on the host. On ephemeral platforms, set `DB_PATH` to a persistent volume or migrate to a managed database before production use.

## Development Checks

Before committing, run:

```powershell
python -m compileall -q src
git diff --check
git status --short
```

Suggested manual smoke test:

```text
/help
/newpoll
/addtask
/addtraining
/headcount <id>
```

## Security Notes

- `.env` must remain untracked.
- `club.db` may contain member, chat, and event data; keep it out of git.
- Use `ALLOWED_CHAT_IDS` to restrict where the bot responds.
- Use `ADMIN_IDS` for bootstrap admin access.
- Rotate `BOT_TOKEN` immediately if it appears in logs, screenshots, commits, or chat.
- Run only one polling worker per Telegram bot token.

## Troubleshooting

### `409 Conflict`

Another process is polling Telegram with the same token. Stop the other process or use a separate test bot token.

### Bot ignores a chat

If `ALLOWED_CHAT_IDS` is set, the current chat ID must be listed. Admin users in `ADMIN_IDS` can still use private chat commands.

### Inline publish does not appear

Enable inline mode for the bot in BotFather.

### AI replies are disabled

Set `GEMINI_API_KEY` in `.env`, confirm `GEMINI_MODEL` if customized, and restart the bot.
