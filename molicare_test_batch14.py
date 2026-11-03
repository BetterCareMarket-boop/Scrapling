from __future__ import annotations
import re,json,html
from scrapling.fetchers import Fetcher
P=[
 dict(row=66,sku="947715",kind="fixpants",qty=25,name="MoliCare Premium FixPants Short XXL Pack 25"),
 dict(row=67,sku="916680",kind="dignity",qty=32,name="MoliCare Dignity Bariatric Brief Super Carton 32"),
 dict(row=68,sku="995086",kind="barrier",qty=12,name="MoliCare Skin Barrier Cream 200ml Carton 12"),
 dict(row=69,sku="995088",kind="lotion",qty=12,name="MoliCare Skin Body Lotion 500ml Carton 12"),
 dict(row=70,sku="995075",kind="tissues",qty=600,name="MoliCare Moist Skin Care Tissues 50 Carton 12")]
S=[
 (66,"Elora Medical","shopify","https://eloramedicalsupplies.com.au/products/molicare-premium-fixpants-short-leg-25-pack"),
 (66,"InCare Supports","shopify","https://incaresupports.com.au/products/molicare-premium-fixpants-short-designed-to-hold-a-continence-pad-securely-in-place"),
 (66,"Sumac Medical Supplies","sumac","https://sumacms.com.au/product/molicare-premium-fixpants-short-leg-xx-large-140-180-cm-unisex-grey-300s-ctn/"),
 (67,"Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-dignity-bariatric-brief-disposable-incontinence-pants"),
 (67,"Independence Australia","independence","https://store.independenceaustralia.com/molicare-dignity-bariatric-briefs-super-unisex-2445ml-15310142"),
 (68,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-skin-protect-cream-200ml"),
 (68,"Independence Australia","independence","https://store.independenceaustralia.com/molicare-skin-barrier-cream-200ml-24310260"),
 (68,"Dove Care","dove","https://dovecaregroup.com.au/product/molicare-skin-barrier-cream/"),
 (68,"Vital Medical Supplies","vital","https://www.vitalmedicalsupplies.com.au/catalogue-products/continence-care/skin-care/skin-care/menalind-tp-skin-protect-200ml-x-12s/"),
 (68,"Assist Ability","shopify","https://shop.assistabilityaustralia.com.au/products/mc-skin-barrier-cream-east-200ml-p1-c12"),
 (69,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-skin-body-lotion-500ml"),
 (69,"Topcat Healthcare","shopify","https://topcathealthcare.com.au/products/molicare-skin-bodylotion"),
 (69,"Independence Australia","independence","https://store.independenceaustralia.com/molicare-skin-body-lotion-500ml-24310156"),
 (69,"Surgical House","surgical","https://surgicalhouse.com.au/Product.php?id=995088"),
 (70,"Platinum Health Supply","shopify","https://www.platinumhealthsupply.com.au/products/molicare-skin-cleanse-tissues"),
 (70,"Independence Australia","independence","https://store.independenceaustralia.com/molicare-skin-moist-skin-care-tissues-20x30cm-24310116"),
 (70,"InCare Supports","shopify","https://incaresupports.com.au/products/molicare-skin-moist-skin-care-tissues"),
 (70,"Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-moist-skin-care-tissues-pack-of-50")
]
def get(url):return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
def page_text(page):
 try:return re.sub(r"\s+"," ",page.get_all_text(separator=" ",strip=True))
 except:return ""
def matches_sku(p,val):
 return bool(re.search(r"(?<!\d)"+p["sku"]+r"(?!\d)",str(val)))
def pricec(val):
 try:return round(int(val)/100,2)
 except:return None
def identity(p,title):
 title=title.lower()
 if "molicare" not in title:return False
 return {"fixpants":("fixpants","short"),"dignity":("dignity","bariatric"),"barrier":("barrier","cream"),"lotion":("body","lotion"),"tissues":("tissue",)}[p["kind"]][0] in title and all(word in title for word in {"fixpants":["short"],"dignity":["bariatric"],"barrier":["cream"],"lotion":["lotion"],"tissues":[]}[p["kind"]])
def variant_is_carton(p,label,description,variants):
 label=label.lower();description=description.lower()
 kind=p["kind"]
 if kind=="fixpants":
  return bool(re.search(r"(25\s*(?:units?|pcs|pieces)|pack\s*of\s*25|25\s*pack)",label+" "+description)) and not bool(re.search(r"(?:carton|case)\s*(?:of\s*)?(?:12|300)\b",label))
 if kind=="dignity":
  return bool(re.search(r"(?:carton|box|case)\s*(?:of\s*)?(?:32|4\s*(?:packs?|pkts?))|32\s*(?:units?|pieces)|4\s*[x×]\s*8",label)) and bool(re.search(r"8\s*(?:briefs?|pants?|units?)\s*per\s*pack|8\s*per\s*pack|4\s*packs?\s*per\s*carton|4\s*[x×]\s*8",description+" "+json.dumps(variants).lower()))
 if kind in ("barrier","lotion"):
  return bool(re.search(r"(?:12\s*(?:units?|bottles?|tubes?)\s*per\s*carton|(?:carton|box|case)\s*(?:of\s*)?12\b|12\s*(?:units?|bottles?|tubes?))",label))
 if kind=="tissues":
  return bool(re.search(r"12\s*(?:packs?|pkts?)\s*per\s*carton|(?:carton|box|case)\s*(?:of\s*)?12\s*(?:packs?|pkts?)|600\s*(?:units?|wipes?)",label)) and bool(re.search(r"50\s*(?:wipes?|units?|tissues?)\s*per\s*pack|50\s*wipes?|pack\s*of\s*50",description+" "+json.dumps(variants).lower()))
 return False
def shopify(p,url):
 pg=get(url.rstrip("/")+".js");status=int(pg.status)
 if status!=200:return dict(status="blocked",http_status=status)
 j=pg.json();title=str(j.get("title") or "")
 if not identity(p,title):return dict(status="wrong_product",title=title)
 desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html.unescape(str(j.get("description") or ""))))
 variants=j.get("variants") or [];out=[]
 for v in variants:
  label=" ".join(str(v.get(k) or "") for k in ("title","option1","option2","option3"))
  sku=str(v.get("sku") or "")
  if not matches_sku(p,sku) and not (not sku and matches_sku(p,title+" "+desc)):continue
  if p["kind"]=="fixpants" and not re.search(r"\b(?:xxl|xx.large|2xl)\b",label,re.I):continue
  if not variant_is_carton(p,label,desc,variants):continue
  out.append(v)
 if len(out)!=1:return dict(status="variant_unresolved",title=title,description_excerpt=desc[:240],variants=[dict(sku=v.get("sku"),label=v.get("title"),price=pricec(v.get("price")),compare=pricec(v.get("compare_at_price"))) for v in variants][:24])
 v=out[0];cur=pricec(v.get("price"));was=pricec(v.get("compare_at_price"))
 return dict(status="success",matched_sku=v.get("sku"),variant=v.get("title"),price=was if was and cur and was>cur else cur,special_price=cur if was and cur and was>cur else None,variant_url=url+"?variant="+str(v.get("id")))
