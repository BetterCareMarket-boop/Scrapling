"""Scrapling-only retailer diagnostics. No DB writes or alternate price capture."""
import json,re,html
from collections import Counter
from pathlib import Path
from scrapling.fetchers import Fetcher
targets=json.loads(Path('novis_missing_targets.json').read_text())
target_ids={345,350,351,357,358,359,368,369,370,371,372,377,378,379,388,389,390,401,402,424,425,435,473,474,463,464,465,487,488,489,490,495,496,497}
targets=[r for r in targets if r['mapping_id'] in target_ids]
out=[]
for t in targets:
  item={k:t.get(k) for k in ('mapping_id','sku','product_name','competitor_name','competitor_url','competitor_sku','competitor_variant_hint')}
  try:
    page=Fetcher.get(t['competitor_url'],impersonate='chrome',stealthy_headers=True,timeout=35)
    item['http_status']=getattr(page,'status',None)
    raw=' '.join(page.css('body').getall())
    text=html.unescape(re.sub(r'<[^>]+>',' ',raw))
    text=re.sub(r'\\s+',' ',text)
    for label,regex in [('currency_dollar',r'\\$\\s*[0-9][0-9,]*(?:\\.[0-9]{1,2})?'),('aud_code',r'(?:AUD|Price|Our Price|Special Price|Sale Price)\\s*[:\\$]?\\s*[0-9][0-9,]*(?:\\.[0-9]{1,2})?')]:
      hits=list(re.finditer(regex,text,re.I))
      item[label+'_count']=len(hits)
      item[label+'_context']=[text[max(0,m.start()-120):m.end()+130] for m in hits[:7]]
    item['sku_context']=[]
    for sku in (t['sku'],t.get('competitor_sku')):
      if not sku:continue
      hits=list(re.finditer(re.escape(sku),text,re.I))
      item['sku_context']+= [text[max(0,m.start()-90):m.end()+90] for m in hits[:3]]
    item['title']=re.sub(r'\\s+',' ',html.unescape(re.sub('<[^>]+>',' ',' '.join(page.css('h1').getall()))))[:250]
    item['body_lead']=text[:500]
    item['selectors']={}
    for sel in ['[itemprop="price"]','meta[property="product:price:amount"]','.price','.ProductPrice','.productPrice','.product-price','.priceSection','.woocommerce-Price-amount','.product-details','.productInfo','[class*="price"]','[id*="price"]','form']:
      try:
        snippets=page.css(sel).getall()
        if snippets:item['selectors'][sel]=[re.sub(r'\\s+',' ',x)[:420] for x in snippets[:3]]
      except Exception as e:item['selectors'][sel]=['ERR '+str(e)[:90]]
    item['script_tokens']={}
    for token in ['price','special','offer','sku','product_id','Cloudflare','cf_chl']:
      item['script_tokens'][token]=len(re.findall(token,raw,re.I))
  except Exception as e:item['error']=f'{type(e).__name__}: {str(e)[:280]}'
  out.append(item)
  print(item['mapping_id'],item.get('http_status'),item.get('currency_dollar_count'),item.get('aud_code_count'),item.get('error',''),flush=True)
Path('novis_retailer_diagnostics.json').write_text(json.dumps(out,indent=2))
print('RESULTS',len(out),'HTTP',dict(Counter(str(x.get('http_status')) for x in out)))
