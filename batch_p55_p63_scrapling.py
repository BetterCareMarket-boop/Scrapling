from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit

from scrapling.fetchers import Fetcher


@dataclass
class Target:
    pnum: int
    mapping_id: int
    competitor: str
    product: str
    url: str
    expected_terms: list[str]
    variant_terms: list[str] | None = None
    variant_sku: str | None = None


@dataclass
class Result:
    pnum: int
    mapping_id: int
    competitor: str
    product: str
    url: str
    final_url: str | None = None
    http_status: int | None = None
    current_price: str | None = None
    special_price: str | None = None
    stock_status: str = "unknown"
    variant_verified: bool = False
    scrape_status: str = "failed"
    extraction_method: str | None = None
    error: str | None = None


def status(page):
    try:
        return int(page.status)
    except Exception:
        try:
            return int(page.status_code)
        except Exception:
            return None


def clean_url(url: str) -> str:
    p=urlsplit(url)
    return urlunsplit((p.scheme,p.netloc,p.path.rstrip("/"),"",""))


def fmt(v: Decimal | None) -> str | None:
    return f"{v:.2f}" if v is not None else None


def shopify_money(v) -> Decimal | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int,float)):
            return Decimal(str(v))/Decimal(100)
        s=str(v).strip()
        if re.fullmatch(r"\d+",s):
            return Decimal(s)/Decimal(100)
        return Decimal(re.sub(r"[^0-9.]","",s))
    except Exception:
        return None


def normalize_prices(vals: list[Decimal]) -> tuple[str|None,str|None]:
    clean=sorted(set(v for v in vals if isinstance(v,Decimal) and v>0))
    if not clean:
        return None,None
    if len(clean)==1:
        return fmt(clean[0]),None
    return fmt(clean[-1]),fmt(clean[0])


def fetch_shopify(target: Target) -> Result:
    js_url=clean_url(target.url)+".js"
    page=Fetcher.get(js_url, impersonate="chrome", stealthy_headers=True, timeout=45)
    http=status(page)
    try:
        data=page.json()
    except Exception as exc:
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=http,scrape_status="unsupported_or_non_shopify",
                      extraction_method="scrapling_shopify_probe",
                      error=f"Shopify product JSON unavailable: {type(exc).__name__}: {exc}")

    blob=json.dumps(data,ensure_ascii=False).lower()
    if not all(term.lower() in blob for term in target.expected_terms):
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=http,scrape_status="variant_mismatch",
                      extraction_method="scrapling_shopify_product_json_exact",
                      error="Approved product identity terms not all present in Shopify JSON.")

    variants=data.get("variants") or []
    chosen=None
    if target.variant_sku:
        wanted=target.variant_sku.strip().lower()
        for v in variants:
            if str(v.get("sku") or "").strip().lower()==wanted:
                chosen=v
                break
        if chosen is None:
            available=[str(v.get("sku") or "").strip() for v in variants]
            return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                          final_url=target.url,http_status=http,scrape_status="variant_unresolved",
                          extraction_method="scrapling_shopify_product_json_exact",
                          error=f"Hard SKU lock failed for {target.variant_sku}; available SKUs={available}")
    elif target.variant_terms:
        for v in variants:
            vb=json.dumps(v,ensure_ascii=False).lower()
            if all(term.lower() in vb for term in target.variant_terms):
                chosen=v
                break
        if chosen is None:
            return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                          final_url=target.url,http_status=http,scrape_status="variant_unresolved",
                          extraction_method="scrapling_shopify_product_json_exact",
                          error=f"Variant terms unresolved: {target.variant_terms}")
    elif len(variants)==1:
        chosen=variants[0]
    else:
        signatures={(v.get("price"),v.get("compare_at_price")) for v in variants}
        if variants and len(signatures)==1:
            chosen=variants[0]
        else:
            return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                          final_url=target.url,http_status=http,scrape_status="variant_unresolved",
                          extraction_method="scrapling_shopify_product_json_exact",
                          error="Multiple variants with different prices and no exact selector.")

    price=shopify_money(chosen.get("price"))
    compare=shopify_money(chosen.get("compare_at_price"))
    current,special=normalize_prices([x for x in (price,compare) if x is not None])
    if current is None:
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=http,variant_verified=True,
                      scrape_status="price_not_found",extraction_method="scrapling_shopify_product_json_exact",
                      error="Exact variant resolved but no valid price.")

    vid=chosen.get("id")
    final=clean_url(target.url)+(f"?variant={vid}" if vid else "")
    av=chosen.get("available")
    stock="in_stock" if av is True else ("out_of_stock" if av is False else "unknown")
    return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                  final_url=final,http_status=http,current_price=current,special_price=special,
                  stock_status=stock,variant_verified=True,scrape_status="success",
                  extraction_method="scrapling_shopify_product_json_exact")


