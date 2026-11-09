from datetime import datetime

from app.services.aicte_data import normalize_records


def test_normalize_yearwise_government_engineering_aggregates():
    synchronized_at = datetime(2026, 11, 9, 12, 0)
    records = [
        {
            "academic_year": "2019-20",
            "number_of_government_engineering_institutes": 123,
            "approved_seats_in_government_engineering_institutes": 45678,
        },
        {
            "academic_year": "2020-21",
            "number_of_government_engineering_institutes": 124,
            "approved_seats_in_government_engineering_institutes": 45900,
        },
    ]

    normalized = normalize_records(records, synchronized_at)

    assert len(normalized) == 2
    assert all(record["record_type"] == "aggregate" for record in normalized)
    assert normalized[0]["academic_year"] == "2019-20"
    assert normalized[0]["government_engineering_institutes_count"] == 123
    assert normalized[0]["approved_seats_count"] == 45678
    assert normalized[0]["synchronized_at"] == synchronized_at.isoformat()


def test_normalize_institution_records_as_before():
    normalized = normalize_records(
        [{"aicte_id": "123", "institution_name": "Example College"}],
        datetime(2026, 11, 9, 12, 0),
    )

    assert len(normalized) == 1
    assert normalized[0]["record_type"] == "institution"
    assert normalized[0]["aicte_id"] == "123"
    assert normalized[0]["name"] == "Example College"


def test_ignore_records_without_supported_public_data_fields():
    assert normalize_records(
        [{"academic_year": "2020-21", "unrelated_count": 5}],
        datetime(2026, 11, 9, 12, 0),
    ) == []
