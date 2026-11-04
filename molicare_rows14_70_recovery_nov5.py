from __future__ import annotations
import concurrent.futures,re,json,html
from scrapling.fetchers import Fetcher
S=[
(14,"168100",336,"Assist Ability","shopify","https://shop.assistabilityaustralia.com.au/products/molicare-pad-2d-p28-c12"),
(14,"168100",336,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-pad-2-drops"),
(14,"168100",336,"Dove Care","dove","https://dovecaregroup.com.au/product/molicare-pad-2-drops/"),
(14,"168100",336,"Ability Warehouse","shopify","https://abilitywarehouse.com.au/products/molicare-pads"),
(14,"168100",336,"HomeHealth Medical Supplies","home","https://hhmedicalsupplies.com.au/product/molicare-pad-2-drops-pack-28-2/"),
(70,"169248",120,"House of Nappies","house","https://www.houseofnappies.com.au/molicare-premium-slip-extra-plus-6d-extra-small-40~199"),
(70,"169248",120,"Assist Ability","shopify","https://shop.assistabilityaustralia.com.au/products/molicare-prem-extra-plus-xsml-p30-c4"),
(70,"169248",120,"AMH Community","shopify","https://www.amhcommunity.com.au/products/molicare-premium-slip"),
(70,"169248",120,"Mediply Plus","shopify","https://mediplyplus.com.au/products/molicare-slip-extra-plus-xs-6-drops"),
(70,"169248",120,"InCare Supports","shopify","https://incaresupports.com.au/products/molicare-slip-6-drops-xs"),
]
def fetch(u):
 return Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
def text(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def cents(v):
 try:return (int(v)/100) if isinstance(v,int) else float(v)
 except:return None
def scann(t,pg):
 row,sku,qty,ret,kind,url=t;r=dict(row=row,sku=sku,qty=qty,retailer=ret,url=url)
 if kind=="shopify":
  d=pg.json();title=str(d.get("title") or "")
  desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(d.get("description") or ""))))
  variants=d.get("variants") or [];found=[]
  for v in variants:
   vsku=str(v.get("sku") or "");label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
   if row==14:
    identity="molicare" in title.lower() and "pad" in title.lower() and re.search(r"\b2\s*drops?\b",title+" "+label,re.I) and "men" not in title.lower() and "lady" not in title.lower()
    qty_ok=bool(re.search(r"\b336\b|\bcarton\b.{0,15}\b12\b|\b12\s*packs?\s*per\s*carton\b|\b12\s*[x×]\s*28\b",label,re.I))
    pack_ok=bool(re.search(r"\b28\s*units?\s*per\s*pack\b|\b28\s*per\s*pack\b|\b12\s*[x×]\s*28\b",label+" "+desc+" "+json.dumps([str(x.get("title")) for x in variants]),re.I))
    if qty_ok and "12" in label and not pack_ok:qty_ok=False
   else:
    identity="molicare" in title.lower() and "slip" in title.lower() and (re.search(r"6\s*(?:drops?|d)\b",title+" "+label,re.I) is not None) and (re.search(r"\bXS\b|x\s*-?\s*small|extra\s*small",title+" "+label,re.I) is not None)
    qty_ok=bool(re.search(r"\b120\b|\bcarton\b.{0,12}\b4\b|\b4\s*[x×]\s*30\b|\b4\s*packs?\s*per\s*carton\b",label,re.I))
    pack_ok=bool(re.search(r"30\s*(?:units?|pieces?)\s*per\s*pack|30\s*disposable|pack\s*of\s*30|\b4\s*[x×]\s*30\b",label+" "+desc+" "+json.dumps([str(x.get("title")) for x in variants]),re.I))
    if "4" in label and not pack_ok:qty_ok=False
   if identity and qty_ok:found.append(v)
  if len(found)!=1:
   r.update(status="unresolved",title=title,desc=desc[:100],variants=[dict(sku=v.get("sku"),title=v.get("title"),price=cents(v.get("price")),old=cents(v.get("compare_at_price"))) for v in variants[:15]])
   return r
  v=found[0];cur=cents(v.get("price"));old=cents(v.get("compare_at_price"))
  if cur is None or cur<=0:return dict(r,status="price_error",variant=v.get("title"))
  r.update(status="success",price=old if old and old>cur else cur,special_price=cur if old and old>cur else None,variant=v.get("title"),matched_sku=v.get("sku"),url=url+"?variant="+str(v.get("id")),available=v.get("available"))
  return r
 tx=text(pg)
 if kind=="dove":
  m=re.search(r"CTN\s*=\s*336\s*PIECES\s*\$\s*([0-9,]+\.\d{2})",tx,re.I)
  good="molicare pad 2 drops" in tx.lower()
 elif kind=="home":
  m=re.search(r"PKT\s*28\s*Units\s*\$\s*[0-9,]+\.\d{2}.{0,120}?Carton\s*12\s*Pkt\(s\)\s*\$\s*([0-9,]+\.\d{2})",tx,re.I)
  good="168100" in tx and "MoliCare Pad 2 drops" in tx
 else:
  m=re.search(r"\$\s*([0-9,]+\.\d{2})",tx)
  good="169248C" in tx and "120" in tx and "6D" in tx and "Extra Small" in tx
 if m and good:r.update(status="success",price=float(m[1].replace(",","")),special_price=None,quantity_evidence=tx[max(0,tx.find("336" if row==14 else "169248C")-80):tx.find("336" if row==14 else "169248C")+120])
 else:r.update(status="unresolved",excerpt=tx[:350])
 return r
def go(t):
 *_,kind,url=t
 r=dict(row=t[0],retailer=t[3],url=url)
 try:
  pg=fetch(url+(".js" if kind=="shopify" else ""))
  st=int(pg.status)
  if st!=200:return dict(r,status="blocked",http_status=st)
  return scann(t,pg)
 except Exception as e:return dict(r,status="error",error=type(e).__name__+": "+str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:out=list(ex.map(go,S))
print("TARGET_MORE_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("TARGET_MORE_END")
