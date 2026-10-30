import json
from scrapling.fetchers import Fetcher

urls=[
 ("P57","https://agedcareandmedical.com.au/products/etac-aktiv-reacher"),
 ("P58","https://mabledirect.com.au/products/dysphagia-cup-green-copy"),
 ("P59","https://mabledirect.com.au/products/one-touch-automatic-bottle-opener"),
 ("P63","https://shop.happyhealthcare.com.au/products/betterliving-ring-cushion-18"),
]
for label,url in urls:
    page=Fetcher.get(url.rstrip("/")+".js",impersonate="chrome",stealthy_headers=True,timeout=45)
    data=page.json()
    print("\nPRODUCT",label,data.get("title"))
    for v in data.get("variants") or []:
        print("VARIANT",json.dumps({
          "id":v.get("id"),"title":v.get("title"),"sku":v.get("sku"),
          "option1":v.get("option1"),"option2":v.get("option2"),"option3":v.get("option3"),
          "price":v.get("price"),"compare_at_price":v.get("compare_at_price"),
          "available":v.get("available")
        },separators=(",",":")))
