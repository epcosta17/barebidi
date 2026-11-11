"""Conversion between Python values and BiDi LocalValue / RemoteValue."""

import math
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import protocol
    from .frame import Frame

_SPECIAL_NUMBERS = {"NaN": math.nan, "-0": -0.0, "Infinity": math.inf, "-Infinity": -math.inf}


def serialize(value: Any) -> "protocol.script_LocalValue":
    from .element import Element

    if isinstance(value, Element):
        return value.reference
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean", "value": value}
    if isinstance(value, int):
        if abs(value) > 2**53:
            return {"type": "bigint", "value": str(value)}
        return {"type": "number", "value": value}
    if isinstance(value, float):
        if math.isnan(value):
            return {"type": "number", "value": "NaN"}
        if math.isinf(value):
            return {"type": "number", "value": "Infinity" if value > 0 else "-Infinity"}
        return {"type": "number", "value": value}
    if isinstance(value, str):
        return {"type": "string", "value": value}
    if isinstance(value, datetime):
        return {"type": "date", "value": value.isoformat()}
    if isinstance(value, (list, tuple)):
        return {"type": "array", "value": [serialize(v) for v in value]}
    if isinstance(value, dict):
        return {"type": "object", "value": [[str(k), serialize(v)] for k, v in value.items()]}
    raise TypeError(f"cannot send {type(value).__name__} to the browser")


def deserialize(remote: dict, frame: "Frame | None" = None) -> Any:
    kind = remote["type"]
    value = remote.get("value")
    match kind:
        case "undefined" | "null":
            return None
        case "string" | "boolean":
            return value
        case "number":
            return _SPECIAL_NUMBERS.get(value, value) if isinstance(value, str) else value
        case "bigint":
            return int(value)
        case "array" | "set" | "nodelist" | "htmlcollection":
            return [deserialize(v, frame) for v in value or []]
        case "object" | "map":
            return {
                k if isinstance(k, str) else _hashable(deserialize(k, frame)): deserialize(v, frame)
                for k, v in value or []
            }
        case "date":
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        case "node" if frame is not None:
            from .element import Element

            return Element(frame, remote)
        case "window" if frame is not None:
            return frame._frame_for(value["context"])
        case _:
            return remote


def _hashable(value: Any) -> Any:
    return repr(value) if isinstance(value, (list, dict)) else value
