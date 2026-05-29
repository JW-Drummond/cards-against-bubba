# src/cards_engine/card_repository.py

import json
from pathlib import Path
from typing import Dict, List, Optional
import zstandard as zstd
from .card import Card
from .data_fetcher import ensure_data

# Sentinel used when no region filtering is needed.
_ALL_REGIONS_TRUE: Dict[str, bool] = {"us": True, "uk": True, "ca": True, "au": True, "intl": True}


class CardRepository:
    """
    Loads cards from a cah-all-full.json (or .json.zst) file.

    On first instantiation the file is downloaded automatically if it does
    not already exist (see data_fetcher.ensure_data).  Pass an explicit
    *path* to skip auto-download and load from that file instead.

    Expected top-level format:
        [
          {
            "name": "CAH Base Set",
            "official": true,
            "white": [{"text": "...", "pack": 0}, ...],
            "black": [{"text": "...", "pick": 1, "pack": 0}, ...]
          },
          ...
        ]

    Because the source file has no region data, every card is tagged with
    all regions set to True.  The filter() method still accepts a regions
    argument for API compatibility, but all cards pass any region filter.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        if path:
            self._path = path
        else:
            # Auto-download if needed, then resolve the path.
            self._path = str(ensure_data())
        self._cards: List[Card] = self._load(self._path)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load(self) -> List[Card]:
        return list(self._cards)

    def filter(
        self,
        card_type:  Optional[str]            = None,
        regions:    Optional[Dict[str, bool]] = None,
        expansions: Optional[List[str]]       = None,
    ) -> List[Card]:
        cards = self._cards
        if card_type:
            cards = [c for c in cards if c.card_type == card_type]
        if regions:
            # All cards have every region True, so any non-empty region dict
            # matches everything.  We keep the check for forward-compatibility.
            cards = [
                c for c in cards
                if any(regions.get(r, False) and c.regions.get(r, False) for r in regions)
            ]
        if expansions:
            exp_set = set(expansions)
            cards = [c for c in cards if c.expansion in exp_set]
        return list(cards)

    def available_expansions(self) -> List[str]:
        seen: Dict[str, None] = {}
        for c in self._cards:
            seen[c.expansion] = None
        return list(seen)

    def available_regions(self) -> List[str]:
        return list(_ALL_REGIONS_TRUE.keys())

    def reload(self, path: Optional[str] = None, force_download: bool = False) -> None:
        if path:
            self._path = path
        elif force_download:
            self._path = str(ensure_data(force=True))
        self._cards = self._load(self._path)

    def print_stats(self) -> None:
        from collections import Counter
        counts = Counter(c.expansion for c in self._cards)
        for exp, n in counts.items():
            print(f"  {exp}: {n} cards")
        print(f"\nGrand total: {len(self._cards)} cards")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_bytes(path: str) -> bytes:
        raw = Path(path).read_bytes()
        if path.lower().endswith(".zst"):
            raw = zstd.ZstdDecompressor().decompress(raw)
        return raw

    def _load(self, path: str) -> List[Card]:
        print(f"[CardRepository] Loading from {path!r}")
        packs: List[Dict] = json.loads(self._read_bytes(path).decode("utf-8"))

        cards: List[Card] = []
        for pack in packs:
            name = pack.get("name", "Unknown Pack")

            for raw in pack.get("white", []):
                cards.append(Card(
                    text      = raw["text"],
                    card_type = "response",
                    pick      = 1,
                    regions   = _ALL_REGIONS_TRUE,
                    expansion = name,
                ))

            for raw in pack.get("black", []):
                cards.append(Card(
                    text      = raw["text"],
                    card_type = "prompt",
                    pick      = raw.get("pick", 1),
                    regions   = _ALL_REGIONS_TRUE,
                    expansion = name,
                ))

        print(f"[CardRepository] Loaded {len(cards)} cards from {len(packs)} packs.")
        return cards