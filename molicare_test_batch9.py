from __future__ import annotations
import re,json
from scrapling.fetchers import Fetcher

P=[
 {"row":41,"sku":"165273","size":"Large","drops":6,"carton":90},
 {"row":42,"sku":"165274","size":"XL","drops":6,"carton":56},
 {"row":43,"sku":"165374","size":"XL","drops":7,"carton":56},
 {"row":44,"sku":"165474","size":"XL","drops":8,"carton":56},
 {"row":45,"sku":"165574","size":"XL","drops":9,"carton":56},
]
S=[
 {"retailer":"Conticare","kind":"group","rows":[41],"url":"https://www.conticare.com.au/molicare-premium-elastic-large-6-drops-165273.html"},
 {"retailer":"Conticare","kind":"group","rows":[42],"url":"https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-extra-large-6-drops-2786ml-140-175cm-165274.html"},
 {"retailer":"Conticare","kind":"group","rows":[45],"url":"https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-extra-large-9-drops-3951ml-140-175cm-165574.html"},
 {"retailer":"Independence Australia","kind":"independence","rows":[41],"url":"https://store.independenceaustralia.com/molicare-premium-elastic-6-d-slip-large-waist-115-145-cm-2349ml-15310155"},
 {"retailer":"Independence Australia","kind":"independence","rows":[42],"url":"https://store.independenceaustralia.com/molicare-premium-elastic-6-d-slip-x-large-waist-140-175cm-2786ml-15310117"},
 {"retailer":"Vital Medical Supplies","kind":"vital","rows":[42],"url":"https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/pants/pull-up-pants/molicare-premium-elastic-6-drops-xl-4s/"},
 {"retailer":"InCare Supports","kind":"shopify","rows":[43],"url":"https://incaresupports.com.au/products/molicare-premium-elastic-7-drops"},
 {"retailer":"InCare Supports","kind":"shopify","rows":[44],"url":"https://incaresupports.com.au/products/molicare-premium-elastic-8-drops"},
 {"retailer":"InCare Supports","kind":"shopify","rows":[45],"url":"https://incaresupports.com.au/products/molicare-premium-elastic-9-drops"},
 {"retailer":"InCare Supports","kind":"shopify","rows":[41,42],"url":"https://incaresupports.com.au/products/molicare-premium-elastic-6-drops"},
]
def get(url):
 return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
def text(page):
 try:return re.sub(r"\s+"," ",page.get_all_text(separator=" ",strip=True))
 except Exception:return ""
def size_match(p,s):
 s=s.lower().replace("extra large","xl").replace("x-large","xl").replace("x large","xl")
 if p["size"]=="XL":return bool(re.search(r"\bxl\b",s))
 return bool(re.search(r"\blarge\b",s)) and not bool(re.search(r"\bxl\b",s))
def qty(p,s):
 t=s.lower()
 if re.search(r"\b"+str(p["carton"])+r"\b",t) and re.search(r"carton|box|units|pieces",t):return True
 for a,b in re.findall(r"(\d+)\s*(?:packs?|packets?|pkt|x|×)\s*(?:of)?\s*(\d+)",t):
  if int(a)*int(b)==p["carton"]:return True
 return False
def exact_sku(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def cent(v):return round(int(v)/100,2) if v is not None else None

def shopify(p,s):
 pg=get(s["url"].rstrip("/")+".js");status=int(pg.status)
 if status!=200:return {"status":"blocked","http_status":status}
 j=pg.json();title=str(j.get("title") or "")
 if not all(k in title.lower() for k in ("molicare","elastic")):return {"status":"family_mismatch","title":title}
 vs=j.get("variants") or [];matches=[]
 for v in vs:
  blob=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  sku=str(v.get("sku") or "")
  if not exact_sku(p,sku) or not size_match(p,blob):continue
  if not re.search(r"(?<!\d)"+str(p["drops"])+r"\s*(?:d|drops?)\b",title+" "+blob,re.I):continue
  if not qty(p,blob):continue
  matches.append(v)
 if len(matches)!=1:
  return {"status":"variant_unresolved","title":title,"candidates":[{"sku":v.get("sku"),"title":v.get("title"),"price":cent(v.get("price")),"compare_at":cent(v.get("compare_at_price"))} for v in vs][:18]}
 v=matches[0];cur=cent(v.get("price"));comp=cent(v.get("compare_at_price"))
 return {"status":"success" if cur else "price_not_found","price":comp if comp and comp>cur else cur,
 "special_price":cur if comp and cur and comp>cur else None,
 "matched_sku":v.get("sku"),"matched_variant":v.get("title"),
 "variant_url":s["url"]+"?variant="+str(v.get("id"))}

def group(p,s):
 pg=get(s["url"]);status=int(pg.status)
 if status!=200:return {"status":"blocked","http_status":status}
 t=text(pg)
 # Capture price immediately after the exact SKU and carton label.
 pat=(r"MoliCare[^$]{0,150}\b"+str(p["drops"])+r"\s+Drops?[^$]{0,160}"
      +p["sku"]+r"\s*\(Box of\s*"+str(p["carton"])+r"\)\s*\$\s*([0-9,]+(?:\.\d{2})?)")
 matches=list(re.finditer(pat,t,re.I))
 if len(matches)!=1:return {"status":"variant_unresolved","sku_present":exact_sku(p,t),"excerpt":t[max(0,t.find(p["sku"])-120):t.find(p["sku"])+340]}
 m=matches[0]
 if not size_match(p,m.group(0)):return {"status":"size_mismatch"}
 return {"status":"success","price":float(m.group(1).replace(",","")),"special_price":None,"matched_excerpt":m.group(0)[-280:]}
def independence(p,s):
 pg=get(s["url"]);status=int(pg.status)
 if status!=200:return {"status":"blocked","http_status":status}
 t=text(pg)
 if not exact_sku(p,t) or not size_match(p,t):return {"status":"identity_unverified"}
 packages=p["carton"]//(30 if p["carton"]==90 else 14)
 m=re.search(r"Carton\s+"+str(packages)+r"\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 if not m:return {"status":"carton_price_unresolved"}
 return {"status":"success","price":float(m.group(1).replace(",","")),"special_price":None,
         "price_basis":"as displayed","matched_excerpt":m.group(0)}
def vital(p,s):
 pg=get(s["url"]);status=int(pg.status)
 if status!=200:return {"status":"blocked","http_status":status}
 t=text(pg)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s+inc GST\s+Supplier Part\s+"+p["sku"]+r"\s+Unit CAR\s+"+str(p["carton"]),t,re.I)
 if not m:return {"status":"identity_or_price_unverified"}
 return {"status":"success","price":float(m.group(1).replace(",","")),"special_price":None,"price_basis":"inc GST"}
OUT=[]
for p in P:
 for s in S:
  if p["row"] not in s["rows"]:continue
  try:
   v=shopify(p,s) if s["kind"]=="shopify" else group(p,s) if s["kind"]=="group" else independence(p,s) if s["kind"]=="independence" else vital(p,s)
  except Exception as e:v={"status":"failed","error":type(e).__name__+": "+str(e)}
  OUT.append({"row":p["row"],"sku":p["sku"],"size":p["size"],"drops":p["drops"],"carton":p["carton"],"retailer":s["retailer"],"url":s["url"],**v})
print("BATCH9_START")
print(json.dumps(OUT,indent=2))
print("BATCH9_END")
