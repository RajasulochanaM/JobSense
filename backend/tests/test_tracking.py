"""Unit tests for the rule-based application reminders (no database needed)."""
from app.services.tracking_service import reminder_for


def kind(status, opened=False, days=0):
    r = reminder_for(status, opened, days)
    return r["type"] if r else None


def test_opened_posting_asks_for_confirmation():
    assert kind("Saved", opened=True) == "confirm_applied"
    assert kind("Saved", opened=False, days=90) is None


def test_applied_follow_up_and_no_response_thresholds():
    assert kind("Applied", days=13) is None
    assert kind("Applied", days=14) == "follow_up"
    assert kind("Applied", days=29) == "follow_up"
    assert kind("Applied", days=30) == "no_response"


def test_interview_follow_up():
    assert kind("Interview", days=6) is None
    assert kind("Interview", days=7) == "interview_follow_up"


def test_final_statuses_never_remind():
    for status in ("Offer", "Rejected", "Withdrawn"):
        assert kind(status, opened=True, days=365) is None


def test_message_states_the_days():
    assert "21 days" in reminder_for("Applied", False, 21)["message"]
    assert reminder_for("Applied", False, None) is None
