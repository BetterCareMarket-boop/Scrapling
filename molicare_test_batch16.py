from __future__ import annotations
import json,re,html
from scrapling.fetchers import Fetcher
P=[
 dict(row=76,sku="995089",name="MoliCare Skin Wash Lotion 500ml",family="lotion",qty=12),
 dict(row=77,sku="995087",name="MoliCare Skin Protection Foam 100ml",family="foam",qty=12),
 dict(row=78,sku="168076",name="MoliCare Pad 3 Drops",family="pad",qty=180),
 dict(row=79,sku="947789",name="MoliCare Premium FixPants Long XXX-Large",family="fix",qty=25),
 dict(row=80,sku="915827",name="MoliCare Premium Men Pants 7 Drops Medium",family="men",qty=32)]
S=[
 (76,"Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-skin-washlotion"),
 (76,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-skin-wash-lotion-500ml"),
 (76,"Independence Australia","ind","https://store.independenceaustralia.com/molicare-skin-wash-lotion-500ml-24310101"),
 (76,"Surgical House","surgical","https://surgicalhouse.com.au/Product.php?id=995089"),
 (76,"LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-skin-wash-lotion-500ml-995089"),
 (77,"Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-skin-protectionfoam"),
 (77,"Independence Australia","ind","https://store.independenceaustralia.com/menalind-molicare-skin-skin-protection-foam-100ml-24310420"),
 (77,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-skin-protection-foam-100ml"),
 (77,"Disposable Medical Supplies","shopify","https://disposablemedicalsupplies.com.au/products/molicare-skin-protection-foam-100ml"),
 (78,"Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-pad-drop-3"),
 (78,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-pad-3-drops-30pcs"),
 (78,"Independence Australia","ind","https://store.independenceaustralia.com/molicare-pad-3-d-330x130mm-unisex-481ml-15310008"),
 (79,"Keeping Contained Care","shopify","https://keepingcontainedcare.com/products/molicare-premium-fixpants-long-leg"),
 (79,"Conticare","conticare","https://www.conticare.com.au/molicare-premium-fixpants-long-unisex-xxx-large-160-200cm-947789.html"),
 (79,"Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/fixation-pants/fixation-pants/molicare-prem-fix-pant-sht-leg-xxxl-25s/"),
 (79,"LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-fixpants-long-leg-small"),
 (79,"InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-fixpants-long-designed-to-hold-a-continence-pad-securely-in-place"),
 (80,"Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-menpants-drop-7-medium"),
 (80,"LuxeMED","shopify","https://www.luxemed.com.au/products/molicare-premium-men-pants-7d-medium"),
 (80,"Conticare","conticare","https://www.conticare.com.au/molicare-premium-mens-pants-medium-85-120cm-7-drops-1455ml-box-of-33.html"),
 (80,"Dove Care","dove","https://dovecaregroup.com.au/product/molicare-premium-men-pants-medium-7-drops/"),
 (80,"Tassway","tassway","https://www.tassway.com.au/product/molicare-premium-men-pants-7-drops/")
]
def fetch(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def text(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def c(v):
 try:return round(int(v)/100,2)
 except:return None
def sku(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def shopify(p,url):
 pg=fetch(url+".js");st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 j=pg.json();title=str(j.get("title") or "")
 desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 vs=j.get("variants") or []
 identity={"lotion":["wash","lotion"],"foam":["protection","foam"],"pad":["pad","3"],"fix":["fixpants","long"],"men":["men","pants","7"]}[p["family"]]
 if not ("molicare" in title.lower() and all(k in title.lower() for k in identity)):return dict(status="wrong_product",title=title)
 candidates=[]
 for v in vs:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  code=str(v.get("sku") or "")
  if not sku(p,code):continue
  if p["family"]=="fix":
   if not re.search(r"(?<![a-z])(?:xxx-large|xxxlarge|3xl|xxxl)(?![a-z])",label,re.I):continue
   quantity=bool(re.search(r"25\s*(?:units?|pieces?|pcs)|pack\s*of\s*25",label+" "+title+" "+desc,re.I)) and not re.search(r"carton\s*(?:of\s*)?[2-9]\s*packs?",label,re.I)
  elif p["family"]=="men":
   if not re.search(r"medium",label,re.I):continue
   quantity=bool(re.search(r"carton\s*\(?32\)?|carton\s*4|4\s*[x×]\s*8|32\s*units?",label,re.I))
  elif p["family"]=="pad":quantity=bool(re.search(r"carton\s*6|6\s*packs?\s*per\s*carton|180\s*(?:units?|pads?)",label,re.I)) and bool(re.search(r"30\s*(?:units?|pads?|pieces?)\s*per\s*pack|packet\s*30|30\s*pcs|30\s*pieces|pack\s*of\s*30",desc+" "+json.dumps(vs),re.I))
  else:quantity=bool(re.search(r"carton\s*\(?12|12\s*(?:units?|bottles?|cans?)\s*per\s*carton|12\s*units?\s*per\s*carton",label,re.I))
  if quantity:candidates.append(v)
 if len(candidates)!=1:return dict(status="variant_unresolved",title=title,variants=[dict(title=v.get("title"),sku=v.get("sku"),price=c(v.get("price")),compare_at=c(v.get("compare_at_price"))) for v in vs][:24],desc_excerpt=desc[:260])
 v=candidates[0];cur=c(v.get("price"));was=c(v.get("compare_at_price"))
 return dict(status="success",price=was if was and cur and was>cur else cur,special_price=cur if was and cur and was>cur else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=url+"?variant="+str(v["id"]))
def ind(p,url):
 pg=fetch(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 if not sku(p,t) and not(p["family"]=="foam" and "995025/995087" in t):return dict(status="identity_unverified")
 if p["family"]=="pad":pattern=r"PKT\s+30\s+Units.*?Carton\s+6\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})"
 else:pattern=r"Carton\s+12\s+EA\(s\)\s*\$\s*([0-9,]+\.\d{2})"
 m=re.search(pattern,t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0)[-140:]) if m else dict(status="carton_price_unresolved")
def surgical(p,url):
 pg=fetch(url);st=int(pg.status);t=text(pg)
 if st!=200:return dict(status="blocked",http_status=st)
 if not sku(p,t):return dict(status="sku_unverified")
 m=re.search(r"EA\s+CT\s+12\.00\s+([0-9,]+\.\d{2})\s+([0-9,]+\.\d{2})",t)
 return dict(status="success",price=float(m.group(2).replace(",","")),special_price=None,price_basis="inc GST",matched_excerpt=m.group(0)) if m else dict(status="carton_price_unresolved")
def conticare(p,url):
 pg=fetch(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 if p["family"]=="fix":pattern=r"MoliCare Premium FixPants Long[^$]{0,200}947789\s*\(Pack of 25\)\s*\$\s*([0-9,]+\.\d{2})"
 else:pattern=r"Molicare Premium Mens Pants Medium[^$]{0,200}915827\s*\(Box of 32\)\s*\$\s*([0-9,]+\.\d{2})"
 m=re.search(pattern,t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0)[-230:]) if m else dict(status="price_unresolved")
def vital(p,url):
 pg=fetch(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s+inc GST\s+Supplier Part\s+947789\s+Unit PAC\s+25",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,price_basis="inc GST") if m else dict(status="unresolved")
def dove(p,url):
 pg=fetch(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 m=re.search(r"CTN\s*=\s*32\s*PIECES\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m and sku(p,t) else dict(status="unresolved")
def tassway(p,url):
 pg=fetch(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 return dict(status="variant_unresolved")
out=[]
for p in P:
 for row,retailer,kind,url in S:
  if row!=p["row"]:continue
  try:r=shopify(p,url) if kind=="shopify" else ind(p,url) if kind=="ind" else surgical(p,url) if kind=="surgical" else conticare(p,url) if kind=="conticare" else vital(p,url) if kind=="vital" else dove(p,url) if kind=="dove" else tassway(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=row,sku=p["sku"],name=p["name"],quantity=p["qty"],retailer=retailer,url=url,**r))
print("BATCH16_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH16_END")
