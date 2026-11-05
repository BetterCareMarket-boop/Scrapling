from __future__ import annotations
import json,re,concurrent.futures
from scrapling.fetchers import Fetcher
MYS=[
 (3,"915831","https://mysupplystore.com.au/molicare-premium-mobile-6d-small-carton-56-915831/",56),
 (4,"166014","https://mysupplystore.com.au/molicare-premium-mobile-6d-medium-carton-42-915832/",42),
 (5,"166015","https://mysupplystore.com.au/molicare-premium-mobile-6d-large-carton-56-915833/",56),
 (33,"166000","https://mysupplystore.com.au/molicare-premium-mobile-5d-medium-carton-42-915852/",42),
 (34,"166001","https://mysupplystore.com.au/molicare-premium-mobile-5d-large-carton-56-915853/",56),
 (35,"915854","https://mysupplystore.com.au/molicare-premium-mobile-5d-xl-carton-56-915854/",56),
 (51,"165473","https://mysupplystore.com.au/molicare-premium-elastic-8d-large-waist-hip-115-145cm-3220ml-carton-72-165473/",72),
]
CONT=[
 (2,"915840","https://www.conticare.com.au/molicare-premium-mobile-g.html"),
 (6,"915834","https://www.conticare.com.au/molicare-premium-mobile-6-drops-unisex-pants-x-large-130-170cm-2140-915834.html"),
 (36,"161065","https://www.conticare.com.au/molicare-premium-bed-mat-med-mats-60-90cm-5-drops-850ml-161066.html"),
 (39,"165271","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-small-6-drops-1890ml-70-90cm-165271.html"),
 (40,"165272","https://www.conticare.com.au/molicare-premium-elastic-6-drops-briefs-medium-85-120cm-2159ml-box-of-91.html"),
 (42,"165274","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-extra-large-6-drops-2786ml-140-175cm-165274.html"),
 (45,"165574","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-extra-large-9-drops-3951ml-140-175cm-165574.html"),
 (49,"165471","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-small-8-drops-2600ml-60-90cm-165471.html"),
 (51,"165473","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-large-8-drops-3095ml-115-150cm-165473.html"),
 (99,"915827","https://www.conticare.com.au/molicare-premium-mens-pants-medium-85-120cm-7-drops-1455ml-box-of-33.html"),
 (100,"166093","https://www.conticare.com.au/molicare-mens-premium-pants-male-pull-ups-large-7-drops-100-150cm-1412ml-915828-box-of-30.html"),
]
def run(item):
 typ,row,sku,url,qty=item
 o=dict(type=typ,row=row,sku=sku,url=url)
 try:
  pg=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=28)
  o["http"]=int(pg.status);o["final_url"]=str(getattr(pg,"url",url))
  if o["http"]==200:
   t=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
   if typ=="mys":
    m=re.search(r"(?<!\d)"+str(qty)+r"(?!\d)",t[:800])
    o["qty"]=bool(m)
    h=pg.css("h1")
    o["title"]=h[0].get_all_text(separator=" ",strip=True)[:200] if h else t[:170]
    p=re.search(r"\$\s*([0-9,]+(?:\.\d{2})?)",t[t.find(o["title"]):t.find(o["title"])+800])
    o["price"]=float(p[1].replace(",","")) if p else None
   else:
    o["found_sku"]=bool(re.search(r"(?<!\d)"+re.escape(sku)+r"(?!\d)",t))
    o["title"]=t[t.find("Product Description")-90:t.find("Product Description")+80][:170]
    q=re.search(r"(?<!\d)"+re.escape(sku)+r"\s*\(Box of\s*(\d+)\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
    o["box"]=q[1] if q else None;o["price"]=float(q[2].replace(",","")) if q else None
  else:o["excerpt"]=pg.body[:110].decode("utf-8","replace") if isinstance(pg.body,bytes) else str(pg.body)[:110]
 except Exception as e:o["error"]=type(e).__name__+":"+str(e)[:130]
 return o
tasks=[("mys",*p) for p in MYS]+[("cont",*p,None) for p in CONT]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: out=list(pool.map(run,tasks))
# Conticare alternative host test on previously confirmed direct product.
alt_urls=[
 "https://conticare.com.au/molicare-premium-mobile-g.html",
 "http://www.conticare.com.au/molicare-premium-mobile-g.html",
 "https://www.conticare.com.au/brands/molicare",
 "https://conticare.com.au/brands/molicare",
 "https://www.conticare.com.au/molicare-premium-mobile-g.html?utm_source=price_audit",
]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:alts=list(pool.map(run,[("alt",0,"915840",u,None) for u in alt_urls]))
print("AUDIT_MYS_CONT_START")
print(json.dumps({"results":out,"alternates":alts},ensure_ascii=False,separators=(",",":")))
print("AUDIT_MYS_CONT_END")
