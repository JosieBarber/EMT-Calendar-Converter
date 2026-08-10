from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _build_calendar_payload(month: int | str, year: int | str) -> dict[str, str]:
    return {
        "action": "get_page_data_calendar",
        "auto_callback": "get_page_data_calendar",
        "form_submit_callback": "get_page_data_calendar",
        "cal_month": str(month),
        "cal_year": str(year),
        "location_id": "1",
    }


def _post_form(url: str, data: dict[str, str], headers: dict[str, str] | None = None) -> str:
    request = Request(
        url,
        data=urlencode(data).encode("utf-8"),
        method="POST",
        headers=headers or {},
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def fetch_html_content(username: str, password: str, month: int, year: int) -> dict[str, Any] | str:
    """Fetch calendar data directly from the Crew Quarters PHP endpoint used by my R scraper."""
    calendar_url = "https://stevensems.com/cq/lib/php/cq_functions.php"

    response_text = _post_form(
        calendar_url,
        _build_calendar_payload(month, year),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": calendar_url,
        },
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return response_text


def fetch_month_data(month: int, year: int, username: str | None = None, password: str | None = None) -> dict[str, Any]:
    """Fetch one month of calendar data and attach the requested month/year metadata."""
    response = fetch_html_content(username or "", password or "", month, year)
    if isinstance(response, dict):
        calendar = response.get("data", {}).get("calendar")
        if isinstance(calendar, list) and calendar:
            first_calendar = dict(calendar[0])
            first_calendar["month"] = month
            first_calendar["year"] = year
            return first_calendar
        return response
    raise TypeError("Calendar response was not parsed into a JSON object")


def get_month_data(month: int, year: int, username: str | None = None, password: str | None = None) -> dict[str, Any]:
    """R-style helper that returns one month of calendar data."""
    return fetch_month_data(month, year, username=username, password=password)


def _coerce_date(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return datetime.strptime(text, "%Y-%m-%d")
        if re.fullmatch(r"\d{4}/\d{2}/\d{2}", text):
            return datetime.strptime(text, "%Y/%m/%d")
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", text):
            return datetime.strptime(text, "%m/%d/%Y")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(int(value))
        except (OverflowError, OSError, ValueError):
            return None
    return None


def _extract_shift_number(item: dict[str, Any]) -> int | None:
    for key in ("shift_number", "shift_num", "shift", "number"):
        if key in item:
            try:
                return int(item[key])
            except (TypeError, ValueError):
                continue

    for key in ("id", "shift_id"):
        value = item.get(key)
        if isinstance(value, str):
            match = re.search(r"_(\d+)$", value)
            if match:
                return int(match.group(1))
            match = re.search(r"_(\d{4}-\d{2}-\d{2})_(\d+)$", value)
            if match:
                return int(match.group(2))

    return None


def _resolve_shift_details(shift_number: int | None, title: str | None) -> tuple[str, str]:
    if title:
        title_match = re.search(r"(AM|PM)\s*(First|Second|Third)", title, flags=re.IGNORECASE)
        if title_match:
            time_value = title_match.group(1).upper()
            shift_value = title_match.group(2).capitalize()
            return time_value, shift_value

    if shift_number is None:
        return "Unknown", "Unknown"

    if 1 <= shift_number <= 3:
        return "AM", "First"
    if 4 <= shift_number <= 6:
        return "PM", "First"
    if 7 <= shift_number <= 9:
        return "AM", "Second"
    if 10 <= shift_number <= 12:
        return "PM", "Second"
    if 13 <= shift_number <= 15:
        return "AM", "Third"
    if 16 <= shift_number <= 18:
        return "PM", "Third"
    return "Unknown", "Unknown"


def _extract_name(item: dict[str, Any], title: str | None) -> str:
    if isinstance(item.get("name"), str) and item["name"].strip():
        return item["name"].strip()

    if not title:
        return "Unknown"

    match = re.search(r"(?:EMT|MEDIC|Crew):\s*([A-Za-z]+)", title)
    if match:
        return match.group(1)
    return "Unknown"


def extract_shift_details(shift_element: Any) -> dict[str, Any] | None:
    """Parse a shift payload into the same dictionary shape used by the HTML scraper."""
    if isinstance(shift_element, dict):
        item = shift_element
    else:
        return None

    title = None
    for key in ("title", "summary", "label"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            title = value.strip()
            break

    date_value = None
    for key in ("date", "shift_date", "day", "start_date"):
        if key in item:
            date_value = _coerce_date(item[key])
            if date_value is not None:
                break

    if date_value is None:
        for key in ("id", "shift_id"):
            value = item.get(key)
            if isinstance(value, str):
                match = re.search(r"(\d{4}-\d{2}-\d{2})", value)
                if match:
                    date_value = _coerce_date(match.group(1))
                    if date_value is not None:
                        break

    if date_value is None:
        return None

    shift_number = _extract_shift_number(item)
    time_value, shift_type = _resolve_shift_details(shift_number, title)
    name = _extract_name(item, title)

    return {
        "date": date_value,
        "time": time_value,
        "shift": shift_type,
        "name": name,
    }


def _looks_like_shift_candidate(item: Any) -> bool:
    if not isinstance(item, dict):
        return False

    if any(isinstance(item.get(key), str) and item.get(key).strip() for key in ("title", "summary", "label")):
        return True
    if any(key in item for key in ("date", "shift_date", "day", "start_date")):
        return True
    if any(key in item for key in ("id", "shift_id")):
        return True
    return False


def _walk_for_shift_candidates(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        if _looks_like_shift_candidate(value):
            return [value]

        results = []
        for nested_value in value.values():
            results.extend(_walk_for_shift_candidates(nested_value))
        return results
    if isinstance(value, list):
        results = []
        for child in value:
            results.extend(_walk_for_shift_candidates(child))
        return results
    return []


def extract_all_shifts(payload: Any, name: str | None = None) -> list[dict[str, Any]]:
    """Extract shift dictionaries from a JSON payload or nested collection of payloads."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return []

    candidates = []
    if isinstance(payload, dict):
        candidates.extend(_walk_for_shift_candidates(payload))
    elif isinstance(payload, list):
        for item in payload:
            candidates.extend(_walk_for_shift_candidates(item))

    shifts: list[dict[str, Any]] = []
    for item in candidates:
        shift = extract_shift_details(item)
        if not shift:
            continue
        if shift["time"] == "Unknown" or shift["shift"] == "Unknown" or shift["name"] == "Unknown":
            continue
        if name and shift["name"] != name:
            continue
        shifts.append(shift)

    return shifts


def scrape_schedule(username: str, password: str, name: str, month: int, year: int) -> list[dict[str, Any]]:
    """Scrape one month of schedule data for a named employee."""
    payload = fetch_html_content(username, password, month, year)
    shifts = extract_all_shifts(payload, name=name)
    print(f"Extracted {len(shifts)} shifts from the schedule.")
    return shifts


def scrape_range(start_month: int, start_year: int, end_month: int, end_year: int, username: str, password: str, name: str | None = None) -> list[dict[str, Any]]:
    """Fetch a range of months and return all matching shifts."""
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)

    collected: list[dict[str, Any]] = []
    current = start_date
    while current <= end_date:
        month_payload = fetch_month_data(current.month, current.year, username, password)
        month_shifts = extract_all_shifts(month_payload, name=name)
        collected.extend(month_shifts)
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    return collected


def get_shift_range(start_month: int, start_year: int, end_month: int, end_year: int, username: str, password: str, name: str | None = None) -> list[dict[str, Any]]:
    """R-style helper that fetches a month range and returns matching shifts."""
    return scrape_range(start_month, start_year, end_month, end_year, username, password, name=name)
