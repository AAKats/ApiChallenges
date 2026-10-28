"""Модели ответов API Challenges."""

from pydantic import BaseModel, ConfigDict

class TodoItem(BaseModel):
    """Задача в ответе API."""

    model_config = ConfigDict(strict=True, extra='forbid')

    id: int
    title: str
    doneStatus: bool
    description: str


class TodoList(BaseModel):
    """Ответ со списком задач."""

    model_config = ConfigDict(strict=True, extra='forbid')

    todos: list[TodoItem]