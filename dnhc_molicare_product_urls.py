#!/usr/bin/env python3
"""Read-only DNHC direct product links, matched to visible product codes via Scrapling."""
import json,re,time
from urllib.parse import urljoin,urlparse
from scrapling.fetchers import StealthySession
BASE="https://www.dnhc.com.au"
URLS=[
"/CONTINENCE/Bed-Pads/pl.php",
"/CONTINENCE/All_dash_In_dash_One/pl.php",
"/CONTINENCE/Pants-_and_-Pull_dash_Ups/pl.php",
"/CONTINENCE/Guards-_and_-Shields/pl.php",
"/CONTINENCE/Form/pl.php",
"/CONTINENCE/Pants-_and_-Pull_dash_Ups/pl.php?pager=3",
"/CONTINENCE/Pants-_and_-Pull_dash_Ups/pl.php?pager=4",
"/CONTINENCE/Fix-Pants/pl.php",
"/CONTINENCE/Fix-Pants/pl.php?pager=2",
"/PERSONAL-_and_-SKIN-CARE/Skin-Care-_and_-Protection/Skin-Creams-_and_-Lotions/pl.php?pager=2",
"/MEDICAL/Wipes/Body-Wipes/pl.php",
"/PERSONAL-_and_-SKIN-CARE/Skin-Care-_and_-Protection/Skin-_and_-Barrier-Protection/pl.php",
]
TARGETS=set("""915840 915831 166014 166015 915834 166030 166031 915874 166041 166042 915880 168077 168404 168405 168406 168401 168408 168409 168035 168044 168045 168046 168051 168600 168705 168069 168066 168407 915861 166000 166001 915854 161065 161070 161061 165271 165272 165273 165274 165374 165474 165574 165371 165372 165373 165471 165472 165473 165571 165572 165573 165671 165672 947790 947791 947792 947793 947794 947711 947712 947713 947714 947715 CTN13070 CTN13064 CTN13072 CTN13054 915867 915868 915817 915818 CTN13069 CTN13068 168076 947789 915827 166093 915877 915870 165435 169111""".split())
codere=re.compile(r"(?i)^Product Code:\s*([a-z0-9._-]+)$")
def tidy(s):return re.sub(r"\W+","",s.lower())
allrows=[];reports=[];start=time.time()
with StealthySession(headless=True,solve_cloudflare=True,timeout=90000) as browser:
 for path in URLS:
    u=BASE+path;rep={"page":u}
    try:
        t=time.time();p=browser.fetch(u)
        rep["http"]=int(p.status);rep["seconds"]=round(time.time()-t,1)
        if int(p.status)!=200:reports.append(rep);continue
        # Anchor links on product cards. Product URL includes code and ends pd.php.
        links={}
        for a in p.css("a"):
            href=str(a.attrib.get("href",""))
            if "pd.php" not in href:continue
            target=urljoin(u,href)
            mm=re.search(r"/([^/]+)/[^/]+/pd\.php",urlparse(target).path,re.I)
            if not mm:continue
            code=mm.group(1).upper()
            atxt=a.get_all_text(separator=" ",strip=True)
            if code in TARGETS:
                links.setdefault(code,[]).append({"url":target,"anchor":atxt[:130]})
        lines=[re.sub(r"\s+"," ",z).strip() for z in p.get_all_text(separator="\n",strip=True).split("\n") if z.strip()]
        codes={}
        for i,line in enumerate(lines):
            m=codere.match(line)
            if not m:continue
            code=m.group(1).upper()
            if code in TARGETS:
                codes[code]=lines[i-1] if i else ""
        for code,name in codes.items():
            exact=[z for z in links.get(code,[]) if tidy(name) in tidy(z["anchor"]) or tidy(z["anchor"]) in tidy(name)] if links.get(code) else []
            best=(exact or links.get(code) or [])
            allrows.append({"code":code,"name":name,"url":best[0]["url"] if best else None,"anchor":best[0]["anchor"] if best else None,"verified":bool(best and (exact or code in best[0]["url"])),"category":u,"link_count":len(links.get(code,[]))})
        rep.update({"codes":len(codes),"urls":len(links),"no_links":[c for c in codes if c not in links]})
    except Exception as e:
        rep["error"]=type(e).__name__+": "+str(e)[:320]
    reports.append(rep)
    print("DNHC_LINK_STEP "+json.dumps(rep),flush=True)
seen={}
for row in allrows:
    if row["code"] not in seen or (not seen[row["code"]]["url"] and row["url"]):
        seen[row["code"]]=row
print("DNHC_LINKS_START")
print(json.dumps({"pages":reports,"links":sorted(seen.values(),key=lambda x:x["code"]),"elapsed":round(time.time()-start,1)},ensure_ascii=False,indent=2))
print("DNHC_LINKS_END")
