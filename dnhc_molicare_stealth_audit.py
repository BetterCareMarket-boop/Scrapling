#!/usr/bin/env python3
"""DNHC MoliCare product prices, directly captured by Scrapling StealthySession."""
import json,re,time
from urllib.parse import urljoin
from scrapling.fetchers import StealthySession
BASE="https://www.dnhc.com.au"
CATS=[
 ("elastic","/CONTINENCE/All_dash_In_dash_One/pl.php",[1,2,3]),
 ("mobile","/CONTINENCE/Pants-_and_-Pull_dash_Ups/pl.php",[1,2,3,4,5]),
 ("bed","/CONTINENCE/Bed-Pads/pl.php",[1]),
 ("form","/CONTINENCE/Form/pl.php",[1]),
 ("fixpants","/CONTINENCE/Fix-Pants/pl.php",[1,2]),
 ("guards","/CONTINENCE/Guards-_and_-Shields/pl.php",[1,2,3]),
 ("light","/CONTINENCE/Light-Shield/pl.php",[1,2]),
 ("liners","/CONTINENCE/Liners-_and_-Boosters/pl.php",[1,2]),
 ("skincream","/PERSONAL-_and_-SKIN-CARE/Skin-Care-_and_-Protection/Skin-Creams-_and_-Lotions/pl.php",[1,2]),
 ("skinbarrier","/PERSONAL-_and_-SKIN-CARE/Skin-Care-_and_-Protection/Skin-_and_-Barrier-Protection/pl.php",[1,2]),
 ("bodywash","/PERSONAL-_and_-SKIN-CARE/Soaps-_and_-Body-Wash/Body-Wash/pl.php",[1]),
 ("wipes","/MEDICAL/Wipes/Body-Wipes/pl.php",[1]),
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
pat=re.compile(r"(?i)^Product Code:\s*([a-z0-9._-]+)$")
money=re.compile(r"\$\s*([0-9][0-9,]*\.\d{2})")
entries=[];checks=[]
def handle(page,cat,url):
    lines=[re.sub(r"\s+"," ",x).strip() for x in page.get_all_text(separator="\n",strip=True).split("\n") if x.strip()]
    found=0
    for i,line in enumerate(lines):
        hit=pat.search(line)
        if hit:
            code=hit.group(1).upper()
            name=lines[i-1] if i>0 else ""
            # Skip arbitrary navigation and old price; use within same product block.
            tail=" ".join(lines[i+1:i+7])
            matches=money.findall(tail)
            if matches:
                price=float(matches[0].replace(",",""))
                entries.append({"sku":code,"name":name,"price":price,"url":url,"category":cat,"all_prices":[float(x.replace(",","")) for x in matches[:2]]})
                found+=1
    return found

start=time.time()
with StealthySession(headless=True,solve_cloudflare=True,timeout=90000) as browser:
    for cat,path,pages in CATS:
        for pg in pages:
            url=BASE+path+("?pager="+str(pg) if pg>1 else "")
            rec={"category":cat,"page":pg,"url":url}
            try:
                t=time.time()
                p=browser.fetch(url)
                rec["http"]=int(p.status)
                rec["seconds"]=round(time.time()-t,1)
                rec["count"]=handle(p,cat,url) if int(p.status)==200 else 0
                if rec["count"]==0:rec["head"]=p.get_all_text(separator=" ",strip=True)[:120]
            except Exception as ex:
                rec["error"]=type(ex).__name__+": "+str(ex)[:250]
            checks.append(rec)
            print("DNHC_STEP "+json.dumps({k:v for k,v in rec.items() if k not in ("url","head")}),flush=True)
            if time.time()-start>1020:
                print("DNHC_TIME_LIMIT_REACHED")
                break
        if time.time()-start>1020:break
seen={}
for e in entries:
    if e["sku"] not in seen or (e["category"]=="mobile" and seen[e["sku"]]["category"]!="mobile"):
        seen[e["sku"]]=e
results=sorted(seen.values(),key=lambda e:(e["sku"],e["name"]))
print("DNHC_STEALTH_START")
print(json.dumps({
 "site":BASE,"captured_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "price_basis":"AUD ex GST","engine":"Scrapling StealthySession 0.5",
 "elapsed_seconds":round(time.time()-start,1),"pages":checks,
 "exact_sku":[e for e in results if e["sku"] in TARGETS],
 "other_molicare":[e for e in results if ("molicare" in e["name"].lower() or "dignity" in e["name"].lower()) and e["sku"] not in TARGETS]
 },indent=2,ensure_ascii=False))
print("DNHC_STEALTH_END")
