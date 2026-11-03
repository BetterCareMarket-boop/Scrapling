import json,re
from scrapling.fetchers import Fetcher
checks=[
 (2,"915831","mySupply Store","https://mysupplystore.com.au/continence-products/disposable-pants-pads-liners/molicare-premium-mobile/","Small",56),
 (3,"915832","mySupply Store","https://mysupplystore.com.au/continence-products/disposable-pants-pads-liners/molicare-premium-mobile/","Medium",42),
 (4,"915833","mySupply Store","https://mysupplystore.com.au/continence-products/disposable-pants-pads-liners/molicare-premium-mobile/","Large",56),
 (2,"915831","Surgical Direct","https://surgicaldirect.com.au/products/molicare-premium-mobile-6-drops/","Small",56),
 (3,"915832","Surgical Direct","https://surgicaldirect.com.au/products/molicare-premium-mobile-6-drops/","Medium",42),
 (4,"915833","Surgical Direct","https://surgicaldirect.com.au/products/molicare-premium-mobile-6-drops/","Large",56),
 (13,"168100","Medshop","https://www.medshop.com.au/products/molicare-pad","2 Drops",336),
 (14,"168077","Platinum Health Supply","https://www.platinumhealthsupply.com.au/products/molicare-pad-4-drops-865ml","4 Drops",270),
 (22,"168132","Medisa","https://medisa.com.au/products/incontinence-aids-pads-pants-liners-pad-pant-system-hartmann-molicare-premium-lady-pad-all-sizes","1 Drop",192),
 (30,"168066","InCare Supports","https://incaresupports.com.au/products/molicare-premium-men-pad","3 Drops",168)]
out=[]
cache={}
for row,sku,retailer,url,size,qty in checks:
 r=dict(row=row,sku=sku,retailer=retailer,url=url)
 try:
  if retailer in ("Platinum Health Supply","Medisa","InCare Supports"):
   uri=url+".js"
  else:uri=url
  if uri not in cache:cache[uri]=Fetcher.get(uri,impersonate="chrome",stealthy_headers=True,timeout=30)
  pg=cache[uri];r["http_status"]=int(pg.status)
  if r["http_status"]!=200:r["status"]="blocked";out.append(r);continue
  if retailer in ("mySupply Store","Surgical Direct","Medshop"):
   t=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
   if retailer=="mySupply Store":
    p=rf"MOLICARE PREMIUM MOBILE 6D {size.upper()}\s*-\s*[^$]{{0,180}}CARTON {qty}\s*-\s*{sku}5?\s*\$\s*([0-9,]+(?:\.\d{{2}})?)"
    m=re.search(p,t,re.I)
    if m:r.update(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0))
    else:r.update(status="unresolved",sku_present=sku in t)
   elif retailer=="Surgical Direct":
    p=rf"{sku}-EA\s*Carton/{qty}[^$]{{0,160}}MoliCare Premium Mobile {size} 6 drops[^$]{{0,90}}\$\s*([0-9,]+(?:\.\d{{2}})?)"
    m=re.search(p,t,re.I)
    if m:r.update(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0))
    else:r.update(status="unresolved",sku_present=sku in t)
   elif retailer=="Medshop":
    p=rf"MPN\s*{sku}\s*\$\s*([0-9,]+(?:\.\d{{2}})?)\s*excl\.\s*GST\s*box of {qty}"
    m=re.search(p,t,re.I)
    if m:r.update(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0),gst_basis="ex GST")
    else:r.update(status="unresolved",sku_present=sku in t)
  else:
   d=pg.json();variants=d.get("variants") or []
   selected=[]
   for v in variants:
    vsku=str(v.get("sku") or "");title=str(v.get("title") or "")
    if retailer=="Platinum Health Supply":
     ok=vsku=="168077/C" and "9 Packs Per Carton" in title and "Pack" in str(d.get("description") or "")
    elif retailer=="Medisa":
     ok=sku in vsku and str(qty) in vsku and "1 Drop" in title and "16 x 12" in title
    else:
     ok=vsku=="168066" and "3 Drops" in title and "12 packets of 14" in title
    if ok:selected.append(v)
   if len(selected)==1:
    v=selected[0];price=int(v["price"])/100;old=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
    r.update(status="success",price=old if old and old>price else price,special_price=price if old and old>price else None,variant_url=url+"?variant="+str(v["id"]),matched_sku=v.get("sku"),matched_variant=v.get("title"))
   else:r.update(status="unresolved",matching_variants=len(selected))
 except Exception as exc:r.update(status="error",error=type(exc).__name__+": "+str(exc))
 out.append(r)
print("FIX_MISSING_START")
print(json.dumps(out,indent=2))
print("FIX_MISSING_END")
