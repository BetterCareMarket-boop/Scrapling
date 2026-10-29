import re
from scrapling.fetchers import Fetcher

for label,url in [
 ("P51","https://www.patienthandling.com.au/product/betterliving-orientation-signage-kitchen-sticker/"),
 ("P54","https://www.patienthandling.com.au/product/confident-care-cleansing-kit/"),
]:
    p=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
    body=p.css("body").get() or ""
    print("\nPAGE",label)
    print("H1",p.css("h1::text").getall())
    for sel in [".price",".woocommerce-Price-amount",".product-price",".elementor-widget-woocommerce-product-price",".summary","main"]:
        vals=p.css(sel).getall()
        if vals: print("SEL",sel,vals[:10])
    for m in re.finditer(r"\$\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?",body):
        print("PRICECTX",m.group(0),re.sub(r"\s+"," ",body[max(0,m.start()-1000):m.start()+2200]))
        break
