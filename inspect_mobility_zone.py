import re
from scrapling.fetchers import Fetcher

url="https://mobilityzone.com.au/product/orientation-signage-better-living/"
page=Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=30)

body=page.css("body").get() or ""
for needle in ["$ 51.50","$51.50","51.50","Bedroom","Kitchen","Bathroom","Toilet"]:
    p=body.lower().find(needle.lower())
    if p>=0:
        print("CTX",needle,re.sub(r"\s+"," ",body[max(0,p-1800):p+3500]))

print("H1",page.css("h1::text").getall())
print("PRICES",page.css(".price").getall())
print("SELECTS",page.css("select").getall())
print("VARIATIONS",page.css(".variations").getall())
print("SUMMARY",page.css(".summary").getall())
