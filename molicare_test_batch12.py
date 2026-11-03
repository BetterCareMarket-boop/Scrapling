from __future__ import annotations
import json,re,html
from scrapling.fetchers import Fetcher
PRODUCTS=[
 dict(row=56,sku="165672",name="MoliCare Premium Elastic 10 Drops Medium carton 56",size="Medium",count=56,kind="elastic"),
 dict(row=57,sku="947790",name="MoliCare Premium FixPants Long Small pack 25",size="Small",count=25,kind="fixpants"),
 dict(row=58,sku="947791",name="MoliCare Premium FixPants Long Medium pack 25",size="Medium",count=25,kind="fixpants"),
 dict(row=59,sku="947792",name="MoliCare Premium FixPants Long Large pack 25",size="Large",count=25,kind="fixpants"),
 dict(row=60,sku="947793",name="MoliCare Premium FixPants Long XL pack 25",size="XL",count=25,kind="fixpants")]
SOURCES=[
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-elastic-10-drops",[56]),
 ("Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-elastic-10-drops-medium",[56]),
 ("Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-premium-elastic10-medium",[56]),
 ("Independence Australia","independence","https://store.independenceaustralia.com/molicare-premium-elastic-10-d-slip-medium-waist-85-120cm-2800ml-15310096",[56]),
 ("Tan Pharmaceuticals","tan","https://www.tanpharm.com.au/165672/MOLICARE-ELASTIC-10D-MED14-CN4/pd.php",[56]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-fixpants-long-designed-to-hold-a-continence-pad-securely-in-place",[57,58,59,60]),
 ("Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-premium-fixpants-long-leg",[57,58,59,60]),
 ("Keeping Contained Care","shopify","https://keepingcontainedcare.com/products/molicare-premium-fixpants-long-leg",[57,58,59,60]),
 ("Surgical House","surgical","https://surgicalhouse.com.au/Product-search-result.php?keyword=molicare+pad",[57,58,59,60]),
]
def fetch(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def tx(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def cents(v):
 try:return round(int(v)/100,2)
 except:return None
def skuok(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def sizeok(p,s):
 z=s.lower().replace("extra large","xl").replace("x-large","xl").replace("x large","xl")
 name=p["size"].lower()
 if name=="xl":return bool(re.search(r"(?<![a-z])xl(?![a-z])",z))
 return bool(re.search(r"(?<![a-z])"+name+r"(?![a-z])",z))
def shopify(p,url,retailer):
 pg=fetch(url+".js");st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 j=pg.json();title=str(j.get("title") or "");description=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 if not ("molicare" in title.lower() and (("elastic" in title.lower() and "10" in title) if p["kind"]=="elastic" else ("fixpants" in title.lower() and "long" in title.lower()))):return dict(status="product_mismatch",title=title)
 variants=j.get("variants") or []
 valid=[]
 for v in variants:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  sku=str(v.get("sku") or "")
  if not skuok(p,sku):continue
  if not (sizeok(p,label) or (len(variants)<=2 and sizeok(p,title))):continue
  if p["kind"]=="elastic":
   carton=bool(re.search(r"\b4\s+packs?\s+per\s+carton\b|\bcarton\s*4\b|\b56\s*(?:units|pieces)\b",label,re.I))
   if retailer=="InCare Supports":carton=bool(re.search(r"Medium\s*\([^)]{0,40}\)\s*56\s*\(\s*4\s*x\s*14\s*\)\s*per\s*carton",description,re.I))
   if retailer=="Platinum Health Supply":
    carton=bool(re.search(r"4\s+packs?\s+per\s+carton",label,re.I) and any(re.search(r"14\s+units?\s+per\s+pack",str(x.get("title") or ""),re.I) for x in variants))
   if retailer=="Topcat Healthcare":
    carton=bool(re.search(r"carton\s*4\b",label,re.I) and re.search(r"packet\s*14\b",json.dumps(variants),re.I))
  else:
   carton=bool(re.search(r"\b25\s*(?:pcs|pieces|units?)\b|\bpack\s*(?:of\s*)?25\b",label+" "+title+" "+description,re.I))
   if retailer=="Keeping Contained Care" and re.search(r"carton\s*5",label,re.I):carton=False
  if carton:valid.append(v)
 if len(valid)!=1:return dict(status="unresolved",title=title,variants=[dict(sku=v.get("sku"),title=v.get("title"),price=cents(v.get("price")),compare_at=cents(v.get("compare_at_price"))) for v in variants][:25],desc=description[:250])
 v=valid[0];cur=cents(v.get("price"));comp=cents(v.get("compare_at_price"))
 return dict(status="success",price=comp if comp and cur and comp>cur else cur,special_price=cur if comp and cur and comp>cur else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=url+"?variant="+str(v.get("id")))
def independence(p,url):
 pg=fetch(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=tx(pg)
 if not skuok(p,t) or "14 Units" not in t:return dict(status="identity_unverified")
 m=re.search(r"Carton\s+4\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m else dict(status="price_unresolved")
def tan(p,url):
 pg=fetch(url);st=int(pg.status);t=tx(pg)
 if st!=200:return dict(status="blocked",http_status=st)
 if not (skuok(p,t) and "4 packets of 14" in t.lower()):return dict(status="identity_unverified")
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*\(Ex GST\)",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,tax="ex GST") if m else dict(status="price_unresolved")
def surgical(p,url):
 pg=fetch(url);st=int(pg.status);t=tx(pg)
 if st!=200:return dict(status="blocked",http_status=st)
 pat=r"MOLICARE PREMIUM FIXPANT LONG LEG\s+"+("X LARGE" if p["size"]=="XL" else p["size"].upper())+r"\s*\(25\)\s*\["+p["sku"]+r"\][^$]{0,100}\$\s*([0-9,]+\.\d{2})"
 m=re.search(pat,t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,tax="GST free") if m else dict(status="unresolved",sku_visible=p["sku"] in t)
out=[]
for p in PRODUCTS:
 for retailer,mode,url,rows in SOURCES:
  if p["row"] not in rows:continue
  try:r=shopify(p,url,retailer) if mode=="shopify" else independence(p,url) if mode=="independence" else tan(p,url) if mode=="tan" else surgical(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=p["row"],name=p["name"],sku=p["sku"],retailer=retailer,url=url,**r))
print("BATCH12_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH12_END")
