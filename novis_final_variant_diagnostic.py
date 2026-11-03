"""Scrapling inspection of final retailer SKUs and dynamic product variants, read-only."""
import json,re,html
from pathlib import Path
from decimal import Decimal
from scrapling.fetchers import Fetcher
targets=json.loads(Path('novis_missing_targets.json').read_text())
IDS={443,444,437,438,439,466,463,464,465,487,403}
rows=[]
for t in targets:
 if t['mapping_id'] not in IDS:continue
 r={**t,'price':None,'price_basis':None,'status':'unresolved','variant_data':None}
 try:
  page=Fetcher.get(t['competitor_url'],impersonate='chrome',stealthy_headers=True,timeout=40)
  r['http']=getattr(page,'status',None)
  if t['mapping_id'] in (443,444):
   raw=' '.join(page.css('body').getall())
   h=html.unescape(re.sub(r'<[^>]+>',' ',raw))
   m=re.search(r'SKU:\s*(NOV-[0-9]+)',h,re.I)
   r['retailer_sku']=m.group(1) if m else None
   prices=page.css('[itemprop="price"]').getall()
   r['price_nodes']=[re.sub(r'\s+',' ',x)[:250] for x in prices[:3]]
   target_sku='NOV-'+t['sku']
   if r['retailer_sku'] == target_sku and prices:
    m=re.search(r'\$\s*([0-9][0-9,]*(?:\.[0-9]{2})?)',html.unescape(re.sub('<[^>]+>',' ',prices[0])))
    if m:r.update(price=m.group(1),status='candidate_explicit_retailer_sku',price_basis='first main product itemprop price; retailer SKU '+target_sku)
  if t['mapping_id'] in (437,438,439):
   url=t['competitor_url'].split('?')[0].rstrip('/')
   product=Fetcher.get(url+'.js',impersonate='chrome',stealthy_headers=True,timeout=40).json()
   r['variant_data']=[{'id':v.get('id'),'title':v.get('title'),'sku':v.get('sku'),'price':v.get('price'),'compare_at_price':v.get('compare_at_price'),'available':v.get('available')} for v in product.get('variants',[])]
  if t['mapping_id']==466:
   forms=page.css('form.variations_form').getall()
   r['form_excerpt']=forms[0][:14000] if forms else None
  if t['mapping_id'] in (463,464,465,487):
   r['option_excerpt']=[x[:2200] for x in page.css('form.cart,select,[data-product_variations],.variations').getall()[:4]]
   r['product_price_excerpt']=[x[:900] for x in page.css('.elementor-widget-woocommerce-product-price').getall()[:1]]
  if t['mapping_id']==403:
   r['price_excerpt']=[x[:1000] for x in page.css('[itemprop="price"],[class*="price"],[class*="Price"]').getall()[:3]]
 except Exception as e:r['error']=type(e).__name__+': '+str(e)[:300]
 rows.append(r)
 print(r['mapping_id'],r['status'],r.get('price'),r.get('http'),flush=True)
Path('novis_final_variant_diagnostic.json').write_text(json.dumps(rows,indent=2))
print('DONE',len(rows))
