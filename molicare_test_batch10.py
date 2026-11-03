from __future__ import annotations
import json,re,html
from scrapling.fetchers import Fetcher
P=[
 {"row":46,"sku":"165371","size":"Small","drops":7,"qty":90,"per_pack":30},
 {"row":47,"sku":"165372","size":"Medium","drops":7,"qty":90,"per_pack":30},
 {"row":48,"sku":"165373","size":"Large","drops":7,"qty":90,"per_pack":30},
 {"row":49,"sku":"165471","size":"Small","drops":8,"qty":78,"per_pack":26},
 {"row":50,"sku":"165472","size":"Medium","drops":8,"qty":78,"per_pack":26},
]
S=[
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-elastic-7-drops",[46,47,48]),
 ("InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-elastic-8-drops",[49,50]),
 ("Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-elastic-7-drops-small",[46,47,48]),
 ("Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-premium-elastic-8-drops-medium",[49,50]),
 ("Surgical Direct","surgical","https://surgicaldirect.com.au/products/molicare-premium-elastic-7-drops/",[46,47,48]),
 ("Surgical Direct","surgical","https://surgicaldirect.com.au/products/molicare-premium-elastic-8-drops/",[49,50]),
 ("Conticare","conticare","https://www.conticare.com.au/molicare-premium-elastic-unisex-briefs-small-8-drops-2600ml-60-90cm-165471.html",[49]),
 ("Day & Night Healthcare","dnhc","https://www.dnhc.com.au/CONTINENCE/All_dash_In_dash_One/pl.php",[46,47,48,49,50]),
]
def get(u):return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=28)
def plain(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def sr(p,v):return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(v)))
def money(v):
 try:return round(int(v)/100,2)
 except:return None
def exactsize(p,s):
 return bool(re.search(r"(?<![a-z])"+p["size"].lower()+r"(?![a-z])",s.lower()))
def shopify(p,url,retailer):
 pg=get(url+".js")
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 d=pg.json();title=str(d.get("title") or "")
 if "molicare" not in title.lower() or "elastic" not in title.lower() or not re.search(r"\b"+str(p["drops"])+r"\s*drops?\b",title,re.I):return dict(status="wrong_product",title=title)
 desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(d.get("description") or ""))))
 size=p["size"];qty=p["qty"];each=p["per_pack"];packs=qty//each
 evidence=re.search(r"\b"+size+r"\s*\([^)]{0,35}\)\s*"+str(qty)+r"\s*\(\s*"+str(packs)+r"\s*[x×]\s*"+str(each)+r"\s*\)\s*per\s*carton",desc,re.I)
 matches=[]
 for v in d.get("variants") or []:
  code=str(v.get("sku") or "");lab=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  if not sr(p,code):continue
  if not exactsize(p,lab) and not (retailer=="Platinum Health Supply" and exactsize(p,title)):continue
  if retailer=="Platinum Health Supply":
   if not re.search(r"\b"+str(packs)+r"\s+packs?\s+per\s+carton\b",lab,re.I):continue
   packvariants=[v2 for v2 in d.get("variants") or [] if str(v2.get("sku") or "").startswith(p["sku"]) and re.search(r"\b"+str(each)+r"\s+units?\s+per\s+pack\b",str(v2.get("title") or ""),re.I)]
   if not packvariants:continue
  elif not evidence:continue
  matches.append(v)
 if len(matches)!=1:return dict(status="unresolved",description_evidence=desc[:700],variants=[dict(sku=v.get("sku"),title=v.get("title"),price=money(v.get("price"))) for v in (d.get("variants") or [])][:20])
 v=matches[0];cur=money(v.get("price"));comp=money(v.get("compare_at_price"))
 return dict(status="success",matched_sku=v.get("sku"),matched_variant=v.get("title"),price=comp if comp and cur and comp>cur else cur,special_price=cur if comp and cur and comp>cur else None,carton_evidence=evidence.group(0) if evidence else f"{packs} packs x {each} per pack",variant_url=url+"?variant="+str(v.get("id")))
def surgical(p,url):
 pg=get(url);tx=plain(pg)
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 pattern=rf"(?<!\d){p['sku']}\s+MoliCare Premium Elastic {p['drops']} Drops,\s*Size:\s*{p['size']},\s*Packaging:\s*Carton/{p['qty']}\s*\$\s*([0-9,]+(?:\.\d{{2}})?)"
 m=re.search(pattern,tx,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0),price_basis="GST Exempt") if m else dict(status="unresolved",sku_visible=p["sku"] in tx)
def conticare(p,url):
 pg=get(url);tx=plain(pg)
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 pat=rf"MoliCare Premium Elastic[^$]{{0,170}}\b{p['sku']}\s*\(Box of {p['qty']}\)\s*\$\s*([0-9,]+(?:\.\d{{2}})?)"
 m=re.search(pat,tx,re.I)
 if not m or not exactsize(p,m.group(0)) or not re.search(r"\b"+str(p["drops"])+r" drops",m.group(0),re.I):return dict(status="unresolved")
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0)[-260:])
def dnhc(p,url):
 pg=get(url);tx=plain(pg)
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 pat=rf"MoliCare Premium Elastic {p['size']} {p['drops']} drops {p['qty']}\s+Product Code:\s*{p['sku']}\s*\$\s*([0-9,]+(?:\.\d{{2}})?)\s*\(ex GST\)"
 m=re.search(pat,tx,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,price_basis="ex GST") if m else dict(status="unresolved")
results=[]
for p in P:
 for retailer,kind,url,rows in S:
  if p["row"] not in rows:continue
  try:
   r=shopify(p,url,retailer) if kind=="shopify" else surgical(p,url) if kind=="surgical" else conticare(p,url) if kind=="conticare" else dnhc(p,url)
  except Exception as e:r=dict(status="failed",error=type(e).__name__+": "+str(e))
  results.append(dict(row=p["row"],sku=p["sku"],product=f"MoliCare Premium Elastic {p['drops']} Drops {p['size']} Carton {p['qty']}",retailer=retailer,url=url,**r))
print("BATCH10_START")
print(json.dumps(results,indent=2,ensure_ascii=False))
print("BATCH10_END")
