from __future__ import annotations
import re,json,html
from scrapling.fetchers import Fetcher
P=[
 {"row":71,"sku":"995016","family":"foam","size":"","qty":12,"drops":0},
 {"row":72,"sku":"915867","family":"lady","size":"Medium","qty":64,"drops":5},
 {"row":73,"sku":"915868","family":"lady","size":"Large","qty":56,"drops":5},
 {"row":74,"sku":"915817","family":"men","size":"Medium","qty":32,"drops":5},
 {"row":75,"sku":"915818","family":"men","size":"Large","qty":28,"drops":5}
]
S=[
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-skin-cleansingfoam",[71]),
 ("Mobiquip","shopify","https://www.mobiquip.com.au/products/molicare-lady-pants",[72,73]),
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-menpants-drop-5-medium",[74]),
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-menpants-drop-5-large",[75]),
 ("AMH Community","shopify","https://www.amhcommunity.com.au/products/molicare-premium-men-pants-5-drops-medium",[74]),
 ("AMH Community","shopify","https://www.amhcommunity.com.au/products/molicare-premium-men-pants-5-drops-large",[75]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-men-pants-5-drops-m",[74,75]),
 ("Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/for-men/men/molicare-premium-men-pants-5-drops-l-4s/",[75]),
 ("Independence Australia","ind","https://store.independenceaustralia.com/molicare-premium-men-pants-medium-medium-970ml-15310452",[74]),
 ("Trugrade Medical","shopify","https://www.trugrademedical.com.au/products/molicare-mens-pants-5-drop",[74,75]),
]
def get(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def txt(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def codeok(p,s):
 return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def cnt(x):return int(x)/100 if x is not None else None
def samesize(p,s):return not p["size"] or bool(re.search(r"\b"+p["size"]+r"\b",s,re.I))
def shopify(p,u,retailer):
 pg=get(u+".js");http=int(pg.status)
 if http!=200:return dict(status="blocked",http_status=http)
 j=pg.json();title=str(j.get("title") or "")
 desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 if "molicare" not in title.lower() or not any(k in title.lower() for k in {"foam":["foam"],"lady":["lady"],"men":["men"]}[p["family"]]):return dict(status="wrong_product",title=title)
 variants=j.get("variants") or [];valid=[]
 for v in variants:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  sku=str(v.get("sku") or "")
  if not codeok(p,sku):continue
  if not samesize(p,label+" "+title):continue
  if p["drops"] and not re.search(r"\b5\s*(?:d|drops)\b",label+" "+title,re.I):continue
  if retailer=="InCare Supports":
   q=re.search(r"\b"+str(p["qty"])+r"\s*\(\s*4\s*x\s*(?:8|7)\s*\)\s*per\s*carton",desc,re.I)
   if not q:continue
  elif retailer=="Mobiquip":
   if not re.search(r"\b"+str(p["qty"])+r"\s*units\b",label,re.I):continue
  elif retailer=="Topcat Healthcare":
   if p["family"]=="foam":vqty=bool(re.search(r"carton\s*12",label,re.I))
   else:vqty=bool(re.search(r"carton\s*4",label,re.I)) and bool(re.search(r"packet\s*"+str(p["qty"]//4),json.dumps(variants),re.I))
   if not vqty:continue
  elif retailer=="AMH Community":
   if not re.search(r"carton\s*of\s*"+str(p["qty"]),label,re.I):continue
  elif retailer=="Trugrade Medical":
   if not re.search(r"carton|ctn",label+" "+sku,re.I) or not re.search(r"carton\s*of\s*"+str(p["qty"])+"|"+str(p["qty"])+r"\s*units",desc+" "+label,re.I):continue
  valid.append(v)
 if len(valid)!=1:return dict(status="unresolved",title=title,variants=[dict(title=v.get("title"),sku=v.get("sku"),price=cnt(v.get("price"))) for v in variants][:18],desc=desc[:230])
 v=valid[0];cur=cnt(v.get("price"));compare=cnt(v.get("compare_at_price"))
 return dict(status="success",matched_sku=v.get("sku"),variant=v.get("title"),price=compare if compare and compare>cur else cur,special_price=cur if compare and compare>cur else None,variant_url=u+"?variant="+str(v.get("id")))
def vital(p,u):
 pg=get(u);http=int(pg.status)
 if http!=200:return dict(status="blocked",http_status=http)
 t=txt(pg)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s+Supplier Part\s+"+p["sku"]+r"\s+Unit CAR\s+"+str(p["qty"]),t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,basis="inc GST") if m else dict(status="unresolved",sku_visible=codeok(p,t))
def indep(p,u):
 pg=get(u);http=int(pg.status)
 if http!=200:return dict(status="blocked",http_status=http)
 t=txt(pg)
 if not re.search(r"Supplier Part Number:\s*9158170",t,re.I):return dict(status="identity_unverified")
 m=re.search(r"Carton\s+4\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,source_sku="9158170") if m else dict(status="unresolved")
out=[]
for p in P:
 for retailer,kind,url,rows in S:
  if p["row"] not in rows:continue
  try:r=shopify(p,url,retailer) if kind=="shopify" else vital(p,url) if kind=="vital" else indep(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=p["row"],sku=p["sku"],retailer=retailer,url=url,**r))
print("BATCH15_RECOVERY_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH15_RECOVERY_END")
