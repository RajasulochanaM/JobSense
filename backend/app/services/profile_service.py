"""Candidate profile: details, social links, avatar, interests, manual skills and completeness."""
import base64
import binascii
import json
import re

from ..config.settings import INTEREST_GROUPS
from ..ml.skill_extraction.taxonomy import SKILL_INDEX, canonical_skill, normalize_skill_key, skill_category
from ..models import career_model, match_model, resume_model, user_model
from ..utils.responses import APIError, NotFound, ValidationError
from ..utils.serialization import load_json_list, row_to_dict
from ..utils.validation import clean_str

REMOTE_OPTIONS = ("any", "remote", "hybrid", "onsite")
SOCIAL_KEYS = ("linkedin", "github", "portfolio", "twitter", "stackoverflow", "behance")
AVATAR_COLORS = ("burgundy", "butter", "teal", "indigo", "forest", "slate")
AVATAR_DATA_URL_RE = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$")
MAX_AVATAR_BYTES = 300 * 1024  # decoded image size; the client resizes photos before upload
MAX_INTERESTS = 25
MAX_INTEREST_LEN = 60


def _social_links(value):
    try:
        data = json.loads(value) if isinstance(value, str) and value else (value or {})
    except ValueError:
        return {}
    return {k: data[k] for k in SOCIAL_KEYS if isinstance(data, dict) and data.get(k)}


def _clean_url(value, field):
    url = clean_str(value, 255, field)
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    if not re.match(r"^https?://[^\s/$.?#][^\s]*\.[^\s]{2,}", url, re.I):
        raise ValidationError(f"Please enter a valid link for {field}", {field: "invalid"})
    return url


def skills_payload(user_id):
    return [{**row_to_dict(s), "category": skill_category(s["skill_name"])}
            for s in resume_model.list_skills(user_id)]


def completeness(user, profile, interests, resume, skill_count):
    """Education/experience count as complete when entered manually OR detected in the resume."""
    resume = resume or {}
    checks = [
        ("Name", bool(user.get("name"))),
        ("Resume uploaded", bool(resume)),
        ("Skills identified", skill_count > 0),
        ("Experience", profile.get("experience_years") is not None or bool(profile.get("experience_summary"))
         or resume.get("experience_years") is not None),
        ("Education", bool(profile.get("education")) or bool(load_json_list(resume.get("education")))),
        ("Location", bool(profile.get("location"))),
        ("Preferred locations", bool(profile.get("preferred_locations"))),
        ("Interests", len(interests) > 0),
    ]
    done = sum(1 for _, ok in checks if ok)
    return {
        "percent": round(done / len(checks) * 100),
        "checks": [{"label": label, "done": ok} for label, ok in checks],
    }


def get_profile(user):
    user_id = user["user_id"]
    profile = row_to_dict(user_model.get_profile(user_id)) or {}
    interests = user_model.get_interests(user_id)
    skills = skills_payload(user_id)
    active = resume_model.get_active_resume(user_id)
    profile.pop("user_id", None)
    profile["social_links"] = _social_links(profile.get("social_links"))
    return {
        "user": {k: row_to_dict(user)[k] for k in ("user_id", "name", "email", "role", "created_at")},
        "profile": profile,
        "interests": interests,
        "skills": skills,
        "has_resume": active is not None,
        "completeness": completeness(user, profile, interests, active, len(skills)),
        "options": {
            "interest_groups": [{"group": g, "interests": items} for g, items in INTEREST_GROUPS.items()],
            "remote_preferences": list(REMOTE_OPTIONS),
            "social_links": list(SOCIAL_KEYS),
            "avatar_colors": list(AVATAR_COLORS),
        },
    }


