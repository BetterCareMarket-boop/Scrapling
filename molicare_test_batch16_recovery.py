import re,json
from scrapling.fetchers import Fetcher
out=[]
p=[
 ("Topcat Healthcare Men Pants","https://topcathealthcare.com.au/products/molicare-premium-menpants-drop-7-medium","915827",32,8),
 ("Topcat Healthcare Pad 3 Drops","https://topcathealthcare.com.au/products/molicare-premium-pad-drop-3","168076",180,30)
]
for name,url,sku,qty,pack in p:
 r=dict(retailer=name,url=url)
 try:
  pg=Fetcher.get(url+".js",impersonate="chrome",stealthy_headers=True,timeout=28)
  r["http_status"]=int(pg.status)
  if r["http_status"]!=200:r["status"]="blocked";out.append(r);continue
  d=pg.json();vs=d.get("variants") or []
  ct=[v for v in vs if str(v.get("sku") or "")==sku+"-Ctn" and str(v.get("title") or "")=="Carton "+str(qty//pack)]
  packets=[v for v in vs if str(v.get("sku") or "")==sku and str(v.get("title") or "")=="Packet "+str(pack)]
  r.update(carton_variant_count=len(ct),exact_packet_variant_count=len(packets),variants=[{"sku":v.get("sku"),"title":v.get("title")} for v in vs])
  if len(ct)==1 and len(packets)==1:
   v=ct[0];r.update(status="success",price=int(v["price"])/100,special_price=None,variant_url=url+"?variant="+str(v["id"]),match_detail=f"{qty//pack} packets x {pack} = {qty}")
  else:r["status"]="carton_quantity_unverified"
 except Exception as e:r.update(status="failed",error=type(e).__name__+": "+str(e))
 out.append(r)
url="https://www.conticare.com.au/molicare-premium-fixpants-long-unisex-xxx-large-160-200cm-947789.html"
r=dict(retailer="Conticare FixPants XXXL",url=url)
try:
 pg=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=28)
 r["http_status"]=int(pg.status)
 if r["http_status"]==200:
  txt=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
  pos=txt.find("947789")
  r["excerpt"]=txt[max(0,pos-180):pos+450]
  price=re.search(r"\$\s*([0-9,]+\.\d{2})",txt[max(0,pos-150):pos+450])
  if price and "Pack of 25" in r["excerpt"] and re.search(r"(?<!\d)947789(?!\d)",r["excerpt"]):
   r.update(status="success",price=float(price.group(1).replace(",","")),special_price=None)
  else:r["status"]="price_unresolved"
 else:r["status"]="blocked"
except Exception as e:r.update(status="failed",error=type(e).__name__+": "+str(e))
out.append(r)
print("BATCH16_RECOVERY_START")
print(json.dumps(out,indent=2))
print("BATCH16_RECOVERY_END")
