# Secure Art Gallery (BIBIFI Group 7, CS 5/43401 - Secure Programming, Fall 2026)

This is a web application for tracking people's movements through a physical art gallery. Employees can record when people
enter and leave the gallery and its rooms, staff can see who is where and search the movement history,
and administrators manage accounts and rooms, and can query an append-only security log. Guests see only their own
location, and may optionally provide some personal information.

Built by **James Markijohn** and **Samaa Hediya**.

## Tech stack

| Layer | Technology |
|---|---|
| Reverse proxy and HTTPS | Caddy (serves React frontend, proxies `/api/`, adds security headers) |
| Frontend | React 19, built with Vite, React Router |
| Backend | Python 3.14, Django 6.1 |
| Database | PostgreSQL 18 |
| Backups | Scheduled with `pg_dump`, encrypted with `age` |
| Deployment | Four containers built with Docker Compose |

## Architecture

This application consists of four containers, which are described below:

- **web** is the only container reachable from the internet. It serves the built React app and forwards
  `/api/*` requests to the backend over Docker's internal network.
- **backend** has no published ports. It sits behind Caddy (which is in the `web` container) and in front of `db`.
- **db** is on the `backend` (`internal`) network only. Like `backend`, it has no published ports and is not reachable from the internet.
- **backup** dumps the PostgreSQL database in `db` once a day, encrypting the dump with a public key before it is written to the disk.

The trust boundaries, data-flow diagram, ERD, and STRIDE threat model can be found at
`docs/design_document.pdf`.

## Installation

**Requirements:** Docker with Docker Compose v2, Git, and `openssl`. Python3 is also needed for running the test scripts.

**Windows:**
- Install Docker Desktop with its default settings. If prompted to install Windows Subsystem for Linux (WSL), do so.
- Install Git for Windows. Git Bash will be needed to run several commands.
- Open Docker Desktop before running any commands in Git Bash.
- Run every command below in Git Bash, *not* in a PowerShell or Command Prompt window. ./setup.sh will create a .env file with randomized secrets, and the backup-private.key is used by the `backup` container for backup encryption.

```sh
git clone https://github.com/jamesmarkijohn/secure-programming-project-fall-2026.git
cd secure-programming-project-fall-2026
./setup.sh
docker compose up --build -d
```

To confirm setup worked, run `grep -c change-me .env`. The output should be `0`, indicating that all placeholder `change-me` values were replaced with randomized secrets.

Run the next command to ensure that all four containers (`db`, `backend`, `web`, `backup`) show as `Up`:

```sh
docker compose ps
```

This application does not have default credentials. Create the first administrator account:

```sh
docker compose exec backend python manage.py create_admin
```

The administrator password must be at least 8 characters in length. MFA setup will take place on first login in the web interface.

In a web browser, open https://localhost. The certificate is issued by Caddy's local certificate authority, so the
browser will warn about it. This can be disregarded. Sign in as the administrator and complete MFA registration.

**Note:** Keep `backup-private.key` and `.env` private. The key is the only way to restore a backup, and
`.env` holds every secret required by Django, PostgreSQL, etc. On Linux and macOS, `setup.sh` makes both
readable only by the user account that ran the script.

### Troubleshooting

- **`web` will not start and mentions ports 80 or 443 in errors:** Another program is using that/those port(s). Stop that program, then run `docker compose up -d` again.
- **A `502` error or a blank page at https://localhost right after starting:** the backend is still starting. Wait a few seconds and refresh.
- **`backend` keeps restarting:** Run `docker compose logs backend` and read the latest errors. A common error encountered during development was
  `Required environment variable <variable> is not set`, which means `.env` is incomplete. Run `./setup.sh` again.

### Stopping and resetting

Use `docker compose down` to stop the application, or `docker compose down -v` to stop and delete the application's data (including backup). Use `./setup.sh --force` to recreate secrets, which is recommended after bringing down the containers and deleting data.

## Database setup

Setup is entirely automatic. On every start, the backend container:

1. Applies Django migrations, which create every table, constraint, and the append-only triggers on the security log.
2. Loads the gallery floor plan from `database/seed.sql`, (only on fresh databases). After that,
   administrators manage rooms through the app, and restarts do not undo their changes. To re-apply the database 
   seed deliberately to recreate the database, use `docker compose exec backend python manage.py load_seed --force`.
3. Creates the internal system account that security events with no associated user are attributed
   to. It has an unusable password and can never sign in.

`database/schema.sql` documents the resulting schema. It is exported from a running database rather, not hard-coded. If it must be regenerated, use:

```sh
docker compose exec -T db sh -c 'pg_dump --schema-only --no-owner --no-privileges -U "$POSTGRES_USER" "$POSTGRES_DB"' > database/schema.sql
```

