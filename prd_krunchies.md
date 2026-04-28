# 📋 Product Requirements Document
## Krunchies Club Planner Telegram Bot

**Version:** 2.0
**Club:** SMU Krunchies (Latin Ballroom Dance)
**Stack:** Python, python-telegram-bot, SQLite, APScheduler, Gemini API
**Hosting:** Railway (free tier)

---

## 1. Overview

A Telegram bot for SMU Ardiente's club management. Members can track tasks, training sessions, competitions, and production milestones — with Count Me In-style named sign-up sheets, automated reminders, partner tracking, and a Gemini-powered AI assistant.

---

## 2. Goals

- Keep members on top of tasks, training, and competition deadlines
- Replace manual headcount pings with structured named sign-up sheets
- Track competition entries, partner pairings, and dance styles per member
- Centralise Un Paso production tracking (roles, milestones, deadlines)
- Automate reminders so admins don't have to chase people

---

## 3. Users

| Role | Description |
|---|---|
| **Admin** | Exco; full control over all features, can post announcements |
| **Member** | Regular member; can sign up, check in, view schedules |

---

## 4. Core Mechanic — Named Sign-Up Sheets (Count Me In style)

Every training session, event, or competition posted by the bot generates a **sign-up sheet card** — a live message with named, numbered lists under each option. Members tap inline buttons to add or remove their own name. No typing needed.

### Sign-Up Card Format (Training example)
```
🕺 Training — Wed 14 May, 7–9PM
📍 SMU Sports Hall B
Focus: Technique

Coming (3):
1. Alice Tan
2. Bob Lim
3. Charlie Ng

Not Coming (1):
1. Dana Koh

[ ✅ Count Me In ] [ ❌ Can't Make It ]
```

### Sign-Up Card Format (Competition example)
```
🏆 SBDTA Open 2025 — 21 Jun
📍 Singapore Expo, Hall 4
Reg Deadline: 1 Jun

Cha-Cha (2):        Rumba (1):
1. Alice Tan         1. Bob Lim
2. Charlie Ng

Jive (0):           Samba (3):          Paso Doble (0):
                     1. Alice Tan
                     2. Dana Koh
                     3. Eve Goh

[ Cha-Cha ] [ Rumba ] [ Jive ] [ Samba ] [ Paso Doble ] [ Not Competing ]
```

### Sign-Up Behaviour
- Tapping a button **adds your display name** to that option's numbered list
- Tapping the same button again **removes your name** (toggle)
- Switching options removes you from the previous one (for single-choice cards like training)
- For competitions, members can sign up for **multiple dance styles** simultaneously
- The card message **edits itself live** after each tap — no extra messages in chat
- Admins see a **🔒 Close Sign-Up** button to lock the sheet; bot posts a final summary
- Names shown are Telegram first names (or display names), not @usernames, for readability

### Sign-Up Commands
| Command | Description |
|---|---|
| `/signup <id>` | Admin reposts a sign-up card for a session/event |
| `/headcount <id>` | Show current tally without reposting |

---

## 5. Features

### 5.1 Task Management
- Create a task with title, description, and deadline (date + time)
- Assign to one or more members by Telegram username
- `/tasks` — view all upcoming tasks sorted by deadline
- `/mytasks` — view your personally assigned tasks
- `/done <task_id>` — mark a task complete
- Admins can delete tasks via `/deletetask <id>`

### 5.2 Event Management
- Create a club event with title, description, and date
- Every event auto-generates a Count Me In sign-up card (Coming / Not Coming)
- `/events` — view all upcoming events with live sign-up counts
- Reminders sent to the group 24 hours and 1 hour before
- Admins delete events via `/deleteevent <id>`

