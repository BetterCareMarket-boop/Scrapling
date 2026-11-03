from __future__ import annotations
import json,re,html
from scrapling.fetchers import Fetcher
P=[
 {"row":61,"sku":"947794","leg":"long","size":"XXL","count":25},
 {"row":62,"sku":"947711","leg":"short","size":"Small","count":25},
 {"row":63,"sku":"947712","leg":"short","size":"Medium","count":25},
 {"row":64,"sku":"947713","leg":"short","size":"Large","count":25},
 {"row":65,"sku":"947714","leg":"short","size":"XL","count":25},
]
S=[
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-fixpants-long-designed-to-hold-a-continence-pad-securely-in-place",[61]),
 ("Keeping Contained Care","shopify","https://keepingcontainedcare.com/products/molicare-premium-fixpants-long-leg",[61]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-fixpants-short-designed-to-hold-a-continence-pad-securely-in-place",[62,63,64,65]),
 ("LuxeMED","shopify","https://www.luxemed.com.au/collections/molicare/products/molicare-premium-fixpants-short-leg-small",[62,63,64,65]),
 ("Elora Medical","shopify","https://eloramedicalsupplies.com.au/products/molicare-premium-fixpants-short-leg-25-pack",[62,63,64,65]),
 ("Conticare","conticare","https://www.conticare.com.au/molicare-premium-fixpants-short-unisex-small-80-120cm-947711.html",[62]),
 ("Conticare","conticare","https://www.conticare.com.au/molicare-premium-fixpants-short-unisex-medium-60-100cm-947712.html",[63]),
 ("Conticare","conticare","https://www.conticare.com.au/molicare-premium-fixpants-short-unisex-large-80-120cm-947713-pack-of-25.html",[64]),
 ("Conticare","conticare","https://www.conticare.com.au/molicare-premium-fixpants-short-unisex-extra-large-90-125cm-947714.html",[65]),
 ("Independence Australia","independence","https://store.independenceaustralia.com/molicare-premium-fixpants-short-leg-small-waist-40-80cm-yellow-15310300",[62]),
 ("Dove Care","dove","https://dovecaregroup.com.au/product/molicare-premium-fixpants-small-unisex-short-leg/",[62]),
 ("Surgical House","surgical","https://surgicalhouse.com.au/Product-search-result.php?keyword=molicare+pad",[61,62,63,64,65]),
]
def get(url):return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=28)
def text(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def sku(p,s):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(s)))
def cost(v):
 try:return round(int(v)/100,2)
 except:return None
def size(p,s):
 s=s.lower().replace("extra large","xl").replace("x-large","xl").replace("xx-large","xxl").replace("xx large","xxl").replace("2xl","xxl")
 if p["size"]=="XXL":return bool(re.search(r"(?<![a-z])xxl(?![a-z])",s))
 if p["size"]=="XL":return bool(re.search(r"(?<![a-z])xl(?![a-z])",s)) and not bool(re.search(r"(?<![a-z])xxl(?![a-z])",s))
 return bool(re.search(r"(?<![a-z])"+p["size"].lower()+r"(?![a-z])",s))
def shopify(p,retailer,url):
 pg=get(url+".js");st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 j=pg.json();title=str(j.get("title") or "")
 if "molicare" not in title.lower() or "fixpants" not in title.lower() or p["leg"] not in title.lower():return dict(status="identity_unverified",title=title)
 description=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 variants=j.get("variants") or [];matches=[]
 for v in variants:
  vs=str(v.get("sku") or "");lab=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  if not sku(p,vs) or not size(p,lab):continue
  if retailer=="InCare Supports":pack=bool(re.search(r"pack\s*of\s*25|25\s*units?\s*per\s*pack",lab,re.I))
  elif retailer=="Keeping Contained Care":pack=bool(re.search(r"25\s*(?:pcs|pieces)|25\s*units?\s*per\s*pack|each\s*size\s*contains\s*25",title+" "+description,re.I))
  else:pack=bool(re.search(r"25\s*(?:units?|pcs|pieces)|pack\s*of\s*25|25\s*pack",title+" "+description+" "+lab,re.I)) and not bool(re.search(r"carton\s*(?:of\s*)?[2-9]\s*packs?",lab,re.I))
  if not pack:continue
  matches.append(v)
 if len(matches)!=1:return dict(status="unresolved",title=title,variants=[dict(sku=v.get("sku"),title=v.get("title"),price=cost(v.get("price"))) for v in variants][:20],description_excerpt=description[:200])
 v=matches[0];now=cost(v.get("price"));was=cost(v.get("compare_at_price"))
 return dict(status="success",price=was if was and now and was>now else now,special_price=now if was and now and was>now else None,matched_sku=v.get("sku"),variant=v.get("title"),variant_url=url+"?variant="+str(v.get("id")))
def conticare(p,url):
 pg=get(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 m=re.search(r"MoliCare Premium FixPants Short[^$]{0,220}"+p["sku"]+r"\s*\(Pack of 25\)\s*\$\s*([0-9,]+(?:\.\d{2})?)",t,re.I)
 if not m or not size(p,m.group(0)):return dict(status="unresolved",sku_visible=sku(p,t))
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0)[-225:])
def independence(p,url):
 pg=get(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 if not sku(p,t):return dict(status="identity_unverified")
 m=re.search(r"Carton\s+25\s+EA\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m else dict(status="unresolved")
def dove(p,url):
 pg=get(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 m=re.search(r"MoliCare Premium FixPants Small Unisex Short Leg\s+CTN\s*=\s*25\s*PIECES\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 if not m or not sku(p,t):return dict(status="unresolved")
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None)
def surgical(p,url):
 pg=get(url);st=int(pg.status)
 if st!=200:return dict(status="blocked",http_status=st)
 t=text(pg)
 leg="LONG LEG" if p["leg"]=="long" else "SHORT LEG"
 size_label={"Small":"SMALL","Medium":"MEDIUM","Large":"LARGE","XL":"X LARGE","XXL":"XX LARGE"}[p["size"]]
 m=re.search(r"MOLICARE PREMIUM FIXPANT "+leg+r"\s+"+size_label+r"\s*\(25\)\s*\["+p["sku"]+r"\][^$]{0,100}\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m else dict(status="unresolved",sku_visible=sku(p,t))
out=[]
for p in P:
 for retailer,kind,url,rows in S:
  if p["row"] not in rows:continue
  try:r=shopify(p,retailer,url) if kind=="shopify" else conticare(p,url) if kind=="conticare" else independence(p,url) if kind=="independence" else dove(p,url) if kind=="dove" else surgical(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  out.append(dict(row=p["row"],sku=p["sku"],leg=p["leg"],size=p["size"],pack=25,retailer=retailer,url=url,**r))
print("BATCH13_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH13_END")