### Tables

| Table | Purpose |
|---|---|
| `accounts` | Users: email, Argon2id password hash, role, current room, encrypted name, phone, and MFA secret |
| `gallery_rooms` | Rooms, including the `Outside` room indicating users who are not in the gallery, and whether each room is staff-only |
| `adjacent_rooms` | Connections between rooms (each stored once, smaller room ID first) |
| `movement_events` | Every move records person, from-room, to-room, time, and who recorded it |
| `security_log` | Append-only security events; details are encrypted |
| `rate_limit_hits` | Recent requests, for rate limiting (this table has no relationship with other tables) |

### Backups

The `backup` container writes an `age`-encrypted dump to the `backups` volume on start and every 24 hours,
keeping seven days. To restore a backup, use:

```sh
docker compose exec backup ls /backups
docker compose cp backup:/backups/<file>.sql.age .
docker compose exec db createdb -U gallery restore_test
age -d -i backup-private.key <file>.sql.age | docker compose exec -T db psql -q -U gallery -d restore_test
```

`age` must be installed on your machine for this. Consult https://github.com/filosottile/age for assistance with installation.

## Roles

| Role | Creation Method | Capabilities |
|---|---|---|
| Guest | Signs up on the sign-in page | See their own location on the map, edit their own name and phone, delete their own account |
| Employee | Created by an administrator | See their own location, edit their own name and phone, record movements, see everyone's location, search the movement history |
| Administrator | Created by an administrator (the first with `create_admin`) | Everything an employee can, plus manage accounts (roles, details, MFA reset, deletion), delete bad movement events, manage room access and connections, query the security log |

Every role is enforced by the server on every request.
Signing up always creates a guest, regardless of what the request says.

## Using the application

- **Home** (`/`, everyone): the currently authenticated user's details, their location on the gallery map, and (for guests) account deletion.
- **Staff** (`/staff`, employees and administrators): record a movement, view the occupancy map with who is
  in each room, query movement history. Administrators also see a Delete button on movement events.
- **Admin** (`/admin`, administrators): account management, creating employee and administrator accounts, room adjacency management,
  and querying the security log.

A person enters the gallery by moving from `Outside` to an entrance room (by default, these are Lobby, Staff Offices, or
Lecture Hall), leaves by moving from one of those to `Outside`, and enters or leaves a room by
moving to a connected room. Every move must start from the person's current room and go to a connected
one.

## API endpoints

All endpoints are under `https://localhost/api/` and exchange JSON data. Every `POST` action must include the
`X-CSRFToken` header, using the token from the `csrftoken` cookie (this is set by `GET /api/auth/csrf/`).

### Authentication and own account

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/api/health/` | Anyone | Confirms the backend is reachable |
| GET | `/api/auth/csrf/` | Anyone | Sets the CSRF cookie |
| POST | `/api/auth/register/` | Anyone | Create a guest account, requires `email`, `password`, optionally takes `full_name`, `phone` |
| POST | `/api/auth/login/` | Anyone | Takes `email`, `password`. If MFA is not yet set up for that account, the response includes the secret and QR-code URI. |
| POST | `/api/auth/verify-mfa/` | Accounts that have completed MFA setup | Takes `code` (six digits). Completes authentication. |
| POST | `/api/auth/logout/` | Authenticated | Ends the session |
| GET | `/api/auth/me/` | Authenticated | Your email and role |
| GET, POST | `/api/auth/profile/` | Authenticated | View, or update `full_name` and `phone` |
| POST | `/api/auth/delete-account/` | Guest | Delete own account. Takes `password`. Account's location must be outside gallery. |

### Gallery

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/api/gallery/my-location/` | Authenticated | Get current room |
| GET | `/api/gallery/rooms/` | Employee, Admin | Gets all rooms and adjacencies |
| GET | `/api/gallery/occupancy/` | Employee, Admin | Get room occupancy |
| POST | `/api/gallery/moves/` | Employee, Admin | Record a move. Takes `person_id`, `room_id` of the destination. |
| GET | `/api/gallery/movement-history/` | Employee, Admin | Search moves. Can filter with `person_id`, `room_id`, `since`, `until` (timestamp are in ISO 8601 format). |
| POST | `/api/gallery/events/<event_id>/delete/` | Admin | Delete a bad or duplicate movement event |

