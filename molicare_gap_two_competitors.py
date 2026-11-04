from scrapling.fetchers import Fetcher
import re,json
checks=[
 ("HomeHealth Medical Supplies","https://hhmedicalsupplies.com.au/product/molicare-premium-mobile-small-8-drops-pack-14-2/"),
 ("Health Ladder Australia","https://www.healthladderaustralia.com.au/product/hartmann-molicare-premium-mobile-8-drops-1791ml-small-60-90cm-166029-148")
]
out=[]
for retailer,url in checks:
 r={"sku":"166029","retailer":retailer,"url":url}
 try:
  pg=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=28)
  r["status_code"]=int(pg.status)
  if r["status_code"]!=200:r["status"]="blocked";out.append(r);continue
  t=re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
  if retailer=="HomeHealth Medical Supplies":
   pat=r"(?:Manufacturer\s*Code:\s*915871|HHMS\s*Code:\s*P-915871)"
   qty=re.search(r"PKT\s+14\s+Units\s*\$\s*[0-9,]+\.\d{2}.{0,80}Carton\s+4\s+Pkt\(s\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
   ok=bool(re.search(pat,t,re.I)) and "Small" in t and "8 drops" in t.lower()
  else:
   qty=re.search(r"Carton\s*4\s*PKT\(S\)\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
   ok="166029" in t and ("8 Drops" in t or "8 drops" in t) and "Small" in t
  if ok and qty:r.update(status="success",price=float(qty.group(1).replace(",","")),special_price=None,matched_excerpt=qty.group(0))
  else:r.update(status="unresolved",identity=ok,excerpt=t[max(0,t.find("Carton")-180):t.find("Carton")+150],sku_context=t[max(0,t.find("166029")-90):t.find("166029")+120])
 except Exception as e:r.update(status="failed",error=type(e).__name__+": "+str(e))
 out.append(r)
print("GAP_TWO_START")
print(json.dumps(out,indent=2))
print("GAP_TWO_END")