### 5.3 Training Management
- Post a training session with day, time, location, and focus (e.g. Technique / Competition Prep)
- Every training post auto-generates a sign-up card (Coming / Not Coming)
- Members mark in-session attendance with `/here` (links to that day's training)
- `/training` — view this week's schedule with live sign-up counts
- **Automatic reminders:**
  - Tuesday ~8 PM → Wednesday training reminder + sign-up card repost
  - Friday ~8 PM → Saturday training reminder + sign-up card repost
- Admins can set a recurring weekly template so the schedule auto-posts

### 5.4 Competition Tracking
- `/addcomp` — create a competition entry with name, date, venue, registration deadline, and dance styles offered (Cha-Cha, Rumba, Jive, Samba, Paso Doble)
- Bot posts a competition sign-up card where members tap their dance styles
- Members can select multiple styles; a "Not Competing" option is also shown
- `/mycomps` — member views their registered competitions and dances
- `/complist <comp_id>` — admin views full competitor list per dance
- **Automated reminders to signed-up competitors:**
  - Registration deadline − 7 days and − 1 day
  - Competition date − 7 days and − 1 day

### 5.5 Partner Management
- `/partners` — view current practice pairings (per competition or session)
- `/addpair @member1 @member2 <context>` — admin logs a pairing for a comp or session
- `/mypairs` — member views their current and past partners
- Pairing history is stored so admins can reference past rotations

### 5.6 Un Paso Production
- Dedicated production tracker via `/production`
- Roles tracked: Choreography, Costume, Screenplay, Logistics, Publicity
- `/prodtask` — add a production task assigned to a role and member
- Named milestone deadlines with dedicated reminders:
  - e.g. "Script Lock", "Costume Fitting", "Dress Rehearsal", "Show Day"
- `/prodstatus` — visual checklist of all milestones (✅ done / 🔲 pending)
- `/prodtasks` — all open production tasks filtered by role
- Production tasks share the same reminder engine as regular tasks

### 5.7 Reminder System
| Trigger | Recipient | Timing |
|---|---|---|
| Task deadline | Assigned member(s) | −24 h, −1 h |
| Event | Group chat | −24 h, −1 h |
| Training (Wed) | Group chat | Tuesday ~8 PM |
| Training (Sat) | Group chat | Friday ~8 PM |
| Comp registration deadline | Signed-up competitors | −7 days, −1 day |
| Comp date | Signed-up competitors | −7 days, −1 day |
| Production milestones | Assigned role members | −7 days, −1 day |

### 5.8 Announcements
- `/announce <message>` — admin broadcasts to the group, prefixed with 📢 **Ardiente Announcement**
- Announcement log kept so admins can review past broadcasts

### 5.9 AI Assistant (Gemini)
- Any free-text message (not a command) is handled by Gemini
- Context-aware: queries the DB and passes structured context before responding
- Can answer things like:
  - "Who signed up for Saturday training?"
  - "Who's competing in Jive at SBDTA?"
  - "What production tasks are still open for Costume?"

---

## 6. Commands Reference

### General
| Command | Access | Description |
|---|---|---|
| `/start` | All | Onboard user, show help |
| `/help` | All | List all commands |

### Tasks
| Command | Access | Description |
|---|---|---|
| `/addtask` | All | Add a task with deadline |
| `/assign` | All | Assign a task to a member |
| `/tasks` | All | View all upcoming tasks |
| `/mytasks` | All | View your assigned tasks |
| `/done <task_id>` | All | Mark task as complete |
| `/deletetask <id>` | Admin | Delete a task |

### Events
| Command | Access | Description |
|---|---|---|
| `/addevent` | Admin | Add an event (auto-creates sign-up card) |
| `/events` | All | View upcoming events + sign-up counts |
| `/deleteevent <id>` | Admin | Delete an event |

### Training
| Command | Access | Description |
|---|---|---|
| `/addtraining` | Admin | Post a training session (auto-creates sign-up card) |
| `/training` | All | View this week's schedule + sign-up counts |
| `/here` | Member | Mark attendance for today's training |

### Competitions
| Command | Access | Description |
|---|---|---|
| `/addcomp` | Admin | Add a competition with dance styles (auto-creates sign-up card) |
| `/mycomps` | Member | View your registered competitions |
| `/complist <id>` | Admin | View all competitors per dance |

### Partners
| Command | Access | Description |
|---|---|---|
| `/partners` | All | View current practice pairings |
| `/addpair` | Admin | Log a practice pair |
| `/mypairs` | Member | View your current and past partners |

### Production
| Command | Access | Description |
|---|---|---|
| `/production` | All | View production milestone status |
| `/prodtask` | Admin | Add a production task |
| `/prodtasks` | All | View open production tasks by role |
| `/prodstatus` | All | Visual checklist of all milestones |

### Sign-Ups
| Command | Access | Description |
|---|---|---|
| `/signup <id>` | Admin | Repost a sign-up card |
| `/headcount <id>` | All | Show current sign-up tally |

### Announcements
| Command | Access | Description |
|---|---|---|
| `/announce <msg>` | Admin | Broadcast an announcement to the group |

---

## 7. Data Models

### Tasks
```
id, title, description, deadline (datetime), assigned_to (username),
created_by, status (pending/done), category (general/production),
production_role, chat_id
```

### Events
```
id, title, description, event_date (datetime), created_by,
signup_sheet_id, chat_id
```

### Training Sessions
```
id, date (datetime), location, focus (technique/comp_prep/social),
recurrence (none/weekly), signup_sheet_id, chat_id
```

### Attendance
```
id, training_id, user_id, checked_in_at
```

### Competitions
```
id, name, comp_date (datetime), venue, registration_deadline,
dance_styles (JSON list), created_by, signup_sheet_id, chat_id
```

### Competition Entries
```
id, comp_id, user_id, dance_style, registered_at
```

### Partners
```
id, member1_id, member2_id, context (comp_id or training_id), paired_at
```

### Production Milestones
```
id, title, deadline (datetime), status (pending/done), chat_id
```

### Sign-Up Sheets
```
id, entity_type (event/training/comp), entity_id,
message_id, chat_id, options (JSON list), is_closed, created_at
```

### Sign-Up Responses
```
id, sheet_id, user_id, display_name, option_chosen, responded_at
```

### Users
```
telegram_id, display_name, username, chat_id, role (admin/member), joined_at
```

### Announcements
```
id, text, sent_by, sent_at, chat_id
```

---

## 8. Tech Stack

| Layer | Tool |
|---|---|
| Bot framework | `python-telegram-bot` v20+ (async) |
| AI | Google Gemini API (`google-generativeai`) |
| Database | SQLite via `sqlite3` |
| Scheduler | `APScheduler` |
| Hosting | Railway |
| Config | `.env` via `python-dotenv` |

---

## 9. Project Structure

```
ardiente-bot/
├── bot.py               # Entry point
├── database.py          # DB init & queries
├── scheduler.py         # APScheduler reminder jobs
├── handlers/
│   ├── tasks.py         # Task commands
│   ├── events.py        # Event commands
│   ├── training.py      # Training + /here attendance
│   ├── competitions.py  # Comp tracking
│   ├── partners.py      # Partner pairing
│   ├── production.py    # Un Paso production
│   ├── signups.py       # Count Me In sign-up sheet logic
│   ├── announce.py      # /announce
│   └── ai.py            # Free-text Gemini handler
├── gemini.py            # Gemini API wrapper
├── requirements.txt
├── Procfile             # Railway: worker: python bot.py
└── .env                 # BOT_TOKEN, GEMINI_API_KEY
```

---

## 10. Non-Functional Requirements

- Bot responds within 3 seconds for commands
- Sign-up card edits (inline button taps) update within 1 second via callback query
- Reminders fire within ±1 minute of scheduled time
- SQLite DB persisted via Railway volume (or migrate to Supabase for persistence)
- No passwords stored; auth is Telegram identity only
- Admin-only commands silently reject non-admins with a friendly message

---

## 11. Out of Scope (v1.0)

- Web dashboard
- Payment / fee collection for events
- File attachments on tasks
- Multi-club / multi-workspace support
- Video/music upload for choreo reference
