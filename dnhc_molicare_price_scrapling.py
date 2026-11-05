#!/usr/bin/env python3
"""DNHC MoliCare catalogue: live price capture via Scrapling only. Read-only."""
import json,re,concurrent.futures,time
from urllib.parse import urljoin
from scrapling.fetchers import Fetcher

BASE="https://www.dnhc.com.au"
PATHS=[
"/CONTINENCE/All_dash_In_dash_One/pl.php",
"/CONTINENCE/Pants-_and_-Pull_dash_Ups/pl.php",
"/CONTINENCE/Bed-Pads/pl.php",
"/CONTINENCE/Form/pl.php",
"/CONTINENCE/Fix-Pants/pl.php",
"/CONTINENCE/Guards-_and_-Shields/pl.php",
"/CONTINENCE/Liners-_and_-Boosters/pl.php",
"/CONTINENCE/Belted-Products/pl.php",
"/PERSONAL-_and_-SKIN-CARE/Skin-Care-_and_-Protection/Skin-Creams-_and_-Lotions/pl.php",
"/PERSONAL-_and_-SKIN-CARE/Skin-Care-_and_-Protection/Skin-_and_-Barrier-Protection/pl.php",
"/PERSONAL-_and_-SKIN-CARE/Soaps-_and_-Body-Wash/Body-Wash/pl.php",
"/MEDICAL/Wipes/Body-Wipes/pl.php",
"/pl.php?filters=ManufacturerName%3AMoliCare",
]
TARGETS=set("""915840 915831 166014 166015 915834 166029 166030 166031 915874
166041 166042 915880 168100 168077 168404 168405 168406 168401
168408 168409 168132 168044 168045 168046 168051 168600 168705
168801 168066 168407 915861 166000 166001 915854 161065
161070 161061 165271 165272 165273 165274 165374 165474
165574 165371 165372 165373 165471 165472 165473 165571
165572 165573 165671 165672 947790 947791 947792 947793
947794 947711 947712 947713 947714 947715 165531 165532
165533 169248 916680 995086 CTN13064 CTN13072 995016 915867
915868 915817 915818 CTN13069 995087 168076 947789
165531-1 915827 166093 915877 915870 168519 165435 169111""".split())

money=re.compile(r"\$\s*([0-9][0-9,]*\.\d{2})")
product_code=re.compile(r"(?i)^Product Code:\s*([A-Za-z0-9._-]+)\s*$")
def fetch(task):
    root,pg=task
    url=BASE+root
    if pg>1:url+=("&" if "?" in root else "?")+"pager="+str(pg)
    out={"url":url,"category":root,"page":pg,"items":[]}
    try:
        p=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=32)
        out["http"]=int(p.status)
        if int(p.status)!=200:return out
        txt=p.get_all_text(separator="\n",strip=True)
        lines=[re.sub(r"\s+"," ",l).strip() for l in txt.splitlines() if l.strip()]
        for idx,line in enumerate(lines):
            m=product_code.match(line)
            if not m:continue
            sku=m.group(1).upper()
            before=lines[max(0,idx-5):idx]
            name=before[-1] if before else ""
            after=" ".join(lines[idx+1:idx+6])
            prices=[float(q.replace(",","")) for q in money.findall(after)]
            if not prices:continue
            # An item is accepted only if its own code and price appear together.
            r={"sku":sku,"name":name,"price":prices[0],"price_candidates":prices[:2],"url":url}
            out["items"].append(r)
        out["text_head"]=txt[:120] if not out["items"] and pg==1 else ""
    except Exception as exc:
        out["error"]=type(exc).__name__+": "+str(exc)[:140]
    return out

# Pages are limited to 5 by default, more for large Pants/All-in-One categories.
tasks=[(r,i) for r in PATHS for i in range(1,7 if ("Pants-_and_" in r or "All_dash_In" in r or "ManufacturerName" in r) else 4)]
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
    batches=list(pool.map(fetch,tasks))
seen={}
for b in batches:
    for r in b["items"]:
        key=(r["sku"],r["name"])
        if key not in seen:seen[key]=r
rows=sorted(seen.values(),key=lambda r:(r["sku"],r["name"]))
print("DNHC_SCRAPLING_START")
print(json.dumps({
 "site":"https://www.dnhc.com.au",
 "price_basis":"AUD excluding GST",
 "scraper":"Scrapling Fetcher 0.5",
 "pages_checked":len(batches),
 "pages_ok":sum(b.get("http")==200 for b in batches),
 "status_counts":{str(x):sum(b.get("http")==x for b in batches) for x in [200,403,404,429,500]},
 "errors":[{"url":b["url"],"error":b.get("error"),"http":b.get("http"),"text_head":b.get("text_head","")} for b in batches if b.get("http")!=200 or (b.get("page")==1 and not b["items"])][:40],
 "exact_matches":[r for r in rows if r["sku"] in TARGETS],
 "other_molicare":[r for r in rows if r["sku"] not in TARGETS and ("molicare" in r["name"].lower() or "dignity" in r["name"].lower())]
},ensure_ascii=False,indent=2))
print("DNHC_SCRAPLING_END")
