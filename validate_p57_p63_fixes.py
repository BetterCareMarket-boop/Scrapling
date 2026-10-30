import json
from scrapling.fetchers import Fetcher
from novis_scrapling_rules import sku_matches, variant_override

targets=[
 ("P57","Aged Care and Medical","80505009","https://agedcareandmedical.com.au/products/etac-aktiv-reacher"),
 ("P58","Mable Direct","KC12","https://mabledirect.com.au/products/dysphagia-cup-green-copy"),
 ("P59","Mable Direct","KC85","https://mabledirect.com.au/products/one-touch-automatic-bottle-opener"),
 ("P63","Happy Healthcare","BL9504","https://shop.happyhealthcare.com.au/products/betterliving-ring-cushion-18"),
]

for pnum,competitor,novis_sku,url in targets:
    data=Fetcher.get(url.rstrip("/")+".js",impersonate="chrome",stealthy_headers=True,timeout=45).json()
    variants=data.get("variants") or []
    ov=variant_override(competitor,novis_sku)
    chosen=None
    if ov:
        terms=[str(x).casefold() for x in ov["variant_terms"]]
        for v in variants:
            blob=json.dumps(v,ensure_ascii=False).casefold()
            if all(t in blob for t in terms):
                chosen=v
                break
        assert chosen is not None, (pnum,"override unresolved")
        assert str(chosen.get("sku")) == str(ov["retailer_sku"]), (pnum,chosen)
        assert int(chosen.get("id")) == int(ov["variant_id"]), (pnum,chosen)
    else:
        for v in variants:
            if sku_matches(competitor,novis_sku,str(v.get("sku") or "")):
                chosen=v
                break
        assert chosen is not None, (pnum,"alias unresolved",variants)

    print("FIXED",pnum,json.dumps({
      "competitor":competitor,
      "novis_sku":novis_sku,
      "retailer_sku":chosen.get("sku"),
      "variant_id":chosen.get("id"),
      "title":chosen.get("title"),
      "price":chosen.get("price"),
      "compare_at_price":chosen.get("compare_at_price"),
      "available":chosen.get("available"),
    },separators=(",",":")))
