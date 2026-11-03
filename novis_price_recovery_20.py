"""Exact product-target price scrape using Scrapling 0.5 only. Read-only."""
import json,re,html,csv
from pathlib import Path
from decimal import Decimal
from scrapling.fetchers import Fetcher

IDS={350,351,368,369,370,371,372,388,389,390,424,425,473,474,488,489,490,495,496,497}
def text(nodes):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',' '.join(nodes.getall())))).strip()
def price(raw):
    m=re.search(r'(?<!\d)(\d{1,6}(?:,\d{3})*\.\d{2})(?!\d)',raw)
    return Decimal(m.group(1).replace(',','')) if m else None
def scrape(t):
    r={**t,'status':'unresolved','regular_price':None,'special_price':None,'stock':'unknown','validation_url':t['competitor_url'],'extraction_method':None,'proof':None,'error':None}
    try:
        page=Fetcher.get(t['competitor_url'],impersonate='chrome',stealthy_headers=True,timeout=40)
        r['http_status']=getattr(page,'status',None)
        if r['http_status']!=200:
            r['status']='http_error';r['error']=str(r['http_status']);return r
        host=t['competitor_url'].split('/')[2].lower()
        title=text(page.css('h1'))
        if 'arthritissolutions' in host:
            expected=(t.get('competitor_sku') or t['sku']).strip()
            if expected.lower() not in title.lower():
                r['status']='sku_mismatch';r['error']='Product code not in H1: '+title[:150];return r
            hits=page.css('span.product-price-value #product_price').getall()
            if len(hits)!=1:
                r['status']='price_unresolved';r['error']='Expected 1 main product_price, got '+str(len(hits));return r
            p=price(text(page.css('span.product-price-value #product_price')))
            if not p:r['status']='price_unresolved';return r
            r.update(status='verified_exact_retailer_code',regular_price=f'{p:.2f}',extraction_method='scrapling_arthritis_product_price_exact',proof='H1 product code: '+expected+'; #product_price')
            # ETAC 80404042 is not proven same as NOVIS base 804040.
            if t['sku']=='804040':
                r.update(status='candidate_retailer_sku_alias',proof='Retailer ETAC-80404042 vs NOVIS 804040; user verification required')
        elif 'feroscare' in host:
            titles={'KC85':['bottle','twizoff'],'KC12':['jar','opener'],'KC26':['can','opener']}
            terms=titles.get(t['sku'],[])
            if not all(x in title.lower() for x in terms):
                r['status']='title_mismatch';r['error']=title[:160];return r
            p=price(text(page.css('.bde-wooproductprice > p.price')))
            if not p:r['status']='price_unresolved';return r
            r.update(status='candidate_product_title',regular_price=f'{p:.2f}',extraction_method='scrapling_feros_primary_product_price',proof='Product title '+title+'; primary bde-wooproductprice; no explicit SKU proof')
        elif 'astleymobility' in host:
            terms={'KC85':['bottle','opener'],'KC12':['jar','opener'],'KC26':['can','opener']}.get(t['sku'],[])
            if not all(x in title.lower() for x in terms):
                r['status']='title_mismatch';r['error']=title[:160];return r
            nodes=page.css('[itemprop="price"][content]')
            if len(nodes)!=1:r['status']='price_unresolved';r['error']='itemprop price nodes='+str(len(nodes));return r
            snippet=nodes.getall()[0]
            m=re.search(r'\bcontent="(\d+(?:\.\d{1,2})?)"',snippet)
            if not m:r['status']='price_unresolved';return r
            p=Decimal(m.group(1))
            r.update(status='candidate_product_title',regular_price=f'{p:.2f}',extraction_method='scrapling_astley_product_itemprop_price',proof='Product title '+title+'; itemprop=price; no explicit SKU proof')
    except Exception as e:
        r.update(status='fetch_failed',error=str(type(e).__name__)+': '+str(e)[:250])
    return r
targets=json.loads(Path('novis_missing_targets.json').read_text())
targets=[t for t in targets if int(t['mapping_id']) in IDS]
assert len(targets)==20,len(targets)
rows=[]
for t in targets:
    r=scrape(t);rows.append(r)
    print(r['mapping_id'],r['sku'],r['status'],r.get('regular_price'),flush=True)
Path('novis_price_recovery_20.json').write_text(json.dumps(rows,indent=2))
with open('novis_price_recovery_20.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Completed',len(rows),'read-only Scrapling targets')
