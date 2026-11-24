from typing import Callable


def public_methods(obj: object) -> dict[str, Callable]:
    """Every public method of ``obj`` by name (used to expose jinja filters/globals)."""
    methods: dict[str, Callable] = {}
    for name in dir(obj):
        if not name.startswith("_"):
            method = getattr(obj, name)
            if callable(method):
                methods[name] = method
    return methods
