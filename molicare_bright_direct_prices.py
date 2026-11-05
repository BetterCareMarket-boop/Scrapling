import json,re,concurrent.futures
from scrapling.fetchers import Fetcher
with open("molicare_bright_sku_urls.json") as fp: targets=json.load(fp)
def fetchone(r):
 try:
  pg=Fetcher.get(r["url"],impersonate="chrome",stealthy_headers=True,timeout=30)
  s=int(pg.status)
  if s!=200:return dict(r,http=s,status="blocked")
  tx=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
  m=re.search(r"\b(?:In stock|Out of stock|Available on backorder|Available)\s+\$\s*([0-9,]+\.\d{2})\s*(CTN|PACK|EACH|PKT)?",tx,re.I)
  # p.price element can be more reliable for unusual products.
  els=pg.css(".summary p.price, .summary .price, .woocommerce-Price-amount")
  els_txt=[e.get_all_text(separator=" ",strip=True)[:100] for e in els[:3]]
  if not m:
   for t in els_txt:
    m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*(CTN|PACK|EACH|PKT)?",t,re.I)
    if m:break
  price=float(m[1].replace(",","")) if m else None
  unit=m[2].upper() if m and m[2] else None
  # Confirm sku and case quantity from scraped page itself, not summary alone.
  mm=re.search(r"Manufacturer Number\s+([a-zA-Z0-9/\-]+)",tx,re.I)
  sku=mm[1] if mm else r.get("sku")
  q=re.search(r"Product UOM\s+(1 Pack\s*=\s*\d+\s*(?:Pieces|Pads|Units?),?\s*1 Carton\s*=\s*\d+\s*(?:Packs?|Packet(?:s)?))",tx,re.I)
  uom=q[1] if q else r.get("uom")
  return dict(sku=sku,title=r.get("title"),price=price,unit=unit,uom=uom,url=r["url"],status="success" if price else "price_unresolved",css=els_txt[:2])
 except Exception as e:return dict(r,status="error",error=type(e).__name__+":"+str(e)[:100])
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:out=list(ex.map(fetchone,targets))
print("BRIGHT_PRICES_START")
print(json.dumps(out,separators=(",",":"),ensure_ascii=False))
print("BRIGHT_PRICES_END")
