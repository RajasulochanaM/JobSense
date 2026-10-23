from flask import Blueprint, g

from ..auth.decorators import login_required
from ..config.settings import INTEREST_GROUPS
from ..ml.skill_extraction.taxonomy import SKILLS
from ..services import dashboard_service, profile_service
from ..utils.responses import success
from ..utils.validation import get_json

bp = Blueprint("profile", __name__, url_prefix="/api")


@bp.get("/profile")
@login_required
def get_profile():
    return success(profile_service.get_profile(g.user))


@bp.put("/profile")
@login_required
def update_profile():
    return success(profile_service.update_profile(g.user, get_json()), "Profile updated")


@bp.put("/profile/avatar")
@login_required
def upload_avatar():
    return success(profile_service.set_avatar(g.user, get_json().get("image")), "Profile picture updated")


@bp.delete("/profile/avatar")
@login_required
def remove_avatar():
    return success(profile_service.set_avatar(g.user, None), "Profile picture removed")


@bp.get("/profile/skills")
@login_required
def my_skills():
    return success({"items": profile_service.skills_payload(g.user["user_id"])})


@bp.post("/profile/skills")
@login_required
def add_skill():
    items = profile_service.add_skill(g.user["user_id"], get_json().get("skill_name"))
    return success({"items": items}, "Skill added", 201)


@bp.delete("/profile/skills/<int:skill_id>")
@login_required
def delete_skill(skill_id):
    items = profile_service.remove_skill(g.user["user_id"], skill_id)
    return success({"items": items}, "Skill removed")


@bp.get("/skills")
@login_required
def skill_taxonomy():
    """The skill taxonomy (used for autocomplete and the Skills page)."""
    categories = {}
    for entry in SKILLS:
        categories.setdefault(entry["category"], []).append(entry["name"])
    return success({"categories": [{"category": c, "skills": sorted(s, key=str.lower)}
                                   for c, s in categories.items()],
                    "total": len(SKILLS)})


@bp.get("/interests")
@login_required
def interest_options():
    """Suggested interests grouped by field (profile interests and career interest areas)."""
    return success({"groups": [{"group": g, "interests": items} for g, items in INTEREST_GROUPS.items()]})


@bp.get("/dashboard")
@login_required
def dashboard():
    return success(dashboard_service.dashboard(g.user))
