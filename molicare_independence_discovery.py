import re,json,concurrent.futures
from scrapling.fetchers import Fetcher
ROOT="https://store.independenceaustralia.com"
TASKS=[
ROOT+"/catalogsearch/result/?q=molicare",
ROOT+"/sitemap.xml",
ROOT+"/robots.txt",
ROOT+"/catalogsearch/result/index/?q=molicare",
ROOT+"/search?q=molicare"]
def one(url):
 r={"url":url}
 try:
  p=Fetcher.get(url,impersonate="chrome",stealthy_headers=True,timeout=30)
  r["status"]=int(p.status)
  r["len"]=len(p.body)
  tx=re.sub(r"\s+"," ",p.get_all_text(separator=" ",strip=True))
  r["excerpt"]=tx[:380]
  urls=[]
  for n in p.css('a[href]'):
   u=n.attrib.get("href","")
   label=n.get_all_text(strip=True)
   if "molicare" in u.lower() or "molicare" in label.lower():
    urls.append([label[:60],u[:180]])
  r["links"]=urls[:65]
  if "sitemap" in url and r["status"]==200:
   r["xml_excerpt"]=p.body[:600].decode("utf-8","replace") if isinstance(p.body,bytes) else str(p.body)[:600]
 except Exception as e:r.update(error=type(e).__name__+":"+str(e))
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:out=list(pool.map(one,TASKS))
print("IND_DISCOVERY_START")
print(json.dumps(out,separators=(",",":"),ensure_ascii=False))
print("IND_DISCOVERY_END")
