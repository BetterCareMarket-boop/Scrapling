from __future__ import annotations
import json,re
from scrapling.fetchers import Fetcher

PRODUCTS=[
 {"row":6,"sku":"915871","alternate":"166029","size":"Small","count":56,"drops":8},
 {"row":7,"sku":"166030","alternate":"915872","size":"Medium","count":42,"drops":8},
 {"row":8,"sku":"166031","alternate":"915873","size":"Large","count":56,"drops":8},
 {"row":9,"sku":None,"alternate":"166032","legacy":"915874","size":"X-Large","count":56,"drops":8},
 {"row":10,"sku":None,"alternate":"166041","legacy":"915878","size":"Medium","count":42,"drops":10}
]
SOURCES=[
 {"retailer":"LuxeMED","drops":8,"kind":"shopify","url":"https://www.luxemed.com.au/products/molicare-premium-mobile-8d-small"},
 {"retailer":"LuxeMED","drops":10,"kind":"shopify","url":"https://www.luxemed.com.au/products/molicare-premium-mobile-10d-medium"},
 {"retailer":"InCare Supports","drops":8,"kind":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-mobile-8-drops"},
 {"retailer":"InCare Supports","drops":10,"kind":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-mobile-10-drops"},
 {"retailer":"Oz Medical","drops":8,"kind":"shopify","url":"https://ozmedical.com.au/products/molicare-premium-mobile-14-pack"},
 {"retailer":"Oz Medical","drops":10,"kind":"shopify","url":"https://ozmedical.com.au/products/molicare-premium-mobile-10-drops"},
 {"retailer":"Surgical Direct","drops":8,"kind":"surgical","url":"https://surgicaldirect.com.au/products/molicare-premium-mobile-8-drops/"},
 {"retailer":"Solmed","drops":8,"kind":"shopify","url":"https://solmed.com.au/products/molicare-mobile-8d"},
 {"retailer":"Assist Ability","drops":8,"kind":"shopify","rows":[8],"url":"https://shop.assistabilityaustralia.com.au/products/molicare-prem-mobile-8d-xlge-p14-c4"},
 {"retailer":"Assist Ability","drops":8,"kind":"shopify","rows":[7],"url":"https://shop.assistabilityaustralia.com.au/products/molicare-premium-mobile-8-drop-pull-up-pants-unisex-medium-80-120cm-2040ml"},
 {"retailer":"Assist Ability","drops":10,"kind":"shopify","rows":[10],"url":"https://shop.assistabilityaustralia.com.au/products/molicare-prem-mobile-10d-med-p14-c3"},
]
def page_text(p):
 try: return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except Exception: return ""
def scrape(url): return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=40)
def status(p):
 try:return int(p.status)
 except Exception:return None
def price(v):
 return round(int(v)/100,2) if v is not None else None
def normal_size(t):
 z=t.lower().replace("extra large","x-large").replace("xlarge","x-large").replace("xl","x-large")
 return z
def size_ok(p,v):
 a=normal_size(str(v.get("option1") or "")+" "+str(v.get("title") or ""))
 size=normal_size(p["size"])
 return bool(re.search(r"(?<![a-z])"+re.escape(size)+r"(?![a-z])",a))
def qty_ok(p,v):
 t=str(v.get("title") or "")+" "+str(v.get("option2") or "")
 count=p["count"]
 return bool(re.search(r"(?:carton|box|ctn|case)[^0-9]{0,18}"+str(count)+r"\b|\b"+str(count)+r"\s*(?:units|pieces|per carton|per box)",t,re.I))
def sku_ok(p,v):
 sku=str(v.get("sku") or "")
 if not sku:return False
 codes=[p.get("sku"),p.get("alternate"),p.get("legacy")]
 return any(re.search(r"(?<!\d)"+re.escape(c)+r"(?!\d)",sku) for c in codes if c)
def run_shopify(p,src):
 page=scrape(src["url"].rstrip("/")+".js")
 if status(page)!=200:return {"status":"blocked","http_status":status(page)}
 try: data=page.json()
 except Exception as e:return {"status":"unreadable_json","http_status":status(page),"error":str(e)}
 title=str(data.get("title") or "")
 if "molicare" not in title.lower() or not re.search(r"\b"+str(p["drops"])+r"\s*(?:drops|d)\b",title,re.I):
  return {"status":"wrong_product","title":title}
 options=[]
 for v in data.get("variants") or []:
  if size_ok(p,v) and qty_ok(p,v):
   options.append(v)
 if len(options)!=1:
  return {"status":"variant_unresolved","count":len(options),"available_variants":[{"title":v.get("title"),"sku":v.get("sku")} for v in (data.get("variants") or [])][:15]}
 v=options[0]
 sku_confirmed=sku_ok(p,v)
 if v.get("sku") and not sku_confirmed:
  return {"status":"sku_mismatch","matched_variant":v.get("title"),"matched_sku":v.get("sku")}
 val=price(v.get("price"))
 compare=price(v.get("compare_at_price"))
 regular=compare if compare is not None and compare>val else val
 special=val if compare is not None and compare>val else None
 return {"status":"success","price":regular,"special_price":special,
         "matched_sku":v.get("sku"),"matched_variant":v.get("title"),
         "match_method":"sku_size_carton" if sku_confirmed else "size_carton_with_blank_retailer_sku",
         "variant_url":src["url"]+("?variant="+str(v.get("id")) if v.get("id") else "")}
def run_surgical(p,src):
 page=scrape(src["url"])
 if status(page)!=200:return {"status":"blocked","http_status":status(page)}
 t=page_text(page)
 codes=[p.get("sku"),p.get("alternate"),p.get("legacy")]
 for code in [x for x in codes if x]:
  m=re.search(r"(?<!\d)"+re.escape(code)+r"(?:-EA)?\s+Carton/"+str(p["count"])+r"[^$]{0,260}\$\s*([0-9,]+(?:\.[0-9]{1,2})?)",t,re.I)
  if m:
   excerpt=m.group(0)
   if not re.search(r"MoliCare Premium Mobile\s+"+re.escape(p["size"])+r"\s+"+str(p["drops"])+r"\s+drops",excerpt,re.I):
    continue
   return {"status":"success","price":float(m.group(1).replace(",","")),"special_price":None,"matched_sku":code,"matched_excerpt":excerpt}
 return {"status":"variant_unresolved","error":"No verified SKU + size + carton row"}
results=[]
for p in PRODUCTS:
 for src in SOURCES:
  if src["drops"]!=p["drops"] or (src.get("rows") and p["row"] not in src["rows"]):continue
  try:d=run_shopify(p,src) if src["kind"]=="shopify" else run_surgical(p,src)
  except Exception as e:d={"status":"failed","error":type(e).__name__+": "+str(e)}
  results.append({"row":p["row"],"input_sku":p["sku"],"reference_sku":p["alternate"],"size":p["size"],"carton":p["count"],"retailer":src["retailer"],"url":src["url"],**d})
print("MOLICARE_BATCH2_START")
print(json.dumps(results,ensure_ascii=False,indent=2))
print("MOLICARE_BATCH2_END")
