"""Chronological ordering of checked spectra, independent from GUI table sorting.

Only opaque acquisition identifiers are tracked.  Checking an already-checked
acquisition does not change its position; unchecking and checking appends it.
"""
from __future__ import annotations


class SelectionOrder:
    def __init__(self, uids=()):
        self._uids: list[str] = []
        self.replace(uids)

    @property
    def uids(self) -> list[str]:
        return self._uids.copy()

    def replace(self, uids):
        ordered = []
        seen = set()
        for uid in uids:
            if not isinstance(uid, str) or not uid:
                raise ValueError('Identificador de espectro inválido.')
            if uid not in seen:
                ordered.append(uid)
                seen.add(uid)
        self._uids = ordered

    def set_checked(self, uid: str, checked: bool) -> None:
        if not isinstance(uid, str) or not uid:
            raise ValueError('Identificador de espectro inválido.')
        if checked:
            if uid not in self._uids:
                self._uids.append(uid)
        elif uid in self._uids:
            self._uids.remove(uid)

    def position(self, uid: str) -> int | None:
        try:
            return self._uids.index(uid) + 1
        except ValueError:
            return None

    def retain_only(self, valid_uids) -> None:
        valid = set(valid_uids)
        self._uids = [uid for uid in self._uids if uid in valid]
