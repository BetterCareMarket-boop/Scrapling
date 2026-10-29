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


def fmt(v: Decimal | None) -> str | None:
    return f"{v:.2f}" if v is not None else None


def money(s) -> Decimal | None:
    if s is None:
        return None
    x=re.sub(r"[^0-9.]", "", str(s).replace(",", ""))
    if not x:
        return None
    try:
        return Decimal(x)
    except Exception:
        return None


def normalize_prices(values: list[Decimal]) -> tuple[str | None,str | None]:
    vals=sorted(set(v for v in values if isinstance(v,Decimal) and v>0))
    if not vals:
        return None,None
    if len(vals)==1:
        return fmt(vals[0]),None
    return fmt(vals[-1]),fmt(vals[0])


def page_text(page) -> str:
    try:
        return re.sub(r"\s+"," ",page.get_all_text(separator=" ",strip=True))
    except Exception:
        return ""


def status(page) -> int | None:
    try:
        return int(page.status)
    except Exception:
        return None


def clean_product_url(url: str) -> str:
    parts=urlsplit(url)
    return urlunsplit((parts.scheme,parts.netloc,parts.path.rstrip("/"),"",""))


def shopify_json_url(url: str) -> str:
    return clean_product_url(url)+".js"


def as_decimal_price(value) -> Decimal | None:
    # Shopify product.js prices are integer cents.
    if value is None:
        return None
    try:
        if isinstance(value,int):
            return Decimal(value)/Decimal(100)
        if isinstance(value,float):
            return Decimal(str(value))/Decimal(100)
        s=str(value).strip()
        if re.fullmatch(r"\d+",s):
            return Decimal(s)/Decimal(100)
        return money(s)
    except Exception:
        return None


def shopify(target: Target) -> Result:
    page=Fetcher.get(shopify_json_url(target.url), impersonate="chrome", stealthy_headers=True, timeout=40)
    data=page.json()
    title=str(data.get("title") or "")
    identity=(title+" "+str(data.get("vendor") or "")).lower()
    if not all(t.lower() in identity or t.lower() in json.dumps(data).lower() for t in target.expected_terms):
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),scrape_status="variant_mismatch",
                      error="Expected product identity terms not found in Shopify product JSON.")

    variants=data.get("variants") or []
    chosen=None
    if target.variant_sku:
        for v in variants:
            if str(v.get("sku") or "").strip().lower()==target.variant_sku.strip().lower():
                chosen=v
                break
    if chosen is None and target.variant_terms:
        for v in variants:
            blob=" ".join([
                str(v.get("title") or ""),
                str(v.get("option1") or ""),
                str(v.get("option2") or ""),
                str(v.get("option3") or ""),
                str(v.get("sku") or ""),
            ]).lower()
            if all(term.lower() in blob for term in target.variant_terms):
                chosen=v
                break

    if target.variant_sku or target.variant_terms:
        if chosen is None:
            return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                          final_url=target.url,http_status=status(page),scrape_status="variant_unresolved",
                          error=f"Exact Shopify variant not resolved: sku={target.variant_sku!r} terms={target.variant_terms!r}")
    else:
        if len(variants)==1:
            chosen=variants[0]
        elif variants:
            # Safe only when every variant has identical price/compare-at price.
            sig={(v.get("price"),v.get("compare_at_price")) for v in variants}
            if len(sig)==1:
                chosen=variants[0]
            else:
                return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                              final_url=target.url,http_status=status(page),scrape_status="variant_unresolved",
                              error="Multiple Shopify variants with different prices; no exact variant requested.")

    if chosen is None:
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),scrape_status="price_not_found",
                      error="No Shopify variants returned.")

    sale=as_decimal_price(chosen.get("price"))
    compare=as_decimal_price(chosen.get("compare_at_price"))
    vals=[v for v in (sale,compare) if v is not None and v>0]
    current,special=normalize_prices(vals)
    if not current:
        st="price_not_found"
        err="No safe variant price extracted."
    else:
        st="success"; err=None

    vid=chosen.get("id")
    final=clean_product_url(target.url)+(f"?variant={vid}" if vid else "")
    available=chosen.get("available")
    stock="in_stock" if available is True else ("out_of_stock" if available is False else "unknown")
    return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                  final_url=final,http_status=status(page),current_price=current,special_price=special,
                  stock_status=stock,variant_verified=True,scrape_status=st,
                  extraction_method="scrapling_shopify_product_json_exact",error=err)


