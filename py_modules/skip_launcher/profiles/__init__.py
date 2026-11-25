"""Registered games. A game is added here only when its facts are real and its tests pass."""
from .batman_aa import PROFILE as _BATMAN_AA
from .max_payne import PROFILE as _MAX_PAYNE
from .max_payne_2 import PROFILE as _MAX_PAYNE_2

PROFILES = {p.appid: p for p in (_BATMAN_AA, _MAX_PAYNE, _MAX_PAYNE_2)}
