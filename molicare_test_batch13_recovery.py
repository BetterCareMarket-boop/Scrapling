import re,json
from scrapling.fetchers import Fetcher
URL="https://eloramedicalsupplies.com.au/products/molicare-premium-fixpants-short-leg-25-pack"
OUT=[]
try:
 p=Fetcher.get(URL+".js",impersonate="chrome",stealthy_headers=True,timeout=30)
 j=p.json()
 t=str(j.get("title") or "");description=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(j.get("description") or "")))
 for row,sku,short,size in [(62,"947711","S","Small"),(63,"947712","M","Medium"),(64,"947713","L","Large")]:
  cand=[v for v in j.get("variants") or [] if str(v.get("sku") or "")==sku and str(v.get("title") or "").strip().upper()==short]
  sizekey=bool(re.search(r"25\s*pack|pack\s*of\s*25",t+" "+description,re.I))
  if len(cand)!=1 or not sizekey:OUT.append(dict(row=row,retailer="Elora Medical",status="unresolved",matched_variants=len(cand),pack_verified=sizekey));continue
  v=cand[0];cur=int(v["price"])/100;was=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
  OUT.append(dict(row=row,retailer="Elora Medical",status="success",sku=sku,size=size,pack=25,price=was if was and was>cur else cur,special_price=cur if was and was>cur else None,url=URL+"?variant="+str(v.get("id"))))
except Exception as e:OUT.append(dict(status="failed",error=type(e).__name__+": "+str(e)))
print("BATCH13_RECOVERY_START")
print(json.dumps(OUT,indent=2))
print("BATCH13_RECOVERY_END")
