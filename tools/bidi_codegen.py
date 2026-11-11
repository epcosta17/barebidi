"""Generate Python types from the WebDriver BiDi CDDL, so the library follows the standard as it changes.

The CDDL lives in the spec; webref (https://github.com/w3c/webref, ed/cddl) extracts it and keeps it current.
This reads that CDDL and emits TypedDicts for its maps, Literal for its text enums, unions for its choices,
and aliases for the rest, with the wire key names kept exactly.

The vendored CDDL (webdriver-bidi.cddl beside this file) is pinned to a webref commit; update it with:

    python tools/bidi_codegen.py --update

then regenerate the types:

    python tools/bidi_codegen.py > ../src/nodriver_bidi/protocol.py
"""

import json
import keyword
import re
import sys
import urllib.request
from pathlib import Path

# webref's extracted CDDL, pinned. Bump COMMIT (or run --update) to follow a newer spec revision.
SOURCE = "https://raw.githubusercontent.com/w3c/webref/{commit}/ed/cddl/webdriver-bidi-all.cddl"
COMMIT = "3b4e4517fdc8e51c06b266093888236e6dbeb529"
VENDORED = Path(__file__).with_name("webdriver-bidi.cddl")

# The base CDDL types the BiDi spec uses, to Python.
_BASE = {"text": "str", "bool": "bool", "float": "float", "null": "None", "any": "Any",
         "js-uint": "int", "js-int": "int", "uint": "int", "int": "int", "number": "float",
         "true": "bool", "false": "bool"}

# Groups that only add open-endedness or are the generic command/event envelopes: no type of their own.
_SKIP_REFS = {"Extensible"}

_TOKEN = re.compile(
    r"""
      (?P<ws>\s+)
    | (?P<comment>;[^\n]*)
    | (?P<string>"[^"]*")
    | (?P<arrow>=>)
    | (?P<gchoice>//)
    | (?P<range>\.\.)
    | (?P<ctrl>\.[a-zA-Z]+)
    | (?P<number>-?\d+(?:\.\d+)?)
    | (?P<name>[a-zA-Z_][a-zA-Z0-9_]*(?:[.-][a-zA-Z0-9_]+)*)
    | (?P<op>[={}()\[\]:,?*+/])
    """,
    re.VERBOSE,
)


def tokenize(source: str) -> list[tuple[str, str]]:
    tokens = []
    for match in _TOKEN.finditer(source):
        kind = match.lastgroup
        if kind not in ("ws", "comment"):
            tokens.append((kind, match.group()))
    return tokens


