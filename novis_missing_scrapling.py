"""Read-only NOVIS missing-mapping audit. Scrapling 0.5 ONLY; no DB writes."""
import json,re,collections
from pathlib import Path
from decimal import Decimal
from urllib.parse import urlparse
from scrapling.fetchers import Fetcher

rows=json.loads(Path("novis_missing_targets.json").read_text())
results=[]
for row in rows:
    out={**row,"status":"unresolved","regular_price":None,"special_price":None,"stock":"unknown","verified_variant":False,"validation_url":row["competitor_url"],"method":None,"reason":None}
    try:
        url=row["competitor_url"]
        path=urlparse(url).path
        if "/products/" not in path:
            out["status"]="unsupported_retailer";out["reason"]="Requires site-specific Scrapling extractor"
        else:
            base=url.split("?")[0].rstrip("/")
            response=Fetcher.get(base+".js", impersonate="chrome", stealthy_headers=True,timeout=35)
            data=response.json()
            if not isinstance(data,dict) or not isinstance(data.get("variants"),list):
                raise ValueError("No Shopify product JSON")
            variations=data["variants"]
            expected={str(row["sku"]).strip().casefold()}
            if row.get("competitor_sku"):expected.add(str(row["competitor_sku"]).strip().casefold())
            exact=[v for v in variations if str(v.get("sku") or "").strip().casefold() in expected and str(v.get("sku") or "").strip()]
            if len(exact)!=1:
                out["status"]="variant_unresolved"
                out["reason"]=f"Expected SKU {sorted(expected)}; exact matches={len(exact)}; variants={len(variations)}"
            else:
                v=exact[0]
                price=v.get("price")
                compare=v.get("compare_at_price")
                if price is None or not isinstance(price,(int,float)) or price<=0:
                    out["status"]="price_not_found";out["reason"]="Invalid variant price"
                else:
                    now=Decimal(str(price))/100
                    orig=Decimal(str(compare))/100 if isinstance(compare,(int,float)) and compare>price else None
                    out.update(status="success",regular_price=f"{(orig or now):.2f}",special_price=f"{now:.2f}" if orig else None,stock="in_stock" if v.get("available") is True else "sold_out" if v.get("available") is False else "unknown",verified_variant=True,validation_url=base+"?variant="+str(v["id"]),method="scrapling_shopify_product_json_exact",reason=None)
    except Exception as e:
        out["status"]="failed";out["reason"]=f"{type(e).__name__}: {str(e)[:250]}"
    results.append(out)
    print(json.dumps({"mapping":row["mapping_id"],"status":out["status"],"price":out["special_price"] or out["regular_price"]}),flush=True)
Path("novis_missing_results.json").write_text(json.dumps(results,indent=2))
with open("novis_missing_results.csv","w") as f:
    import csv
    writer=csv.DictWriter(f,fieldnames=list(results[0].keys()))
    writer.writeheader();writer.writerows(results)
print("SUMMARY",dict(collections.Counter(x["status"] for x in results)))
print("NO DATABASE WRITES. Review and explicitly approve before importing.")
