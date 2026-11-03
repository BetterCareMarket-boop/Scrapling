from __future__ import annotations
import json,re,html
from scrapling.fetchers import Fetcher
P=[
 dict(row=81,sku="915828",kind="men",size="Large",qty=28,pack=7),
 dict(row=82,sku="915877",kind="lady",size="Medium",qty=32,pack=8),
 dict(row=83,sku="915870",kind="lady",size="Large",qty=28,pack=7),
]
S=[
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-menpants-drop-7-large",[81]),
 ("Conticare","group","https://www.conticare.com.au/molicare-mens-premium-pants-male-pull-ups-large-7-drops-100-150cm-1412ml-915828-box-of-30.html",[81]),
 ("Oz Medical","shopify","https://ozmedical.com.au/products/molicare-premium-mens-pants",[81]),
 ("Oz Medical","shopify","https://ozmedical.com.au/products/molicare-premium-lady-pants-7-drops",[82,83]),
 ("Mobiquip","shopify","https://www.mobiquip.com.au/products/molicare-lady-pants",[82,83]),
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-lady-pants-7d-medium",[82,83]),
 ("Trugrade Medical","shopify","https://www.trugrademedical.com.au/products/molicare-lady-pants-7-drop",[82,83]),
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-ladypants-drop-7-medium",[82]),
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-ladypants-drop-7-large",[83]),
 ("Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/for-men/men/molicare-premium-men-pants-7-drops-l-4s/",[81])
]
def get(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def tx(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def skuok(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def cents(n):return round(int(n)/100,2) if n is not None else None
def shop(p,url,ret):
 pg=get(url+".js");st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 j=pg.json();title=str(j.get("title") or "")
 desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 variants=j.get("variants") or [];valid=[]
 if not "molicare" in title.lower() or not p["kind"] in title.lower():return dict(status="wrong_product",title=title)
 for v in variants:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  vs=str(v.get("sku") or "")
  if not skuok(p,vs):continue
  if not re.search(r"\b"+p["size"]+r"\b",label+" "+title,re.I):continue
  if not re.search(r"\b7\s*(?:drops?|d)\b",label+" "+title,re.I):continue
  if ret=="Mobiquip":
   quantity=bool(re.search(r"\b"+str(p["qty"])+r"\s*units?\b",label,re.I))
  elif ret=="Topcat Healthcare":
   quantity=bool(re.search(r"\bcarton\s*4\b",label,re.I)) and any(str(x.get("sku") or "")==p["sku"] and re.search(r"packet\s*"+str(p["pack"])+r"\b",str(x.get("title") or ""),re.I) for x in variants)
  else:
   quantity=bool(re.search(r"\b"+str(p["qty"])+r"\s*(?:units?|box|carton)\b|\b"+str(p["qty"])+r"\s*-\s*box|\bcarton(?:\s*of)?\s*4\s*[x×]\s*"+str(p["pack"])+r"\b|\b4\s*[x×]\s*"+str(p["pack"])+r"(?:pk)?\b",label,re.I))
  if not quantity:continue
  valid.append(v)
 if len(valid)!=1:return dict(status="unresolved",title=title,variants=[dict(title=v.get("title"),sku=v.get("sku"),price=cents(v.get("price"))) for v in variants][:16],description_excerpt=desc[:180])
 v=valid[0];cur=cents(v.get("price"));old=cents(v.get("compare_at_price"))
 return dict(status="success",price=old if old and old>cur else cur,special_price=cur if old and old>cur else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=url+"?variant="+str(v["id"]))
def group(p,url):
 pg=get(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=tx(pg)
 pat=r"Molicare Mens Premium Pants[^$]{0,210}915828\s*\(Box of 28\)\s*\$\s*([0-9,]+\.\d{2})"
 m=re.search(pat,t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0)[-270:]) if m else dict(status="unresolved",sku_visible=skuok(p,t))
def vital(p,url):
 pg=get(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=tx(pg)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s+Supplier Part\s+915828\s+Unit CAR\s+28",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,basis="inc GST") if m else dict(status="unresolved",sku_visible=skuok(p,t))
out=[]
for p in P:
 for ret,mode,url,rows in S:
  if p["row"] not in rows:continue
  try:r=shop(p,url,ret) if mode=="shopify" else group(p,url) if mode=="group" else vital(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=p["row"],sku=p["sku"],size=p["size"],carton=p["qty"],retailer=ret,url=url,**r))
print("BATCH17_START")
print(json.dumps(out,indent=2))
print("BATCH17_END")
