from __future__ import annotations

from dataclasses import dataclass, field
import xml.etree.ElementTree as ET


@dataclass
class Line:
    tag: str
    attrib: dict[str, str] = field(default_factory=dict)
    text: str | None = None
    tail: str | None = None
    children: list[ET.Element] = field(default_factory=list)


@dataclass
class Meaning:
    blocks: list[Line] = field(default_factory=list)


@dataclass
class Homonym:
    blocks: list[Meaning | Line] = field(default_factory=list)


@dataclass
class Card:
    headword: Line | None = None
    blocks: list[Meaning | Homonym | Line] = field(default_factory=list)


@dataclass
class Dictionary:
    cards: list[Card] = field(default_factory=list)
