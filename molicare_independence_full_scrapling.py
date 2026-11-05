from __future__ import annotations
import re,json,concurrent.futures,time
from scrapling.fetchers import Fetcher
ROOT="https://store.independenceaustralia.com"
TARGET_QTY={"915840":56,"915831":56,"166014":42,"166015":56,"915834":56,"166029":56,"166030":42,"166031":56,"915874":56,"166041":42,"166042":56,"915880":56,"168100":336,"168077":270,"168404":128,"168405":128,"168406":128,"168401":128,"168408":128,"168409":64,"168132":192,"168044":216,"168045":144,"168046":168,"168051":168,"168600":168,"168705":168,"168801":168,"168066":168,"168407":128,"915861":56,"166000":42,"166001":56,"915854":56,"161065":120,"161070":100,"161061":180,"165271":90,"165272":90,"165273":90,"165274":56,"165374":56,"165474":56,"165574":56,"165371":90,"165372":90,"165373":90,"165471":78,"165472":78,"165473":72,"165571":78,"165572":78,"165573":72,"165671":66,"165672":56,"947790":25,"947791":25,"947792":25,"947793":25,"947794":25,"947711":25,"947712":25,"947713":25,"947714":25,"947715":25,"165531":56,"165532":56,"165533":56,"169248":120,"916680":32,"995086":12,"CTN13064":12,"CTN13072":12,"995016":12,"915867":64,"915868":56,"915817":32,"915818":28,"CTN13069":12,"995087":12,"168076":180,"947789":25,"165531-1":14,"915827":32,"166093":28,"915877":32,"915870":28,"168519":54,"165435":56,"169111":150}
SKU_ALIAS={"168035":"168132","168075":"168100","995088":"CTN13064","995075":"CTN13072","995089":"CTN13069","915828":"166093"}
def fetch(url):
 return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
def txt(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except Exception:return ""
def urlpage(p):
 u=[]
 for n in p.css('a[href]'):
  href=n.attrib.get("href","")
  label=n.get_all_text(strip=True)
  if href.startswith(ROOT+"/") and "molicare" in (href+label).lower() and not "catalogsearch" in href.lower() and "javascript:" not in href:
   u.append(href.split("?")[0])
 return list(dict.fromkeys(u))
all_urls=[];pages=[]
for i in range(1,8):
 u=f"{ROOT}/catalogsearch/result/?q=molicare&p={i}"
 try:
  p=fetch(u);h=urlpage(p) if int(p.status)==200 else []
  pages.append({"page":i,"status":int(p.status),"links":len(h),"examples":h[:3]})
  for x in h:
   if x not in all_urls:all_urls.append(x)
 except Exception as e:pages.append({"page":i,"error":str(e)[:130]})
 if i<7:time.sleep(8)
def getone(url):
 try:
  p=fetch(url);status=int(p.status)
  if status!=200:return dict(url=url,status="blocked",http=status)
  text=txt(p)
  m=re.search(r"Supplier Part Number:\s*([a-zA-Z0-9/\-]+)",text,re.I)
  if not m:return dict(url=url,status="no_sku",head=text[:180])
  supplier=m.group(1).strip()
  target=supplier if supplier in TARGET_QTY else SKU_ALIAS.get(supplier)
  if not target and len(supplier)>6:
   for sku in TARGET_QTY:
    if supplier.startswith(sku) and len(supplier)<=len(sku)+2 and sku.startswith("947"):
     target=sku;break
  if not target:return dict(url=url,status="not_target",sku=supplier)
  snippet=text[m.end():m.end()+780]
  # The store supports pack-level and carton-level ordering.
  # Extract the *published* carton price, never compute it from packet price.
  mpack=re.search(r"\b(PKT|EA|BOX)\s+(\d+)\s+Units?\s*\$\s*([0-9,]+\.\d{2})",snippet,re.I)
  mctn=re.search(r"\bCarton\s+(\d+)\s+(PKT\(s\)|EA\(s\)|BOX\(s\))\s*\$\s*([0-9,]+\.\d{2})",snippet,re.I)
  if not mctn:return dict(url=url,status="no_carton",sku=supplier,target=target,snippet=snippet[:230])
  carton_n=int(mctn.group(1));kind=mctn.group(2).lower()
  if kind.startswith("ea"):
   unit_count=carton_n
  elif mpack:
   unit_count=int(mpack.group(2))*carton_n
  else:
   return dict(url=url,status="no_pack_qty",sku=supplier,target=target,snippet=snippet[:260])
  required=TARGET_QTY[target]
  if unit_count!=required:return dict(url=url,status="qty_mismatch",sku=supplier,target=target,got=unit_count,expected=required,ctn=str(mctn.group(0)),packet=str(mpack.group(0)) if mpack else None)
  price=float(mctn.group(3).replace(",",""))
  if price<=0:return dict(url=url,status="invalid_price",sku=supplier)
  return dict(url=url,status="success",sku=supplier,target=target,qty=unit_count,price=price,special_price=None,carton=mctn.group(0),pack=mpack.group(0) if mpack else None)
 except Exception as e:return dict(url=url,status="failed",error=type(e).__name__+":"+str(e)[:130])
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:offers=list(ex.map(getone,all_urls))
print("INDEPENDENCE_FULL_START")
print(json.dumps({"pages":pages,"discovered":len(all_urls),"offers":offers},separators=(",",":"),ensure_ascii=False))
print("INDEPENDENCE_FULL_END")
