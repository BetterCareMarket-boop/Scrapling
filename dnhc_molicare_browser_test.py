from scrapling.fetchers import StealthyFetcher, Fetcher
import json,time
URL="https://www.dnhc.com.au/CONTINENCE/All_dash_In_dash_One/pl.php"
urls=[URL,"https://dnhc.com.au/CONTINENCE/All_dash_In_dash_One/pl.php"]
result=[]
for name,u in [("static_alt",urls[1]),("stealth",URL)]:
    start=time.time()
    try:
        if name=="stealth":
            p=StealthyFetcher.fetch(u,headless=True,solve_cloudflare=True,timeout=60000)
        else:
            p=Fetcher.get(u,impersonate="chrome",timeout=20)
        t=p.get_all_text(separator=" ",strip=True)
        result.append({"method":name,"status":int(p.status),"url":u,"seconds":round(time.time()-start,1),"text":t[:650],"codes":t.count("Product Code:")})
        if int(p.status)==200 and "Product Code:" in t:break
    except Exception as e:
        result.append({"method":name,"error":type(e).__name__+": "+str(e)[:450]})
print("DNHC_BROWSER_TEST_START")
print(json.dumps(result,indent=2))
print("DNHC_BROWSER_TEST_END")
