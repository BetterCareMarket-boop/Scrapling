from __future__ import annotations
import json, re, html
from scrapling.fetchers import Fetcher

CHECKS=[
 (110,"168519",54,"Dove Care","html","https://dovecaregroup.com.au/product/molicare-premium-form-size/"),
 (110,"168519",54,"House of Nappies","html","https://www.houseofnappies.com.au/molicare-premium-form-size-8d-3347ml-3x18-carton-o"),
 (111,"165435",56,"Trugrade Medical","shopify","https://www.trugrademedical.com.au/products/molicare-slip-size-8-drop"),
 (111,"165435",56,"Medisa","shopify","https://medisa.com.au/products/molicare-slip-size-8-drops-2xl-3xl-175-245cm-3478ml-unisex-1ctn-4-x-14-pack-165435"),
 (111,"165435",56,"Day & Night Healthcare","html","https://www.dnhc.com.au/CONTINENCE/All_dash_In_dash_One/pl.php"),
 (112,"169111",150,"Independence Australia","html","https://store.independenceaustralia.com/molicare-slip-junior-8-drops-xs-sml-waist-50-80cm-unisex-1900ml-15310420"),
 (112,"169111",150,"HomeHealth Medical Supplies","html","https://hhmedicalsupplies.com.au/product/molicare-slip-junior-8d-xs-s-pack-10/"),
 (112,"169111",150,"Trugrade Medical","shopify","https://www.trugrademedical.com.au/products/molicare-slip-junior-8-drop"),
 (112,"169111",150,"Medisa","shopify","https://medisa.com.au/products/molicare-slip-junior-8-drops-xs-small-50-80cm-1914ml-1ctn-10-x-15-pack-169111"),
 (112,"169111",150,"Day & Night Healthcare","html","https://www.dnhc.com.au/169111/MoliCare-Slip-Junior-8D-XS_or_S-150/pd.php"),
 (75,"169248",120,"Incontinence Products Australia","shopify","https://incontinenceproducts.com.au/products/molicare-premium-slip-extra-plus-6dopen-style"),
 (73,"165533",56,"Conticare","html","https://www.conticare.com.au/molicare-slip-unisex-briefs-large-maxi-3815ml-120-150cm-165533.html"),
 (71,"165531",56,"ILCMC","html","https://www.ilcmc.com.au/molicare-slip-maxi~1983"),
 (72,"165532",56,"ILCMC","html","https://www.ilcmc.com.au/molicare-slip-maxi~1983"),
 (73,"165533",56,"ILCMC","html","https://www.ilcmc.com.au/molicare-slip-maxi~1983"),
 (103,"165531-1",42,"ILCMC","html","https://www.ilcmc.com.au/molicare-slip-maxi~1983"),
]
def get(url):
 return Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
def tpage(pg):
 try:return re.sub(r"\s+"," ",pg.get_all_text(separator=" ",strip=True))
 except:return ""
def skuok(sku,text):
 return bool(re.search(r"(?<!\d)"+re.escape(sku)+r"(?!\d)",str(text),re.I))
def parse_shop(row,sku,count,retailer,url):
 pg=get(url+".js")
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 j=pg.json()
 vs=j.get("variants") or []
 title=str(j.get("title") or "")
 if "molicare" not in title.lower():return dict(status="wrong_product",title=title)
 if row==111:pack=r"(?:4\s*[x×]\s*14|carton\s*of\s*4\s*x\s*14|1ctn\s*\(4\s*x\s*14|carton\s*of\s*56|56\s*units?)"
 elif row==112:pack=r"(?:10\s*[x×]\s*15|carton\s*of\s*10\s*x\s*15|1ctn\s*\(10\s*x\s*15|carton\s*of\s*150|150\s*units?)"
 else:pack=r"(?:4\s*[x×]\s*30|carton\s*of\s*120|120\s*units?)"
 found=[]
 for v in vs:
  vtitle=str(v.get("title") or "")
  vsku=str(v.get("sku") or "")
  if not skuok(sku,vsku+" "+title):continue
  if not re.search(pack,vsku+" "+vtitle+" "+title,re.I):continue
  found.append(v)
 if len(found)!=1:return dict(status="variant_unresolved",title=title,variants=[{"title":v.get("title"),"sku":v.get("sku"),"price":(v.get("price") or 0)/100} for v in vs[:20]])
 v=found[0];price=(v.get("price") or 0)/100;old=(v.get("compare_at_price") or 0)/100
 if price<=0:return dict(status="price_unresolved")
 return dict(status="success",price=old if old>price else price,special_price=price if old>price else None,matched_sku=v.get("sku"),variant=v.get("title"),url=url+"?variant="+str(v.get("id")))
def parse_html(row,sku,count,retailer,url):
 pg=get(url)
 if int(pg.status)!=200:return dict(status="blocked",http_status=int(pg.status))
 text=tpage(pg)
 if not skuok(sku,text):return dict(status="sku_not_visible",excerpt=text[:200])
 if retailer=="Dove Care":
  m=re.search(r"CTN\s*=\s*54\s*PIECES\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
 elif retailer=="Independence Australia":
  m=re.search(r"PKT\s+15\s+Units\s+\$\s*[0-9,]+\.\d{2}.{0,200}?Carton\s+10\s+PKT\(s\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
 elif retailer=="HomeHealth Medical Supplies":
  m=re.search(r"Carton\s+10\s+Pkt\(s\)\s*\$\s*([0-9,]+\.\d{2})",text,re.I)
 elif retailer=="Day & Night Healthcare":
  m=re.search(r"\$\s*([0-9,]+\.\d{2})\s*\(ex GST\).{0,200}?Product Code:\s*"+sku,text,re.I)
  if m and row==111 and not re.search(r"Slip Plus Size 8D 2/3XL 56",text[max(0,m.start()-120):m.end()+160],re.I):m=None
  if m and row==112 and not re.search(r"Slip Junior 8D XS/S 150",text[max(0,m.start()-120):m.end()+160],re.I):m=None
 elif retailer=="House of Nappies":
  m=re.search(r"\$\s*([0-9,]+\.\d{2})",text)
 else:m=None
 if m:return dict(status="success",price=float(m.group(1).replace(",","")),special_price=None,url=url,gst_basis="ex GST" if retailer=="Day & Night Healthcare" else "displayed")
 return dict(status="price_unresolved",excerpt=text[max(0,text.find(sku)-90):text.find(sku)+350][:440])
out=[]
for row,sku,qty,retailer,kind,url in CHECKS:
 try:r=parse_shop(row,sku,qty,retailer,url) if kind=="shopify" else parse_html(row,sku,qty,retailer,url)
 except Exception as e:r=dict(status="error",error=type(e).__name__+": "+str(e))
 out.append(dict(row=row,sku=sku,qty=qty,retailer=retailer,source_url=url,**r))
print("NEW_CATALOGUE_START")
print(json.dumps(out,indent=2,ensure_ascii=False))
print("NEW_CATALOGUE_END")