TARGETS=[
    Target(57,470,"Australian Assistive Technology Centre","Aktiv Reacher 90cm - Etac",
           "https://www.australianatc.com.au/products/etac-aktiv-reacher-cc",
           ["Etac","Aktiv","Reacher"],["90"],"80505009"),
    Target(57,477,"Mobility Aids For You","Aktiv Reacher 90cm - Etac",
           "https://mobilityaidsforyou.com.au/products/etac-aktiv-reacher",
           ["Etac","Aktiv","Reacher"],["90"],"80505009"),
    Target(57,484,"Aged Care and Medical","Aktiv Reacher 90cm - Etac",
           "https://agedcareandmedical.com.au/products/etac-aktiv-reacher",
           ["Etac","Aktiv","Reacher"],["90"],"80505009"),
    Target(57,485,"Aesthetics Healthcare","Aktiv Reacher 90cm - Etac",
           "https://www.ahealthcare.com.au/products/etac-aktiv-reacher",
           ["Etac","Aktiv","Reacher"],["90"],"80505009"),

    Target(58,493,"Mable Direct","One Touch Jar Opener",
           "https://mabledirect.com.au/products/dysphagia-cup-green-copy",
           ["One Touch","Jar","Opener"],None,"KC12"),

    Target(59,492,"Mable Direct","One Touch Bottle Opener",
           "https://mabledirect.com.au/products/one-touch-automatic-bottle-opener",
           ["One Touch","Bottle","Opener"],None,"KC85"),

    Target(60,499,"Dementia Shop Australia","Thermo Plate - Ornamin",
           "https://dementiashop.com.au/products/ornamin-thermo-plate",
           ["Ornamin","Thermo","Plate"],["25.5"],"10863"),

    Target(62,498,"Dementia Shop Australia","Interactive Companion Pet",
           "https://dementiashop.com.au/products/companion-pups",
           ["Companion","Pup"],["Golden Retriever"],"B9108"),

    Target(63,468,"Australian Assistive Technology Centre","Oval Foam Donut Cushion - BetterLiving",
           "https://www.australianatc.com.au/products/betterliving-ring-cushion-behi",
           ["BetterLiving","Ring","Cushion"],["18"],"BL9504"),
    Target(63,475,"Mobility Aids For You","Oval Foam Donut Cushion - BetterLiving",
           "https://mobilityaidsforyou.com.au/products/betterliving-ring-cushion",
           ["BetterLiving","Ring","Cushion"],["18"],"BL9504"),
    Target(63,494,"Happy Healthcare","Oval Foam Donut Cushion - BetterLiving",
           "https://shop.happyhealthcare.com.au/products/betterliving-ring-cushion-18",
           ["BetterLiving","Ring","Cushion"],["18"],"BL9504"),
]


results=[]
for t in TARGETS:
    try:
        results.append(fetch_shopify(t))
    except Exception as exc:
        results.append(Result(
            t.pnum,t.mapping_id,t.competitor,t.product,t.url,
            scrape_status="failed",extraction_method="scrapling_fetcher",
            error=f"{type(exc).__name__}: {exc}"
        ))

print("P55_P63_RESULTS_START")
print(json.dumps([asdict(r) for r in results],indent=2))
print("P55_P63_RESULTS_END")
