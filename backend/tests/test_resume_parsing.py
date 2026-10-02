import pytest

from app.ml.preprocessing.resume_parser import ResumeParseError, extract_text, parse_sections
from app.ml.resume_processor import ResumeProcessor
from app.services.resume_service import sniff_file_type


def test_pdf_text_extraction(pdf_bytes):
    text = extract_text(pdf_bytes, "pdf")
    assert "Priya Sharma" in text
    assert "ReactJS" in text


def test_docx_text_extraction(docx_bytes):
    text = extract_text(docx_bytes, "docx")
    assert "Priya Sharma" in text
    assert "B.Tech in Computer Science" in text


def test_unsupported_and_corrupt_files():
    with pytest.raises(ResumeParseError):
        extract_text(b"hello", "txt")
    with pytest.raises(ResumeParseError):
        extract_text(b"%PDF-1.4 not really a pdf", "pdf")
    with pytest.raises(ResumeParseError):
        extract_text(b"PK\x03\x04 broken zip", "docx")


def test_content_sniffing(pdf_bytes, docx_bytes):
    assert sniff_file_type(pdf_bytes) == "pdf"
    assert sniff_file_type(docx_bytes) == "docx"
    assert sniff_file_type(b"MZ\x90\x00 executable") is None
    assert sniff_file_type(b"plain text resume") is None


def test_section_parsing(resume_text):
    sections = parse_sections(resume_text)
    assert any("B.Tech" in line for line in sections["education"])
    assert any("Acme" in line for line in sections["experience"])
    assert sections["experience_years"] == 2.0      # explicit "2 years of experience"


def test_experience_from_date_ranges():
    text = "Experience\nDeveloper, X Corp  Jan 2019 - Dec 2020\nIntern, Y Ltd  Jun 2018 - Dec 2018\n"
    years = parse_sections(text)["experience_years"]
    assert years == 2.6      # 24 + 7 inclusive months = 31 months


def test_full_resume_pipeline(pdf_bytes):
    result = ResumeProcessor().process_file(pdf_bytes, "pdf")
    assert {"React", "JavaScript", "HTML", "CSS", "Node.js", "MySQL", "Git", "Python"} <= set(result.skills)
    assert result.processed_text
    assert result.education


def test_empty_pdf_is_rejected():
    from tests.conftest import make_pdf
    with pytest.raises(ResumeParseError):
        ResumeProcessor().process_file(make_pdf("Hi"), "pdf")
