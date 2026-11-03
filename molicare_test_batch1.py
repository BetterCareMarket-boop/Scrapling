from __future__ import annotations
import json, re, html
from urllib.parse import urlsplit
from scrapling.fetchers import Fetcher

PRODUCTS = [
    {"row":1,"sku":"915840","name":"MoliCare Pull Up Pants - 6 Drops - XS - Carton 56 units","size":"X-Small","carton":56},
    {"row":2,"sku":"915831","name":"MoliCare Pull Up Pants - 6 Drops - S - Carton 56 units","size":"Small","carton":56},
    {"row":3,"sku":"915832","name":"MoliCare Pull up Pants - 6 Drops - M - Carton 42","size":"Medium","carton":42,"sku_source":"recovered_from_hartmann"},
    {"row":4,"sku":"915833","name":"MoliCare Pull up Pants - 6 drops - L - Carton 56","size":"Large","carton":56,"sku_source":"recovered_from_hartmann"},
    {"row":5,"sku":"915834","name":"MoliCare Pull up pants - 6 Drops - XL - Carton 56","size":"X-Large","carton":56},
]

CANDIDATES = [
    {"retailer":"LuxeMED","kind":"shopify_family","url":"https://www.luxemed.com.au/products/molicare-premium-mobile-6d-small"},
    {"retailer":"Surgical Direct","kind":"surgical_direct","url":"https://surgicaldirect.com.au/products/molicare-premium-mobile-6-drops/"},
    {"retailer":"mySupply Store","kind":"mysupply_family","url":"https://mysupplystore.com.au/continence-products/disposable-pants-pads-liners/molicare-premium-mobile/"},
    {"retailer":"Conticare","kind":"conticare_xs","rows":[1],"url":"https://www.conticare.com.au/molicare-premium-mobile-g.html"},
    {"retailer":"Conticare","kind":"conticare_xl","rows":[5],"url":"https://www.conticare.com.au/molicare-premium-mobile-6-drops-unisex-pants-x-large-130-170cm-2140-915834.html"},
    {"retailer":"Day & Night Healthcare","kind":"generic_exact","rows":[2],"url":"https://www.dnhc.com.au/915831/MoliCare-Premium-Mobile-Small-6-drops-56/pd.php"},
    {"retailer":"Australian Home Nursing Supplies","kind":"generic_exact","rows":[3],"url":"https://www.ahns.com.au/product/molicare-mobile-medium-4x14-56-carton/"},
    {"retailer":"Australian Home Nursing Supplies","kind":"generic_exact","rows":[4],"url":"https://www.ahns.com.au/product/molicare-mobile-large-4x14-56-carton/"},
    {"retailer":"Australian Home Nursing Supplies","kind":"generic_exact","rows":[5],"url":"https://www.ahns.com.au/product/molicare-mobile-extra-large-4x14-56-carton/"},
]

def status(page):
    try: return int(page.status)
    except Exception: return None

def text_of(page):
    try:
        return re.sub(r"\s+"," ",page.get_all_text(separator=" ",strip=True))
    except Exception:
        return ""

def money_values(s):
    vals=[]
    for m in re.findall(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", s):
        try: vals.append(float(m.replace(",","")))
        except Exception: pass
    return vals

def normalize(prices):
    vals=sorted(set(round(float(x),2) for x in prices if x and float(x)>0))
    if not vals: return None,None
    if len(vals)==1: return vals[0],None
    return vals[-1],vals[0]

def fetch(url):
    return Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=45)

def shopify_family(prod, cand):
    page=fetch(cand["url"].rstrip("/")+".js")
    data=page.json()
    variants=data.get("variants") or []
    wanted=[]
    for v in variants:
        title=(str(v.get("title") or "")+" "+str(v.get("sku") or "")).lower()
        size_ok=prod["size"].lower() in title
        carton_ok=(f"carton ({prod['carton']})".lower() in title or f"carton {prod['carton']}".lower() in title)
        sku=str(v.get("sku") or "")
        sku_ok=prod["sku"] in sku or (prod["row"] in (3,4) and size_ok)
        if size_ok and carton_ok and sku_ok:
            wanted.append(v)
    if len(wanted)!=1:
        return {"status":"variant_unresolved","http_status":status(page),"error":f"matched {len(wanted)} Shopify variants"}
    v=wanted[0]
    p=(float(v["price"])/100) if v.get("price") is not None else None
    c=(float(v["compare_at_price"])/100) if v.get("compare_at_price") is not None else None
    regular,special=normalize([x for x in (p,c) if x])
    return {"status":"success" if regular else "price_not_found","http_status":status(page),
            "price":regular,"special_price":special,"matched_sku":v.get("sku"),
            "matched_variant":v.get("title"),"variant_id":v.get("id")}

