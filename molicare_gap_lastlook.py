import json,re,concurrent.futures
from scrapling.fetchers import Fetcher
TASKS=[
 ("165531","OzChemist","https://ozchemist.com/products/molicare-slip-maxi-small","carton","56"),
 ("165532","OzChemist","https://ozchemist.com/products/molicare-slip-maxi-medium","carton","56"),
 ("165533","OzChemist","https://ozchemist.com/products/molicare-slip-maxi-large","carton","56"),
 ("166029","Assist Ability","https://shop.assistabilityaustralia.com.au/products/molicare-premium-mobile-8d-s-p14-c4","carton","56"),
 ("166029","Health Ladder Australia","https://www.healthladderaustralia.com.au/product/hartmann-molicare-premium-mobile-8-drops-1791ml-small-60-90cm-166029-148","html","56"),
 ("166029","LuxeMED","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-mobile-8d-small","carton","56")
]
def one(p):
 sku,ret,url,mode,count=p;r=dict(sku=sku,retailer=ret,url=url)
 try:
  pg=Fetcher.get(url+(".js" if mode=="carton" else ""),impersonate="chrome",stealthy_headers=True,timeout=30)
  r["http_status"]=int(pg.status)
  if r["http_status"]!=200:r["status"]="blocked";return r
  if mode=="html":
   tx=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
   m=re.search(r"PKT14 UNIT\(S\)\s*\$\s*[0-9,]+\.\d{2}\s*Carton\s*4\s*PKT\(S\)\s*\$\s*([0-9,]+\.\d{2})",tx,re.I)
   r.update(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m and "166029" in tx and "8 Drops" in tx else r.update(status="unresolved",excerpt=tx[:360])
   return r
  d=pg.json();vs=d.get("variants") or []
  r["title"]=d.get("title")
  for v in vs:
   vt=str(v.get("title") or "");vs_sku=str(v.get("sku") or "")
   if sku=="166029":same=bool(re.search(r"(?<!\d)166029(?!\d)",vs_sku)) and bool(re.search("carton.{0,10}56|56.{0,10}carton",vt,re.I))
   else:same=bool(re.search(r"(?<!\d)"+sku+r"(?!\d)",vs_sku+" "+d.get("title",""))) and bool(re.search("4 packs per carton|4 x 14|carton.{0,10}56",vt,re.I))
   if same:
    cur=int(v.get("price") or 0)/100;old=int(v.get("compare_at_price") or 0)/100
    if cur>0:r.update(status="success",price=old if old>cur else cur,special_price=cur if old>cur else None,matched_sku=vs_sku,variant=vt,url=url+"?variant="+str(v.get("id")),available=v.get("available"))
    break
  if "status" not in r:r.update(status="unresolved",variants=[dict(sku=v.get("sku"),variant=v.get("title"),price=v.get("price"),available=v.get("available")) for v in vs[:10]])
 except Exception as e:r.update(status="error",error=type(e).__name__+": "+str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:out=list(ex.map(one,TASKS))
print("FINAL_GAP_START")
print(json.dumps(out,ensure_ascii=False,separators=(",",":")))
print("FINAL_GAP_END")
