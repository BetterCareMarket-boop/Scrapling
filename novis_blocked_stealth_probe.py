"""One-time Scrapling StealthyFetcher test of three blocked NOVIS retailer pages."""
import json,re,html
from pathlib import Path
from scrapling.fetchers import Fetcher,StealthyFetcher
targets=[
('Solutions Medical','https://www.solutionsmedical.net.au/index.php?product_id=5201&route=product%2Fproduct',['Sensory Cushion','BL0065']),
('Rehab Hire & Sales','https://www.rehabhire.com.au/product/stander-handybar/',['Stander','Handy']),
('Max Healthcare Equipment','https://www.maxhealthcareequipment.com.au/product/etac-flex-grab-rails-screw-mounted/',['Etac','Flex'])
]
rows=[]
for brand,url,terms in targets:
 try:
  page=StealthyFetcher.fetch(url,headless=True,solve_cloudflare=True,network_idle=True,timeout=60000)
  txt=re.sub(r'\s+',' ',page.get_all_text(separator=' ',strip=True))
  r={'competitor':brand,'url':url,'status':getattr(page,'status',None),'title':page.css('title::text').getall()[:2],'length':len(txt),'identity_hits':[x for x in terms if x.casefold() in txt.casefold()],'price_samples':re.findall(r'\$\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?',txt)[:15],'lead':txt[:500]}
 except Exception as e:r={'competitor':brand,'url':url,'error':type(e).__name__+': '+str(e)[:350]}
 rows.append(r);print(json.dumps(r)[:1200],flush=True)
Path('novis_blocked_stealth_probe.json').write_text(json.dumps(rows,indent=2))
