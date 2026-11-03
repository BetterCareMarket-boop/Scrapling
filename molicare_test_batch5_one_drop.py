import json,re
from scrapling.fetchers import Fetcher
url="https://medisa.com.au/products/incontinence-aids-pads-pants-liners-pad-pant-system-hartmann-molicare-premium-lady-pad-all-sizes"
out={"retailer":"Medisa","url":url,"row":22,"sku":"168132","carton":192}
try:
 p=Fetcher.get(url+".js",impersonate="chrome",stealthy_headers=True,timeout=38)
 out["http_status"]=int(p.status)
 if int(p.status)==200:
  j=p.json();out["title"]=j.get("title")
  candidates=[]
  for v in j.get("variants") or []:
   txt=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
   sku=str(v.get("sku") or "")
   one=bool(re.search(r"\b1\s*Drop\b",txt,re.I)) and ("168132" in txt or "168132" in sku)
   carton=bool(re.search(r"16\s*[x×]\s*12|16\s*x\s*12\s*/\s*packs?",txt,re.I))
   if one and carton:
    cur=int(v["price"])/100;prev=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
    candidates.append(dict(status="success",sku=sku,variant=txt,price=prev if prev and prev>cur else cur,special_price=cur if prev and prev>cur else None,url=url+"?variant="+str(v.get("id"))))
  out["candidates"]=candidates
  out["variants"]=[dict(title=v.get("title"),sku=v.get("sku")) for v in j.get("variants") or []][:35]
except Exception as e:out["error"]=type(e).__name__+": "+str(e)
print("BATCH5_XS_START")
print(json.dumps(out,indent=2))
print("BATCH5_XS_END")
