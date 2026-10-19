"""Centralised logging setup: rotation by size and date, retention, redaction."""

import contextvars
import logging
import os
import re
import sys
import time
import uuid
from datetime import date, datetime
from logging.handlers import BaseRotatingHandler
from pathlib import Path


LOG_DIR = Path(os.getenv("LOG_DIR") or Path(__file__).with_name("logs"))
LOG_LEVEL = (os.getenv("LOG_LEVEL") or "INFO").upper()
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES") or 5 * 1024 * 1024)
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS") or 9)
LOG_TO_CONSOLE = (os.getenv("LOG_TO_CONSOLE") or "1").lower() not in {"0", "false", "no"}

APP_LOG_NAME = "app.log"
ERROR_LOG_NAME = "error.log"
AI_LOG_NAME = "ai_requests.log"
AI_LOGGER_NAME = "ai_api_requests"

APP_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | pid=%(process)d | %(request_id)s | "
    "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
)
AI_FORMAT = "%(asctime)s.%(msecs)03d | %(request_id)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_request_id = contextvars.ContextVar("request_id", default="-")
_configured = False

_SECRET_PATTERNS = (
    (re.compile(r"(/bot)[^/\s\"'?]+"), r"\1***"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+"), r"\1***"),
    (re.compile(r"(?i)((?:api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?)[^\s\"',}&]+"), r"\1***"),
)


def redact(text: str) -> str:
    """Mask bot tokens and API keys that may leak through URLs or errors."""
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def set_request_id(value: str | None = None) -> contextvars.Token:
    return _request_id.set(value or uuid.uuid4().hex[:12])


def reset_request_id(token: contextvars.Token) -> None:
    _request_id.reset(token)


class RequestIdFilter(logging.Filter):
    """Attach the current request id to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


class RedactingFormatter(logging.Formatter):
    """Formatter that never writes secrets, including inside tracebacks."""

    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


class DailySizeRotatingFileHandler(BaseRotatingHandler):
    """Rotate when the day changes or the file exceeds ``max_bytes``.

    Archives are named ``<stem>.<YYYY-MM-DD>.<n><suffix>`` where the date is the
    day the content was written. Archives older than ``retention_days`` are
    deleted on start-up and after every rotation.
    """

    def __init__(self, filename, max_bytes: int, retention_days: int, encoding="utf-8"):
        super().__init__(filename, mode="a", encoding=encoding, delay=False)
        self.max_bytes = max_bytes
        self.retention_days = retention_days
        self._path = Path(self.baseFilename)
        self._current_day = self._initial_day()
        self._delete_expired()

    def _initial_day(self) -> date:
        try:
            stat = self._path.stat()
            if stat.st_size > 0:
                return datetime.fromtimestamp(stat.st_mtime).date()
        except OSError:
            pass
        return date.today()

    def shouldRollover(self, record: logging.LogRecord) -> bool:
        if date.today() != self._current_day:
            return True
        try:
            size = self._path.stat().st_size
        except OSError:
            return False
        return size > 0 and size + len(self.format(record).encode("utf-8")) + 1 > self.max_bytes

    def doRollover(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None
        try:
            if self._path.exists() and self._path.stat().st_size > 0:
                self._path.rename(self._next_archive_path())
        except OSError:
            pass
        self._current_day = date.today()
        self.stream = self._open()
        self._delete_expired()

    def _next_archive_path(self) -> Path:
        index = 1
        while True:
            candidate = self._path.with_name(
                f"{self._path.stem}.{self._current_day.isoformat()}.{index}{self._path.suffix}"
            )
            if not candidate.exists():
                return candidate
            index += 1

    def _delete_expired(self) -> None:
        cutoff = time.time() - self.retention_days * 86400
        pattern = f"{self._path.stem}.*{self._path.suffix}"
        for archive in self._path.parent.glob(pattern):
            if archive == self._path:
                continue
            try:
                if archive.stat().st_mtime < cutoff:
                    archive.unlink()
            except OSError:
                pass


def _file_handler(name: str, level: int, fmt: str) -> DailySizeRotatingFileHandler:
    handler = DailySizeRotatingFileHandler(LOG_DIR / name, LOG_MAX_BYTES, LOG_RETENTION_DAYS)
    handler.setLevel(level)
    handler.setFormatter(RedactingFormatter(fmt, DATE_FORMAT))
    handler.addFilter(RequestIdFilter())
    return handler


def setup_logging() -> None:
    """Configure root and AI-payload loggers once per process."""
    global _configured
    if _configured:
        return
    _configured = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(_file_handler(APP_LOG_NAME, level, APP_FORMAT))
    root.addHandler(_file_handler(ERROR_LOG_NAME, logging.WARNING, APP_FORMAT))
    if LOG_TO_CONSOLE:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(level)
        console.setFormatter(RedactingFormatter(APP_FORMAT, DATE_FORMAT))
        console.addFilter(RequestIdFilter())
        root.addHandler(console)

    ai_logger = logging.getLogger(AI_LOGGER_NAME)
    ai_logger.setLevel(logging.INFO)
    ai_logger.propagate = False
    ai_logger.addHandler(_file_handler(AI_LOG_NAME, logging.INFO, AI_FORMAT))

    for noisy in ("werkzeug", "urllib3", "httpx", "httpcore", "openai"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))

    logging.captureWarnings(True)
    sys.excepthook = _log_uncaught
    logging.getLogger(__name__).info(
        "Logging started: dir=%s level=%s max_bytes=%d retention_days=%d",
        LOG_DIR, LOG_LEVEL, LOG_MAX_BYTES, LOG_RETENTION_DAYS,
    )


def _log_uncaught(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("uncaught").critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


def register_request_logging(app) -> None:
    """Assign a request id and log every request with status and duration."""
    from flask import g, request

    logger = logging.getLogger("http")

    @app.before_request
    def _start_request():
        g.request_started = time.perf_counter()
        g.request_id_token = set_request_id()
        level = logging.DEBUG if request.path == "/" else logging.INFO
        logger.log(level, "Request started: %s %s from %s", request.method, request.path,
                   request.headers.get("X-Forwarded-For", request.remote_addr))

    @app.after_request
    def _finish_request(response):
        started = g.get("request_started")
        if started is not None:
            elapsed_ms = (time.perf_counter() - started) * 1000
            level = logging.DEBUG if request.path == "/" else logging.INFO
            if response.status_code >= 500:
                level = logging.ERROR
            elif response.status_code >= 400:
                level = logging.WARNING
            logger.log(level, "Request finished: %s %s -> %d in %.1f ms",
                       request.method, request.path, response.status_code, elapsed_ms)
        return response

    @app.teardown_request
    def _end_request(_error):
        token = g.pop("request_id_token", None)
        if token is not None:
            reset_request_id(token)
