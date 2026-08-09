#!/usr/bin/env python3
"""Instagram 4-letter username availability checker.

This tool is intentionally conservative: it does not include scraping,
authentication bypasses, CAPTCHA handling, or anti-bot evasion. The default
checker is a dry-run/authorized placeholder so operators can wire in an
officially permitted or otherwise authorized verification mechanism.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import itertools
import os
import random
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
TOTAL_FOUR_LETTER_USERNAMES = 26 ** 4
STATUSES = {"available", "taken", "unknown"}


class TemporaryCheckError(Exception):
    """Raised when a username check failed temporarily and can be retried."""


class PermanentCheckError(Exception):
    """Raised when a username check cannot be completed safely."""


@dataclass(frozen=True)
class CheckResult:
    username: str
    status: str
    timestamp: str


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for result records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def four_letter_usernames(start: str = "aaaa", end: str = "zzzz") -> Iterator[str]:
    """Yield lowercase A-Z 4-letter usernames from start through end."""
    validate_username_bound(start, "start")
    validate_username_bound(end, "end")
    if start > end:
        raise ValueError("--start must sort before or equal to --end")

    for chars in itertools.product(ALPHABET, repeat=4):
        username = "".join(chars)
        if username < start:
            continue
        if username > end:
            break
        yield username


def validate_username_bound(value: str, name: str) -> None:
    if len(value) != 4 or any(ch not in ALPHABET for ch in value):
        raise ValueError(f"--{name} must be exactly four letters from a-z")


def iter_pattern(pattern: str, start: str, end: str) -> Iterator[str]:
    """Yield generated usernames matching a shell-style pattern such as ab??."""
    for username in four_letter_usernames(start, end):
        if fnmatch.fnmatchcase(username, pattern.lower()):
            yield username


def iter_custom_list(path: Path) -> Iterator[str]:
    """Yield normalized usernames from a custom list file, one per line."""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            username = line.strip().lower()
            if not username or username.startswith("#"):
                continue
            yield username


def check_username(username: str, *, dry_run: bool = False) -> str:
    """Return available, taken, or unknown for a username.

    Replace this function's non-dry-run branch with an officially permitted
    Instagram/API mechanism or another verification method you are authorized
    to use. Do not add scraping, CAPTCHA bypasses, login automation, IP-block
    evasion, or other techniques that violate Instagram's terms or safeguards.
    """
    if dry_run:
        # Deterministic-ish local behavior for demos/tests without network use.
        bucket = sum(ord(ch) for ch in username) % 10
        if bucket == 0:
            return "available"
        if bucket in {1, 2}:
            return "unknown"
        return "taken"

    # Safe default: no unauthorized checking method is hard-coded.
    return "unknown"


def checked_with_retries(username: str, *, dry_run: bool, retries: int, base_delay: float) -> str:
    """Check a username and retry temporary failures with exponential backoff."""
    attempt = 0
    while True:
        try:
            status = check_username(username, dry_run=dry_run)
            if status not in STATUSES:
                raise PermanentCheckError(f"invalid status returned: {status}")
            return status
        except TemporaryCheckError:
            if attempt >= retries:
                return "unknown"
            delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
            time.sleep(delay)
            attempt += 1
        except (PermanentCheckError, OSError):
            return "unknown"


class ResultStore:
    """Append-only result storage with checkpoint support."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.status_paths = {status: self.output_dir / f"{status}.txt" for status in STATUSES}
        self.csv_path = self.output_dir / "results.csv"
        self.checkpoint_path = self.output_dir / "checkpoint.txt"
        self._ensure_csv_header()

    def _ensure_csv_header(self) -> None:
        if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
            with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(["username", "status", "timestamp"])

    def append(self, result: CheckResult) -> None:
        with self.status_paths[result.status].open("a", encoding="utf-8") as handle:
            handle.write(result.username + "\n")
            handle.flush()
            os.fsync(handle.fileno())

        with self.csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([result.username, result.status, result.timestamp])
            handle.flush()
            os.fsync(handle.fileno())

        tmp_path = self.checkpoint_path.with_suffix(".tmp")
        tmp_path.write_text(result.username + "\n", encoding="utf-8")
        os.replace(tmp_path, self.checkpoint_path)

    def last_checkpoint(self) -> Optional[str]:
        if not self.checkpoint_path.exists():
            return None
        value = self.checkpoint_path.read_text(encoding="utf-8").strip().lower()
        return value or None

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for status, path in self.status_paths.items():
            if not path.exists():
                counts[status] = 0
                continue
            with path.open("r", encoding="utf-8") as handle:
                counts[status] = sum(1 for _ in handle)
        return counts


