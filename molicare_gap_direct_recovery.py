import json,re,concurrent.futures
from scrapling.fetchers import Fetcher
TASKS=[
 ("166029","LuxeMED","shopify","https://www.luxemed.com.au/products/molicare-premium-mobile-8d-small",56),
 ("168100","Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-pad-2-drops",336),
 ("168100","Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/small-shaped-pad/molicare-pad-2-drops-12s/",336),
 ("916680","Independence Australia","ind","https://store.independenceaustralia.com/hartmann-all-in-one-dignity-bariatric-briefs-160-239-cm-unisex-2445ml-white-15310145",32),
 ("165531","ILCMC","ilcmc","https://www.ilcmc.com.au/molicare-slip-maxi~1983",56),
 ("165532","ILCMC","ilcmc","https://www.ilcmc.com.au/molicare-slip-maxi~1983",56),
 ("165533","Conticare","group","https://www.conticare.com.au/molicare-slip-unisex-briefs-large-maxi-3815ml-120-150cm-165533.html",56),
 ("169248","Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-premium-slip-extra-plus-6dopen-style",120),
 ("916680","Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-dignity-bariatric-brief-disposable-incontinence-pants",32),
]
def txt(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def one(t):
 sku,ret,kind,url,qty=t;r=dict(sku=sku,retailer=ret,url=url,qty=qty)
 try:
  pg=Fetcher.get(url+(".js" if kind=="shopify" else ""),impersonate="chrome",stealthy_headers=True,timeout=28);r["http_status"]=int(pg.status)
  if r["http_status"]!=200:r["status"]="blocked";return r
  if kind=="shopify":
   j=pg.json();title=str(j.get("title") or "");vs=j.get("variants") or [];cands=[]
   for v in vs:
    label=str(v.get("title") or "");code=str(v.get("sku") or "")
    if not re.search(r"(?<!\d)"+sku+r"(?!\d)",code):continue
    if sku=="166029":ok="Small" in label and "Carton (56)" in label
    elif sku=="168100":
     ok="12 Packs Per Carton" in label and any("28 Units Per Pack" in str(x.get("title")) for x in vs)
    elif sku=="916680":ok="Carton" in label and ("4" in label or "32" in label)
    else:ok=False
    if ok:cands.append(v)
   if len(cands)==1:
    v=cands[0];price=int(v["price"])/100;old=int(v.get("compare_at_price") or 0)/100
    r.update(status="success",price=old if old>price else price,special_price=price if old>price else None,url=url+"?variant="+str(v["id"]),matched_sku=v.get("sku"),variant=v.get("title"))
   else:r.update(status="variant_unresolved",title=title,variants=[dict(sku=v.get("sku"),title=v.get("title"),price=v.get("price")) for v in vs[:18]])
  else:
   text=txt(pg)
   if kind=="vital":
    m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s+Supplier Part\s*168100\s+Unit CAR\s+336",text,re.I)
   elif kind=="ind":
    m=re.search(r"Supplier Part Number:\s*916680.*?PKT\s+8\s+Units.*?Carton\s+4\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
   elif kind=="group":
    m=re.search(r"165533\s*\(Box of 56\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
   else:m=None
   if m:r.update(status="success",price=float(m.group(1).replace(",","")),special_price=None,excerpt=m.group(0)[-190:])
   else:r.update(status="unresolved",excerpt=text[max(0,text.find(sku)-80):text.find(sku)+280])
 except Exception as e:r.update(status="error",error=type(e).__name__+": "+str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:out=list(pool.map(one,TASKS))
print("DIRECT_START")
print(json.dumps(out,separators=(",",":")))
print("DIRECT_END")
