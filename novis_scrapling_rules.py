from __future__ import annotations

# Explicit Procedure 2 SKU/variant equivalences validated by the user and
# re-verified live with Scrapling. Keep this narrow: no global prefix stripping.

SKU_ALIASES: dict[tuple[str, str], set[str]] = {
    ("Mable Direct", "KC12"): {"LK113-KC12"},
    ("Mable Direct", "KC85"): {"LK113-KC85"},
    ("Happy Healthcare", "BL9504"): {"NOVBL9504"},
}

# Aged Care and Medical uses its own SKU family for Etac Aktiv Reachers.
# The NOVIS 90cm item must be selected by exact option, not by NOVIS SKU.
VARIANT_OVERRIDES: dict[tuple[str, str], dict[str, object]] = {
    ("Aged Care and Medical", "80505009"): {
        "variant_terms": ["90cm"],
        "retailer_sku": "NS0006907",
        "variant_id": 33803357388859,
    },
}


def sku_matches(competitor: str, novis_sku: str, retailer_sku: str) -> bool:
    if retailer_sku.strip().casefold() == novis_sku.strip().casefold():
        return True
    allowed = SKU_ALIASES.get((competitor, novis_sku), set())
    return retailer_sku.strip().casefold() in {x.casefold() for x in allowed}


def variant_override(competitor: str, novis_sku: str) -> dict[str, object] | None:
    return VARIANT_OVERRIDES.get((competitor, novis_sku))
