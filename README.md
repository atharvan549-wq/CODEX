# Instagram 4-Letter Username Availability Checker

A Python 3 command-line project that systematically processes every 4-letter username from `aaaa` through `zzzz` (`26^4 = 456,976` combinations) without loading all combinations into memory.

The checker is intentionally conservative. It does **not** hard-code scraping, CAPTCHA bypasses, login automation, IP-block evasion, or other anti-automation techniques. By default, non-dry-run checks return `unknown` until you connect `check_username()` in `checker.py` to an officially permitted Instagram/API mechanism or another verification method you are authorized to use.

## Project structure

```text
.
├── README.md
├── checker.py
└── requirements.txt
```

Runtime output defaults to `output/`:

```text
output/
├── available.txt
├── checkpoint.txt
├── results.csv
├── taken.txt
└── unknown.txt
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No third-party Python packages are currently required.

## Usage

Dry-run a small sample without external requests:

```bash
python checker.py --dry-run --limit 25 --delay 0 --output output
```

Resume from the last successfully saved username:

```bash
python checker.py --resume --output output
```

Process a bounded generated range:

```bash
python checker.py --start aaaa --end abzz --dry-run
```

Process only usernames matching a pattern:

```bash
python checker.py --pattern 'ab??' --dry-run
```

Process a custom list:

```bash
python checker.py --list usernames.txt --dry-run
```

## Command-line options

- `--start`: first generated 4-letter username, inclusive; default `aaaa`.
- `--end`: last generated 4-letter username, inclusive; default `zzzz`.
- `--resume`: continue after the last username written to `checkpoint.txt`.
- `--output`: result directory; default `output`.
- `--limit`: maximum usernames to process in the current run.
- `--pattern`: shell-style filter such as `ab??`.
- `--list`: custom username file, one username per line.
- `--dry-run`: test mode that makes no external requests.
- `--delay`: delay between checks in seconds; default `1.0`.
- `--retries`: retry count for temporary checker failures; default `3`.

## Output files

- `available.txt`: usernames that appear available.
- `taken.txt`: usernames that appear taken.
- `unknown.txt`: usernames that could not be verified.
- `results.csv`: append-only CSV with `username,status,timestamp`.
- `checkpoint.txt`: the most recently persisted username for resume support.

Each result is appended and flushed to disk, then the checkpoint is atomically replaced. If the process is interrupted, `--resume` continues after the last successfully checkpointed username.

## Authorized checking only

The function `check_username(username)` is isolated in `checker.py`. Replace its non-dry-run branch only with an official, permitted, or otherwise authorized verification method. Respect Instagram's rate limits and terms of service, and do not attempt to bypass CAPTCHAs, authentication requirements, IP blocks, or other anti-bot protections.
