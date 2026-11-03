import json,re
from scrapling.fetchers import Fetcher
T=[
(13,"168100",336,"https://www.medshop.com.au/products/molicare-pad","medshop"),
(14,"168077",270,"https://ozmedical.com.au/products/molicare-pad-865ml-168077","shopify"),
(14,"168077",270,"https://www.luxemed.com.au/products/molicare-pad-4d","shopify"),
(14,"168077",270,"https://www.platinumhealthsupply.com.au/products/molicare-pad-4-drops-865ml","shopify"),
(14,"168077",270,"https://store.independenceaustralia.com/molicare-pad-4-d-unisex-865ml-15310013","independence")
]
R=[]
for row,sku,qty,url,mode in T:
 d={"row":row,"sku":sku,"url":url}
 try:
  p=Fetcher.get(url+(".js" if mode=="shopify" else ""),impersonate="chrome",stealthy_headers=True,timeout=32)
  d["http_status"]=int(p.status)
  if mode=="shopify":
   if d["http_status"]!=200:d["status"]="blocked"
   else:
    j=p.json()
    valid=[]
    for v in j.get("variants") or []:
     title=" ".join(str(v.get(k) or "") for k in ("title","option1","option2"))
     if sku not in str(v.get("sku") or ""):continue
     if not re.search(r"\b"+str(qty)+r"\b",title) and not (qty==270 and re.search(r"9\s*packs?\s*(?:per\s*carton|/carton)",title,re.I)):continue
     valid.append(v)
    if len(valid)==1:
     v=valid[0]; price=int(v["price"])/100;comp=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
     d.update(status="success",retailer_sku=v.get("sku"),variant=v.get("title"),price=comp if comp and comp>price else price,special_price=price if comp and comp>price else None,variant_url=url+"?variant="+str(v.get("id")))
    else:d.update(status="unresolved",variants=[{"sku":v.get("sku"),"title":v.get("title")} for v in j.get("variants") or []][:12])
  else:
   text=re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
   if d["http_status"]!=200:d["status"]="blocked"
   elif sku not in text or str(qty) not in text:d["status"]="identity_unverified"
   elif mode=="medshop":
    vals=re.findall(r"\$\s*([0-9]+(?:\.\d\d)?)",text)
    d.update(status="review",prices=vals[:12],sku_verified=True,carton_verified=True,excerpt=text[max(0,text.index(sku)-200):text.index(sku)+350])
   else:
    match=re.search(r"Carton\s+9\s+PKT\(s\)\s+\$\s*([0-9,]+(?:\.\d{2})?)",text,re.I)
    d.update(status="success" if match else "unresolved",price=float(match.group(1).replace(",","")) if match else None)
 except Exception as e:d.update(status="failed",error=type(e).__name__+": "+str(e))
 R.append(d)
print("B3_FOLLOWUP_START")
print(json.dumps(R,indent=2))
print("B3_FOLLOWUP_END")
