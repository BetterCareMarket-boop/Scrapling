from __future__ import annotations
import re,json,html
from scrapling.fetchers import Fetcher
R=[]
items=[
 ("Solmed",55,"165671",66,"https://solmed.com.au/collections/new-arrivals/products/molicare-premium-elastic-10d-briefs","shopify"),
 ("Sumac Medical Supplies",54,"165573",72,"https://sumacms.com.au/product/molicare-premium-elastic-9-d-x-large-waist-140-175cm-unisex-3951ml-ctn/","html"),
]
for retailer,row,sku,qty,url,kind in items:
 d={"row":row,"retailer":retailer,"url":url,"sku":sku}
 try:
  p=Fetcher.get(url+(".js" if kind=="shopify" else ""),impersonate="chrome",stealthy_headers=True,timeout=30)
  d["http_status"]=int(p.status)
  if d["http_status"]!=200:d["status"]="blocked"
  elif kind=="shopify":
   j=p.json()
   desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
   title=str(j.get("title") or "")
   vars=j.get("variants") or []
   carton=[v for v in vars if str(v.get("sku") or "")==sku+"/C" and "small" in str(v.get("title") or "").lower() and "carton" in str(v.get("title") or "").lower()]
   packet=[v for v in vars if str(v.get("sku") or "")==sku and "small" in str(v.get("title") or "").lower() and "pack" in str(v.get("title") or "").lower()]
   # Quantity must be explicitly verified in source, not inferred from price ratios.
   qty_evidence=re.search(r"(?<!\d)66\s*(?:units?|pieces?)\s*(?:per\s*)?carton|carton\s*(?:of\s*)?66\s*(?:units?|pieces?)|3\s*[x×]\s*22|22\s*(?:units?|pieces?)\s*per\s*pack",desc,re.I)
   d.update(title=title,carton_sku=carton[0].get("sku") if len(carton)==1 else None,packet_sku=packet[0].get("sku") if len(packet)==1 else None,description_evidence=desc[:850],quantity_evidence=qty_evidence.group(0) if qty_evidence else None)
   if len(carton)==1 and len(packet)==1 and qty_evidence and "10d" in title.lower():
    v=carton[0];cur=int(v["price"])/100;was=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
    d.update(status="success",price=was if was and was>cur else cur,special_price=cur if was and was>cur else None,variant_url=url+"?variant="+str(v["id"]))
   else:d["status"]="quantity_unverified"
  else:
   t=re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
   # Treat URL as unreliable and rely on exact visible identity.
   skuok=bool(re.search(r"(?<!\d)165573(?!\d)",t))
   titleok=bool(re.search(r"MoliCare Premium Elastic Large 9 drops\s*\|\s*CTN/72",t,re.I))
   packok=bool(re.search(r"PKT/24,\s*CTN/72",t,re.I))
   pricepos=t.find("MoliCare Premium Elastic Large 9 drops")
   excerpt=t[max(0,pricepos-70):pricepos+550] if pricepos>=0 else t[:500]
   price_match=re.search(r"\$\s*([0-9,]+\.\d{2})",excerpt)
   d.update(identity_evidence=excerpt,sku_confirmed=skuok,title_confirmed=titleok,carton_confirmed=packok)
   if skuok and titleok and packok and price_match:
    d.update(status="success",price=float(price_match.group(1).replace(",","")),special_price=None)
   else:d["status"]="unresolved"
 except Exception as e:d.update(status="failed",error=type(e).__name__+": "+str(e))
 R.append(d)
print("BATCH11_RECOVERY_START")
print(json.dumps(R,indent=2))
print("BATCH11_RECOVERY_END")