class Parser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> tuple[str, str]:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def eat(self, value: str) -> None:
        kind, got = self.next()
        if got != value:
            raise SyntaxError(f"expected {value!r}, got {got!r}")

    def rules(self) -> list[tuple[str, dict]]:
        rules = []
        while self.peek() is not None:
            name = self.next()[1]
            self.eat("=")
            rules.append((name, self.definition()))
        return rules

    def definition(self) -> dict:
        """A rule's right-hand side: a map, a group, or a choice of types."""
        kind, value = self.peek()
        if value in ("{", "("):
            return self.braced(value, "}" if value == "{" else ")")
        return self.choice()

    def braced(self, open_: str, close: str) -> dict:
        """`{ ... }` or `( ... )`, classified by its depth-1 content: // group choice (union), key:type
        entries a map, / a type choice, or *text => any (opaque)."""
        marks = self._depth1_marks(open_, close)
        if "//" in marks:
            return self.group_choice(open_, close)
        if ":" in marks:
            return self.map(open_, close)
        if "=>" in marks:
            self._skip_balanced(open_, close)  # (*text => any) and the like: no type of its own
            return {"kind": "opaque"}
        if open_ == "{":
            return self.map(open_, close)  # a map with no typed entries, e.g. { Extensible } or {}
        self.eat(open_)
        node = self.choice()  # ( ... ): a parenthesized type or type choice
        self.eat(close)
        return node

    def _depth1_marks(self, open_: str, close: str) -> set[str]:
        """Marks (// : =>) that sit directly in this bracket, not inside a nested one of any kind."""
        opens, closes = "({[", ")}]"
        depth, at, marks = 1, self.pos + 1, set()
        while depth:
            value = self.tokens[at][1]
            if depth == 1 and value in ("//", ":", "=>"):
                marks.add(value)
            depth += (value in opens) - (value in closes)
            at += 1
        return marks

    def _skip_balanced(self, open_: str, close: str) -> None:
        self.eat(open_)
        depth = 1
        while depth:
            value = self.next()[1]
            depth += {open_: 1, close: -1}.get(value, 0)

    def group_choice(self, open_: str, close: str) -> dict:
        self.eat(open_)
        alternatives = []
        while True:
            member = self.type()
            if not (member["kind"] == "ref" and member["name"] in _SKIP_REFS):
                alternatives.append(member)
            if self.peek()[1] != "//":
                break
            self.eat("//")
        self.eat(close)
        return {"kind": "union", "options": alternatives}

    def map(self, open_: str, close: str) -> dict:
        self.eat(open_)
        entries, inlines = [], []
        extensible = False
        while self.peek()[1] != close:
            optional = self.peek()[1] == "?"
            if optional:
                self.eat("?")
            if self.peek()[1] in ("(", "{"):  # an inline group: (A // B) discriminates the map's shape
                inlines.append(self.braced(self.peek()[1], "}" if self.peek()[1] == "{" else ")"))
            elif self.peek()[1] == "*":  # *text => any: extra keys of any type
                while self.peek()[1] not in (",", close):
                    self.next()
                extensible = True
            elif self._is_bare_ref(close):  # a group reference: Extensible, or a named group to inline
                ref = self.next()[1]
                if ref in _SKIP_REFS:
                    extensible = True
                else:
                    inlines.append({"kind": "ref", "name": ref})  # its fields flatten into this map
            else:
                kind, text = self.next()
                key = text[1:-1] if kind == "string" else text  # a key may be a text literal: "any-hover"
                self.eat(":")
                entries.append({"key": key, "optional": optional, "type": self.choice()})
            if self.peek()[1] == ",":
                self.eat(",")
        self.eat(close)
        return {"kind": "map", "entries": entries, "inlines": inlines, "extensible": extensible}

    def _is_bare_ref(self, close: str) -> bool:
        # A name not followed by ":" is a group reference inlined into the map (e.g. Extensible).
        return self.peek()[0] == "name" and self.tokens[self.pos + 1][1] != ":"

    def choice(self) -> dict:
        options = [self.type()]
        while self.peek() and self.peek()[1] == "/":
            self.eat("/")
            options.append(self.type())
        if len(options) == 1:
            return options[0]
        if all(o["kind"] == "literal" for o in options):
            return {"kind": "enum", "values": [o["value"] for o in options]}
        return {"kind": "union", "options": options}

    def type(self) -> dict:
        kind, value = self.peek()
        if value in ("{", "("):
            node = self.braced(value, "}" if value == "{" else ")")
        elif value == "[":
            node = self.array()
        elif kind == "string":
            self.next()
            node = {"kind": "literal", "value": value[1:-1]}
        elif kind == "number":
            node = self.range_or_number()
        else:
            self.next()
            node = {"kind": "ref", "name": value}
        self._skip_control()
        return node

    def array(self) -> dict:
        self.eat("[")
        members, homogeneous = [], False
        while self.peek()[1] != "]":
            if self.peek()[1] in ("*", "+"):  # zero-or-more / one-or-more: a homogeneous list
                self.next()
                homogeneous = True
            members.append(self.choice())
            if self.peek()[1] == ",":
                self.eat(",")
        self.eat("]")
        if homogeneous or len(members) == 1:
            return {"kind": "array", "element": members[0]}
        return {"kind": "tuple", "members": members}  # a fixed-length array

    def range_or_number(self) -> dict:
        self.next()
        if self.peek() and self.peek()[1] == "..":
            self.eat("..")
            self.next()
            return {"kind": "ref", "name": "int"}
        return {"kind": "ref", "name": "int"}

    def _skip_control(self) -> None:
        while self.peek() and self.peek()[0] == "ctrl":  # .default / .ge / .gt and its argument
            self.next()
            self.type()


def mangle(name: str) -> str:
    return name.replace(".", "_").replace("-", "_")


