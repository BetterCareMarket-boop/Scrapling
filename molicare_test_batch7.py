from __future__ import annotations
import json,re
from scrapling.fetchers import Fetcher
P=[
 {"row":31,"sku":"168407","family":"form","drops":7,"qty":128,"size":None},
 {"row":32,"sku":"915861","family":"mobile","drops":5,"qty":56,"size":"small"},
 {"row":33,"sku":"915852","family":"mobile","drops":5,"qty":42,"size":"medium"},
 {"row":34,"sku":"915853","family":"mobile","drops":5,"qty":56,"size":"large"},
 {"row":35,"sku":"915854","family":"mobile","drops":5,"qty":56,"size":"x-large"}
]
S=[
 {"rows":[31],"retailer":"InCare Supports","mode":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-form-4-drops"},
 {"rows":[31],"retailer":"Platinum Health Supply","mode":"shopify","url":"https://www.platinumhealthsupply.com.au/products/molicare-premium-form-7-drops"},
 {"rows":[31],"retailer":"AMH Community","mode":"shopify","url":"https://www.amhcommunity.com.au/products/molicare-premium-form-7-drops"},
 {"rows":[31],"retailer":"LuxeMED","mode":"shopify","url":"https://www.luxemed.com.au/collections/molicare/products/molicare-premium-form-7-drops"},
 {"rows":[32,33,34,35],"retailer":"InCare Supports","mode":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-mobile-5-drops"},
 {"rows":[32,33,34,35],"retailer":"Oz Medical","mode":"shopify","url":"https://ozmedical.com.au/products/molicare-premium-mobile-5-drops"},
 {"rows":[32,33,34,35],"retailer":"Mobiquip","mode":"shopify","url":"https://www.mobiquip.com.au/products/molicare-premium-mobile"},
 {"rows":[32,33,34,35],"retailer":"mySupply Store","mode":"listing","url":"https://mysupplystore.com.au/continence-products/disposable-pants-pads-liners/molicare-premium-mobile/"},
 {"rows":[32],"retailer":"Vital Medical Supplies","mode":"vital","url":"https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/pants/molicare-premium-mobile-5-drops-s-4s/"}
]
def get(url):return Fetcher.get(url, impersonate="chrome",stealthy_headers=True,timeout=35)
def text(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def ok_code(p,sku):
 return bool(re.search(r"(?<!\d)"+re.escape(p["sku"])+r"(?!\d)",str(sku)))
def price(v):
 try:return round(int(v)/100,2)
 except:return None
def size_match(p,v):
 if not p["size"]:return True
 sz=p["size"]
 normalized=v.lower().replace("extra large","x-large").replace("xlarge","x-large")
 if sz=="x-large":return bool(re.search(r"\bx-large\b|\bxl\b",normalized))
 return bool(re.search(r"(?<![a-z])"+sz+r"(?![a-z])",normalized))
def qty_match(p,s,parent="",allvars=None):
 q=p["qty"]
 t=s.lower()
 if re.search(r"\b"+str(q)+r"\b",t) and re.search(r"units|pieces|carton|box|ctn|case",t):return True
 for a,b in re.findall(r"(\d+)\s*(?:packets?|packs?|pkt|x|×)\s*(?:of)?\s*(\d+)",t):
  if int(a)*int(b)==q:return True
 k=re.search(r"(\d+)\s*(?:packs?|packets?)\s*per\s*carton",t)
 if k and allvars:
  pack_counts=set()
  for v in allvars:
   lab=str(v.get("title") or "")
   m=re.search(r"(\d+)\s*(?:units?|pieces?)\s*per\s*pack",lab,re.I)
   if m:pack_counts.add(int(m.group(1)))
  return len(pack_counts)==1 and int(k.group(1))*next(iter(pack_counts))==q
 return False
def shopify(p,s):
 page=get(s["url"]+".js")
 st=int(page.status)
 if st!=200:return {"status":"blocked","http_status":st}
 try:j=page.json()
 except Exception as e:return {"status":"invalid_json","error":str(e)}
 title=str(j.get("title") or "")
 if "molicare" not in title.lower() or p["family"] not in title.lower():return {"status":"wrong_product","title":title}
 candidates=[]
 variants=j.get("variants") or []
 for v in variants:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  code=str(v.get("sku") or "")
  identity=title+" "+label
  if not ok_code(p,code):continue
  if not size_match(p,label if p["size"] and any(x in label.lower() for x in ("small","medium","large","xl")) else identity):continue
  if not re.search(r"(?<!\d)"+str(p["drops"])+r"\s*(?:drops?|d)\b",identity,re.I):continue
  if not qty_match(p,label,title,variants):continue
  candidates.append(v)
 if len(candidates)!=1:return {"status":"unresolved","title":title,"variants":[{"sku":v.get("sku"),"title":v.get("title"),"price":price(v.get("price"))} for v in variants][:30]}
 v=candidates[0];val=price(v.get("price"));was=price(v.get("compare_at_price"))
 return {"status":"success","price":was if was and val and was>val else val,"special_price":val if was and val and was>val else None,"matched_sku":v.get("sku"),"variant":v.get("title"),"variant_url":s["url"]+"?variant="+str(v.get("id"))}
def listing(p,s):
 page=get(s["url"]);st=int(page.status)
 if st!=200:return {"status":"blocked","http_status":st}
 tx=text(page)
 sizes={"small":"SMALL","medium":"MEDIUM","large":"LARGE","x-large":"XL"}
 pattern=rf"MOLICARE PREMIUM MOBILE 5D {sizes[p['size']]}\s+-\s+[^$]{{0,220}}CARTON\s+{p['qty']}\s+-\s+({p['sku']}\d*)\s+\$\s*([0-9,]+(?:\.\d{{2}})?)"
 m=re.search(pattern,tx,re.I)
 if not m:return {"status":"unresolved","error":"Exact SKU/size/carton/price row absent"}
 return {"status":"success","price":float(m.group(2).replace(",","")),"special_price":None,"matched_sku":m.group(1),"matched_excerpt":m.group(0)[:300]}
def vital(p,s):
 page=get(s["url"]);st=int(page.status)
 if st!=200:return {"status":"blocked","http_status":st}
 tx=text(page)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s+inc\s+GST\s+Supplier Part\s+"+p["sku"]+r"\s+Unit CAR\s+"+str(p["qty"]),tx,re.I)
 if not m:return {"status":"unresolved"}
 return {"status":"success","price":float(m.group(1).replace(",","")),"special_price":None,"price_basis":"inc GST"}
out=[]
for p in P:
 for s in S:
  if p["row"] not in s["rows"]:continue
  try:r=shopify(p,s) if s["mode"]=="shopify" else listing(p,s) if s["mode"]=="listing" else vital(p,s)
  except Exception as e:r={"status":"failed","error":type(e).__name__+": "+str(e)}
  out.append({"row":p["row"],"sku":p["sku"],"carton":p["qty"],"retailer":s["retailer"],"url":s["url"],**r})
print("BATCH7_START")
print(json.dumps(out,indent=2))
print("BATCH7_END")
