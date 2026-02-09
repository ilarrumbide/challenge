import pytest

from app.services.normalizer import normalize


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
