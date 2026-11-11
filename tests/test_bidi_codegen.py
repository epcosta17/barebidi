import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from bidi_codegen import generate


def test_text_choice_becomes_a_literal():
    out = generate('script.RealmType = "window" / "worker" / "dedicated-worker"')
    assert 'type script_RealmType = Literal["window", "worker", "dedicated-worker"]' in out


def test_map_becomes_a_typeddict_with_wire_key_names():
    out = generate(dedent('''
        browsingContext.Navigate = {
          context: text,
          url: text,
          ? wait: text,
        }
    '''))
    assert "class browsingContext_Navigate(TypedDict):" in out
    assert "    context: str" in out
    assert "    url: str" in out
    assert "    wait: NotRequired[str]" in out


def test_type_choice_becomes_a_union():
    out = generate("session.UnsubscribeParameters = session.ByAttributes / session.ByID")
    assert 'type session_UnsubscribeParameters = session_ByAttributes | session_ByID' in out


def test_base_types_and_arrays():
    out = generate(dedent('''
        X = {
          count: js-uint,
          names: [*text],
          flag: bool,
        }
    '''))
    assert "    count: int" in out
    assert "    names: list[str]" in out
    assert "    flag: bool" in out


def test_inline_group_reference_flattens_its_fields():
    # `? session.SocksProxyConfiguration` inside a map contributes its fields, not nothing.
    out = generate(dedent('''
        X = {
          proxyType: "manual",
          ? Socks,
        }
        Socks = (
          socksProxy: text,
          socksVersion: js-uint,
        )
    '''))
    assert "class X(TypedDict):" in out
    assert "socksProxy: NotRequired[str]" in out
    assert "socksVersion: NotRequired[int]" in out


def test_hyphenated_keys_use_the_functional_typeddict():
    out = generate('emulation.MediaFeatures = { "any-hover": "none" / "hover" }')
    assert 'emulation_MediaFeatures = TypedDict("emulation_MediaFeatures"' in out
    assert '"any-hover"' in out


def test_recursive_types_use_lazy_type_aliases():
    # script.LocalValue refers to itself; `type` statements resolve lazily so this doesn't NameError.
    out = generate("X = text / [*X]")
    assert "type X = str | list[X]" in out


def test_the_generated_module_is_up_to_date_with_the_vendored_cddl():
    # If this fails, regenerate: python tools/bidi_codegen.py > src/nodriver_bidi/protocol.py
    from bidi_codegen import VENDORED

    generated = generate(VENDORED.read_text())
    committed = (Path(__file__).parent.parent / "src" / "nodriver_bidi" / "protocol.py").read_text()
    assert generated == committed


def test_generated_types_match_the_spec():
    # Annotations are strings (from __future__ import annotations), which is what type checkers read;
    # pyright honours the NotRequired wrappers even though TypedDict's runtime metadata can't.
    from nodriver_bidi import protocol

    def annotations(td):  # strings, whether Python stored them as str or ForwardRef
        return {key: getattr(value, "__forward_arg__", value) for key, value in td.__annotations__.items()}

    assert protocol.script_RealmType.__value__.__args__[:2] == ("window", "dedicated-worker")
    cookie = annotations(protocol.network_Cookie)
    assert cookie["name"] == "str" and cookie["value"] == "network_BytesValue"
    assert cookie["expiry"] == "NotRequired[int]"
    assert annotations(protocol.emulation_MediaFeatures)["any-hover"].startswith("NotRequired[")
