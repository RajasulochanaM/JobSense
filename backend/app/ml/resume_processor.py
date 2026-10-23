"""ResumeProcessor - the end-to-end resume NLP pipeline.

    file bytes -> text extraction (pypdf / python-docx)
               -> section parsing (education, experience, years)
               -> skill extraction (spaCy PhraseMatcher + taxonomy)
               -> preprocessing (normalise, tokenise, remove noise, lemmatise)
"""
from dataclasses import dataclass, field

from .preprocessing.resume_parser import ResumeParseError, extract_text, parse_sections
from .preprocessing.text_preprocessor import get_preprocessor
from .skill_extraction.skill_extractor import get_skill_extractor

MIN_TEXT_LENGTH = 50


@dataclass
class ProcessedResume:
    extracted_text: str
    processed_text: str
    skills: list = field(default_factory=list)
    education: list = field(default_factory=list)
    experience: list = field(default_factory=list)
    experience_years: float | None = None

    
class ResumeProcessor:
    def __init__(self, skill_extractor=None, preprocessor=None):
        self.skill_extractor = skill_extractor or get_skill_extractor()
        self.preprocessor = preprocessor or get_preprocessor()

    def process_text(self, text):
        sections = parse_sections(text)
        return ProcessedResume(
            extracted_text=text,
            processed_text=self.preprocessor.preprocess(text),
            skills=self.skill_extractor.extract(text),
            education=sections["education"],
            experience=sections["experience"],
            experience_years=sections["experience_years"],
        )

    def process_file(self, data: bytes, file_type: str):
        text = extract_text(data, file_type)
        if len(text.strip()) < MIN_TEXT_LENGTH:
            raise ResumeParseError(
                "Very little text could be extracted. If this is a scanned/image PDF, "
                "please upload a text-based PDF or DOCX.")
        return self.process_text(text)