def update_profile(user, data):
    user_id = user["user_id"]
    if "name" in data:
        name = clean_str(data.get("name"), 120, "name", required=True)
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters", {"name": "too_short"})
        user_model.update_name(user_id, name)
    # "role" and "email" are deliberately ignored: they are not editable through the profile.

    fields = {}
    for key, max_len in (("headline", 160), ("location", 120), ("preferred_locations", 500)):
        if key in data:
            fields[key] = clean_str(data.get(key), max_len, key) or None
    for key in ("experience_summary", "education"):
        if key in data:
            fields[key] = clean_str(data.get(key), 4000, key) or None
    if "experience_years" in data:
        raw = data.get("experience_years")
        if raw in (None, ""):
            fields["experience_years"] = None
        else:
            try:
                years = float(raw)
            except (TypeError, ValueError):
                raise ValidationError("Experience must be a number of years", {"experience_years": "invalid"})
            if not 0 <= years <= 60:
                raise ValidationError("Experience must be between 0 and 60 years", {"experience_years": "range"})
            fields["experience_years"] = round(years, 1)
    if "remote_preference" in data:
        pref = str(data.get("remote_preference") or "any").lower()
        if pref not in REMOTE_OPTIONS:
            raise ValidationError("Invalid remote preference", {"remote_preference": "invalid"})
        fields["remote_preference"] = pref
    if "social_links" in data:
        links = data.get("social_links") or {}
        if not isinstance(links, dict):
            raise ValidationError("social_links must be an object")
        cleaned = {k: _clean_url(links.get(k), k) for k in SOCIAL_KEYS}
        fields["social_links"] = json.dumps({k: v for k, v in cleaned.items() if v}) or None
    if "avatar_color" in data:
        color = data.get("avatar_color") or None
        if color is not None and color not in AVATAR_COLORS:
            raise ValidationError("Invalid avatar colour", {"avatar_color": "invalid"})
        fields["avatar_color"] = color
    user_model.update_profile(user_id, fields)

    if "interests" in data:
        interests = data.get("interests") or []
        if not isinstance(interests, list):
            raise ValidationError("Interests must be a list")
        # Any interest is allowed (the suggested list is just a starting point); de-duplicate case-insensitively.
        cleaned = {}
        for item in interests:
            text = " ".join(clean_str(item, MAX_INTEREST_LEN, "interest").split())
            if text:
                cleaned.setdefault(text.lower(), text)
        if len(cleaned) > MAX_INTERESTS:
            raise ValidationError(f"You can select up to {MAX_INTERESTS} interests")
        user_model.set_interests(user_id, list(cleaned.values()))
        # Interests influence career recommendations -> recompute lazily.
        career_model.clear_recommendations(user_id)

    return get_profile(user_model.get_by_id(user_id))


def set_avatar(user, image):
    """image: a data:image/(png|jpeg|webp);base64 URL, or None to remove the photo."""
    if image:
        match = AVATAR_DATA_URL_RE.match(image) if isinstance(image, str) else None
        if not match:
            raise ValidationError("Profile picture must be a PNG, JPEG or WebP image")
        try:
            size = len(base64.b64decode(match.group(2), validate=True))
        except (binascii.Error, ValueError):
            raise ValidationError("Profile picture could not be read")
        if size > MAX_AVATAR_BYTES:
            raise ValidationError(f"Profile picture must be under {MAX_AVATAR_BYTES // 1024} KB")
    user_model.update_profile(user["user_id"], {"avatar_image": image or None})
    return get_profile(user)


def add_skill(user_id, skill_name):
    raw = clean_str(skill_name, 80, "skill", required=True)
    name = canonical_skill(raw)
    if normalize_skill_key(name) not in SKILL_INDEX and len(name) < 2:
        raise ValidationError("Please enter a valid skill name")
    if not resume_model.add_manual_skill(user_id, name):
        raise APIError(f"'{name}' is already in your skills", "DUPLICATE_SKILL", 409)
    match_model.clear_user_matches(user_id)
    return skills_payload(user_id)


def remove_skill(user_id, skill_id):
    if not resume_model.delete_skill(user_id, skill_id):
        raise NotFound("Skill not found")
    match_model.clear_user_matches(user_id)
    return skills_payload(user_id)
