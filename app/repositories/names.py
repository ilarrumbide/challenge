import csv
from pathlib import Path

from app.services.normalizer import normalize


class NamesRepository:
    """Repository for accessing names database with prefix-based blocking."""

    def __init__(self, dataset_path: Path | str | None = None):
        """
        Initialize the repository.

        Args:
            dataset_path: Path to the CSV file. If None, uses default location.
        """
        if dataset_path is None:
            dataset_path = Path(__file__).parent.parent.parent / "names_dataset.csv"
        self._path = Path(dataset_path)
        self._data: dict[int, str] = {}
        self._prefix_index: dict[str, list[tuple[int, str]]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load names from CSV file and build prefix index."""
        if not self._path.exists():
            raise FileNotFoundError(f"Dataset not found: {self._path}")

        self._data = {}
        with open(self._path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both "Full Name" and "name" column formats
                record_id = int(row.get("ID") or row.get("id"))
                name = row.get("Full Name") or row.get("name")
                self._data[record_id] = name
        self._loaded = True
        self._build_prefix_index()

    def _build_prefix_index(self) -> None:
        """
        Build prefix-based index for faster candidate selection.

        Groups names by their first 2 normalized characters.
        This reduces comparison space from N to approximately N/676 (26^2).
        """
        self._prefix_index = {}
        for record_id, name in self._data.items():
            normalized = normalize(name)
            # Use first 2 characters as blocking key (handles empty/short names)
            key = normalized[:2] if len(normalized) >= 2 else normalized
            if key not in self._prefix_index:
                self._prefix_index[key] = []
            self._prefix_index[key].append((record_id, name))

    def candidates_for(self, query: str) -> list[tuple[int, str]]:
        """
        Get candidate names that could match the query based on prefix.

        This significantly reduces the search space for large datasets.

        Args:
            query: The query name to find candidates for

        Returns:
            List of (id, name) tuples that share the same prefix
        """
        normalized = normalize(query)
        key = normalized[:2] if len(normalized) >= 2 else normalized
        return self._prefix_index.get(key, [])

    @property
    def data(self) -> dict[int, str]:
        """Get all names data. Loads if not already loaded."""
        if not self._loaded:
            self.load()
        return self._data

    def get(self, record_id: int) -> str | None:
        """Get a name by ID."""
        return self.data.get(record_id)

    def __len__(self) -> int:
        """Return number of records."""
        return len(self.data)

    def __iter__(self):
        """Iterate over (id, name) pairs."""
        return iter(self.data.items())
