import pytest

from app.services.normalizer import normalize, normalize_spanish


class TestNormalize:
    """Test cases for the normalize function."""

    def test_lowercase_conversion(self):
        assert normalize("JUAN GARCIA") == "juan garcia"

    def test_accent_removal(self):
        assert normalize("María García") == "maria garcia"
        assert normalize("José Núñez") == "jose nunez"

    def test_whitespace_collapse(self):
        assert normalize("Juan   García") == "juan garcia"
        assert normalize("  Juan García  ") == "juan garcia"

    def test_multiple_spaces_between_words(self):
        assert normalize("Juan    María    López") == "juan maria lopez"

    def test_mixed_case_and_accents(self):
        assert normalize("MARÍA JOSÉ GARCÍA") == "maria jose garcia"

    def test_empty_string(self):
        assert normalize("") == ""

    def test_only_whitespace(self):
        assert normalize("   ") == ""

    def test_preserves_numbers(self):
        assert normalize("Juan García 3rd") == "juan garcia 3rd"

    def test_handles_special_characters(self):
        # Keeps alphanumeric and spaces
        assert normalize("Juan-García") == "juan-garcia"

    def test_remove_particles_option(self):
        # Test particle removal option
        assert normalize("Juan de la Cruz", remove_particles=True) == "juan cruz"
        assert normalize("María del Carmen", remove_particles=True) == "maria carmen"
        # Without the option, particles are kept
        assert normalize("Juan de la Cruz", remove_particles=False) == "juan de la cruz"

    def test_sanitize_corrupted_characters(self):
        assert normalize("Isabel R(odríguez García") == "isabel rodriguez garcia"
        assert normalize("Pablo Góme&z") == "pablo gomez"
        assert normalize("Javier Ruiz Rome~ro") == "javier ruiz romero"
        assert normalize("Isabel M@oreno") == "isabel moreno"
        assert normalize("Tere$sa Romero") == "teresa romero"

    def test_strip_titles(self):
        assert normalize("Dr. Juan García") == "juan garcia"
        assert normalize("Lic. María López") == "maria lopez"
        assert normalize("Col. Pedro Martínez") == "pedro martinez"
        assert normalize("Sra. Ana Fernández") == "ana fernandez"
        assert normalize("Mg. Carlos Díaz") == "carlos diaz"
        assert normalize("Sr. Luis Rodríguez") == "luis rodriguez"


class TestNormalizeSpanish:
    """Test cases for Spanish-specific normalization."""

    def test_particle_removal(self):
        assert normalize_spanish("Juan de la Cruz") == "juan cruz"
        assert normalize_spanish("María del Carmen García") == "maria carmen garcia"
        assert normalize_spanish("Pedro de los Santos") == "pedro santos"

    def test_nickname_resolution(self):
        assert normalize_spanish("Pepe García") == "jose garcia"
        assert normalize_spanish("Paco Rodríguez") == "francisco rodriguez"
        assert normalize_spanish("Nacho López") == "ignacio lopez"
        assert normalize_spanish("Lupe Martínez") == "guadalupe martinez"

    def test_combined_particles_and_nicknames(self):
        # Test both particle removal and nickname resolution
        result = normalize_spanish("Pepe de la Cruz")
        assert result == "jose cruz"

    def test_y_particle_removal(self):
        # Test "y" particle (common in compound surnames)
        assert normalize_spanish("García y López") == "garcia lopez"

    def test_preserves_regular_names(self):
        # Names without particles or nicknames should just be normalized
        assert normalize_spanish("Juan García López") == "juan garcia lopez"

    def test_empty_string(self):
        assert normalize_spanish("") == ""

    def test_case_insensitive_nicknames(self):
        # Nicknames should work regardless of case
        assert normalize_spanish("PEPE GARCÍA") == "jose garcia"
        assert normalize_spanish("Pepe García") == "jose garcia"

    def test_multiple_nicknames(self):
        # Test name with multiple nicknames
        assert normalize_spanish("Pepe y Paco") == "jose francisco"
