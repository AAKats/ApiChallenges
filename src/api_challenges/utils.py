import csv
import io
import re
import xml.etree.ElementTree as ET
from html import unescape


def _todo_text(element: ET.Element, field: str) -> str:
    child = element.find(field)
    return child.text if child is not None and child.text is not None else ''


def _todo_to_dict(element: ET.Element) -> dict:
    return {
        'id': int(_todo_text(element, 'id')),
        'title': _todo_text(element, 'title'),
        'doneStatus': _todo_text(element, 'doneStatus') == 'true',
        'description': _todo_text(element, 'description'),
    }


def todo_from_xml(xml_text: str) -> dict:
    return _todo_to_dict(ET.fromstring(xml_text))


def todos_from_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    return [_todo_to_dict(el) for el in root.findall('todo')]


def request_todo_from_xml(xml_text: str) -> dict:
    element = ET.fromstring(xml_text)
    return {
        'title': _todo_text(element, 'title'),
        'doneStatus': _todo_text(element, 'doneStatus') == 'true',
        'description': _todo_text(element, 'description'),
    }


def _html_cells(section_html: str) -> list[str]:
    return [
        unescape(cell) for cell in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', section_html, re.DOTALL)
    ]


def todos_from_html(html_text: str) -> list[dict]:
    thead = re.search(r'<thead>(.*?)</thead>', html_text, re.DOTALL)
    assert thead, 'Missing <thead> in HTML export'
    header = _html_cells(thead.group(1))
    assert header == ['id', 'title', 'doneStatus', 'description'], (
        f'Unexpected HTML header: {header!r}'
    )
    tbody = re.search(r'<tbody>(.*?)</tbody>', html_text, re.DOTALL)
    assert tbody, 'Missing <tbody> in HTML export'
    result = []
    for row in re.findall(r'<tr>(.*?)</tr>', tbody.group(1), re.DOTALL):
        cells = _html_cells(row)
        if not cells or all(cell == '' for cell in cells):
            continue
        result.append(
            {
                'id': int(cells[0]),
                'title': cells[1],
                'doneStatus': cells[2] == 'true',
                'description': cells[3],
            }
        )
    return result


def _todos_from_delimited(text: str, *, delimiter: str) -> list[dict]:
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    header = rows[0]
    assert header == ['id', 'title', 'doneStatus', 'description'], f'Unexpected header: {header!r}'
    result = []
    for row in rows[1:]:
        if not row or all(cell == '' for cell in row):
            continue
        result.append(
            {
                'id': int(row[0]),
                'title': row[1],
                'doneStatus': row[2] == 'true',
                'description': row[3],
            }
        )
    return result


def todos_from_csv(csv_text: str) -> list[dict]:
    return _todos_from_delimited(csv_text, delimiter=',')


def todos_from_tsv(tsv_text: str) -> list[dict]:
    return _todos_from_delimited(tsv_text, delimiter='\t')