def exact_product_price(target: Target, selector: str, method: str, allow_family_option: str | None=None) -> Result:
    page=Fetcher.get(target.url,impersonate="chrome",stealthy_headers=True,timeout=40)
    text=page_text(page)
    if not all(term.lower() in text.lower() for term in target.expected_terms):
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),scrape_status="variant_mismatch",
                      error="Expected product identity terms not found.")

    if allow_family_option and allow_family_option.lower() not in text.lower():
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),scrape_status="variant_mismatch",
                      error=f"Requested family option {allow_family_option!r} not described on page.")

    blocks=page.css(selector).getall()
    if not blocks:
        blocks=page.css("h1").getall()+page.css(".summary").getall()
    blob=" ".join(blocks)
    vals=[]
    for raw in re.findall(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",blob):
        v=money(raw)
        if v is not None and v>0:
            vals.append(v)
    current,special=normalize_prices(vals)
    if current is None:
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),variant_verified=True,
                      scrape_status="price_not_found",extraction_method=method,
                      error="No safe product-block price extracted.")
    stock="in_stock" if re.search(r"\bin stock\b|backorder|pre.?order",text,re.I) else (
        "out_of_stock" if re.search(r"out of stock|sold out",text,re.I) else "unknown"
    )
    return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                  final_url=target.url,http_status=status(page),current_price=current,special_price=special,
                  stock_status=stock,variant_verified=True,scrape_status="success",
                  extraction_method=method)


def enquiry_only(target: Target, method: str) -> Result:
    page=Fetcher.get(target.url,impersonate="chrome",stealthy_headers=True,timeout=40)
    text=page_text(page)
    if not all(term.lower() in text.lower() for term in target.expected_terms):
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),scrape_status="variant_mismatch",
                      error="Expected product identity terms not found.")
    # Restrict price search to likely main product area; these pages currently expose none.
    main=" ".join(page.css("main").getall()[:1] or page.css("body").getall()[:1])
    price_hits=re.findall(r"\$\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?",main)
    if "Send Enquiry" in text and not price_hits:
        return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                      final_url=target.url,http_status=status(page),variant_verified=True,
                      scrape_status="price_not_found",extraction_method=method,
                      error="Enquiry-only page; no public product price.")
    # Do not accept unrelated related-product prices.
    return Result(target.pnum,target.mapping_id,target.competitor,target.product,target.url,
                  final_url=target.url,http_status=status(page),variant_verified=True,
                  scrape_status="price_not_found",extraction_method=method,
                  error="No safe public product price found.")


