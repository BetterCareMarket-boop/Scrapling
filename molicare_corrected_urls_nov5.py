from scrapling.fetchers import Fetcher
import re,json,concurrent.futures
TASKS=[
("165532",56,"Conticare","https://www.conticare.com.au/molicare-slip-unisex-briefs-medium-maxi-2485ml-90-120cm-165533.html"),
("169248",120,"Conticare","https://www.conticare.com.au/molicare-premium-elastic-slips-x-small-6-drops-40-60cm-1170ml-169249.html"),
("165533",56,"OzChemist","https://ozchemist.com/products/molicare-slip-maxi-9-drops-large-pad"),
]
def run(t):
 sku,qty,ret,url=t;r=dict(sku=sku,qty=qty,retailer=ret,url=url)
 try:
  pg=Fetcher.get(url+(".js" if ret=="OzChemist" else ""),impersonate="chrome",stealthy_headers=True,timeout=30)
  r["http_status"]=int(pg.status)
  if int(pg.status)!=200:r["status"]="blocked";return r
  if ret=="OzChemist":
   d=pg.json();v=[x for x in d.get("variants") or [] if str(x.get("sku") or "")=="165533/C" and "4 Packs Per Carton"==str(x.get("title") or "")]
   if len(v)==1:
    x=v[0];cur=float(x["price"]);old=float(x.get("compare_at_price") or 0)
    return dict(r,status="success",price=old if old>cur else cur,special_price=cur if old>cur else None,variant=x.get("title"),url=url+"?variant="+str(x.get("id")),available=x.get("available"))
   return dict(r,status="unresolved",variants=d.get("variants"))
  text=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
  r["sku_visible"]=sku in text
  r["carton_excerpt"]=text[max(0,text.find(sku)-190):text.find(sku)+460]
  r["matches"]=re.findall(r"((?:Box of|Carton)\s*(?:of)?\s*"+str(qty)+r".{0,60}?\$\s*[0-9,]+\.\d{2})",text,re.I)[:10]
  pat=r"(?<!\d)"+sku+r"\s*\(Box of "+str(qty)+r"\)\s*\$\s*([0-9,]+\.\d{2})"
  m=re.search(pat,text,re.I)
  if m:r.update(status="success",price=float(m[1].replace(",","")),special_price=None)
  else:r.update(status="unresolved")
 except Exception as e:r.update(status="failed",error=str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:out=list(ex.map(run,TASKS))
print("CORRECTED_URLS_START")
print(json.dumps(out,indent=2))
print("CORRECTED_URLS_END")
