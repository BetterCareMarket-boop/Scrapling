from __future__ import annotations
import json,re,concurrent.futures,collections
from scrapling.fetchers import Fetcher
URL="https://brightsky.com.au/att-brand/molicare/?showall=1"
def fetch(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=35)
def txt(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except Exception:return ""
def anyhref(x):
 try:return x.attrib.get("href","")
 except:return ""
pg=fetch(URL)
out={"archive_status":int(pg.status),"archive_entries":[],"products":[],"errors":[]}
if int(pg.status)==200:
 t=txt(pg)
 out["archive_excerpt"]=t[:350]
 a=pg.css('a[href*="/product/"]')
 urls=[]
 for n in a:
  u=anyhref(n)
  if u.startswith("http") and re.search(r"^https://brightsky\.com\.au/product/[^?#]+/?$",u):
   urls.append(u.rstrip("/"))
 urls=list(dict.fromkeys(urls))
 out["discovered_urls"]=len(urls)
 if len(urls)<60:
  for x in range(1,7):
   p=fetch("https://brightsky.com.au/att-brand/molicare/?product-page="+str(x))
   for n in p.css('a[href*="/product/"]'):
    u=anyhref(n)
    if u.startswith("http") and re.search(r"^https://brightsky\.com\.au/product/[^?#]+/?$",u) and u.rstrip("/") not in urls:
     urls.append(u.rstrip("/"))
 def one(u):
  try:
   page=fetch(u);st=int(page.status)
   if st!=200:return {"url":u,"http":st}
   t=txt(page)
   nodes=page.css("h1.product_title")
   title=nodes[0].get_all_text(strip=True) if nodes else ""
   if not title:
    m=re.search(r"MoliCare.{0,130}(?:Pack|Pk\d+)",t,re.I)
    title=m.group(0) if m else ""
   m=re.search(r"Manufacturer Number\s+([0-9a-zA-Z/\-]+)",t,re.I)
   sku=m.group(1).rstrip(".,") if m else None
   m=re.search(r"Product UOM\s+(.{10,100}?)(?=Backorder|Product Number|Gender|Brand|Capacity|$)",t,re.I)
   uom=m.group(1).strip() if m else None
   # More precise detail around product title, e.g. In stock $70.47 PACK, or $385.91 CTN
   pos=t.find(title)
   sub=t[pos:pos+420] if pos>=0 else t[:500]
   mm=re.search(r"\$\s*([0-9,]+\.\d{2})\s*(PACK|CTN|EACH|PKT)?",sub,re.I)
   if not mm:
    mm=re.search(r"\$\s*([0-9,]+\.\d{2})\s*(PACK|CTN|EACH|PKT)?",t[:700],re.I)
   price=float(mm.group(1).replace(",","")) if mm else None
   unit=mm.group(2) if mm else None
   return dict(url=u,title=title,sku=sku,unit=unit,price=price,uom=uom,http=st,excerpt=sub[:190])
  except Exception as e:return dict(url=u,error=type(e).__name__+":"+str(e)[:130])
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:out["products"]=list(pool.map(one,urls))
print("BRIGHTSKY_DISCOVERY_START")
print(json.dumps(out,separators=(",",":"),ensure_ascii=False))
print("BRIGHTSKY_DISCOVERY_END")