TARGETS=[
    Target(47,454,"Mobility Aids For You","Non - Slip Cup with Flower - Ornamin-Orange/Red",
      "https://mobilityaidsforyou.com.au/products/ornamin-non-slip-cup-flower-design",
      ["Ornamin","Non Slip Cup","Flower"],["Orange/Red"],"8707"),
    Target(47,461,"Aesthetics Healthcare","Non - Slip Cup with Flower - Ornamin-Orange/Red",
      "https://www.ahealthcare.com.au/products/ornamin-non-slip-cup-flower-design",
      ["Ornamin","Non Slip Cup","Flower"],["Orange/Red"],"8707"),

    Target(48,453,"Mobility Aids For You","Non - Slip Cup with Flower - Ornamin-Blue/Yellow",
      "https://mobilityaidsforyou.com.au/products/ornamin-non-slip-cup-flower-design",
      ["Ornamin","Non Slip Cup","Flower"],["Blue/Yellow"],"8711"),
    Target(48,460,"Aesthetics Healthcare","Non - Slip Cup with Flower - Ornamin-Blue/Yellow",
      "https://www.ahealthcare.com.au/products/ornamin-non-slip-cup-flower-design",
      ["Ornamin","Non Slip Cup","Flower"],["Blue/Yellow"],"8711"),

    Target(49,452,"Mobility Aids For You","Non - Slip Cup with Flower - Ornamin-Blue/White",
      "https://mobilityaidsforyou.com.au/products/ornamin-non-slip-cup-flower-design",
      ["Ornamin","Non Slip Cup","Flower"],["Blue/White"],"9484"),
    Target(49,459,"Aesthetics Healthcare","Non - Slip Cup with Flower - Ornamin-Blue/White",
      "https://www.ahealthcare.com.au/products/ornamin-non-slip-cup-flower-design",
      ["Ornamin","Non Slip Cup","Flower"],["Blue/White"],"9484"),

    Target(50,448,"Australian Assistive Technology Centre","Orientation Sign for Dementia - Bedroom",
      "https://www.australianatc.com.au/products/betterliving-orientation-signage-cc",
      ["BetterLiving","Orientation Signage"],["Bedroom"],"BL0036BE"),
    Target(50,451,"Mobility Aids For You","Orientation Sign for Dementia - Bedroom",
      "https://mobilityaidsforyou.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage"],["Bedroom"],"BL0036BE"),
    Target(50,458,"Scooters & Mobility","Orientation Sign for Dementia - Bedroom",
      "https://www.scootersandmobility.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage","Bedroom"],["Bedroom"],"BL0036BE"),
    Target(50,465,"Mobility Zone","Orientation Sign for Dementia - Bedroom",
      "https://mobilityzone.com.au/product/orientation-signage-better-living/",
      ["Orientation Signage","Better Living"],["Bedroom"],None),

    Target(51,445,"Patient Handling","Orientation Sign for Dementia - Kitchen",
      "https://www.patienthandling.com.au/product/betterliving-orientation-signage-kitchen-sticker/",
      ["BetterLiving","Orientation Signage","Kitchen"]),
    Target(51,447,"Australian Assistive Technology Centre","Orientation Sign for Dementia - Kitchen",
      "https://www.australianatc.com.au/products/betterliving-orientation-signage-cc",
      ["BetterLiving","Orientation Signage"],["Kitchen"],"BL0036K"),
    Target(51,450,"Mobility Aids For You","Orientation Sign for Dementia - Kitchen",
      "https://mobilityaidsforyou.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage"],["Kitchen"],"BL0036K"),
    Target(51,457,"Scooters & Mobility","Orientation Sign for Dementia - Kitchen",
      "https://www.scootersandmobility.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage","Kitchen"],["Kitchen"],"BL0036K"),
    Target(51,464,"Mobility Zone","Orientation Sign for Dementia - Kitchen",
      "https://mobilityzone.com.au/product/orientation-signage-better-living/",
      ["Orientation Signage","Better Living"],["Kitchen"],None),

    Target(52,446,"Australian Assistive Technology Centre","Orientation Signage for Dementia - Bathroom",
      "https://www.australianatc.com.au/products/betterliving-orientation-signage-cc",
      ["BetterLiving","Orientation Signage"],["Bathroom"],"BL0036SHBA"),
    Target(52,449,"Mobility Aids For You","Orientation Signage for Dementia - Bathroom",
      "https://mobilityaidsforyou.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage"],["Bathroom"],"BL0036SHBA"),
    Target(52,456,"Scooters & Mobility","Orientation Signage for Dementia - Bathroom",
      "https://www.scootersandmobility.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage","Bathroom"],["Bathroom"],"BL0036SHBA"),
    Target(52,463,"Mobility Zone","Orientation Signage for Dementia - Bathroom",
      "https://mobilityzone.com.au/product/orientation-signage-better-living/",
      ["Orientation Signage","Better Living"],["Bathroom"],None),

    Target(53,472,"Australian Assistive Technology Centre","Orientation Signage for Dementia - Toilet",
      "https://www.australianatc.com.au/products/betterliving-orientation-signage-cc",
      ["BetterLiving","Orientation Signage"],["Toilet"],"BL0036T"),
    Target(53,479,"Mobility Aids For You","Orientation Signage for Dementia - Toilet",
      "https://mobilityaidsforyou.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage"],["Toilet"],"BL0036T"),
    Target(53,481,"Scooters & Mobility","Orientation Signage for Dementia - Toilet",
      "https://www.scootersandmobility.com.au/products/betterliving-orientation-signage",
      ["BetterLiving","Orientation Signage","Toilet"],["Toilet"],"BL0036T"),
    Target(53,487,"Mobility Zone","Orientation Signage for Dementia - Toilet",
      "https://mobilityzone.com.au/product/orientation-signage-better-living/",
      ["Orientation Signage","Better Living"],["Toilet"],None),

    Target(54,467,"Patient Handling","Cleansing Kit - Confident Care",
      "https://www.patienthandling.com.au/product/confident-care-cleansing-kit/",
      ["Confident Care","Cleansing Kit"]),
    Target(54,471,"Australian Assistive Technology Centre","Cleansing Kit - Confident Care",
      "https://www.australianatc.com.au/products/confident-care-cleansing-kit",
      ["Confident Care","Cleansing Kit"]),
    Target(54,478,"Mobility Aids For You","Cleansing Kit - Confident Care",
      "https://mobilityaidsforyou.com.au/products/confident-care-cleansing-kit",
      ["Confident Care","Cleansing Kit"]),
    Target(54,480,"Scooters & Mobility","Cleansing Kit - Confident Care",
      "https://www.tamworthscootersandmobility.com.au/products/confident-care-cleansing-kit",
      ["Confident Care","Cleansing Kit"]),
    Target(54,486,"Aesthetics Healthcare","Cleansing Kit - Confident Care",
      "https://www.ahealthcare.com.au/products/confident-care-cleansing-kit",
      ["Confident Care","Cleansing Kit"]),
]


