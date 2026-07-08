from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_fxmacrodata_calendar(currency: str = "usd", top_tier_only: bool = True) -> list[dict[str, Any]]:
    params: dict[str, str] = {}
    api_key = os.getenv("FXMD_API_KEY")
    if api_key:
        params["api_key"] = api_key
    query = f"?{urlencode(params)}" if params else ""
    request = Request(
        f"https://fxmacrodata.com/api/v1/calendar/{currency.lower()}{query}",
        headers={"Accept": "application/json", "User-Agent": "pyalgotrader-fxmacrodata-example"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = list(payload.get("data") or [])
    if top_tier_only:
        rows = [row for row in rows if row.get("top_tier_for_currency") or row.get("market_tier") == 1]
    return rows


def should_pause_for_macro_event(timestamp: datetime, events: list[dict[str, Any]]) -> bool:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    before = timedelta(hours=4)
    after = timedelta(hours=2)
    for row in events:
        value = row.get("announcement_datetime_utc") or row.get("announcement_datetime_local")
        if not value:
            continue
        event_time = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if event_time - before <= timestamp <= event_time + after:
            return True
    return False


if __name__ == "__main__":
    calendar = fetch_fxmacrodata_calendar("usd")
    print(f"Loaded {len(calendar)} top-tier USD macro releases")
    print("Pause now:", should_pause_for_macro_event(datetime.now(timezone.utc), calendar))

