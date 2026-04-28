# Krunchies Bot

Telegram bot for club operations, training sign-ups, custom named polls, task tracking, reminders, partner logging, production milestones, announcements, and Gemini-powered assistance.

## Features

- Training, event, and competition sign-up cards with live named lists.
- Custom named polls via `/newpoll`.
- Inline poll publishing support when inline mode is enabled in BotFather.
- Admin-only training, event, competition, milestone, partner, and announcement workflows.
- Task management with 24-hour and 1-hour reminders.
- Event reminders with 24-hour and 1-hour notifications.
- Attendance check-in for same-day training via `/here`.
- Chat allowlisting and admin authorization through environment variables.
- SQLite persistence with optional configurable database path.
- Gemini assistant that answers from current bot data.

## Tech Stack

- Python 3.10+
- `python-telegram-bot`
- SQLite
- APScheduler
- Google Gemini API
- `python-dotenv`

## Project Structure

```text
Krunchies-Bot/
├── src/
│   ├── main.py
│   ├── database/
│   │   ├── connection.py
│   │   └── repos/
│   ├── handlers/
│   ├── services/
│   ├── utils/
│   └── views/
├── .env.example
├── .gitignore
├── Procfile
├── README.md
└── requirements.txt
```

## Prerequisites

- Python 3.10 or newer.
- Telegram bot token from BotFather.
- Gemini API key from Google AI Studio.
- Optional: inline mode enabled in BotFather if you want the `Publish poll` button to work.

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

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Fill in the values in `.env`. Do not commit `.env`.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather. |
| `GEMINI_API_KEY` | Yes, for AI | Google Gemini API key. |
| `GEMINI_MODEL` | No | Gemini model name. Defaults to `gemini-1.5-flash`. |
| `BOT_TIMEZONE` | No | Timezone for reminders. Defaults to `Asia/Singapore`. |
| `DB_PATH` | No | SQLite database path. Defaults to `club.db`. |
| `ALLOWED_CHAT_IDS` | Recommended | Comma-separated Telegram chat IDs allowed to use the bot. |
| `ADMIN_IDS` | Recommended | Comma-separated Telegram user IDs with admin privileges. |

## Running Locally

```powershell
python -m src.main
```

If you see a Telegram `409 Conflict`, another instance of the same bot token is already running. Stop the deployed worker or the other local process before starting this one.

## Command Reference

### General

| Command | Access | Description |
| --- | --- | --- |
| `/start` | All | Register user and show welcome message. |
| `/help` | All | Show command help. |

### Tasks

| Command | Access | Description |
| --- | --- | --- |
| `/addtask` | All | Create a task with title, description, deadline, and assignee. |
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

### Custom Polls

| Command | Access | Description |
| --- | --- | --- |
| `/newpoll` | All | Create a custom named poll with up to 10 options. |
| `/done` | Poll creator flow | Finish and publish a poll while creating it. |
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
| `/addmilestone Title \| YYYY-MM-DD` | Admin | Add a production milestone. |
| `/announce <message>` | Admin | Send a formatted announcement. |

## Custom Poll Workflow

1. Run `/newpoll`.
2. Send the poll title.
3. Send each option as a separate message.
4. Run `/done` to publish.
5. Members tap buttons to add or remove their names.
6. The poll owner or an admin can close, reopen, publish, or delete the poll.

For inline publishing, enable inline mode for the bot in BotFather. Then use the `Publish poll` button or type the bot username in another chat and choose the poll result.

## Security

- `.env` is ignored by git and must never be committed.
- `club.db` is ignored by git because it can contain member and event data.
- `__pycache__` and `*.pyc` files are ignored.
- Use `ALLOWED_CHAT_IDS` to prevent random chats from using the bot.
- Use `ADMIN_IDS` for bootstrap admin access.
- If a bot token is ever pasted in logs or chat, revoke and rotate it in BotFather.

## Deployment

The included `Procfile` starts the bot as a worker:

```text
worker: python -m src.main
```

Only one running instance may poll Telegram for a given bot token. If you run the bot locally while it is deployed, stop the deployed worker first or use a separate test bot token.

SQLite persistence depends on where the bot is hosted. On ephemeral platforms, configure `DB_PATH` to point at a persistent volume or migrate to a managed database before production use.

## Development Checks

Before committing:

```powershell
python -m compileall -q src
git status --short --ignored
git check-ignore -v .env club.db src\__pycache__
```

Optional manual smoke test:

```powershell
python -m src.main
```

Then try `/help`, `/newpoll`, `/addtraining`, and `/headcount <id>` in Telegram.

## Troubleshooting

### `409 Conflict`

Another copy of the same bot is already running. Stop the other local process or deployed worker.

### Bot ignores your private messages

If `ALLOWED_CHAT_IDS` is set, private chats are restricted. Admin users listed in `ADMIN_IDS` can still use private chat commands.

### Inline publish does not appear

Enable inline mode for the bot in BotFather.

### Gemini says the API key is not configured

Check `GEMINI_API_KEY` in `.env`, then restart the bot.