SHOPIFY_DOMAINS={
    "mobilityaidsforyou.com.au","www.mobilityaidsforyou.com.au",
    "ahealthcare.com.au","www.ahealthcare.com.au",
    "australianatc.com.au","www.australianatc.com.au",
}

results=[]
for t in TARGETS:
    try:
        host=urlsplit(t.url).netloc.lower()
        if host in SHOPIFY_DOMAINS:
            r=shopify(t)
        elif host=="www.patienthandling.com.au":
            r=exact_product_price(t,".summary .price, .elementor-widget-woocommerce-product-price .price","scrapling_patient_handling")
        elif host=="mobilityzone.com.au":
            opt=(t.variant_terms or [None])[0]
            r=exact_product_price(t,".elementor-widget-woocommerce-product-price .price","scrapling_mobility_zone_family_price",allow_family_option=opt)
        elif host in {"www.scootersandmobility.com.au","www.tamworthscootersandmobility.com.au"}:
            r=enquiry_only(t,"scrapling_enquiry_only")
        else:
            r=Result(t.pnum,t.mapping_id,t.competitor,t.product,t.url,scrape_status="unsupported_website")
    except Exception as e:
        r=Result(t.pnum,t.mapping_id,t.competitor,t.product,t.url,
                 scrape_status="failed",error=f"{type(e).__name__}: {e}")
    results.append(r)

print("BATCH_RESULTS_START")
print(json.dumps([asdict(r) for r in results],indent=2))
print("BATCH_RESULTS_END")
