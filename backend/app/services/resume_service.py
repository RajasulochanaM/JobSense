"""Resume upload, validation, storage and NLP processing.

Security measures:
  * extension allow-list (.pdf / .docx) AND content sniffing (magic bytes) -
    the client-supplied MIME type and filename are never trusted
  * size limit (MAX_RESUME_SIZE_MB)
  * server-generated random storage names (uuid4) - user filenames are only
    kept, sanitised, for display
Each resume is processed once; results are persisted so NLP never re-runs.
"""
import io
import logging
import os
import uuid
import zipfile

from flask import current_app
from werkzeug.utils import secure_filename

from ..ml.preprocessing.resume_parser import ResumeParseError
from ..ml.resume_processor import ResumeProcessor
from ..models import match_model, resume_model
from ..utils.responses import APIError, NotFound, ValidationError
from ..utils.serialization import dump_json, load_json_list, row_to_dict

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx"}
ALLOWED_MIME = {
    "pdf": {"application/pdf", "application/x-pdf", "application/octet-stream"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
             "application/octet-stream", "application/zip"},
}


def _extension(filename):
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def sniff_file_type(data: bytes):
    """Detect the real file type from content, independent of the filename."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if "word/document.xml" in zf.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            return None
    return None


def validate_upload(file_storage):
    if file_storage is None or not file_storage.filename:
        raise ValidationError("Please choose a resume file to upload", {"file": "required"})
    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise APIError("Unsupported file type. Please upload a PDF or DOCX file.", "UNSUPPORTED_FILE_TYPE", 415)
    mimetype = (file_storage.mimetype or "").lower()
    if mimetype and mimetype not in ALLOWED_MIME[ext]:
        raise APIError("The file's content type does not match a PDF or DOCX document.", "UNSUPPORTED_FILE_TYPE", 415)

    max_bytes = current_app.config["MAX_RESUME_SIZE_MB"] * 1024 * 1024
    data = file_storage.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise APIError(f"File is too large. Maximum size is {current_app.config['MAX_RESUME_SIZE_MB']} MB.",
                       "FILE_TOO_LARGE", 413)
    if not data:
        raise ValidationError("The uploaded file is empty", {"file": "empty"})
    detected = sniff_file_type(data)
    if detected != ext:
        raise APIError("The file content is not a valid PDF or DOCX document.", "UNSUPPORTED_FILE_TYPE", 415)

    display_name = secure_filename(file_storage.filename) or f"resume.{ext}"
    return data, ext, display_name[:255]


def _store_file(data, ext):
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(folder, name), "wb") as fh:
        fh.write(data)
    return name


def _remove_file(name):
    if not name:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(name))
    try:
        os.remove(path)
    except OSError:
        pass


def resume_payload(row, include_text=False):
    data = row_to_dict(row, exclude=("file_path", "processed_text", "extracted_text", "user_id"))
    for key in ("education", "experience"):
        if key in data:
            data[key] = load_json_list(data[key])
    data["is_active"] = bool(data.get("is_active"))
    if include_text:
        text = row.get("extracted_text") or ""
        data["text_preview"] = text[:3000]
        data["text_length"] = len(text)
    return data


def upload_resume(user_id, file_storage):
    data, ext, display_name = validate_upload(file_storage)
    stored = _store_file(data, ext)
    resume_id = resume_model.create_resume(user_id, display_name, ext, stored, len(data))
    stages = ["uploaded"]
    try:
        stages.append("extracting_text")
        result = ResumeProcessor().process_file(data, ext)
        stages.append("analyzing_skills")
    except ResumeParseError as exc:
        resume_model.mark_failed(resume_id, str(exc))
        resume_model.activate_latest(user_id)
        logger.warning("Resume %s could not be processed: %s", resume_id, exc)
        raise APIError(str(exc), "RESUME_PROCESSING_FAILED", 422)
    except Exception:
        resume_model.mark_failed(resume_id, "Unexpected processing error")
        resume_model.activate_latest(user_id)
        logger.exception("Unexpected failure processing resume %s", resume_id)
        raise APIError("The resume could not be processed. Please try another file.",
                       "RESUME_PROCESSING_FAILED", 500)

    resume_model.mark_processed(resume_id, result.extracted_text, result.processed_text,
                                dump_json(result.education), dump_json(result.experience), result.experience_years)
    resume_model.replace_resume_skills(user_id, result.skills)
    match_model.clear_user_matches(user_id)  # cached matches were based on the previous resume
    stages.append("profile_updated")
    logger.info("Resume %s processed for user %s: %d skills", resume_id, user_id, len(result.skills))

    return {
        "resume": resume_payload(resume_model.get_resume(user_id, resume_id), include_text=True),
        "skills": result.skills,
        "stages": stages,
    }


def list_resumes(user_id):
    return [resume_payload(r) for r in resume_model.list_resumes(user_id)]


def get_resume(user_id, resume_id):
    row = resume_model.get_resume(user_id, resume_id)
    if not row:
        raise NotFound("Resume not found")
    return resume_payload(row, include_text=True)


def delete_resume(user_id, resume_id):
    row = resume_model.get_resume(user_id, resume_id)
    if not row:
        raise NotFound("Resume not found")
    resume_model.delete_resume(user_id, resume_id)
    _remove_file(row["file_path"])

    if row["is_active"]:
        # Rebuild resume-derived skills from the newest remaining resume (if any).
        new_active = resume_model.activate_latest(user_id)
        skills = []
        if new_active:
            remaining = resume_model.get_resume(user_id, new_active)
            skills = ResumeProcessor().skill_extractor.extract(remaining.get("extracted_text") or "")
        resume_model.replace_resume_skills(user_id, skills)
        match_model.clear_user_matches(user_id)
    return True
