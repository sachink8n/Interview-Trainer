"""
Resume parser: extract raw text from PDF using PyMuPDF,
then identify skills via a curated keyword list.
"""
import re
from pathlib import Path

import pymupdf as fitz  # PyMuPDF (fitz is the legacy alias)

# ── Skill keyword catalogue ───────────────────────────────────────────────────
_SKILLS: dict[str, list[str]] = {
    # Programming languages
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "Java": [r"\bjava\b"],
    "C++": [r"c\+\+", "cpp"],
    "C#": [r"c#", "csharp", r"c sharp"],
    "Go": [r"\bgolang\b", r"\bgo\b"],
    "Rust": [r"\brust\b"],
    "Ruby": [r"\bruby\b"],
    "PHP": [r"\bphp\b"],
    "Swift": [r"\bswift\b"],
    "Kotlin": [r"\bkotlin\b"],
    "R": [r"\br programming\b", r"\blanguage r\b"],
    # Web / Frontend
    "React": [r"\breact\b"],
    "Angular": [r"\bangular\b"],
    "Vue.js": [r"\bvue\.?js\b", r"\bvuejs\b"],
    "HTML": [r"\bhtml\b"],
    "CSS": [r"\bcss\b"],
    "Node.js": [r"\bnode\.?js\b", r"\bnodejs\b"],
    # Backend / Frameworks
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "Spring Boot": [r"\bspring boot\b", r"\bspringboot\b"],
    "Express.js": [r"\bexpress\.?js\b"],
    # Data / ML / AI
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Deep Learning": [r"\bdeep learning\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "PyTorch": [r"\bpytorch\b"],
    "scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "OpenCV": [r"\bopencv\b"],
    "Hugging Face": [r"\bhugging face\b", r"\bhuggingface\b"],
    "LangChain": [r"\blangchain\b"],
    "RAG": [r"\brag\b", r"\bretrieval augmented\b"],
    # Databases
    "SQL": [r"\bsql\b"],
    "MySQL": [r"\bmysql\b"],
    "PostgreSQL": [r"\bpostgresql\b", r"\bpostgres\b"],
    "MongoDB": [r"\bmongodb\b"],
    "Redis": [r"\bredis\b"],
    "SQLite": [r"\bsqlite\b"],
    "Elasticsearch": [r"\belasticsearch\b"],
    # Cloud / DevOps
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "CI/CD": [r"\bci/cd\b", r"\bcontinuous integration\b"],
    "Git": [r"\bgit\b"],
    "Linux": [r"\blinux\b", r"\bunix\b"],
    # Data Engineering
    "Spark": [r"\bapache spark\b", r"\bpyspark\b"],
    "Kafka": [r"\bkafka\b"],
    "Airflow": [r"\bairflow\b"],
    # Soft skills / methodologies
    "Agile": [r"\bagile\b"],
    "Scrum": [r"\bscrum\b"],
    "REST API": [r"\brest api\b", r"\brestful\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Microservices": [r"\bmicroservices\b"],
    "System Design": [r"\bsystem design\b"],
    "Data Structures": [r"\bdata structures\b"],
    "Algorithms": [r"\balgorithms\b"],
    "OOP": [r"\boop\b", r"\bobject.oriented\b"],
}


def extract_text(pdf_path: str | Path) -> str:
    """Return all text from a PDF file."""
    doc = fitz.open(str(pdf_path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def extract_skills(text: str) -> list[str]:
    """Return a de-duplicated list of detected skill names."""
    text_lower = text.lower()
    found: list[str] = []
    for skill_name, patterns in _SKILLS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                found.append(skill_name)
                break  # don't double-count the same skill
    return found
