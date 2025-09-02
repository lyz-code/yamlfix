"""Define utility helpers."""
from typing import Any, Callable, Iterable, Mapping


def walk_object(
    target: Any, callback_fn: Callable[[Any], None]  # noqa: ANN401
) -> None:
    """Walk a YAML/JSON-like object and call a function on all values."""
    callback_fn(target)  # Call the callback and whatever we received.

    if isinstance(target, Mapping):
        # Map type
        for _, value in target.items():
            walk_object(value, callback_fn)
    elif isinstance(target, Iterable) and not isinstance(target, (bytes, str)):
        # List type
        for value in target:
            walk_object(value, callback_fn)
