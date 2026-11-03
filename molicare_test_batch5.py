from __future__ import annotations
import re,json
from scrapling.fetchers import Fetcher
PRODUCTS=[
 dict(row=21,sku="168409",aliases=[],name="MoliCare Premium Form 9 Drops",drops=9,qty=64),
 dict(row=22,sku="168132",aliases=["168035"],name="MoliCare Premium Lady Pad 1 Drop",drops=1,qty=192),
 dict(row=23,sku="168634",aliases=["168044"],name="MoliCare Premium Lady Pad 2 Drops",drops=2,qty=252),
 dict(row=24,sku="168045",aliases=["168644"],name="MoliCare Premium Lady Pad 3 Drops",drops=3,qty=144),
 dict(row=25,sku="168682",aliases=["168046"],name="MoliCare Premium Lady Pad 4 Drops",drops=4,qty=168),
]
SOURCES=[
 (21,"LuxeMED","shopify","https://www.luxemed.com.au/collections/continence/products/molicare-premium-form-9d"),
 (21,"Independence Australia","html","https://store.independenceaustralia.com/molicare-premium-form-9-drops-3399ml-15310071"),
 (22,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-lady-pad-1-drop"),
 (23,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-lady-pad-2-drops"),
 (23,"Oz Medical","shopify","https://ozmedical.com.au/products/molicare-premium-lady-pad-2-drops-331ml"),
 (24,"Vital Medical Supplies","html","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/continence/molicare-prem-lady-pad-3d-12pk-x-12s/"),
 (24,"Day & Night Healthcare","html","https://www.dnhc.com.au/168045/MoliCare-Premium-Lady-Pad-3-drops-144/pd.php"),
 (24,"Independence Australia","html","https://store.independenceaustralia.com/molicare-premium-lady-pads-3-drops-female-504ml-15310032"),
 (24,"AMH Community","shopify","https://www.amhcommunity.com.au/products/molicare-premium-lady-pad-3-drops"),
 (25,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-lady-pad-4-drops"),
 (25,"Vital Medical Supplies","html","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/small-shaped-pad/molicare-premium-lady-pad-4-drops-12s/"),
]
def qty_ok(q,t):
 t=t.lower()
 if re.search(r"\b"+str(q)+r"\b",t) and re.search(r"carton|case|box|units|pieces|ctn|pack size",t):return True
 for a,b in re.findall(r"(\d+)\s*(?:packs?|packets?|pkts?|x|×)\s*(?:of)?\s*(\d+)",t):
  if int(a)*int(b)==q:return True
 for a,b in re.findall(r"(\d+)\s*(?:x|×)\s*(\d+)",t):
  if int(a)*int(b)==q:return True
 return False
def sku_ok(p,t):
 return any(re.search(r"(?<!\d)"+re.escape(code)+r"(?!\d)",str(t)) for code in [p["sku"]]+p["aliases"])
def price(v):
 if v is None:return None
 try:return round(int(v)/100,2)
 except:return None
def get(url):
 return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=38)
def page_text(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def shopify(p,url):
 pg=get(url.rstrip("/")+".js")
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 try:j=pg.json()
 except Exception as e:return dict(status="unreadable_json",error=str(e))
 title=str(j.get("title") or "")
 if "molicare" not in title.lower() or ("lady" in p["name"].lower() and "lady" not in title.lower()):
  return dict(status="family_mismatch",title=title)
 results=[]
 for v in j.get("variants") or []:
  t=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  sku=str(v.get("sku") or "")
  # Sale price accepted only for a manufacturer code and verified exact carton.
  # Shopify family titles may contain drop info in parent title or chosen variant.
  if not sku_ok(p,sku):continue
  if not qty_ok(p["qty"],t):continue
  dropmatch=bool(re.search(r"(?<!\d)"+str(p["drops"])+r"\s*(?:d|drops?)\b",title+" "+t,re.I))
  if not dropmatch:continue
  results.append(v)
 if len(results)!=1:
  return dict(status="variant_unresolved",title=title,candidates=[dict(sku=v.get("sku"),title=v.get("title"),price=price(v.get("price")),compare_at=price(v.get("compare_at_price"))) for v in j.get("variants") or []][:20])
 v=results[0];cur=price(v.get("price"));was=price(v.get("compare_at_price"))
 return dict(status="success" if cur else "price_not_found",price=was if was and was>cur else cur,special_price=cur if was and cur and was>cur else None,matched_sku=v.get("sku"),matched_variant=v.get("title"),variant_url=url+"?variant="+str(v.get("id")))
def html(p,url):
 pg=get(url)
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 t=page_text(pg)
 if "molicare" not in t.lower() or not sku_ok(p,t):return dict(status="identity_unverified")
 if not qty_ok(p["qty"],t):return dict(status="carton_unverified")
 codepos=next((t.find(code) for code in [p["sku"]]+p["aliases"] if code in t),0)
 nearby=t[max(0,codepos-300):codepos+400]
 if "vitalmedicalsupplies" in url:
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s+Supplier Part\s+"+re.escape(p["sku"])+r"\b",t,re.I)
  if m:return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,price_basis="inc GST",matched_excerpt=t[max(0,m.start()-120):m.end()+90])
 if "dnhc.com.au" in url:
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*\(ex GST\)",t,re.I)
  if m:return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,price_basis="ex GST",matched_excerpt=nearby)
 if "independenceaustralia" in url:
  m=re.search(r"Carton\s+(\d+)\s+PKT\(s\)\s+\$\s*([0-9,]+\.\d{2})",t,re.I)
  if m and int(m.group(1)) in (4,12,16,18):
   return dict(status="success",price=float(m.group(2).replace(",","")),special_price=None,matched_excerpt=t[m.start():m.end()])
 return dict(status="price_unresolved",matched_excerpt=nearby)
output=[]
for p in PRODUCTS:
 for row,retailer,mode,url in SOURCES:
  if row!=p["row"]:continue
  try: r=shopify(p,url) if mode=="shopify" else html(p,url)
  except Exception as e:r=dict(status="error",error=type(e).__name__+": "+str(e))
  output.append(dict(row=row,sku=p["sku"],carton=p["qty"],retailer=retailer,url=url,**r))
print("BATCH5_START")
print(json.dumps(output,indent=2))
print("BATCH5_END")