def surgical_direct(prod,cand):
    page=fetch(cand["url"])
    txt=text_of(page)
    # Require exact manufacturer code and carton quantity in the same local window.
    hits=[m.start() for m in re.finditer(re.escape(prod["sku"]),txt,re.I)]
    for pos in hits:
        snip=txt[max(0,pos-120):pos+420]
        if str(prod["carton"]) not in snip: continue
        if "MoliCare Premium Mobile" not in snip: continue
        vals=money_values(snip)
        if vals:
            regular,special=normalize(vals[:3])
            return {"status":"success","http_status":status(page),"price":regular,"special_price":special,
                    "matched_excerpt":snip[:360]}
    return {"status":"price_not_found","http_status":status(page),"error":"exact SKU/carton row not safely resolved"}

def mysupply_family(prod,cand):
    page=fetch(cand["url"])
    txt=text_of(page)
    size_map={"X-Small":"X-SMALL","Small":"SMALL","Medium":"MEDIUM","Large":"LARGE","X-Large":"XL"}
    needle=f"MOLICARE PREMIUM MOBILE 6D {size_map[prod['size']]}"
    pos=txt.upper().find(needle)
    if pos<0:
        return {"status":"variant_unresolved","http_status":status(page),"error":"exact size title not found"}
    snip=txt[pos:pos+420]
    if f"CARTON {prod['carton']}" not in snip.upper():
        return {"status":"variant_mismatch","http_status":status(page),"error":"carton quantity mismatch","matched_excerpt":snip}
    # Site often appends a pack-level suffix to the manufacturer's code, so require the base SKU prefix.
    if prod["sku"] not in snip:
        return {"status":"variant_mismatch","http_status":status(page),"error":"manufacturer code not present near title","matched_excerpt":snip}
    vals=money_values(snip)
    if not vals:
        return {"status":"price_not_found","http_status":status(page),"matched_excerpt":snip}
    regular,special=normalize(vals[:2])
    return {"status":"success","http_status":status(page),"price":regular,"special_price":special,"matched_excerpt":snip[:360]}

def generic_exact(prod,cand):
    page=fetch(cand["url"])
    txt=text_of(page)
    low=txt.lower()
    identity_ok=("molicare" in low and "6 drop" in low and prod["sku"] in txt)
    qty_ok=(str(prod["carton"]) in txt and ("carton" in low or "ctn" in low or "unit" in low or "box" in low))
    if not identity_ok:
        return {"status":"variant_mismatch","http_status":status(page),"error":"MoliCare/6-drop/SKU identity not all present"}
    if not qty_ok:
        return {"status":"variant_mismatch","http_status":status(page),"error":"carton quantity not safely present"}
    vals=money_values(txt)
    # For exact single-product pages, take prices from title/product-area neighbourhood when possible.
    pos=txt.find(prod["sku"])
    snip=txt[max(0,pos-500):pos+900] if pos>=0 else txt[:1200]
    local=money_values(snip)
    vals=local or vals
    if not vals:
        return {"status":"price_not_found","http_status":status(page)}
    regular,special=normalize(vals[:4])
    return {"status":"success","http_status":status(page),"price":regular,"special_price":special,"matched_excerpt":snip[:360]}

def conticare(prod,cand):
    page=fetch(cand["url"])
    txt=text_of(page)
    # grouped/detail pages explicitly state SKU, carton/box quantity and price
    pos=txt.find(prod["sku"])
    if pos<0:
        return {"status":"variant_mismatch","http_status":status(page),"error":"SKU not found"}
    snip=txt[max(0,pos-700):pos+1100]
    if str(prod["carton"]) not in snip:
        return {"status":"variant_mismatch","http_status":status(page),"error":"carton quantity not in local product block","matched_excerpt":snip[:360]}
    vals=money_values(snip)
    # Prefer values >= $100 for carton listings when both packet and carton are present.
    carton_vals=[v for v in vals if v>=100]
    vals=carton_vals or vals
    if not vals:
        return {"status":"price_not_found","http_status":status(page),"matched_excerpt":snip[:360]}
    regular,special=normalize(vals[:4])
    return {"status":"success","http_status":status(page),"price":regular,"special_price":special,"matched_excerpt":snip[:360]}

def run_one(prod,cand):
    if cand.get("rows") and prod["row"] not in cand["rows"]: return None
    try:
        if cand["kind"]=="shopify_family": data=shopify_family(prod,cand)
        elif cand["kind"]=="surgical_direct": data=surgical_direct(prod,cand)
        elif cand["kind"]=="mysupply_family": data=mysupply_family(prod,cand)
        elif cand["kind"].startswith("conticare"): data=conticare(prod,cand)
        else: data=generic_exact(prod,cand)
    except Exception as e:
        data={"status":"failed","error":f"{type(e).__name__}: {e}"}
    return {"row":prod["row"],"sku":prod["sku"],"product":prod["name"],"retailer":cand["retailer"],"url":cand["url"],**data}

results=[]
for p in PRODUCTS:
    for c in CANDIDATES:
        r=run_one(p,c)
        if r is not None:
            results.append(r)

print("SCRAPLING_MOLICARE_TEST_START")
print(json.dumps(results,indent=2,ensure_ascii=False))
print("SCRAPLING_MOLICARE_TEST_END")
