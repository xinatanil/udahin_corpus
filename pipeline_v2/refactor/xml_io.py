from __future__ import annotations

import copy
from pathlib import Path
import xml.etree.ElementTree as ET

from .model import Card, Dictionary, Homonym, Line, Meaning


def line_from_element(element: ET.Element) -> Line:
    return Line(
        tag=element.tag,
        attrib=dict(element.attrib),
        text=element.text,
        tail=element.tail,
        children=[copy.deepcopy(child) for child in list(element)],
    )


def element_from_line(line: Line) -> ET.Element:
    element = ET.Element(line.tag, line.attrib)
    element.text = line.text
    for child in line.children:
        element.append(copy.deepcopy(child))
    element.tail = line.tail
    return element


def meaning_from_element(element: ET.Element) -> Meaning:
    return Meaning(blocks=[line_from_element(child) for child in list(element)])


def element_from_meaning(meaning: Meaning) -> ET.Element:
    element = ET.Element('meaning')
    for block in meaning.blocks:
        element.append(element_from_line(block))
    return element


def homonym_from_element(element: ET.Element) -> Homonym:
    blocks: list[Meaning | Line] = []
    for child in list(element):
        if child.tag == 'meaning':
            blocks.append(meaning_from_element(child))
        else:
            blocks.append(line_from_element(child))
    return Homonym(blocks=blocks)


def element_from_homonym(homonym: Homonym) -> ET.Element:
    element = ET.Element('homonym')
    for block in homonym.blocks:
        if isinstance(block, Meaning):
            element.append(element_from_meaning(block))
        else:
            element.append(element_from_line(block))
    return element


def card_from_element(element: ET.Element) -> Card:
    headword = None
    blocks: list[Meaning | Homonym | Line] = []

    for child in list(element):
        if child.tag == 'k' and headword is None:
            headword = line_from_element(child)
        elif child.tag == 'meaning':
            blocks.append(meaning_from_element(child))
        elif child.tag == 'homonym':
            blocks.append(homonym_from_element(child))
        else:
            blocks.append(line_from_element(child))

    return Card(headword=headword, blocks=blocks)


def element_from_card(card: Card) -> ET.Element:
    element = ET.Element('card')
    if card.headword is not None:
        element.append(element_from_line(card.headword))
    for block in card.blocks:
        if isinstance(block, Meaning):
            element.append(element_from_meaning(block))
        elif isinstance(block, Homonym):
            element.append(element_from_homonym(block))
        else:
            element.append(element_from_line(block))
    return element


def load_dictionary(path: str | Path) -> Dictionary:
    tree = ET.parse(path)
    root = tree.getroot()
    cards = [card_from_element(card) for card in root.findall('card')]
    return Dictionary(cards=cards)


def save_dictionary(dictionary: Dictionary, path: str | Path) -> None:
    root = ET.Element('root')
    for card in dictionary.cards:
        root.append(element_from_card(card))

    tree = ET.ElementTree(root)
    if hasattr(ET, 'indent'):
        ET.indent(tree, space='\t', level=0)
    tree.write(path, encoding='UTF-8', xml_declaration=True)
