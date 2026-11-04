import json,re,concurrent.futures
from scrapling.fetchers import Fetcher
TASKS=[
("OzChemist collection","https://ozchemist.com/collections/disposable-pads-pants-liners/products.json?limit=250","json"),
("Betta Health www","https://www.bettahealthoutcomes.com.au/product/molicare-slip-maxi-waist-60-90-cm-small-2153ml-poa/","html"),
("HelpCo Small","https://helpco.com.au/shop/continence-care/wrap-around/molicare-slip-maxi-small-9d/","html"),
("HelpCo Medium","https://helpco.com.au/shop/continence-care/wrap-around/molicare-slip-maxi-medium-9d/","html"),
("Conticare unisex category","https://www.conticare.com.au/disposable-products/unisex.html","html"),
("Conticare brand","https://www.conticare.com.au/brands/molicare?p=2","html"),
]
def do(t):
 name,url,kind=t;r={"store":name,"url":url}
 try:
  p=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
  r["http_status"]=int(p.status)
  if r["http_status"]!=200:r["status"]="blocked";return r
  if kind=="json":
   d=p.json();rows=[]
   for prod in d.get("products") or []:
    title=str(prod.get("title") or "")
    if "slip maxi" in title.lower():
     rows.append({"title":title,"handle":prod.get("handle"),"variants":[{"sku":v.get("sku"),"title":v.get("title"),"price":v.get("price"),"compare":v.get("compare_at_price"),"id":v.get("id"),"available":v.get("available")} for v in prod.get("variants") or []]})
   r.update(status="review",results=rows)
   return r
  text=re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
  if name.startswith("Conticare"):
   hits=[]
   for sku in ("165531","165532","165533","169248"):
    pos=text.find(sku)
    if pos>=0:hits.append({"sku":sku,"excerpt":text[max(0,pos-230):pos+300]})
   # Also retrieve candidate direct links from page CSS selector.
   try:
    nodes=p.css('a')
    for n in nodes:
     title=n.get_all_text(strip=True)
     if "slip" in title.lower() and ("maxi" in title.lower() or "x-small" in title.lower()):
      href=n.attrib.get("href","")
      if href.startswith("http"):hits.append({"label":title[:100],"href":href})
   except Exception:pass
   r.update(status="review",hits=hits[:22])
   return r
  if name.startswith("HelpCo"):
   pos=text.find("165531" if "Small" in name else "165532")
   r.update(status="review",snippet=text[max(0,pos-130):pos+190] if pos>=0 else text[:450])
   return r
  if "Betta" in name:
   m=re.search(r"MoliCare Slip Maxi Waist 60-90 Cm S 2153ml C56 165531.{0,180}\$\s*([0-9,]+\.\d{2})",text,re.I)
   r.update(status="success" if m else "unresolved",price=float(m[1].replace(",","")) if m else None,excerpt=text[:400])
 except Exception as e:r.update(status="failed",error=type(e).__name__+": "+str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:out=list(ex.map(do,TASKS))
print("RECOVERY2_START")
print(json.dumps(out,ensure_ascii=False,indent=2))
print("RECOVERY2_END")
