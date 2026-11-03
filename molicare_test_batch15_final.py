import re,json,html
from scrapling.fetchers import Fetcher
S=[
("InCare Supports","https://incaresupports.com.au/products/molicare-premium-men-pants-5-drops-m"),
("Trugrade Medical","https://www.trugrademedical.com.au/products/molicare-mens-pants-5-drop"),
]
out=[]
for retailer,url in S:
 try:
  pg=Fetcher.get(url+".js",impersonate="chrome",stealthy_headers=True,timeout=30);http=int(pg.status)
  if http!=200:out.append(dict(retailer=retailer,status="blocked",http_status=http));continue
  j=pg.json();title=str(j.get("title") or "")
  variants=j.get("variants") or []
  for row,sku,sz,qty,pack in ((74,"915817","Medium",32,8),(75,"915818","Large",28,7)):
   r=dict(row=row,sku=sku,retailer=retailer,url=url)
   candidates=[]
   for v in variants:
    vs=str(v.get("sku") or "");lab=str(v.get("title") or "")
    if not re.search(r"(?<!\d)"+sku+r"(?!\d)",vs):continue
    if retailer=="InCare Supports":
     okay=bool(re.search(r"\b5\s*Drops\s*"+("M" if row==74 else "L")+r"\s*\(\s*4\s*packets?\s*of\s*"+str(pack)+r"\s*units?\s*per\s*carton\s*\)",lab,re.I))
    else:
     okay=bool(re.search(sz+r".*Carton\s*of\s*4\s*x\s*"+str(pack)+r"\s*pk",lab,re.I))
    if okay:candidates.append(v)
   if len(candidates)==1:
    v=candidates[0];cur=int(v["price"])/100;compare=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
    r.update(status="success",price=compare if compare and compare>cur else cur,special_price=cur if compare and compare>cur else None,variant=v.get("title"),matched_sku=v.get("sku"),variant_url=url+"?variant="+str(v["id"]))
   else:r.update(status="unresolved",matches=len(candidates))
   out.append(r)
 except Exception as e:out.append(dict(retailer=retailer,status="error",error=type(e).__name__+": "+str(e)))
print("BATCH15_FINAL_START")
print(json.dumps(out,indent=2))
print("BATCH15_FINAL_END")
