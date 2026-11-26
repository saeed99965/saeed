from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote

RESERVED = {"addstickers","addemoji","addlist","addtheme","apps","auth","bg","boost","c","confirmphone","contact","faq","giftcode","invoice","iv","joinchat","login","proxy","s","setlanguage","share","socks","blog","privacy","terms","wallet"}
@dataclass(frozen=True)
class TelegramLink:
    normalized_link: str
    public_username: str | None
    invite_hash: str | None

def normalize_telegram_link(raw: str):
    value = raw.strip().strip("<>()[]{}.,;\\\"'")
    if not value: return None
    if not re.match(r"^https?://", value, re.I): value = "https://" + value
    p = urlparse(value)
    if (p.hostname or "").lower() not in {"t.me","www.t.me","telegram.me","www.telegram.me"}: return None
    parts = [unquote(x) for x in p.path.split("/") if x]
    if not parts: return None
    if parts[0].lower() == "joinchat" and len(parts) > 1: parts = ["+" + parts[1]]
    if parts[0].startswith("+"):
        invite = re.sub(r"[^A-Za-z0-9_-]", "", parts[0][1:])
        return TelegramLink(f"https://t.me/+{invite}", None, invite) if invite else None
    if parts[0].lower() in RESERVED or len(parts) != 1: return None
    username = parts[0].lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]{4,31}", username): return None
    return TelegramLink(f"https://t.me/{username}", username, None)

def inactivity_status(last_message_at, tracking_started_at, min_days=2, max_days=90, now=None):
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    def parse(v):
        if not v: return None
        try: d = v if isinstance(v, datetime) else datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, TypeError): return None
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    last, started = parse(last_message_at), parse(tracking_started_at)
    if last is None:
        if started is None: return {"status":"UNKNOWN","days":None,"basis":"no_data"}
        return {"status":"NO_MESSAGE_OBSERVED","days":max(0,(moment-started).days),"basis":"monitoring_started"}
    days=max(0,(moment-last).days)
    status="ACTIVE" if days < min_days else "INACTIVE" if days <= max_days else "LONG_INACTIVE"
    return {"status":status,"days":days,"basis":"last_message_observed"}
