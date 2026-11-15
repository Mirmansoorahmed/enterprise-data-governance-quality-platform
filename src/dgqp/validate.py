"""Minimal, dependency-free JSON-Schema-subset validator.

Why this exists
---------------
The offline CI sandbox cannot install ``jsonschema``. This module validates our
own JSON-Schema files (``schemas/*.schema.json``) against parsed data using a
supported subset of Draft-07 keywords:

``type`` (object/array/string/number/integer/boolean/null and lists thereof),
``properties``, ``required``, ``additionalProperties`` (bool), ``items``,
``enum``, ``minLength``, ``minItems``, ``pattern``, ``const``.

It is the documented unit equivalent for schema checks. The official ODCS
v3.2.0 JSON Schema can be run with ``jsonschema`` locally where network allows;
CI uses this subset so it stays green offline (see design.md s10, requirements
R1.4).
"""

from __future__ import annotations

import json
import re
from typing import Any


class ValidationError(ValueError):
    """Raised with a dotted path to the first failing node."""


def load_schema(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(instance: Any, schema: dict, path: str = "$") -> None:
    """Validate *instance* against *schema*; raise :class:`ValidationError`."""
    if "const" in schema and instance != schema["const"]:
        raise ValidationError(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema and instance not in schema["enum"]:
        raise ValidationError(f"{path}: {instance!r} not in enum {schema['enum']}")

    if "type" in schema:
        _check_type(instance, schema["type"], path)

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise ValidationError(f"{path}: shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            raise ValidationError(f"{path}: does not match pattern")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise ValidationError(f"{path}: fewer than minItems")
        if "items" in schema:
            for i, item in enumerate(instance):
                validate(item, schema["items"], f"{path}[{i}]")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise ValidationError(f"{path}: missing required '{key}'")
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties", True) is False:
                raise ValidationError(f"{path}: additional property '{key}'")


_PY_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _check_type(instance: Any, expected: Any, path: str) -> None:
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if _matches(instance, t):
            return
    raise ValidationError(f"{path}: expected type {expected}, got {type(instance).__name__}")


def _matches(instance: Any, t: str) -> bool:
    if t == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if t == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if t == "boolean":
        return isinstance(instance, bool)
    py = _PY_TYPES.get(t)
    if py is None:
        return False
    if py is dict or py is list or py is str or py is type(None):
        return isinstance(instance, py)
    return isinstance(instance, py)
