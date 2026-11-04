from scrapling.fetchers import Fetcher
import re,json
u="https://www.houseofnappies.com.au/molicare-premium-slip-extra-plus-6d-extra-small-40~199"
p=Fetcher.get(u,impersonate="chrome",stealthy_headers=True,timeout=30)
result={"url":u,"http_status":int(p.status)}
if int(p.status)==200:
 t=re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 anchors=[]
 for pattern in (r"MoliCare Premium Slip Extra Plus 6D Extra Small.{0,350}",r"\$\s*267\.99",r"169248C"):
  m=re.search(pattern,t,re.I)
  anchors.append(m.group(0) if m else None)
 result["evidence"]=anchors
 has_code="169248C" in t
 has_count=bool(re.search(r"Carton of 120|4\s*[x×]\s*30|120 briefs|4 packs of 30",t,re.I))
 m=re.search(r"MoliCare Premium Slip Extra Plus 6D Extra Small.{0,250}?\$\s*([0-9,]+\.\d{2})",t,re.I)
 if not m or float(m.group(1).replace(",",""))<=0:
  candidates=[x for x in re.finditer(r"\$\s*([0-9,]+\.\d{2})",t) if float(x.group(1).replace(",",""))>0]
  m=candidates[0] if candidates else None
 if has_code and has_count and m and float(m.group(1).replace(",",""))>0:
  result.update(status="success",price=float(m.group(1).replace(",","")),special_price=None,sku="169248C",qty=120)
 else:result.update(status="unresolved",code=has_code,count=has_count,match=m.group(0) if m else None)
print("HOUSE_START")
print(json.dumps(result,ensure_ascii=False))
print("HOUSE_END")
