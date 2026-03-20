from __future__ import annotations

import importlib
from dataclasses import dataclass

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover
    import importlib_metadata  # type: ignore


@dataclass(frozen=True)
class Requirement:
    import_name: str
    package_name: str
    minimum_version: str


REQUIREMENTS = (
    Requirement("numpy", "numpy", "1.23"),
    Requirement("pandas", "pandas", "1.5"),
    Requirement("scipy", "scipy", "1.10"),
    Requirement("matplotlib", "matplotlib", "3.7"),
    Requirement("tqdm", "tqdm", "4.65"),
)


class DependencyError(RuntimeError):
    """Raised when one or more runtime dependencies are missing or too old."""


def _normalize_version(version: str) -> tuple[int, ...]:
    parts = []
    for token in version.replace("-", ".").split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        if digits:
            parts.append(int(digits))
        else:
            break
    return tuple(parts) if parts else (0,)


def _is_compatible(installed: str, minimum: str) -> bool:
    return _normalize_version(installed) >= _normalize_version(minimum)


def _installed_version(req: Requirement) -> str | None:
    try:
        importlib.import_module(req.import_name)
        return importlib_metadata.version(req.package_name)
    except Exception:
        return None


def ensure_dependencies(quiet: bool = False) -> None:
    missing_or_old: list[tuple[Requirement, str | None]] = []
    for req in REQUIREMENTS:
        version = _installed_version(req)
        if version is None or not _is_compatible(version, req.minimum_version):
            missing_or_old.append((req, version))
        elif not quiet:
            print(f"[OK] {req.package_name}=={version}")

    if not missing_or_old:
        if not quiet:
            print("All required runtime packages are available.")
        return

    lines = ["Missing or incompatible runtime packages detected:"]
    for req, version in missing_or_old:
        if version is None:
            lines.append(f"- {req.package_name}>={req.minimum_version} (not installed)")
        else:
            lines.append(
                f"- {req.package_name}>={req.minimum_version} (found {version})"
            )
    lines.append("Install or upgrade them manually, then run the script again.")
    lines.append(
        'Example: pip install "numpy>=1.23" "pandas>=1.5" "scipy>=1.10" "matplotlib>=3.7" "tqdm>=4.65"'
    )
    raise DependencyError("\n".join(lines))


if __name__ == "__main__":
    try:
        ensure_dependencies(quiet=False)
    except DependencyError as exc:
        raise SystemExit(str(exc))
