import json,re
from scrapling.fetchers import Fetcher
urls=[
 ("InCare Supports","https://incaresupports.com.au/products/molicare-premium-mobile-8-drops"),
 ("LuxeMED","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-mobile-8d-small"),
 ("Platinum Health Supply","https://www.platinumhealthsupply.com.au/products/molicare-premium-mobile-8-drop"),
]
out=[]
for ret,url in urls:
 r=dict(row=8,sku="166029",retailer=ret,url=url)
 try:
  pg=Fetcher.get(url+".js",impersonate="chrome",stealthy_headers=True,timeout=30)
  r["http_status"]=int(pg.status)
  if r["http_status"]!=200:r["status"]="blocked";out.append(r);continue
  j=pg.json()
  vs=j.get("variants") or [];match=[]
  for v in vs:
   title=" ".join(str(v.get(k) or "") for k in ("title","option1","option2"))
   sku=str(v.get("sku") or "")
   if not re.search(r"(?<!\d)166029(?!\d)",sku):continue
   if not re.search("small",title,re.I):continue
   if not re.search(r"carton\s*\(?56\)?|4\s*packets?\s*of\s*14\s*units?\s*per\s*carton",title,re.I):continue
   match.append(v)
  if len(match)==1:
   v=match[0];cur=int(v["price"])/100;was=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
   r.update(status="success",price=was if was and was>cur else cur,special_price=cur if was and was>cur else None,variant_url=url+"?variant="+str(v["id"]),matched_sku=v.get("sku"),variant=v.get("title"))
  else:r.update(status="variant_unresolved",variants=[dict(sku=v.get("sku"),title=v.get("title"),price=(v.get("price") or 0)/100) for v in vs[:20]])
 except Exception as e:r.update(status="error",error=str(e))
 out.append(r)
print("SMALL8_START")
print(json.dumps(out,indent=2))
print("SMALL8_END")
