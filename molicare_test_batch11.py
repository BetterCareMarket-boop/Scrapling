from __future__ import annotations
import json,re,html
from scrapling.fetchers import Fetcher

PRODUCTS=[
 {"row":51,"sku":"165473","size":"Large","drops":8,"carton":72,"pack":24},
 {"row":52,"sku":"165571","size":"Small","drops":9,"carton":78,"pack":26},
 {"row":53,"sku":"165572","size":"Medium","drops":9,"carton":78,"pack":26},
 {"row":54,"sku":"165573","size":"Large","drops":9,"carton":72,"pack":24},
 {"row":55,"sku":"165671","size":"Small","drops":10,"carton":66,"pack":22}
]
SOURCES=[
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-elastic-8-drops",[51]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-elastic-9-drops",[52,53,54]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-elastic-10-drops",[55]),
 ("Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-elastic-8-drops-medium",[51]),
 ("Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-elastic-9-drops-small",[52,53,54]),
 ("Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-elastic-10-drops-small",[55]),
 ("mySupply Store","listing","https://mysupplystore.com.au/continence-products/disposable-pants-pads-liners/molicare-premium-elastic/",[51,52,53,54,55]),
 ("Conticare","group","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-large-8-drops-3095ml-115-150cm-165473.html",[51]),
 ("Sumac Medical Supplies","sumac","https://sumacms.com.au/product/molicare-premium-elastic-9-d-x-large-waist-140-175cm-unisex-3951ml-ctn/",[54]),
 ("Solmed","shopify","https://solmed.com.au/collections/new-arrivals/products/molicare-premium-elastic-10d-briefs",[55]),
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-elastic-9d-small",[52,53,54]),
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-elastic-10d-small",[55])
]
def fetch(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def tx(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def match_sku(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def norm(s):return s.lower().replace("extra large","xl").replace("x-large","xl")
def money(s):
 try:return round(int(s)/100,2)
 except:return None
def evidence(p,description):
 sz=p["size"];n=p["carton"];pack=p["pack"];mult=n//pack
 pattern=r"(?<![a-z])"+sz+r"\s*\([^)]{0,40}\)\s*"+str(n)+r"\s*\(\s*"+str(mult)+r"\s*[x×]\s*"+str(pack)+r"\s*\)\s*per\s*carton"
 m=re.search(pattern,description,re.I)
 return m.group(0) if m else None

def shopify(p,u,retailer):
 pg=fetch(u+".js")
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 j=pg.json();title=str(j.get("title") or "")
 if not ("molicare" in title.lower() and "elastic" in title.lower() and re.search(r"\b"+str(p["drops"])+r"\s*(?:drops?|d)\b",title,re.I)):
  return dict(status="wrong_product",title=title)
 variants=j.get("variants") or []
 description=re.sub(r"\s+"," ",re.sub(r"<[^>]*>"," ",html.unescape(str(j.get("description") or ""))))
 desc_evidence=evidence(p,description)
 matches=[]
 for v in variants:
  sku=str(v.get("sku") or ""); label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  if not match_sku(p,sku):continue
  if not re.search(r"(?<![a-z])"+p["size"]+r"(?![a-z])",norm(label),re.I) and not re.search(r"(?<![a-z])"+p["size"]+r"(?![a-z])",norm(title),re.I):continue
  carton_title=bool(re.search(r"carton|case|box",label,re.I))
  if retailer=="InCare Supports":
   if not desc_evidence:continue
  elif carton_title:
   # Need carton-quantity corroboration, not just carton word
   multiples=bool(re.search(r"\b"+str(p["carton"])+r"\b",label)) or (
      bool(re.search(r"\b"+str(p["carton"]//p["pack"])+r"\s*pack",label,re.I))
      and bool(re.search(r"\b"+str(p["pack"])+r"\s*(?:units?|pieces?)\s*per\s*pack",description+" "+json.dumps(variants),re.I))
   )
   if not multiples:continue
  else:continue
  matches.append(v)
 if len(matches)!=1:
  return dict(status="unresolved",title=title,description_excerpt=description[:520],variants=[dict(title=v.get("title"),sku=v.get("sku"),price=money(v.get("price"))) for v in variants][:20])
 v=matches[0];val=money(v.get("price"));old=money(v.get("compare_at_price"))
 return dict(status="success",price=old if old and val and old>val else val,special_price=val if old and val and old>val else None,matched_sku=v.get("sku"),matched_variant=v.get("title"),carton_evidence=desc_evidence or str(p["carton"]),variant_url=u+"?variant="+str(v["id"]))
def listing(p,u):
 pg=fetch(u);status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 s=tx(pg);size=p["size"].upper()
 pattern=rf"MOLICARE PREMIUM ELASTIC\s+{p['drops']}D\s+{size}\b[^$]{{0,210}}CARTON\s+{p['carton']}\s*-\s*({p['sku']}\d*)\s*\$\s*([0-9,]+(?:\.\d{{2}})?)"
 m=re.search(pattern,s,re.I)
 if not m:return dict(status="unresolved",sku_visible=p["sku"] in s)
 return dict(status="success",price=float(m.group(2).replace(",","")),special_price=None,matched_sku=m.group(1),matched_excerpt=m.group(0))
def group(p,u):
 pg=fetch(u);status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 s=tx(pg)
 pattern=rf"MoliCare Premium Elastic[^$]{{0,180}}\b{p['sku']}\s*\(Box of {p['carton']}\)\s*\$\s*([0-9,]+(?:\.\d{{2}})?)"
 m=re.search(pattern,s,re.I)
 if not m or p["size"].lower() not in m.group(0).lower() or str(p["drops"])+" Drops" not in m.group(0):return dict(status="unresolved")
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0))
def sumac(p,u):
 pg=fetch(u);status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 s=tx(pg)
 if not (p["sku"] in s and "CTN/72" in s.upper() and "Large 9 drops" in s):return dict(status="identity_unverified")
 m=re.search(r"\$\s*([0-9,]+(?:\.\d{2})?)",s)
 return dict(status="review" if m else "unresolved",price=float(m.group(1).replace(",","")) if m else None)
out=[]
for p in PRODUCTS:
 for retailer,mode,url,rows in SOURCES:
  if p["row"] not in rows:continue
  try:r=shopify(p,url,retailer) if mode=="shopify" else listing(p,url) if mode=="listing" else group(p,url) if mode=="group" else sumac(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=p["row"],sku=p["sku"],size=p["size"],drops=p["drops"],carton=p["carton"],retailer=retailer,url=url,**r))
print("BATCH11_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH11_END")
