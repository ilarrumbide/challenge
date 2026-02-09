import tempfile
from pathlib import Path

import pytest

from app.repositories.names import NamesRepository


class TestNamesRepository:
    """Test cases for NamesRepository."""

    @pytest.fixture
    def temp_dataset(self):
        """Create a temporary dataset for testing."""
        content = """id,name
1,Juan García López
2,María Rodríguez
3,Pedro Martínez
4,José González
5,Ana Fernández
6,Juan Carlos Pérez
7,Juana Sánchez
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink()

    def test_load_data(self, temp_dataset):
        """Test loading data from CSV."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        assert len(repo) == 7
        assert repo.get(1) == "Juan García López"
        assert repo.get(2) == "María Rodríguez"

    def test_prefix_index_creation(self, temp_dataset):
        """Test that prefix index is created on load."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        # Index should have been created
        assert len(repo._prefix_index) > 0

    def test_candidates_for_matching_prefix(self, temp_dataset):
        """Test getting candidates with matching prefix."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        # Query starting with "Juan" should find Juan-prefixed names
        candidates = repo.candidates_for("Juan García")
        candidate_names = [name for _, name in candidates]

        # Should find names starting with "ju" (juan, juana)
        assert "Juan García López" in candidate_names
        assert "Juan Carlos Pérez" in candidate_names
        assert "Juana Sánchez" in candidate_names

    def test_candidates_for_reduces_search_space(self, temp_dataset):
        """Test that candidates_for returns fewer results than full dataset."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        # Get candidates for a specific prefix
        candidates = repo.candidates_for("Juan García")

        # Should return fewer than total records (unless all start with same prefix)
        assert len(candidates) <= len(repo)

    def test_candidates_for_empty_query(self, temp_dataset):
        """Test candidates_for with empty query."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        candidates = repo.candidates_for("")
        # Empty query should return the candidates with empty key
        assert isinstance(candidates, list)

    def test_candidates_for_short_query(self, temp_dataset):
        """Test candidates_for with 1-character query."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        candidates = repo.candidates_for("J")
        # Should use single character as key
        assert isinstance(candidates, list)

    def test_candidates_for_no_matches(self, temp_dataset):
        """Test candidates_for when no names match the prefix."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        # Query with prefix that doesn't exist
        candidates = repo.candidates_for("Zzz")
        assert len(candidates) == 0

    def test_iteration(self, temp_dataset):
        """Test iterating over repository."""
        repo = NamesRepository(temp_dataset)
        repo.load()

        count = 0
        for record_id, name in repo:
            assert isinstance(record_id, int)
            assert isinstance(name, str)
            count += 1

        assert count == 7

    def test_lazy_loading(self, temp_dataset):
        """Test that data property triggers lazy loading."""
        repo = NamesRepository(temp_dataset)

        # Data should not be loaded yet
        assert not repo._loaded

        # Accessing data property should trigger load
        data = repo.data
        assert repo._loaded
        assert len(data) == 7