class Emitter:
    def __init__(self, rules: list[tuple[str, dict]]):
        self.rules = rules
        self.names = {name for name, _ in rules}
        self.by_name = dict(rules)

    def python(self, node: dict) -> str:
        kind = node["kind"]
        if kind == "ref":
            name = node["name"]
            if name in _SKIP_REFS:  # Extensible used as a type: an open map of extra keys
                return "dict[str, Any]"
            return _BASE[name] if name in _BASE else mangle(name)  # lazy: `type` aliases resolve on use
        if kind == "literal":
            return f"Literal[{_str(node['value'])}]"
        if kind == "array":
            return f"list[{self.python(node['element'])}]"
        if kind == "tuple":
            return "tuple[" + ", ".join(self.python(m) for m in node["members"]) + "]"
        if kind == "enum":
            return "Literal[" + ", ".join(_str(v) for v in node["values"]) + "]"
        if kind == "union":
            return " | ".join(self.python(o) for o in node["options"])
        if kind in ("map", "opaque"):
            return "dict[str, Any]"  # an inline or open-ended map
        return "Any"

    def emit(self) -> str:
        blocks = []
        for name, node in self.rules:
            if name in _SKIP_REFS:
                continue
            blocks.append(self.emit_rule(mangle(name), node))
        header = (
            '"""WebDriver BiDi protocol types, generated from the spec CDDL by tools/bidi_codegen.py.\n\n'
            f"Source: webref ed/cddl at commit {COMMIT}.\n"
            "Do not edit by hand; regenerate from the spec CDDL. Names keep the spec's, with . and - as _.\n"
            '"""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import Any, Literal, NotRequired, TypedDict\n"
        )
        return header + "\n\n".join(blocks) + "\n"

    def emit_rule(self, name: str, node: dict) -> str:
        if node["kind"] == "map":
            return self.emit_typeddict(name, node)
        return f"type {name} = {self.python(node)}"  # PEP 695: lazy, so forward refs and recursion resolve

    def emit_typeddict(self, name: str, node: dict) -> str:
        entries = self._merged_entries(node)
        annotations = [(entry["key"], self._annotation(entry)) for entry in entries]
        if all(key.isidentifier() and not keyword.iskeyword(key) for key, _ in annotations):
            lines = [f"class {name}(TypedDict):"]
            lines += [f"    {key}: {annotation}" for key, annotation in annotations] or ["    pass"]
            return "\n".join(lines)
        # A key that isn't a Python identifier (e.g. "any-hover") needs the functional form.
        fields = ", ".join(f"{_str(key)}: {_str(annotation)}" for key, annotation in annotations)
        return f"{name} = TypedDict({_str(name)}, {{{fields}}})"

    def _annotation(self, entry: dict) -> str:
        annotation = self.python(entry["type"])
        return f"NotRequired[{annotation}]" if entry["optional"] else annotation

    def _merged_entries(self, node: dict) -> list[dict]:
        """A map's own entries, plus those of any inline group flattened in as NotRequired (an inline group
        choice makes the map one of several shapes, so its fields can't all be required)."""
        merged = {entry["key"]: dict(entry) for entry in node["entries"]}
        for inline in node.get("inlines", ()):
            for entry in self._fields_of(inline, set()):
                existing = merged.get(entry["key"])
                if existing is None:
                    merged[entry["key"]] = {**entry, "optional": True}
                elif self.python(existing["type"]) != self.python(entry["type"]):
                    existing["type"] = {"kind": "union", "options": [existing["type"], entry["type"]]}
        return list(merged.values())

    def _fields_of(self, node: dict, seen: set) -> list[dict]:
        """The entries a node contributes to a map it is inlined into, resolving refs and group choices."""
        if node["kind"] == "ref":
            target = self.by_name.get(node["name"])
            if target is None or node["name"] in seen:
                return []
            return self._fields_of(target, seen | {node["name"]})
        if node["kind"] == "map":
            fields = list(node["entries"])
            for inline in node.get("inlines", ()):
                fields += self._fields_of(inline, seen)
            return fields
        if node["kind"] == "union":
            fields = []
            for option in node["options"]:
                fields += [{**entry, "optional": True} for entry in self._fields_of(option, seen)]
            return fields
        return []


def _str(value: str) -> str:
    return json.dumps(value)


def generate(cddl: str) -> str:
    rules = Parser(tokenize(cddl)).rules()
    return Emitter(rules).emit()


def update() -> None:
    """Fetch the pinned CDDL from webref into the vendored copy."""
    with urllib.request.urlopen(SOURCE.format(commit=COMMIT), timeout=30) as response:
        VENDORED.write_bytes(response.read())


if __name__ == "__main__":
    if "--update" in sys.argv:
        update()
    elif len(sys.argv) > 1:
        print(generate(Path(sys.argv[1]).read_text()), end="")
    else:
        print(generate(VENDORED.read_text()), end="")
