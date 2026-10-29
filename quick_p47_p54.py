from __future__ import annotations

import json
import re
from scrapling.fetchers import Fetcher

TARGETS = [
    ("P50-P53 Mobility Zone", "https://mobilityzone.com.au/product/orientation-signage-better-living/"),
    ("P50-P53 Scooters & Mobility", "https://www.scootersandmobility.com.au/products/betterliving-orientation-signage"),
    ("P54 Tamworth Scooters", "https://www.tamworthscootersandmobility.com.au/products/confident-care-cleansing-kit"),
]

out=[]
for label,url in TARGETS:
    try:
        page=Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=30)
        try:
            text=page.get_all_text(separator=" ", strip=True)
        except Exception:
            text=getattr(page,"text","") or ""
        text=re.sub(r"\s+"," ",str(text))
        title=None
        try:
            title=page.css("title::text").get()
        except Exception:
            pass
        prices=[]
        for x in re.findall(r"(?:AUD\s*)?\$\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?",text,re.I):
            if x not in prices:
                prices.append(x)
        out.append({
            "label":label,"url":url,
            "status":getattr(page,"status",getattr(page,"status_code",None)),
            "title":title,"text_length":len(text),
            "prices":prices[:30],
            "text_start":text[:2500],
        })
    except Exception as e:
        out.append({"label":label,"url":url,"error":f"{type(e).__name__}: {e}"})

print("QUICK_RESULTS_START")
print(json.dumps(out,indent=2,default=str))
print("QUICK_RESULTS_END")
