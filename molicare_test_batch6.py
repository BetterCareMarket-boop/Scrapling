from __future__ import annotations
import json,re
from scrapling.fetchers import Fetcher
PRODUCTS=[
 {"row":26,"given":"168600","sku":"168670","other":["168051"],"family":"lady","drops":5,"carton":168},
 {"row":27,"given":"168705","sku":"168600","other":[],"family":"men","drops":2,"carton":168},
 {"row":28,"given":"168801","sku":"168705","other":["168068"],"family":"men","drops":4,"carton":168},
 {"row":29,"given":None,"sku":"168801","other":[],"family":"men","drops":5,"carton":168},
 {"row":30,"given":None,"sku":"168603","other":["168066"],"family":"men","drops":3,"carton":168}
]
SOURCES=[
 {"rows":[26],"retailer":"InCare Supports","type":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-lady-pad-1-drop"},
 {"rows":[27,28,29,30],"retailer":"InCare Supports","type":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-men-pad"},
 {"rows":[26],"retailer":"Platinum Health Supply","type":"shopify","url":"https://www.platinumhealthsupply.com.au/products/molicare-premium-lady-pad-5-drops"},
 {"rows":[27],"retailer":"Platinum Health Supply","type":"shopify","url":"https://www.platinumhealthsupply.com.au/products/molicare-premium-men-pad-2-drops"},
 {"rows":[28],"retailer":"Platinum Health Supply","type":"shopify","url":"https://www.platinumhealthsupply.com.au/products/molicare-premium-men-pad-4-drops"},
 {"rows":[29],"retailer":"Platinum Health Supply","type":"shopify","url":"https://www.platinumhealthsupply.com.au/products/molicare-premium-men-pad-5-drops"},
 {"rows":[30],"retailer":"LuxeMED","type":"shopify","url":"https://www.luxemed.com.au/collections/molicare/products/molicare-premium-men-pad-3-drops"},
 {"rows":[26],"retailer":"LuxeMED","type":"shopify","url":"https://www.luxemed.com.au/products/molicare-premium-lady-pad-5-drops"},
 {"rows":[29],"retailer":"LuxeMED","type":"shopify","url":"https://www.luxemed.com.au/collections/molicare/products/molicare-premium-men-pad-5-drops"},
 {"rows":[26],"retailer":"Dove Care","type":"html","url":"https://dovecaregroup.com.au/product/molicare-premium-lady-pad-5-drops/"},
 {"rows":[29],"retailer":"Tassway","type":"html","url":"https://www.tassway.com.au/product/molicare-premium-men-pad-5-drops/"},
 {"rows":[29],"retailer":"HomeHealth Medical","type":"hh","url":"https://hhmedicalsupplies.com.au/product/molicare-premium-men-pad-5-drops-pack-14-2/"},
 {"rows":[26],"retailer":"HomeHealth Medical","type":"hh","url":"https://hhmedicalsupplies.com.au/product/molicare-premium-lady-pad-5-drops-pack-14-2/"},
 {"rows":[28],"retailer":"Vital Medical Supplies","type":"vital","url":"https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/for-men/men/molicare-prem-men-pad-4-drops-14s-x-12/"}
]
def get(u):return Fetcher.get(u, impersonate="chrome",stealthy_headers=True,timeout=28)
def textpage(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def codes(p):return [p["sku"]]+p["other"]
def sku_ok(p,s):
 return any(re.search(r"(?<!\d)"+re.escape(code)+r"(?!\d)",str(s),re.I) for code in codes(p))
def cents(v):return round(int(v)/100,2) if v is not None else None
def cart_ok(q,title):
 t=title.lower()
 if re.search(r"\b"+str(q)+r"\b",t) and re.search(r"carton|units?|pieces?|box|ctn",t):return True
 for x,y in re.findall(r"(\d+)\s*(?:packets?|packs?|pkt|x|×)\s*(?:of)?\s*(\d+)",t):
  if int(x)*int(y)==q:return True
 return False
def shopify(p,s):
 page=get(s["url"]+".js")
 if int(page.status)!=200:return dict(status="blocked",http_status=int(page.status))
 try:d=page.json()
 except Exception as e:return dict(status="invalid_json",error=str(e))
 title=str(d.get("title") or "")
 if "molicare" not in title.lower() or p["family"] not in title.lower():return dict(status="wrong_family",title=title)
 candidates=[]
 for v in d.get("variants") or []:
  desc=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  sku=str(v.get("sku") or "")
  family_title=title+" "+desc
  if not sku_ok(p,sku):continue
  if not re.search(r"(?<!\d)"+str(p["drops"])+r"\s*(?:d|drops?)\b",family_title,re.I):continue
  if cart_ok(p["carton"],desc):candidates.append(v);continue
  # Variant named N Packs Per Carton, with separately verified pack count 14.
  m=re.search(r"(\d+)\s*(?:packs?|packets?)\s*per\s*carton",desc,re.I)
  if m and int(m.group(1))*14==p["carton"]:
   # Only if the page explicitly verifies units per packet, or another pack variant says 14 units
   page_description=json.dumps(d).lower()
   if re.search(r"14\s*(?:units?|pieces?)\s*per\s*pack|pack\s*of\s*14|14\s*units?\s*per\s*pack",page_description):candidates.append(v)
 if len(candidates)!=1:
  return dict(status="variant_unresolved",title=title,variants=[dict(title=v.get("title"),sku=v.get("sku"),price=cents(v.get("price")),compare_at=cents(v.get("compare_at_price"))) for v in d.get("variants") or []][:15])
 v=candidates[0];current=cents(v.get("price"));compare=cents(v.get("compare_at_price"))
 return dict(status="success",price=compare if compare and compare>current else current,special_price=current if compare and compare>current else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=s["url"]+"?variant="+str(v.get("id")))
def html(p,s):
 page=get(s["url"]);http=int(page.status)
 if http!=200:return dict(status="blocked",http_status=http)
 t=textpage(page)
 if not sku_ok(p,t):return dict(status="sku_unverified")
 if not re.search(r"molicare",t,re.I):return dict(status="brand_unverified")
 if p["family"]=="lady" and not re.search(r"lady",t,re.I):return dict(status="family_unverified")
 if p["family"]=="men" and not re.search(r"men",t,re.I):return dict(status="family_unverified")
 if not cart_ok(p["carton"],t):return dict(status="carton_unverified")
 if s["type"]=="vital":
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc\s*GST\s+Supplier Part\s+\d+\s*/OLD:"+re.escape(p["sku"])+r"\b\s+Unit CAR\s+"+str(p["carton"]),t,re.I)
 elif s["type"]=="hh":
  m=re.search(r"Carton\s+12\s+Pkt\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 elif s["retailer"]=="Dove Care":
  m=re.search(r"CTN\s*=\s*168\s*PIECES\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 elif s["retailer"]=="Tassway":
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*ex\s*GST",t,re.I)
 else:m=None
 if not m:return dict(status="price_unresolved")
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_sku=p["sku"],basis="ex GST" if s["retailer"]=="Tassway" else "inc GST" if s["type"]=="vital" else "unspecified")
out=[]
for p in PRODUCTS:
 for s in SOURCES:
  if p["row"] not in s["rows"]:continue
  try:r=shopify(p,s) if s["type"]=="shopify" else html(p,s)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=p["row"],given_sku=p["given"],product_sku=p["sku"],family=p["family"],drops=p["drops"],carton=p["carton"],retailer=s["retailer"],url=s["url"],**r))
print("BATCH6_START")
print(json.dumps(out,indent=2))
print("BATCH6_END")
