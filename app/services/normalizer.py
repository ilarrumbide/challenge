import re
import unicodedata

SPANISH_TITLES = {
    "lic", "lic.", "licenciado", "licenciada",
    "dr", "dr.", "doctor", "doctora",
    "mg", "mg.", "magister",
    "col", "col.", "coronel", "coronela",
    "sr", "sr.", "señor",
    "sra", "sra.", "señora",
    "srta", "srta.", "señorita",
}


def sanitize_name(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[()~$@&]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def strip_titles(text: str) -> str:
    if not text:
        return ""
    words = text.lower().split()
    filtered = [w for w in words if w not in SPANISH_TITLES]
    return ' '.join(filtered)


def normalize(text: str) -> str:
    if not text:
        return ""

    text = sanitize_name(text)
    text = strip_titles(text)

    text = text.lower()

    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    text = re.sub(r"\s+", " ", text).strip()

    return text