### Administration

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/api/admin/accounts/` | Admin | List accounts. Takes `role`, `email`, `include_deleted=1`. |
| POST | `/api/admin/accounts/create/` | Admin | Create an employee or admin. Takes `email`, `password`, `role`. |
| GET | `/api/admin/accounts/<id>/` | Admin | One account, including decrypted name and phone (this view is logged) |
| POST | `/api/admin/accounts/<id>/update/` | Admin | Change any of `role`, `full_name`, `phone` |
| POST | `/api/admin/accounts/<id>/reset-mfa/` | Admin | Issue a new MFA secret, which the user sets up again at next sign-in |
| POST | `/api/admin/accounts/<id>/delete/` | Admin | Delete an account |
| GET | `/api/admin/rooms/` | Admin | Unifiied admin view of rooms, adjacencies, and occupants |
| POST | `/api/admin/rooms/<id>/update/` | Admin | Contains `is_restricted` |
| POST | `/api/admin/rooms/connect/` | Admin | Takes `room_a_id`, `room_b_id` |
| POST | `/api/admin/rooms/disconnect/` | Admin | Takes `room_a_id`, `room_b_id` |
| GET | `/api/audit/security-logs/` | Admin | Search the security log. Filter by `event_type`, `user_id`, `since`, `until`. |

Common error codes for APIs are listed below:
- 400: invalid input
- 401: not authenticated or authentication failure
- 403: forbidden
- 404: not found
- 429: rate limited

## Testing

There are 92 automated tests: 28 functional and 64 security. They are located next to the code they test
(`src/backend/*/test*.py`), tagged `functional` or `security`, and run inside the backend container
against a temporary test database, so the real data is not touched. With the app running, run the first command for the functional tests, the second command for the security tests, and use the third command's syntax to list each individual test in the output:

```sh
python3 tests/functional/func-test.py
python3 tests/security/sec-test.py
python3 tests/security/sec-test.py -v 2
```

**Note:** Any new tests must be tagged `@tag("functional")` or `@tag("security")`, or these scripts will not run them.

The security tests include role checks on every endpoint, along with tests for account lockout, rate limits, CSRF cookies, SQL injection
and malformed input, identical responses for every failed sign-in, session invalidation, simultaneous
moves, and the database refusing any change to the security log.

## Security controls

| Area | Control |
|---|---|
| Passwords | Argon2id hashing, at least 8 characters, common passwords rejected |
| Authentication | Mandatory TOTP MFA for every account |
| Brute force | Accounts lock for 5 minutes after 5 wrong passwords, 10 sign-in attempts per 5 minutes per client IP, 10 database queries per minute per account |
| Account enumeration | Unknown email, wrong password, and locked account get the same message, status, and response time |
| Sessions | Server-side sessions, cookies with `Secure`, `HttpOnly`, `SameSite=Strict`, new session ID at sign-in, 60 seconds to finish MFA (this window is extended to 5 minutes during first-time setup), 8-hour inactivity timeout. Every session ends when the user's password, role, or MFA secret changes, or the account is deleted. |
| Authorization | Role checked on every endpoint, deny by default, no endpoint accepts another user's ID to read or change their own-account data. Users signing up cannot choose a role for themselves, and admins cannot demote or delete themselves |
| CSRF | Django CSRF tokens on every state-changing request, including sign-in |
| SQL injection | All queries through the Django ORM, which parameterizes the queries |
| XSS | React escapes all output. Content Security Policy allows only same-origin scripts. |
| Input validation | Server-side type, length, and format checks on every field, strict query-filter parsing |
| Business logic | Moves validated against current room and room connections, inside one transaction that locks the person's row, so simultaneous requests cannot create an invalid state |
| Encryption | HTTPS in transit. Names, phone numbers, MFA secrets, and security-log details encrypted at rest with field-level Fernet encryption. Backups encrypted with age. |
| Audit logging | Security log of sign-ins, failures, lockouts, account changes, admin actions, personal-data views, database queries, and guests entering staff-only rooms. Log is append-only, enforced by database triggers. |
| Privacy | Guests see only their own location. Deleted accounts are pseudonymized, meaning the identity is removed, but account activity history remains. |
| Secrets | All secrets in `.env`, generated randomly by `setup.sh`. No default credentials |
| Common Misconfigurations | Debugging modes are disabled. No Django admin site. Generic error messages. Only Caddy is exposed to the internet; database is on an internal network. The backend and backup containers run as non-root users. |

## Known limitations

- Single machine: this runs locally with Docker Compose. Production scaling and a publicly trusted
  certificate are out of scope.
- Fixed floor plan: the map is drawn from a hard-coded floor plan, so administrators can change
  room access and connections but cannot add, rename, or remove rooms without editing the source code.
- No self-service password reset or MFA recovery: a user who loses their authenticator needs an
  administrator to reset their MFA.
- Rate limits are per IP address: clients behind one shared address (a proxy or NAT) share a limit.
- Lockout can be abused: anyone who knows an account's email can lock it for five minutes by
  repeatedly guessing wrong. The per-IP rate limit slows this down but does not prevent it.
