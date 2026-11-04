from __future__ import annotations
import re,json,html,concurrent.futures
from scrapling.fetchers import Fetcher

TARGETS=[
 (14,"168100",336,"Vital Medical Supplies","html","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/small-shaped-pad/molicare-pad-2-drops-12s/"),
 (22,"168132",192,"Vital Medical Supplies","html","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/small-shaped-pad/molicare-premium-lady-pad-1d-16pk-x-12s/"),
 (22,"168132",192,"Medisa","shopify","https://medisa.com.au/products/incontinence-aids-pads-pants-liners-pad-pant-system-hartmann-molicare-premium-lady-pad-all-sizes"),
 (67,"165531",56,"OzChemist","shopify","https://ozchemist.com/products/molicare-slip-maxi-small"),
 (67,"165531",56,"Betta Health Outcomes","html","https://bettahealthoutcomes.com.au/product/molicare-slip-maxi-waist-60-90-cm-small-2153ml-poa/"),
 (67,"165531",56,"ILCMC","html","https://www.ilcmc.com.au/molicare-slip-maxi~1983"),
 (68,"165532",56,"Conticare","html","https://www.conticare.com.au/molicare-slip-unisex-briefs-medium-maxi-2485ml-90-120cm-165532.html"),
 (68,"165532",56,"OzChemist","shopify","https://ozchemist.com/products/molicare-slip-maxi-medium"),
 (69,"165533",56,"Conticare","html","https://www.conticare.com.au/molicare-slip-unisex-briefs-large-maxi-3815ml-120-150cm-165533.html"),
 (69,"165533",56,"OzChemist","shopify","https://ozchemist.com/products/molicare-slip-maxi-large"),
 (70,"169248",120,"Conticare","html","https://www.conticare.com.au/molicare-premium-elastic-slips-x-small-6-drops-40-60cm-1170ml-169248.html"),
 (70,"169248",120,"Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-premium-slip-extra-plus-6dopen-style"),
 (71,"916680",32,"Assist Ability","shopify","https://shop.assistabilityaustralia.com.au/products/dignity-bariatric-brief-white-p8-c4"),
 (71,"916680",32,"Independence Australia","html","https://store.independenceaustralia.com/hartmann-all-in-one-dignity-bariatric-briefs-160-239-cm-unisex-2445ml-white-15310145"),
 (71,"916680",32,"Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-dignity-bariatric-brief-disposable-incontinence-pants"),
 (71,"916680",32,"Vital Medical Supplies","html","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/all-in-one/bariatric/dignity-bariatric-brief-8d-xxl-32s/"),
 (98,"165531-1",14,"OzChemist","shopify","https://ozchemist.com/products/molicare-slip-maxi-small"),
 (98,"165531-1",14,"ILCMC","html","https://www.ilcmc.com.au/molicare-slip-maxi~1983"),
]
def tx(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def skuok(sku,s):
 return bool(re.search(r"(?<!\d)"+re.escape(sku)+r"(?!\d)",str(s)))
def fetch(u):
 return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def shopify(t,j):
 row,sku,count,ret,url=t
 title=str(j.get("title") or "");vs=j.get("variants") or []
 desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 found=[]
 for v in vs:
  vsku=str(v.get("sku") or "");label=str(v.get("title") or "")
  evidence=title+" "+label+" "+vsku
  if row==22:
   valid=skuok("168132",vsku) and re.search(r"\b1\s*Drop\b",label,re.I) and re.search(r"(?:192|16\s*x\s*12)",label+vsku,re.I)
  elif row==67:
   valid=("molicare" in title.lower() and "slip" in title.lower() and "maxi" in title.lower() and "small" in title.lower() and re.search(r"4\s*packs?\s*per\s*carton",label,re.I) and skuok("165531",vsku))
  elif row==69:
   valid=("molicare" in title.lower() and "slip" in title.lower() and "maxi" in title.lower() and "large" in title.lower() and re.search(r"4\s*packs?\s*per\s*carton",label,re.I) and skuok("165533",vsku))
  elif row==68:
   valid=("slip" in title.lower() and "medium" in title.lower() and re.search(r"4\s*packs?\s*per\s*carton",label,re.I) and skuok("165532",vsku))
  elif row==98:
   valid=("slip" in title.lower() and "small" in title.lower() and re.search(r"14\s*units?\s*per\s*pack",label,re.I) and skuok("165531",vsku))
  elif row==70:
   valid=skuok("169248",vsku) and re.search(r"4\s*packs?\s*per\s*carton|120\s*(?:units|pcs)",label,re.I) and re.search(r"(?i)(?:XS|X-Small|Extra Small)",title+label)
  elif row==71:
   valid=skuok("916680",vsku) and re.search(r"32\s*pieces?\s*per\s*carton|carton.{0,10}32|carton.{0,10}4|4\s*packs",label,re.I)
  else:valid=False
  if valid:found.append(v)
 if len(found)!=1:return dict(status="unresolved",title=title,variants=[dict(sku=v.get("sku"),title=v.get("title"),price=v.get("price"),compare_at=v.get("compare_at_price"),available=v.get("available")) for v in vs[:16]])
 v=found[0]
 raw=v.get("price");old=v.get("compare_at_price")
 try:
  cur=float(raw)/100 if isinstance(raw,int) else float(raw)
  comp=float(old)/100 if isinstance(old,int) else float(old) if old else None
 except: return dict(status="bad_price",variant=v.get("title"))
 if not cur or cur<=0:return dict(status="bad_price")
 return dict(status="success",price=round(comp,2) if comp and comp>cur else round(cur,2),special_price=round(cur,2) if comp and comp>cur else None,sku=v.get("sku"),variant=v.get("title"),url=t[5]+"?variant="+str(v.get("id")),availability=v.get("available"))
def html_price(t,text):
 row,sku,count,ret,url=t
 if row==22:
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s*Supplier Part\s*168035\s*Unit CAR\s*192",text,re.I)
  return dict(status="success",price=float(m[1].replace(",","")),special_price=None,source_sku="168035 (old code)",basis="inc GST") if m else dict(status="unresolved",excerpt=text[max(0,text.find("168035")-100):text.find("168035")+170])
 if row==14:
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s*Supplier Part\s*168100\s*Unit CAR\s*336",text,re.I)
  return dict(status="success",price=float(m[1].replace(",","")),special_price=None,basis="inc GST") if m else dict(status="unresolved")
 if row==71:
  if ret=="Vital Medical Supplies":
   m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s*Supplier Part\s*916680\s*Unit CAR\s*32",text,re.I)
  else:
   m=re.search(r"Supplier Part Number:\s*916680.{0,250}?Carton\s*4\s*PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
  return dict(status="success",price=float(m[1].replace(",","")),special_price=None) if m else dict(status="unresolved",sku_present="916680" in text,excerpt=text[max(0,text.find("916680")-100):text.find("916680")+300])
 if row==67 and ret=="Betta Health Outcomes":
  m=re.search(r"MoliCare Slip Maxi Waist 60-90 Cm S 2153ml C56 165531.{0,170}\$\s*([0-9,]+\.\d{2})",text,re.I)
  return dict(status="success",price=float(m[1].replace(",","")),special_price=None,availability="out of stock") if m else dict(status="unresolved",excerpt=text[:450])
 if ret=="Conticare":
  m=re.search(r"(?<!\d)"+re.escape(sku)+r"\s*\(Box of "+str(count)+r"\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
  return dict(status="success",price=float(m[1].replace(",","")),special_price=None) if m else dict(status="unresolved",sku_visible=sku in text,excerpt=text[max(0,text.find(sku)-90):text.find(sku)+450])
 if ret=="ILCMC":
  m=re.search(r"\[Size S\] SKU: 165531.{0,80}\$\s*([0-9,]+\.\d{2})",text,re.I)
  if row==98 and m:return dict(status="success",price=float(m[1].replace(",","")),special_price=None,availability="sold out",basis="14-unit pack")
  return dict(status="unresolved",excerpt=text[max(0,text.find(sku)-50):text.find(sku)+230])
 return dict(status="unresolved")
def do(t):
 row,sku,count,ret,url=t
 res=dict(row=row,our_sku=sku,qty=count,retailer=ret,url=url)
 try:
  is_js=ret in ("Medisa","OzChemist","Assist Ability","Incontinence Products Australia")
  pg=fetch(url+(".js" if is_js else ""))
  res["http_status"]=int(pg.status)
  if res["http_status"]!=200:res["status"]="blocked";return res
  v=shopify(t,pg.json()) if is_js else html_price(t,tx(pg))
  res.update(v)
 except Exception as e:res.update(status="failed",error=type(e).__name__+": "+str(e))
 return res
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:out=list(ex.map(do,TARGETS))
print("FOCUS_PRODUCTS_START")
print(json.dumps(out,ensure_ascii=False,indent=2))
print("FOCUS_PRODUCTS_END")
