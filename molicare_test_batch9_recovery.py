import json,re
from scrapling.fetchers import Fetcher
P=[
 (41,"165273",6,"Large",90,"https://incaresupports.com.au/products/molicare-premium-elastic-6-drops"),
 (42,"165274",6,"XL",56,"https://incaresupports.com.au/products/molicare-premium-elastic-6-drops"),
 (43,"165374",7,"XL",56,"https://incaresupports.com.au/products/molicare-premium-elastic-7-drops"),
 (44,"165474",8,"XL",56,"https://incaresupports.com.au/products/molicare-premium-elastic-8-drops"),
 (45,"165574",9,"XL",56,"https://incaresupports.com.au/products/molicare-premium-elastic-9-drops")
]
out=[]
for row,sku,drops,size,qty,url in P:
 r={"row":row,"retailer":"InCare Supports","sku":sku,"url":url}
 try:
  page=Fetcher.get(url+".js",impersonate="chrome",stealthy_headers=True,timeout=25)
  r["http_status"]=int(page.status)
  if r["http_status"]!=200:r["status"]="blocked";out.append(r);continue
  d=page.json();description=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",d.get("description") or ""))
  variants=d.get("variants") or []
  matches=[v for v in variants if str(v.get("sku") or "")==sku]
  # Prove carton count from size-specific description, never from a different size.
  if size=="XL":pat=r"XL\s*\(?[^)]{0,30}\)?\s*(?:\(?\s*)?56\s*\(\s*4\s*x\s*14\s*\)\s*(?:per carton)?"
  else:pat=r"Large\s*\(?[^)]{0,30}\)?\s*(?:\(?\s*)?90\s*\(\s*3\s*x\s*30\s*\)\s*(?:per carton)?"
  confirmed=bool(re.search(pat,description,re.I))
  # Store snippet near size to aid manual audit
  start=description.lower().find("xl " if size=="XL" else "large ")
  r["carton_evidence"]=description[max(0,start-35):start+170] if start>=0 else description[:450]
  r["carton_confirmed"]=confirmed
  if len(matches)!=1 or not confirmed:
   r["status"]="variant_or_carton_unresolved"
  else:
   v=matches[0];cur=int(v["price"])/100;was=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
   r.update(status="success",price=was if was and was>cur else cur,special_price=cur if was and was>cur else None,matched_variant=v.get("title"),variant_url=url+"?variant="+str(v["id"]))
 except Exception as e:r.update(status="failed",error=type(e).__name__+": "+str(e))
 out.append(r)
print("BATCH9_RECOVERY_START")
print(json.dumps(out,indent=2))
print("BATCH9_RECOVERY_END")
