import re
import unicodedata

SPANISH_PARTICLES = {"de", "del", "de la", "de los", "de las", "y"}

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
    """Remove corrupted characters from text."""
    if not text:
        return ""
    text = re.sub(r'[()~$@&]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def strip_titles(text: str) -> str:
    """Remove Spanish titles from text."""
    if not text:
        return ""
    words = text.lower().split()
    filtered = [w for w in words if w not in SPANISH_TITLES]
    return ' '.join(filtered)


def normalize(text: str, remove_particles: bool = False) -> str:
    """
    Normalize text for comparison.

    Steps:
    1. Convert to lowercase
    2. Remove accents (diacritical marks)
    3. Collapse multiple spaces into single space
    4. Trim leading/trailing whitespace
    5. Optionally remove Spanish particles

    Args:
        text: Input string to normalize
        remove_particles: Whether to remove Spanish particles (de, del, etc.)

    Returns:
        Normalized string
    """
    if not text:
        return ""

    text = sanitize_name(text)
    text = strip_titles(text)

    text = text.lower()

    # Remove accents using Unicode normalization
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    text = re.sub(r"\s+", " ", text).strip()

    # Remove Spanish particles if requested
    if remove_particles:
        text = _remove_particles(text)

    return text


def _remove_particles(text: str) -> str:
    """
    Remove Spanish particles from text, handling multi-word particles.

    Args:
        text: Normalized text

    Returns:
        Text with particles removed
    """
    # Handle multi-word particles first (order matters: longest first)
    text = re.sub(r'\bde las\b', '', text)
    text = re.sub(r'\bde los\b', '', text)
    text = re.sub(r'\bde la\b', '', text)
    text = re.sub(r'\bdel\b', '', text)
    text = re.sub(r'\bde\b', '', text)
    text = re.sub(r'\by\b', '', text)

    # Clean up extra spaces that may result from removal
    text = re.sub(r'\s+', ' ', text).strip()

    return text
