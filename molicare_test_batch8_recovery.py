import re,json
from scrapling.fetchers import Fetcher
S=[
 (38,"HomeHealth Medical","https://hhmedicalsupplies.com.au/product/molicare-premium-bed-mat-40x60cm-5-drops-pack-30-2/","hh"),
 (38,"Independence Australia","https://store.independenceaustralia.com/continence-aids/bedding-chair-floor-protection/disposable-bed-protection/molicare-premium-bed-mat-5-drops-40x60cm-400ml-15310601","ind"),
 (37,"Vital Medical Supplies","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/underpad/bed--chair-protection/molicare-prem-bed-mat-7drop-60x90-4s/","vital"),
 (37,"Topcat Healthcare","https://topcathealthcare.com.au/products/molicare-premium-bedmat-drop-7-6090","shopify"),
 (36,"LuxeMED","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-bed-mat-40x60cm-5-drops","shopify"),
]
out=[]
for row,retailer,url,mode in S:
 d=dict(row=row,retailer=retailer,url=url)
 sku={36:"161065",37:"161070",38:"161061"}[row]
 try:
  p=Fetcher.get(url+(".js" if mode=="shopify" else ""),impersonate="chrome",stealthy_headers=True,timeout=30)
  d["http_status"]=int(p.status)
  if d["http_status"]!=200:d["status"]="blocked"
  elif mode=="shopify":
   j=p.json();d["title"]=j.get("title")
   d["variants"]=[dict(title=v.get("title"),sku=v.get("sku"),price=int(v["price"])/100 if v.get("price") else None,compare=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None,variant_id=v.get("id")) for v in j.get("variants") or []]
   d["status"]="diagnostic"
  else:
   t=re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
   if sku not in t:d["status"]="sku_unverified"
   elif mode=="hh":
    m=re.search(r"Carton\s+6\s+Pkt\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
    d.update(status="success" if m else "price_unresolved",price=float(m.group(1).replace(",","")) if m else None,excerpt=t[max(0,t.find("Manufacturer Code:")-80):t.find("Manufacturer Code:")+330])
   elif mode=="ind":
    m=re.search(r"Carton\s+6\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
    d.update(status="success" if m else "price_unresolved",price=float(m.group(1).replace(",","")) if m else None)
   elif mode=="vital":
    m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc\s*GST\s+Supplier Part\s+"+sku+r"\s+Unit CAR\s+100",t,re.I)
    d.update(status="success" if m else "price_unresolved",price=float(m.group(1).replace(",","")) if m else None,basis="inc GST")
 except Exception as e:d.update(status="error",error=type(e).__name__+": "+str(e))
 out.append(d)
print("BATCH8_RECOVERY_START")
print(json.dumps(out,indent=2))
print("BATCH8_RECOVERY_END")