def independence(p,url):
 page=get(url);status=int(page.status)
 if status!=200:return dict(status="blocked",http_status=status)
 t=page_text(page)
 if not (matches_sku(p,t) or p["kind"]=="barrier" and "9950862" in t):return dict(status="sku_not_visible")
 multiplier="4" if p["kind"]=="dignity" else "12"
 uom="PKT" if p["kind"] in ("tissues","dignity") else "EA"
 pattern=r"Carton\s+"+multiplier+r"\s+"+uom+r"\(s\)\s*\$\s*([0-9,]+\.\d{2})"
 m=re.search(pattern,t,re.I)
 if not m:return dict(status="carton_price_unresolved",excerpt=t[max(0,t.find(p["sku"])-100):t.find(p["sku"])+350])
 if p["kind"]=="dignity" and "8 Units" not in t and "8 Briefs" not in t:return dict(status="pack_count_unverified")
 if p["kind"]=="tissues" and "50 Units" not in t:return dict(status="pack_count_unverified")
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,matched_excerpt=m.group(0))
def surgical(p,url):
 pg=get(url);status=int(pg.status);t=page_text(pg)
 if status!=200:return dict(status="blocked",http_status=status)
 if not matches_sku(p,t):return dict(status="sku_not_visible")
 m=re.search(r"EA\s+CT\s+12\.00\s+([0-9,]+\.\d{2})\s+([0-9,]+\.\d{2})",t)
 return dict(status="success",price=float(m.group(2).replace(",","")),special_price=None,basis="inc GST",matched_excerpt=m.group(0)) if m else dict(status="carton_price_unresolved")
def dove(p,url):
 pg=get(url);status=int(pg.status);t=page_text(pg)
 if status!=200:return dict(status="blocked",http_status=status)
 m=re.search(r"CTN\s*=\s*12\s*PIECES\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m and matches_sku(p,t) else dict(status="unresolved")
def vital(p,url):
 pg=get(url);status=int(pg.status);t=page_text(pg)
 if status!=200:return dict(status="blocked",http_status=status)
 m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*inc GST\s+Supplier Part\s+"+p["sku"]+r"\s+Unit CAR\s+12",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,basis="inc GST") if m else dict(status="unresolved")
def sumac(p,url):
 pg=get(url);status=int(pg.status);t=page_text(pg)
 if status!=200:return dict(status="blocked",http_status=status)
 if not matches_sku(p,t) or not ("XX-Large" in t and "PKT/25" in t):return dict(status="identity_unverified")
 m=re.search(r"MoliCare Premium FixPants Short XX-Large\s*\|\s*PKT/25\s*\$\s*([0-9,]+\.\d{2})",t,re.I)
 return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None) if m else dict(status="price_unresolved")
out=[]
for row,retailer,mode,url in S:
 p=next(x for x in P if x["row"]==row)
 try:
  d=shopify(p,url) if mode=="shopify" else independence(p,url) if mode=="independence" else surgical(p,url) if mode=="surgical" else dove(p,url) if mode=="dove" else vital(p,url) if mode=="vital" else sumac(p,url)
 except Exception as e:d=dict(status="failed",error=type(e).__name__+": "+str(e))
 out.append(dict(row=row,name=p["name"],sku=p["sku"],retailer=retailer,url=url,**d))
print("BATCH14_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("BATCH14_END")
