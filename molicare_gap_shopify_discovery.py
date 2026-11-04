import json,re,concurrent.futures
from scrapling.fetchers import Fetcher
SKUS="915840 915834 166029 915874 166042 915880 168100 168077 168404 168405 168406 168401 168409 168132 168044 168600 168066 161065 165271 165272 165273 165374 165474 165571 165572 165573 947712 947713 947714 947715 165531 165532 165533 169248 916680 915868 165531-1 166093 168519".split()
STORES={
"AMH Community":"https://www.amhcommunity.com.au/collections/molicare/products.json?limit=250",
"Topcat Healthcare":"https://topcathealthcare.com.au/collections/hartmann/products.json?limit=250",
"Platinum Health Supply":"https://www.platinumhealthsupply.com.au/collections/molicare/products.json?limit=250",
"LuxeMED":"https://www.luxemed.com.au/collections/molicare/products.json?limit=250",
"InCare Supports":"https://incaresupports.com.au/collections/molicare/products.json?limit=250",
"Medisa":"https://medisa.com.au/collections/molicare/products.json?limit=250",
"Mobiquip":"https://www.mobiquip.com.au/collections/molicare/products.json?limit=250",
"Trugrade Medical":"https://www.trugrademedical.com.au/collections/molicare/products.json?limit=250",
"Keeping Contained Care":"https://keepingcontainedcare.com/collections/molicare/products.json?limit=250",
"Assist Ability":"https://shop.assistabilityaustralia.com.au/collections/molicare/products.json?limit=250",
}
def run(item):
 name,url=item
 try:
  pg=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=35)
  st=int(pg.status)
  if st!=200:return dict(store=name,status=st)
  d=pg.json()
  products=d.get("products") or []
  hits=[]
  for p in products:
   title=str(p.get("title") or "")
   if "molicare" not in title.lower() and "dignity" not in title.lower():continue
   for v in p.get("variants") or []:
    sku=str(v.get("sku") or "")
    for target in SKUS:
     if not re.search(r"(?<!\d)"+re.escape(target)+r"(?!\d)",sku):continue
     hits.append(dict(target=target,sku=sku,title=title,variant=v.get("title"),price=v.get("price"),compare=v.get("compare_at_price"),id=v.get("id"),handle=p.get("handle"),product_id=p.get("id")))
  return dict(store=name,status=st,count=len(products),hits=hits)
 except Exception as e:return dict(store=name,error=type(e).__name__+": "+str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:out=list(ex.map(run,STORES.items()))
print("DISCOVERY_START")
print(json.dumps(out,separators=(",",":"),ensure_ascii=False))
print("DISCOVERY_END")
