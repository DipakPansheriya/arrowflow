"""
Central source of truth for ArrowFlow application version.
"""

CURRENT_VERSION = "1.0.14"


def parse_version(version_str: str) -> tuple:
    """
    Parses a version string into a tuple of integers for comparison.
    Strips leading 'v' or 'V' if present.
    Example: 'v1.2.3' -> (1, 2, 3)
    """
    if not version_str:
        return (0, 0, 0)
    cleaned = str(version_str).strip().lstrip("vV")
    # Extract numeric components prior to any pre-release tags like -beta
    main_part = cleaned.split("-")[0]
    parts = []
    for chunk in main_part.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer_version(current: str, latest: str) -> bool:
    """
    Returns True if latest version is strictly greater than current version.
    """
    return parse_version(latest) > parse_version(current)