def successor(username: str) -> str:
    """Return the next lexicographic 4-letter username after username."""
    validate_username_bound(username, "checkpoint")
    chars = list(username)
    for idx in range(3, -1, -1):
        if chars[idx] != "z":
            chars[idx] = chr(ord(chars[idx]) + 1)
            return "".join(chars[: idx + 1] + ["a"] * (3 - idx))
    return "zzzz"


def dashboard(processed: int, total: Optional[int], counts: dict[str, int], current: str, started: float) -> None:
    elapsed = max(time.time() - started, 0.001)
    rate = processed / elapsed
    if total:
        pct = (processed / total) * 100
        remaining = max(total - processed, 0)
        eta = remaining / rate if rate else 0
        progress = f"{processed:,} / {total:,}"
        complete = f"{pct:.2f}%"
    else:
        eta = 0
        progress = f"{processed:,} / unknown"
        complete = "n/a"

    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write("Instagram Username Checker\n\n")
    sys.stdout.write(f"Progress: {progress}\n")
    sys.stdout.write(f"Completed: {complete}\n\n")
    sys.stdout.write(f"Available: {counts.get('available', 0):,}\n")
    sys.stdout.write(f"Taken: {counts.get('taken', 0):,}\n")
    sys.stdout.write(f"Unknown: {counts.get('unknown', 0):,}\n\n")
    sys.stdout.write(f"Current username: {current}\n")
    sys.stdout.write(f"Estimated remaining time: {format_seconds(eta)}\n")
    sys.stdout.flush()


def format_seconds(seconds: float) -> str:
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def build_username_iterator(args: argparse.Namespace) -> tuple[Iterable[str], Optional[int]]:
    if args.list:
        return iter_custom_list(Path(args.list)), None
    if args.pattern:
        return iter_pattern(args.pattern, args.start, args.end), None
    total = username_index(args.end) - username_index(args.start) + 1
    return four_letter_usernames(args.start, args.end), total


def username_index(username: str) -> int:
    validate_username_bound(username, "username")
    value = 0
    for ch in username:
        value = value * 26 + (ord(ch) - ord("a"))
    return value


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Python Instagram 4-letter username availability checker")
    parser.add_argument("--start", default="aaaa", help="first generated username, inclusive (default: aaaa)")
    parser.add_argument("--end", default="zzzz", help="last generated username, inclusive (default: zzzz)")
    parser.add_argument("--resume", action="store_true", help="continue after the last checkpointed username")
    parser.add_argument("--output", default="output", help="directory for result files (default: output)")
    parser.add_argument("--limit", type=int, help="maximum usernames to process in this run")
    parser.add_argument("--pattern", help="shell-style pattern filter, for example ab?? or a*c?")
    parser.add_argument("--list", help="custom username list file, one username per line")
    parser.add_argument("--dry-run", action="store_true", help="do not make external requests; use deterministic local statuses")
    parser.add_argument("--delay", type=float, default=1.0, help="delay between checks in seconds (default: 1.0)")
    parser.add_argument("--retries", type=int, default=3, help="temporary failure retries (default: 3)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    args.start = args.start.lower()
    args.end = args.end.lower()
    store = ResultStore(Path(args.output))

    if args.resume:
        checkpoint = store.last_checkpoint()
        if checkpoint and not args.list:
            args.start = successor(checkpoint)

    usernames, total = build_username_iterator(args)
    counts = store.counts()
    processed = 0
    started = time.time()
    interrupted = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    for username in usernames:
        if interrupted or (args.limit is not None and processed >= args.limit):
            break
        status = checked_with_retries(username, dry_run=args.dry_run, retries=args.retries, base_delay=max(args.delay, 0.1))
        store.append(CheckResult(username=username, status=status, timestamp=utc_timestamp()))
        counts[status] = counts.get(status, 0) + 1
        processed += 1
        dashboard(processed, total, counts, username, started)
        if args.delay > 0:
            time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
