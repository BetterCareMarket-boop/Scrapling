"""Extract WooCommerce Tasty Beaker variation prices strictly with Scrapling."""
import re,json,html
from pathlib import Path
from scrapling.fetchers import Fetcher
url='https://www.patienthandling.com.au/product/etac-tasty-beaker/'
page=Fetcher.get(url,impersonate='chrome',stealthy_headers=True,timeout=45)
forms=page.css('form.variations_form').getall()
result={'url':url,'status':getattr(page,'status',None),'form_count':len(forms),'variations':[]}
if forms:
 m=re.search(r'data-product_variations=(["\'])(.*?)\1',forms[0],re.S)
 if m:
  data=json.loads(html.unescape(m.group(2)))
  for v in data:
   result['variations'].append({'attributes':v.get('attributes'),'regular':v.get('display_regular_price'),'price':v.get('display_price'),'sku':v.get('sku'),'variation_id':v.get('variation_id'),'is_in_stock':v.get('is_in_stock'),'availability_html':v.get('availability_html')})
 else:result['error']='product variation data not embedded'
Path('novis_tasty_beaker_variants.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2)[:10000])
