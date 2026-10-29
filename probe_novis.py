from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from scrapling.fetchers import Fetcher, StealthyFetcher


@dataclass
class ProbeResult:
    label: str
    url: str
    mode: str
    status: int | None
    title: str | None
    text_length: int
    price_tokens: list[str]
    identity_hits: list[str]
    error: str | None = None


TARGETS = [
    ("CONTROL_MAFY_P47", "https://mobilityaidsforyou.com.au/products/ornamin-non-slip-cup-flower-design",
     ["Ornamin", "Non Slip Cup", "Flower", "Orange"]),
    ("P50_MOBILITY_ZONE", "https://mobilityzone.com.au/product/orientation-signage-better-living/",
     ["Orientation Signage", "Better Living", "Bedroom", "Kitchen", "Bathroom", "Toilet"]),
    ("P50_SCOOTERS", "https://www.scootersandmobility.com.au/products/betterliving-orientation-signage",
     ["BetterLiving", "Orientation Signage", "Bedroom", "Kitchen", "Bathroom", "Toilet"]),
    ("P54_TAMWORTH", "https://www.tamworthscootersandmobility.com.au/products/confident-care-cleansing-kit",
     ["Confident Care", "Cleansing Kit"]),
    ("REHAB_P22", "https://www.rehabhire.com.au/product/stander-handybar/",
     ["Stander", "Handybar", "31003"]),
    ("MAX_P39", "https://www.maxhealthcareequipment.com.au/product/etac-flex-grab-rails-screw-mounted/",
     ["Etac", "Flex", "HAEFRW30"]),
    ("SOLUTIONS_P20", "https://www.solutionsmedical.net.au/index.php?route=product/product&product_id=5201",
     ["Sensory Cushion", "Emerald Green", "King Fisher Blue"]),
]


def text_of(page) -> str:
    try:
        return page.get_all_text(separator=" ", strip=True)
    except Exception:
        try:
            return page.text
        except Exception:
            return str(page)


def title_of(page) -> str | None:
    try:
        vals = page.css("title::text").getall()
        return " ".join(v.strip() for v in vals if v.strip()) or None
    except Exception:
        return None


def status_of(page) -> int | None:
    for attr in ("status", "status_code"):
        try:
            value = getattr(page, attr)
            if value is not None:
                return int(value)
        except Exception:
            pass
    return None


def summarize(label: str, url: str, mode: str, page, expected: list[str]) -> ProbeResult:
    text = re.sub(r"\s+", " ", text_of(page))
    prices = []
    for token in re.findall(r"(?:AUD\s*)?\$\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?", text, flags=re.I):
        if token not in prices:
            prices.append(token)
        if len(prices) >= 30:
            break
    hits = [term for term in expected if term.lower() in text.lower()]
    return ProbeResult(
        label=label,
        url=url,
        mode=mode,
        status=status_of(page),
        title=title_of(page),
        text_length=len(text),
        price_tokens=prices,
        identity_hits=hits,
    )


def run():
    results: list[ProbeResult] = []

    for label, url, expected in TARGETS:
        # Fast Scrapling HTTP/TLS fetch first.
        try:
            page = Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=45)
            results.append(summarize(label, url, "fetcher", page, expected))
        except Exception as exc:
            results.append(ProbeResult(label, url, "fetcher", None, None, 0, [], [], f"{type(exc).__name__}: {exc}"))

        # Browser fallback for blocked/dynamic sites.
        try:
            page = StealthyFetcher.fetch(
                url,
                headless=True,
                solve_cloudflare=True,
                network_idle=True,
                timeout=60000,
            )
            results.append(summarize(label, url, "stealthy", page, expected))
        except Exception as exc:
            results.append(ProbeResult(label, url, "stealthy", None, None, 0, [], [], f"{type(exc).__name__}: {exc}"))

    print("SCRAPLING_RESULTS_START")
    print(json.dumps([asdict(r) for r in results], indent=2))
    print("SCRAPLING_RESULTS_END")


if __name__ == "__main__":
    run()
