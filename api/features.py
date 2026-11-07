"""Feature flags (env). Default on; set FEATURE_<NAME>=0 to hide a feature (routes 404, app hides it)."""
import os

from api.errors import not_found

FEATURES = ("learn", "ranked", "accounts")


def enabled(name: str) -> bool:
    return os.environ.get(f"FEATURE_{name.upper()}", "1") not in ("0", "false", "no", "off")


def all_flags() -> dict[str, bool]:
    return {f: enabled(f) for f in FEATURES}


def require(name: str):
    """FastAPI dependency factory: 404 unless the feature is on."""

    def check() -> None:
        if not enabled(name):
            raise not_found("Route")

    return check
