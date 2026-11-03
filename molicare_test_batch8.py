from __future__ import annotations
import re,json
from scrapling.fetchers import Fetcher
PRODUCTS=[
 dict(row=36,sku="161065",name="MoliCare Premium Bed Mat 60x90cm 5 Drops",qty=120,size="60x90",drops=5),
 dict(row=37,sku="161070",name="MoliCare Premium Bed Mat 60x90cm 7 Drops",qty=100,size="60x90",drops=7),
 dict(row=38,sku="161061",name="MoliCare Premium Bed Mat 40x60cm 5 Drops",qty=180,size="40x60",drops=5),
 dict(row=39,sku="165271",name="MoliCare Premium Elastic 6 Drops Small",qty=90,size="small",drops=6),
 dict(row=40,sku="165272",name="MoliCare Premium Elastic 6 Drops Medium",qty=90,size="medium",drops=6),
]
SOURCES=[
 (36,"Conticare","group","https://www.conticare.com.au/molicare-premium-bed-mat-med-mats-60-90cm-5-drops-850ml-161066.html"),
 (37,"Independence Australia","independence","https://store.independenceaustralia.com/molicare-premium-bed-mat-7-drops-60x90cm-1200ml-15310641"),
 (38,"Vital Medical Supplies","vital","https://prep.vitalmedicalsupplies.com.au/catalogue-products/continence-care/underpad/"),
 (39,"Conticare","group","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-small-6-drops-1890ml-70-90cm-165271.html"),
 (40,"Conticare","group","https://www.conticare.com.au/molicare-premium-elastic-6-drops-briefs-medium-85-120cm-2159ml-box-of-91.html"),
 (39,"Surgical House","surgical","https://surgicalhouse.com.au/Product.php?id=165271"),
 (40,"Surgical House","surgical","https://surgicalhouse.com.au/Product.php?id=165272"),
 (39,"Sumac Medical Supplies","sumac","https://sumacms.com.au/product/molicare-premium-elastic-6-d-small-waist-70-90cm-unisex-1667ml-ctn/"),
 (36,"Day & Night Healthcare","dnhc","https://www.dnhc.com.au/CONTINENCE/Bed-Pads/pl.php"),
 (37,"Day & Night Healthcare","dnhc","https://www.dnhc.com.au/CONTINENCE/Bed-Pads/pl.php"),
 (38,"Day & Night Healthcare","dnhc","https://www.dnhc.com.au/CONTINENCE/Bed-Pads/pl.php"),
 (39,"Day & Night Healthcare","dnhc","https://www.dnhc.com.au/CONTINENCE/All_dash_In_dash_One/pl.php"),
 (40,"Day & Night Healthcare","dnhc","https://www.dnhc.com.au/CONTINENCE/All_dash_In_dash_One/pl.php"),
]
def fetch(url):return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=35)
def text(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def money(x):return float(x.replace(",",""))
def run(p,retailer,kind,url):
 pg=fetch(url);status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 t=text(pg)
 sku=p["sku"]
 if sku not in t:return dict(status="sku_unverified",http_status=status)
 if kind=="group":
  # The grouped product page has a dedicated box/carton row. Do not select the adjacent pack price.
  matches=re.findall(r"([^$]{0,250}\(Box of\s*"+str(p["qty"])+r"\)\s*\$\s*([0-9,]+(?:\.\d\d)?)\s*)",t,re.I)
  exact=[(snippet,amt) for snippet,amt in matches if sku in snippet or p["size"].lower() in snippet.lower() and str(p["drops"])+" drops" in snippet.lower()]
  if len(exact)==1:return dict(status="success",price=money(exact[0][1]),special_price=None,matched_excerpt=exact[0][0][-220:],price_basis="not specified")
  return dict(status="carton_price_unresolved",matches=matches[:5])
 if kind=="independence":
  if "100 Units" not in t or "7 drops" not in t.lower() or "60x90" not in t.lower():return dict(status="variant_unverified")
  m=re.search(r"BOX\s+100\s+Units\s+\$\s*([0-9,]+\.\d{2})",t,re.I)
  return dict(status="success",price=money(m.group(1)),special_price=None) if m else dict(status="price_unresolved")
 if kind=="surgical":
  # Select carton conversion from the OUM table, never the per-pack header price.
  m=re.search(r"PK\s+CT\s+3\.00\s+([0-9,]+\.\d{2})\s+([0-9,]+\.\d{2})",t)
  if m and "6 DROP" in t.upper() and p["size"].upper() in t.upper():
   return dict(status="success",price=money(m.group(2)),special_price=None,matched_excerpt=m.group(0),price_basis="incl GST")
  if p["row"]==39:
   m=re.search(r"GST free\s+\$\s*([0-9,]+\.\d{2})",t,re.I)
   if m and "30X3" in t.upper():return dict(status="success",price=money(m.group(1)),special_price=None,matched_excerpt="30X3 carton and GST-free product price")
  return dict(status="carton_price_unresolved")
 if kind=="sumac":
  if "CTN/90" not in t.upper() or "6 drops" not in t.lower() or "small" not in t.lower():return dict(status="variant_unverified")
  m=re.search(r"\$\s*([0-9,]+\.\d{2})",t)
  return dict(status="success",price=money(m.group(1)),special_price=None) if m else dict(status="price_unresolved")
 if kind=="vital":
  m=re.search(r"Supplier Part:\s*"+sku+r"\s+Units:\s*CAR\s+"+str(p["qty"])+r"\s+\$\s*([0-9,]+\.\d{2})\s+inc GST",t,re.I)
  return dict(status="success",price=money(m.group(1)),special_price=None,price_basis="incl GST") if m else dict(status="price_unresolved")
 if kind=="dnhc":
  # Category page multiple products: anchor exact labelled title/code/price.
  pos=t.find("Product Code: "+sku)
  if pos<0:return dict(status="variant_unverified")
  block=t[max(0,pos-180):pos+120]
  if str(p["qty"]) not in block or (p["size"].lower() not in block.lower() and p["size"] not in ("60x90","40x60")):
   return dict(status="variant_unverified",excerpt=block)
  m=re.search(r"Product Code:\s*"+sku+r"\s+\$\s*([0-9,]+\.\d{2})\s*\(ex GST\)",block,re.I)
  return dict(status="success",price=money(m.group(1)),special_price=None,price_basis="ex GST",matched_excerpt=block) if m else dict(status="price_unresolved")
 return dict(status="unsupported")
out=[]
for row,retailer,kind,url in SOURCES:
 p=next(x for x in PRODUCTS if x["row"]==row)
 try:r=run(p,retailer,kind,url)
 except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
 out.append(dict(row=row,product=p["name"],sku=p["sku"],carton=p["qty"],retailer=retailer,url=url,**r))
print("BATCH8_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH8_END")
