# -*- coding: utf-8 -*-
"""Append-only audit log for administrative actions."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo

import config

AUDIT_FILE = "audit_log.jsonl"
TZ = ZoneInfo("Europe/Amsterdam")
RETENTION_DAYS = 90

@dataclass
class AuditEvent:
    ts: str
    actor_id: int
    actor_username: Optional[str]
    actor_name: Optional[str]
    section: str
    action: str
    scope: Optional[str] = None
    entity: Optional[str] = None
    before: Any = None
    after: Any = None
    notes: Optional[str] = None
    chat_id: Optional[int] = None
    message_id: Optional[int] = None
    project_id: Optional[str] = None
    request_id: Optional[str] = None

    @staticmethod
    def create(**kwargs) -> "AuditEvent":
        now = datetime.now(TZ)
        return AuditEvent(ts=now.isoformat(), **kwargs)


def _path() -> str:
    os.makedirs(config.JSON_DIR, exist_ok=True)
    return os.path.join(config.JSON_DIR, AUDIT_FILE)


def append_event(event: AuditEvent) -> None:
    path = _path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def add_event(
    *,
    user: Any,
    section: str,
    action: str,
    scope: Optional[str] = None,
    entity: Optional[str] = None,
    before: Any = None,
    after: Any = None,
    notes: Optional[str] = None,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
    project_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    ev = AuditEvent.create(
        actor_id=getattr(user, "id", 0),
        actor_username=getattr(user, "username", None),
        actor_name=getattr(user, "full_name", None) or getattr(user, "first_name", None),
        section=section,
        action=action,
        scope=scope,
        entity=entity,
        before=before,
        after=after,
        notes=notes,
        chat_id=chat_id,
        message_id=message_id,
        project_id=project_id,
        request_id=request_id or str(uuid.uuid4()),
    )
    append_event(ev)


def load_events(limit: int = 1000) -> List[Dict[str, Any]]:
    path = _path()
    if not os.path.exists(path):
        return []
    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events[-limit:]


def query_events(
    *,
    period: str = "all",
    section_filter: Optional[str] = None,
    author_id: Optional[int] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    events = load_events()
    now = datetime.now(TZ)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        events = [e for e in events if datetime.fromisoformat(e["ts"]).astimezone(TZ) >= start]
    elif period == "24h":
        start = now - timedelta(days=1)
        events = [e for e in events if datetime.fromisoformat(e["ts"]).astimezone(TZ) >= start]
    elif period == "7d":
        start = now - timedelta(days=7)
        events = [e for e in events if datetime.fromisoformat(e["ts"]).astimezone(TZ) >= start]
    if section_filter and section_filter != "all":
        events = [e for e in events if e.get("section", "").startswith(section_filter)]
    if author_id:
        events = [e for e in events if e.get("actor_id") == author_id]
    return events[-limit:]
