from __future__ import annotations
import re,json,html
from scrapling.fetchers import Fetcher
RESULTS=[]
checks=[
 (66,"Elora Medical","shopify","https://eloramedicalsupplies.com.au/products/molicare-premium-fixpants-short-leg-25-pack"),
 (67,"Independence Australia","independence","https://store.independenceaustralia.com/hartmann-all-in-one-dignity-bariatric-briefs-160-239-cm-unisex-2445ml-white-15310145"),
 (67,"Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/all-in-one/bariatric/dignity-bariatric-brief-8d-xxl-32s/"),
 (68,"Assist Ability","shopify","https://shop.assistabilityaustralia.com.au/products/mc-skin-barrier-cream-east-200ml-p1-c12")
]
for row,retailer,kind,url in checks:
 r=dict(row=row,retailer=retailer,url=url)
 try:
  pg=Fetcher.get(url+(".js" if kind=="shopify" else ""),impersonate="chrome",stealthy_headers=True,timeout=30)
  r["http_status"]=int(pg.status)
  if r["http_status"]!=200:r["status"]="blocked";RESULTS.append(r);continue
  if kind=="shopify":
   j=pg.json();title=str(j.get("title") or "")
   variants=j.get("variants") or []
   if row==66:
    candidates=[v for v in variants if str(v.get("sku") or "")=="947715" and str(v.get("title") or "").strip().upper()=="2XL"]
    quantity_ok=bool(re.search(r"25\s*pack|pack\s*of\s*25",title+" "+str(j.get("description") or ""),re.I))
   else:
    candidates=[v for v in variants if re.search(r"Carton\s*-\s*12\s*Pieces per Carton",str(v.get("title") or ""),re.I) and "995086" in str(v.get("sku") or "")]
    quantity_ok=bool(re.search(r"Carton\s*-\s*12\s*Pieces per Carton",str(candidates[0].get("title") or ""),re.I)) if len(candidates)==1 else False
   if len(candidates)!=1 or not quantity_ok:r.update(status="unresolved",variants=[dict(title=v.get("title"),sku=v.get("sku")) for v in variants])
   else:
    v=candidates[0];price=int(v["price"])/100;compare=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
    r.update(status="success",price=compare if compare and compare>price else price,special_price=price if compare and compare>price else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=url+"?variant="+str(v["id"]))
  else:
   text=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
   if not re.search(r"(?<!\d)916680(?!\d)",text):r["status"]="sku_unverified"
   elif kind=="independence":
    m=re.search(r"PKT\s+8\s+Units\s+\$\s*([0-9,]+\.\d{2}).{0,200}?Carton\s+4\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
    if m:r.update(status="success",price=float(m.group(2).replace(",","")),special_price=None,proof=m.group(0))
    else:r.update(status="unresolved",proof=text[max(0,text.find("916680")-150):text.find("916680")+420])
   elif kind=="vital":
    m=re.search(r"\$\s*([0-9,]+\.\d{2})\s+inc GST\s+Supplier Part\s+916680\s+Unit CAR\s+32",text,re.I)
    if m:r.update(status="success",price=float(m.group(1).replace(",","")),special_price=None,basis="inc GST")
    else:r.update(status="unresolved",proof=text[max(0,text.find("916680")-160):text.find("916680")+300])
 except Exception as e:r.update(status="failed",error=type(e).__name__+": "+str(e))
 RESULTS.append(r)
print("BATCH14_RECOVERY_START")
print(json.dumps(RESULTS,indent=2))
print("BATCH14_RECOVERY_END")
