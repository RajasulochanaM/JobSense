from flask import Blueprint, g, request

from ..auth.decorators import login_required
from ..services import resume_service
from ..utils.responses import success

bp = Blueprint("resumes", __name__, url_prefix="/api/resumes")


@bp.post("")
@login_required
def upload():
    result = resume_service.upload_resume(g.user["user_id"], request.files.get("file"))
    return success(result, "Resume processed successfully", 201)


@bp.get("")
@login_required
def list_resumes():
    return success({"items": resume_service.list_resumes(g.user["user_id"])})


@bp.get("/<int:resume_id>")
@login_required
def get_resume(resume_id):
    return success(resume_service.get_resume(g.user["user_id"], resume_id))


@bp.delete("/<int:resume_id>")
@login_required
def delete_resume(resume_id):
    resume_service.delete_resume(g.user["user_id"], resume_id)
    return success(None, "Resume deleted")
