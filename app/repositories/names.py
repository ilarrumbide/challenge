import csv
from pathlib import Path

from app.services.normalizer import normalize


class NamesRepository:

    def __init__(self, dataset_path: Path | str | None = None):
        if dataset_path is None:
            dataset_path = Path(__file__).parent.parent.parent / "names_dataset.csv"
        self._path = Path(dataset_path)
        self._data: dict[int, str] = {}
        self._normalized: dict[int, str] = {}
        self._prefix_index: dict[str, list[tuple[int, str]]] = {}
        self._loaded = False

    def load(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(f"Dataset not found: {self._path}")

        self._data = {}
        self._normalized = {}
        with open(self._path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record_id = int(row.get("ID") or row.get("id"))
                name = row.get("Full Name") or row.get("name")
                self._data[record_id] = name
                self._normalized[record_id] = normalize(name)
        self._loaded = True
        self._build_prefix_index()

    def _build_prefix_index(self) -> None:
        self._prefix_index = {}
        for record_id, name in self._data.items():
            normalized = self._normalized[record_id]
            key = normalized[:2] if len(normalized) >= 2 else normalized
            if key not in self._prefix_index:
                self._prefix_index[key] = []
            self._prefix_index[key].append((record_id, name))

    def candidates_for(self, query: str) -> list[tuple[int, str, str]]:
        normalized = normalize(query)
        key = normalized[:2] if len(normalized) >= 2 else normalized
        candidates = self._prefix_index.get(key, [])
        return [(rid, name, self._normalized[rid]) for rid, name in candidates]

    @property
    def data(self) -> dict[int, str]:
        if not self._loaded:
            self.load()
        return self._data

    def get(self, record_id: int) -> str | None:
        return self.data.get(record_id)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        if not self._loaded:
            self.load()
        return ((rid, name, self._normalized[rid]) for rid, name in self._data.items())
