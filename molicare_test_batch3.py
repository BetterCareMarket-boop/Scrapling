from __future__ import annotations
import re,json
from scrapling.fetchers import Fetcher
TARGETS=[
 {"row":11,"sku":"166042","aliases":["915879"],"family":"mobile","drops":10,"size":"Large","carton":56},
 {"row":12,"sku":"915880","aliases":[],"family":"mobile","drops":10,"size":"X-Large","carton":56},
 {"row":13,"sku":"168100","aliases":[],"family":"pad","drops":2,"carton":336},
 {"row":14,"sku":"168077","aliases":[],"family":"pad","drops":4,"carton":270},
 {"row":15,"sku":"168404","aliases":["168019"],"family":"form","drops":4,"carton":128}
]
SOURCES=[
 {"retailer":"LuxeMED","family":"mobile","mode":"shopify","url":"https://www.luxemed.com.au/products/molicare-premium-mobile-10d-medium"},
 {"retailer":"InCare Supports","family":"mobile","mode":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-mobile-10-drops"},
 {"retailer":"AHNS","family":"mobile","rows":[11],"mode":"exact_html","url":"https://www.ahns.com.au/product/molicare-mobile-10-drop-large-4x14-56-carton/"},
 {"retailer":"Independence Australia","family":"mobile","rows":[12],"mode":"independence","url":"https://store.independenceaustralia.com/molicare-premium-mobile-10-drops-x-large-2757ml-15310140"},
 {"retailer":"Vital Medical Supplies","family":"mobile","rows":[11],"mode":"exact_html","url":"https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/pants/pull-up-pants/molicare-premium-mobile-10-drops-l-4s/"},
 {"retailer":"Medshop","family":"pad","rows":[13],"mode":"exact_html","url":"https://www.medshop.com.au/products/molicare-pad"},
 {"retailer":"LuxeMED","family":"form","mode":"shopify","url":"https://www.luxemed.com.au/products/molicare-premium-form-4-drops"},
 {"retailer":"InCare Supports","family":"form","mode":"shopify","url":"https://incaresupports.com.au/products/molicare-premium-form-4-drops"},
 {"retailer":"Chooze","family":"form","mode":"exact_html","url":"https://www.chooze.com.au/molicare-premium-form-4-drops/p"},
]
def textpage(p):
 try:return re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
 except:return ""
def get(url):return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=35)
def st(p):
 try:return int(p.status)
 except:return None
def codes(t):return [t["sku"]]+t.get("aliases",[])
def sku_match(t,s):
 return any(re.search(r"(?<!\d)"+re.escape(c)+r"(?!\d)",str(s)) for c in codes(t))
def qty_match(t,s):
 s=str(s).lower();n=t["carton"]
 if re.search(r"\b"+str(n)+r"\b",s) and re.search(r"carton|box|ctn|case|units|pieces",s):return True
 for a,b in re.findall(r"(\d+)\s*(?:packets?|packs?|pkt|x|×)\s*(?:of)?\s*(\d+)",s):
  if int(a)*int(b)==n:return True
 return False
def size_match(t,s):
 if not t.get("size"):return True
 sz=t["size"].lower()
 s=s.lower().replace("extra large","x-large").replace("xlarge","x-large")
 return bool(re.search(r"(?<![a-z])"+re.escape(sz)+r"(?![a-z])",s))
def shopify(t,src):
 p=get(src["url"]+".js")
 if st(p)!=200:return {"status":"blocked","http_status":st(p)}
 try:d=p.json()
 except Exception as e:return {"status":"unreadable_json","error":str(e)}
 title=str(d.get("title") or "")
 if "molicare" not in title.lower():return {"status":"wrong_product","title":title}
 matches=[]
 for v in d.get("variants") or []:
  desc=" ".join([str(v.get(k) or "") for k in ("title","option1","option2","option3")])
  parent=title+" "+desc
  if not size_match(t,parent):continue
  if not (re.search(r"\b"+str(t["drops"])+r"\s*(?:d|drops)\b",parent,re.I) or t["family"]=="form" and "4 Drops" in desc):continue
  if not qty_match(t,desc):continue
  if not sku_match(t,v.get("sku")):continue
  matches.append(v)
 if len(matches)!=1:return {"status":"unresolved","matched":len(matches),"variants":[{"title":v.get("title"),"sku":v.get("sku")} for v in (d.get("variants") or [])][:20]}
 v=matches[0]
 value=int(v["price"])/100
 comp=int(v["compare_at_price"])/100 if v.get("compare_at_price") else None
 return {"status":"success","price":comp if comp and comp>value else value,
         "special_price":value if comp and comp>value else None,
         "matched_sku":v.get("sku"),"matched_variant":v.get("title"),
         "variant_url":src["url"]+"?variant="+str(v.get("id"))}
def htmlprice(t,src):
 p=get(src["url"]);tx=textpage(p)
 if st(p)!=200:return {"status":"blocked","http_status":st(p)}
 if not sku_match(t,tx):return {"status":"sku_not_found"}
 if not qty_match(t,tx):return {"status":"carton_unverified"}
 if not size_match(t,tx):return {"status":"size_unverified"}
 if "molicare" not in tx.lower():return {"status":"identity_unverified"}
 # Avoid picking up prices from navigational or related products.
 h1=" ".join(p.css("h1").getall())
 selections=p.css("main").getall()[:1]
 raw=" ".join(selections)
 raw=re.sub(r"<[^>]+>"," ",raw);raw=re.sub(r"\s+"," ",raw)
 dollar=re.findall(r"\$\s*([0-9,]+(?:\.\d{1,2})?)",raw)
 if len(dollar)!=1:return {"status":"price_ambiguous","main_prices":dollar[:15]}
 return {"status":"success","price":float(dollar[0].replace(",","")),"special_price":None,"verification":"sku_size_carton_main_product"}
def independence(t,src):
 p=get(src["url"]);tx=textpage(p)
 if st(p)!=200:return {"status":"blocked","http_status":st(p)}
 if not sku_match(t,tx) or not qty_match(t,tx) or not size_match(t,tx):return {"status":"identity_unverified"}
 m=re.search(r"Carton\s+4\s+PKT\(s\)\s+\$\s*([0-9,]+(?:\.\d{2})?)",tx,re.I)
 if not m:return {"status":"carton_price_unresolved"}
 return {"status":"success","price":float(m.group(1).replace(",","")),"special_price":None,"verification":"carton_4x14"}
results=[]
for t in TARGETS:
 for src in SOURCES:
  if src["family"]!=t["family"] or src.get("rows") and t["row"] not in src["rows"]:continue
  try:
   d=shopify(t,src) if src["mode"]=="shopify" else independence(t,src) if src["mode"]=="independence" else htmlprice(t,src)
  except Exception as e:d={"status":"failed","error":type(e).__name__+": "+str(e)}
  results.append({"row":t["row"],"sku":t["sku"],"retailer":src["retailer"],"url":src["url"],**d})
print("MOLICARE_BATCH3_START")
print(json.dumps(results,indent=2,ensure_ascii=False))
print("MOLICARE_BATCH3_END")
