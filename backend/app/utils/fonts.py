"""
Font analysis utilities.

Helpers for determining font properties from font names and flags,
classifying fonts as body/heading/code, and detecting emphasis.
"""

from __future__ import annotations

import re

# Known monospace font families (case-insensitive substrings)
MONOSPACE_INDICATORS = [
    "courier", "consolas", "mono", "menlo", "firacode",
    "source code", "jetbrains", "inconsolata", "droid sans mono",
    "liberation mono", "lucida console", "andale mono",
    "dejavu sans mono", "ubuntu mono", "noto mono",
    # LaTeX / Computer Modern typewriter fonts
    "cmtt", "typewriter",
    # Additional modern monospace fonts
    "fixedsys", "hack", "iosevka", "roboto mono", "sf mono",
    "cascadia",
]

# Known bold indicators in font names
BOLD_INDICATORS = ["bold", "black", "heavy", "demi", "semibold"]

# Known italic indicators in font names
ITALIC_INDICATORS = ["italic", "oblique", "slanted"]


def is_bold_font(font_name: str, flags: int = 0) -> bool:
    """Determine if a font is bold from its name or flags.
    
    Args:
        font_name: The font's PostScript name or family name
        flags: PDF font descriptor flags (bit 19 = force bold)
    """
    name_lower = font_name.lower()
    # Check name
    if any(indicator in name_lower for indicator in BOLD_INDICATORS):
        return True
    # Check PDF font flags (bit 19 = ForceBold in some implementations)
    if flags & (1 << 18):  # ForceBold flag
        return True
    return False


def is_italic_font(font_name: str, flags: int = 0) -> bool:
    """Determine if a font is italic from its name or flags.
    
    Args:
        font_name: The font's PostScript name or family name
        flags: PDF font descriptor flags (bit 7 = italic)
    """
    name_lower = font_name.lower()
    if any(indicator in name_lower for indicator in ITALIC_INDICATORS):
        return True
    if flags & (1 << 6):  # Italic flag
        return True
    return False


def is_monospace_font(font_name: str, flags: int = 0) -> bool:
    """Determine if a font is monospaced from its name or flags.
    
    Args:
        font_name: The font's PostScript name or family name
        flags: PDF font descriptor flags (bit 1 = FixedPitch)
    """
    name_lower = font_name.lower()
    if any(indicator in name_lower for indicator in MONOSPACE_INDICATORS):
        return True
    if flags & 1:  # FixedPitch flag
        return True
    return False


def normalize_font_name(font_name: str) -> str:
    """Normalize a font name by removing common prefixes and suffixes.
    
    PDF fonts often have prefixes like "BCDEAF+" or suffixes like ",Bold".
    This strips those to get the base family name.
    """
    # Remove subset prefix (6 uppercase letters + "+")
    name = re.sub(r"^[A-Z]{6}\+", "", font_name)
    # Remove common separators and style suffixes for family grouping
    name = name.split(",")[0]  # "TimesNewRoman,Bold" → "TimesNewRoman"
    name = name.split("-")[0]  # "Arial-BoldMT" → "Arial"
    return name.strip()


def get_font_family(font_name: str) -> str:
    """Extract the font family name, stripping style indicators."""
    normalized = normalize_font_name(font_name)
    # Remove style words
    for word in BOLD_INDICATORS + ITALIC_INDICATORS:
        normalized = re.sub(rf"\b{word}\b", "", normalized, flags=re.IGNORECASE)
    return normalized.strip() or font_name
