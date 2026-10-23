"""Automatic application tracking: status history and rule-based reminders.

JobSense cannot see what happens on the employer's site, so it tracks what it can observe
(the candidate opening the posting, every status change) and suggests the next step.
Reminders are suggestions only; the status is never changed without the candidate.
"""
from datetime import date, datetime

from flask import current_app

from ..models import tracking_model
from ..utils.serialization import row_to_dict


def _days_since(value, today):
    if value is None:
        return None
    if isinstance(value, datetime):
        value = value.date()
    return (today - value).days


def reminder_for(status, posting_opened, days_in_status, follow_up_days=14, no_response_days=30,
                 interview_days=7):
    """Return the suggested next step for one application, or None."""
    if status == "Saved" and posting_opened:
        return {"type": "confirm_applied", "message": "You opened this job posting. Did you apply?"}
    if days_in_status is None:
        return None
    if status == "Applied" and days_in_status >= no_response_days:
        return {"type": "no_response",
                "message": f"No update for {days_in_status} days. Follow up once more, or mark it Withdrawn."}
    if status == "Applied" and days_in_status >= follow_up_days:
        return {"type": "follow_up",
                "message": f"Applied {days_in_status} days ago with no update. A short follow-up email is reasonable now."}
    if status == "Interview" and days_in_status >= interview_days:
        return {"type": "interview_follow_up",
                "message": f"In the interview stage for {days_in_status} days. Consider asking about next steps."}
    return None


def serialize(row, events=(), today=None):
    today = today or date.today()
    item = row_to_dict(row)
    days = _days_since(row.get("status_changed_at"), today)
    cfg = current_app.config
    item["days_in_status"] = days
    item["reminder"] = reminder_for(row["status"], row.get("posting_opened_at") is not None, days,
                                    cfg["FOLLOW_UP_DAYS"], cfg["NO_RESPONSE_DAYS"], cfg["INTERVIEW_FOLLOW_UP_DAYS"])
    item["events"] = [row_to_dict(e, exclude=("application_id",)) for e in events]
    return item


def serialize_many(user_id, rows):
    by_app = {}
    for e in tracking_model.list_events(user_id, [r["application_id"] for r in rows]):
        by_app.setdefault(e["application_id"], []).append(e)
    return [serialize(r, by_app.get(r["application_id"], [])) for r in rows]
