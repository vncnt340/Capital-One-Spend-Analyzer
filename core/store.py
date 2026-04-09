from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal

from core.loader import load_csv
from core.tagger import apply_rules

_APP_SUPPORT = Path.home() / "Library" / "Application Support" / "SpendAnalyzer"
_RULES_FILE = _APP_SUPPORT / "rules.json"


def _ensure_dir() -> None:
    _APP_SUPPORT.mkdir(parents=True, exist_ok=True)


def _load_rules_from_disk() -> list[dict]:
    if _RULES_FILE.exists():
        try:
            return json.loads(_RULES_FILE.read_text())
        except Exception:
            pass
    return []


def _save_rules_to_disk(rules: list[dict]) -> None:
    _ensure_dir()
    tmp = _RULES_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(rules, indent=2))
    tmp.replace(_RULES_FILE)


class AppStore(QObject):
    data_changed = pyqtSignal()
    rules_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._df: pd.DataFrame | None = None
        self._rules: list[dict] = _load_rules_from_disk()
        self._csv_path: str = ""

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def df(self) -> pd.DataFrame | None:
        return self._df

    @property
    def rules(self) -> list[dict]:
        return list(self._rules)

    @property
    def is_loaded(self) -> bool:
        return self._df is not None and not self._df.empty

    @property
    def csv_path(self) -> str:
        return self._csv_path

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_csv(self, path: str) -> None:
        """Load and tag CSV. Raises LoaderError on failure."""
        df = load_csv(path)
        df = apply_rules(df, self._rules)
        self._df = df
        self._csv_path = path
        self.data_changed.emit()

    def reload_tags(self) -> None:
        """Re-apply current rules to loaded data without re-reading CSV."""
        if self._df is not None:
            self._df = apply_rules(self._df, self._rules)
            self.data_changed.emit()

    # ── Rules CRUD ────────────────────────────────────────────────────────────

    def add_rule(self, keyword: str, sub_category: str, match_case: bool = False) -> None:
        self._rules.append({"keyword": keyword, "sub_category": sub_category, "match_case": match_case})
        _save_rules_to_disk(self._rules)
        self.rules_changed.emit()
        self.reload_tags()

    def update_rule(self, index: int, keyword: str, sub_category: str, match_case: bool = False) -> None:
        self._rules[index] = {"keyword": keyword, "sub_category": sub_category, "match_case": match_case}
        _save_rules_to_disk(self._rules)
        self.rules_changed.emit()
        self.reload_tags()

    def delete_rule(self, index: int) -> None:
        self._rules.pop(index)
        _save_rules_to_disk(self._rules)
        self.rules_changed.emit()
        self.reload_tags()

    def move_rule(self, index: int, direction: int) -> None:
        new_index = index + direction
        if 0 <= new_index < len(self._rules):
            self._rules[index], self._rules[new_index] = self._rules[new_index], self._rules[index]
            _save_rules_to_disk(self._rules)
            self.rules_changed.emit()
            self.reload_tags()
