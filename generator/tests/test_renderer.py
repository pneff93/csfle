"""Tests for the renderer's macro contract enforcement."""
import pytest

from csfle_gen.renderer import (
    LANGUAGE_MACRO_CONTRACT,
    MacroContractError,
    TEMPLATES_DIR,
    _build_env,
    _macros_in,
    _validate_macros,
)

LANGUAGES = ["python", "java", "javascript", "dotnet", "go"]


@pytest.mark.parametrize("language", LANGUAGES)
def test_macro_contract_passes_for_all_partials(language: str) -> None:
    env = _build_env()
    _validate_macros(env, language)


@pytest.mark.parametrize("language", LANGUAGES)
def test_kms_partials_define_all_required_macros(language: str) -> None:
    env = _build_env()
    partials_dir = TEMPLATES_DIR / language / "partials"
    required = LANGUAGE_MACRO_CONTRACT[language]["kms"]
    for partial in partials_dir.glob("kms_*.j2"):
        defined = _macros_in(env, partial.read_text())
        missing = required - defined
        assert not missing, f"{language}/{partial.name} missing macros: {missing}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_target_partials_define_all_required_macros(language: str) -> None:
    env = _build_env()
    partials_dir = TEMPLATES_DIR / language / "partials"
    required = LANGUAGE_MACRO_CONTRACT[language]["target"]
    for partial in partials_dir.glob("target_*.j2"):
        defined = _macros_in(env, partial.read_text())
        missing = required - defined
        assert not missing, f"{language}/{partial.name} missing macros: {missing}"


def test_missing_macro_raises_clear_error(tmp_path, monkeypatch) -> None:
    """If a partial omits a required macro, validation fails with the partial name."""
    fake_partials = tmp_path / "python" / "partials"
    fake_partials.mkdir(parents=True)
    fake_shared = tmp_path / "python" / "shared"
    fake_shared.mkdir(parents=True)
    (fake_partials / "kms_broken.j2").write_text(
        "{% macro imports() %}x{% endmacro %}\n"
    )
    monkeypatch.setattr("csfle_gen.renderer.TEMPLATES_DIR", tmp_path)

    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(tmp_path)))
    with pytest.raises(MacroContractError) as exc_info:
        _validate_macros(env, "python")
    assert "kms_broken" in str(exc_info.value)
    assert "register" in str(exc_info.value)
