from __future__ import annotations
import re,json,html
from scrapling.fetchers import Fetcher
P=[
 dict(row=71,given="915867",sku="995016",family="foam",size=None,drops=None,qty=12,pack=1),
 dict(row=72,given="915868",sku="915867",family="lady",size="Medium",drops=5,qty=64,pack=8),
 dict(row=73,given="915817",sku="915868",family="lady",size="Large",drops=5,qty=56,pack=7),
 dict(row=74,given="915818",sku="915817",family="men",size="Medium",drops=5,qty=32,pack=8),
 dict(row=75,given="995089",sku="915818",family="men",size="Large",drops=5,qty=28,pack=7),
]
S=[
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-skin-cleansing-foam-400ml",[71]),
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-skin-cleansingfoam",[71]),
 ("Independence Australia","ind","https://store.independenceaustralia.com/molicare-skin-cleansing-foam-400ml-24310105",[71]),
 ("Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/skin-care/skin-care/molicare-cleansing-foam-400ml/",[71]),
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-lady-pants-5d-medium",[72,73]),
 ("Mobiquip","shopify","https://www.mobiquip.com.au/products/molicare-lady-pants",[72,73]),
 ("Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/continence/molicare-prem-lady-pants-5-drops-m-8s/",[72]),
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-men-pants-5d-medium",[74,75]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-lady-pants-5-drops",[72,73]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-men-pants-5-drops",[74,75]),
]
def fetch(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=32)
def txt(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def skuok(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def cents(v):
 try:return round(int(v)/100,2)
 except:return None
def sizeok(p,s):
 if not p["size"]:return True
 return bool(re.search(r"(?<![a-z])"+p["size"].lower()+r"(?![a-z])",s.lower()))
def quantityok(p,s):
 s=s.lower()
 if p["family"]=="foam":return bool(re.search(r"carton\s*(?:of\s*)?\(?12\s*[x×]\s*400\s*ml|carton\s*\(?12\s*[x×]\s*400\s*ml|carton\s*\(?12\s*(?:units?|bottles?)",s))
 return bool(re.search(r"carton\s*\(?"+str(p["qty"])+r"\s*(?:pcs|units?|pieces)?\)?|"+str(p["qty"])+r"\s*(?:units?|pieces?)\s*[-/]?\s*(?:carton|box)|"+str(p["qty"])+r"\s*-\s*box",s)) or bool(re.search(r"carton\s*\(?"+str(p["qty"])+r"\)?",s))
def shopify(p,retailer,url):
 pg=fetch(url+".js");status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 d=pg.json();title=str(d.get("title") or "")
 if "molicare" not in title.lower() or not {"foam":("foam",),"lady":("lady","pants"),"men":("men","pants")}[p["family"]][0] in title.lower():return dict(status="wrong_product",title=title)
 description=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(d.get("description") or ""))))
 variants=d.get("variants") or [];valid=[]
 for v in variants:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  code=str(v.get("sku") or "")
  identity=title+" "+label
  if not skuok(p,code):continue
  if not sizeok(p,label) and not (len(variants)==1 and sizeok(p,title)):continue
  if p["drops"] and not re.search(r"\b"+str(p["drops"])+r"\s*(?:d|drops?)\b",identity,re.I):continue
  if not quantityok(p,label):
   # Some Shopify listings store carton sizes in product descriptions,
   # but only use this when a single correct-size variant exists.
   if not (len(variants)==1 and quantityok(p,description)):continue
  valid.append(v)
 if len(valid)!=1:return dict(status="unresolved",title=title,variants=[dict(sku=v.get("sku"),title=v.get("title"),price=cents(v.get("price"))) for v in variants][:22],description_excerpt=description[:150])
 v=valid[0];now=cents(v.get("price"));compare=cents(v.get("compare_at_price"))
 return dict(status="success",price=compare if compare and now and compare>now else now,special_price=now if compare and now and compare>now else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=url+"?variant="+str(v["id"]))
def ind(p,url):
 pg=fetch(url);status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 t=txt(pg)
 if not skuok(p,t) or not "400ml" in t.lower():return dict(status="identity_unverified")
 m=re.search(r"Carton\s+12\s+EA\(s\)\s+\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0)) if m else dict(status="unresolved")
def vital(p,url):
 pg=fetch(url);status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 t=txt(pg)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s+Supplier Part\s+"+p["sku"]+r"\s+Unit CAR\s+"+str(p["qty"]),t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,basis="inc GST") if m else dict(status="unresolved",sku_visible=skuok(p,t))
results=[]
for p in P:
 for retailer,mode,url,rows in S:
  if p["row"] not in rows:continue
  try:r=shopify(p,retailer,url) if mode=="shopify" else ind(p,url) if mode=="ind" else vital(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  results.append(dict(row=p["row"],supplied_sku=p["given"],manufacturer_sku=p["sku"],family=p["family"],size=p["size"],carton=p["qty"],retailer=retailer,url=url,**r))
print("BATCH15_START")
print(json.dumps(results,indent=2,ensure_ascii=False))
print("BATCH15_END")
