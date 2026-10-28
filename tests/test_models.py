"""Проверки настроек моделей ответов."""

import pytest
from pydantic import ValidationError

from api_challenges.models import TodoItem, TodoList


@pytest.mark.parametrize(
    ('changes', 'removed_field', 'expected_location'),
    [
        pytest.param({'id': '42'}, None, ('id',), id='string-id'),
        pytest.param({'id': True}, None, ('id',), id='boolean-id'),
        pytest.param(
            {'doneStatus': 'false'},
            None,
            ('doneStatus',),
            id='string-done-status',
        ),
        pytest.param(
            {'doneStatus': 0},
            None,
            ('doneStatus',),
            id='integer-done-status',
        ),
        pytest.param(
            {'description': None},
            None,
            ('description',),
            id='null-description',
        ),
        pytest.param({}, 'title', ('title',), id='missing-title'),
        pytest.param(
            {'priority': 'high'},
            None,
            ('priority',),
            id='extra-field',
        ),
    ],
)
def test_todo_item_rejects_invalid_data(changes, removed_field, expected_location):
    """Модель отвергает нарушение контракта на ожидаемом поле."""
    payload = {
        'id': 42,
        'title': 'Test title',
        'doneStatus': False,
        'description': '',
    }
    payload.update(changes)

    if removed_field is not None:
        del payload[removed_field]

    with pytest.raises(ValidationError) as exc:
        TodoItem.model_validate(payload)

    locations = {error['loc'] for error in exc.value.errors()}
    assert expected_location in locations


def test_todo_list_rejects_invalid_nested_todo():
    """Ошибка вложенной задачи содержит путь до неверного поля."""
    payload = {
        'todos': [
            {
                'id': 42,
                'title': 'Test title',
                'doneStatus': 'false',
                'description': '',
            },
        ],
    }

    with pytest.raises(ValidationError) as exc:
        TodoList.model_validate(payload)

    locations = {error['loc'] for error in exc.value.errors()}
    assert ('todos', 0, 'doneStatus') in locations
