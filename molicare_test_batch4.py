import json,re
from scrapling.fetchers import Fetcher
P=[
(16,"168405",128,"form","5"),
(17,"168406",128,"form","6"),
(18,"168401",128,"men","6"),
(19,"168408",128,"form","8"),
(20,"168167",60,"plus","8")
]
S=[
("InCare Supports","https://incaresupports.com.au/products/molicare-premium-form-4-drops","shopify",[16,17,19,20]),
("LuxeMED 5D","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-form-5-drops","shopify",[16]),
("LuxeMED 6D","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-form-6-drops","shopify",[17]),
("LuxeMED Men","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-form-for-men-6-drops","shopify",[18]),
("LuxeMED 8D","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-form-8-drops","shopify",[19]),
("LuxeMED Plus","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-form-size-8-drops","shopify",[20]),
("Platinum 8D","https://www.platinumhealthsupply.com.au/products/molicare-premium-form-8-drops","shopify",[19]),
("Platinum Men","https://www.platinumhealthsupply.com.au/products/molicare-premium-form-for-men-6-drops","shopify",[18]),
("Platinum Plus","https://www.platinumhealthsupply.com.au/products/molicare-premium-plus-size-8-drops-1","shopify",[20]),
("Independence Australia 5D","https://store.independenceaustralia.com/molicare-premium-form-5-drops-1662-ml-15310056","independence",[16]),
("Independence Australia 6D","https://store.independenceaustralia.com/molicare-premium-form-6-drops-2353ml-15310270","independence",[17]),
("Dove Care","https://dovecaregroup.com.au/product/molicare-premium-form-6-drops-men/","html",[18]),
("BrightSky","https://brightsky.com.au/product/molicare-premium-form-plus-size-8-drops-carton-60/","html",[20]),
("Vital Medical Men","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/two-piece---shaped-pad/molicare-premium-form-6-drops-men-128s/","html",[18]),
("Vital Medical Plus","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/skin-care/skin-care/molicare-premium--size-8-drops-3s/","html",[20])
]
def fetch(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=25)
def txt(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def price(v):
 try:return round(int(v)/100,2)
 except:return None
def size_ok(n,label):
 label=label.lower()
 if n==60:return bool(re.search(r"60\s*(?:units|pieces)|3\s*(?:packs?|packets?)\s*(?:of)?\s*20|3\s*(?:packs?|packets?)\s*per\s*carton",label))
 return bool(re.search(r"128\s*(?:units|pieces)|4\s*(?:packs?|packets?)\s*(?:of)?\s*32|4\s*(?:packs?|packets?)\s*per\s*carton",label))
R=[]
for row,sku,n,kind,drops in P:
 for retailer,url,mode,rows in S:
  if row not in rows:continue
  r={"row":row,"sku":sku,"retailer":retailer,"url":url}
  try:
   page=fetch(url+(".js" if mode=="shopify" else ""))
   r["http_status"]=int(page.status)
   if r["http_status"]!=200:r["status"]="blocked";R.append(r);continue
   if mode=="shopify":
    data=page.json();title=str(data.get("title") or "").lower()
    if "molicare" not in title or (kind=="men" and "men" not in title) or (kind=="plus" and not any(k in title for k in ("plus","+size","size"))):
     r.update(status="family_mismatch",title=title);R.append(r);continue
    vs=[]
    for v in data.get("variants") or []:
     label=str(v.get("title") or "")+" "+str(v.get("option1") or "")
     vs_sku=str(v.get("sku") or "")
     sk=bool(re.search(r"(?<!\d)"+sku+r"(?!\d)",vs_sku))
     qt=size_ok(n,label)
     drops_ok=kind!="form" or drops in label or drops in title
     if sk and qt and drops_ok:vs.append(v)
    if len(vs)==1:
     v=vs[0];cur=price(v.get("price"));compare=price(v.get("compare_at_price"))
     r.update(status="success",matched_sku=v.get("sku"),variant=v.get("title"),price=compare if compare and cur and compare>cur else cur,special_price=cur if compare and cur and compare>cur else None,variant_url=url+"?variant="+str(v.get("id")))
    else:r.update(status="variant_unresolved",variants=[{"sku":v.get("sku"),"title":v.get("title"),"price":price(v.get("price"))} for v in (data.get("variants") or [])][:18])
   else:
    t=txt(page)
    if sku not in t:r["status"]="sku_not_visible"
    elif kind=="men" and "men" not in t.lower():r["status"]="gender_mismatch"
    elif not (str(n) in t and "molicare" in t.lower()):r["status"]="carton_unverified"
    elif mode=="independence":
     m=re.search(r"Carton\s+4\s+PKT\(s\)\s+\$\s*([0-9,]+(?:\.\d{2})?)",t,re.I)
     r.update(status="success" if m else "price_not_found",price=float(m.group(1).replace(",","")) if m else None,special_price=None)
    else:
     h=re.search(r"\$\s*([0-9,]+(?:\.\d{2})?)",t)
     r.update(status="review" if h else "price_not_found",price=float(h.group(1).replace(",","")) if h else None,special_price=None,excerpt=t[max(0,t.find(sku)-180):t.find(sku)+270])
  except Exception as e:r.update(status="error",error=type(e).__name__+": "+str(e))
  R.append(r)
print("BATCH4_START")
print(json.dumps(R,indent=2,ensure_ascii=False))
print("BATCH4_END")
