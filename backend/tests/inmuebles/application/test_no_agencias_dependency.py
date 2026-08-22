"""Static import-boundary test for `inmuebles/application`.

Covers task 3.5 of `openspec/changes/hu-002/tasks.md` and design.md's
"Context"/decisión 1 of `openspec/changes/hu-002/`: `inmuebles/application`
(and `inmuebles/domain`, by the same rule) must never import anything from
`agencias` — the cross-domain authorization query lives exclusively in
`inmuebles/infrastructure/api/router.py` (out of scope for this test).

This is a deliberately simple static/textual check (grep-style), not an
AST-based import analyzer: it fails the moment any `application/*.py` file
contains a line with `from agencias` or `import agencias`, regardless of
whether that import would actually be reachable/used at runtime. It's a
regression guard against the direction-of-dependency invariant established
in `openspec/changes/hu-007/design.md` and reaffirmed by hu-002's design.md.
"""

from __future__ import annotations

from pathlib import Path

APPLICATION_DIR = Path(__file__).resolve().parents[3] / "inmuebles" / "application"


def _application_source_files() -> list[Path]:
    assert APPLICATION_DIR.is_dir(), f"expected directory to exist: {APPLICATION_DIR}"
    files = sorted(APPLICATION_DIR.glob("*.py"))
    assert files, f"expected at least one .py file under {APPLICATION_DIR}"
    return files


class TestInmueblesApplicationHasNoAgenciasImport:
    def test_no_application_file_imports_from_agencias(self) -> None:
        offenders: dict[str, list[str]] = {}
        for path in _application_source_files():
            bad_lines = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if "from agencias" in line or "import agencias" in line
            ]
            if bad_lines:
                offenders[str(path)] = bad_lines

        assert offenders == {}, (
            "inmuebles/application must never import from agencias "
            f"(design.md decisión 1): {offenders}"
        )
