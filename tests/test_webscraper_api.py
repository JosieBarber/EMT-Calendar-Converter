from datetime import datetime

from src.webscraper_api import extract_all_shifts, extract_shift_details


def test_extract_shift_details_from_payload():
    payload = {
        "id": "shift_1_2026-03-03_14",
        "title": "AM Third EMT: Joseph H Dalen",
    }

    result = extract_shift_details(payload)

    assert isinstance(result, dict)
    assert result["date"] == datetime(2026, 3, 3)
    assert result["time"] == "AM"
    assert result["shift"] == "Third"
    assert result["name"] == "Joseph"


def test_extract_all_shifts_from_nested_payload():
    payload = {
        "data": {
            "calendar": [
                {
                    "shifts": [
                        {"id": "shift_1_2026-03-04_11", "title": "PM Second EMT: Alice Smith"},
                        {"id": "shift_1_2026-03-05_2", "title": "AM First EMT: Bob Johnson"},
                    ]
                }
            ]
        }
    }

    result = extract_all_shifts(payload)

    assert len(result) == 2
    assert {shift["name"] for shift in result} == {"Alice", "Bob"}
