"""Read-only Scrapling audit of 62 unmapped NOVIS prices."""
import csv,json,re
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from scrapling.fetchers import Fetcher
IDS={345,350,351,357,358,359,360,362,368,369,370,371,372,377,378,379,388,389,390,401,402,403,424,425,435,437,438,439,440,443,444,463,464,465,466,473,474,487,488,489,490,491,495,496,497}
HINTS={421:['extension','30'],437:['extension','30'],438:['60'],439:['30'],469:['complete'],476:['complete'],483:['complete'],463:['bathroom'],464:['kitchen'],465:['bedroom'],487:['toilet'],345:['emerald'],359:['king fisher'],357:['long'],358:['short'],378:['long'],379:['short']}
def dollars(n):
    if not isinstance(n,(int,float)) or isinstance(n,bool) or n<=0:return None
    return Decimal(str(n))/100
def fmt(n):return f"{n:.2f}" if n is not None else None
def clean(url):
    u=urlsplit(url)
    return urlunsplit((u.scheme,u.netloc,u.path.rstrip('/'),'',''))
def run(t):
    result={**t,'status':'unresolved','regular_price':None,'special_price':None,'candidate_price':None,'stock':'unknown','validation_url':t['competitor_url'],'method':None,'reason':None}
    url=t['competitor_url']; mid=int(t['mapping_id'])
    try:
        if '/products/' in urlsplit(url).path:
            base=clean(url)
            data=Fetcher.get(base+'.js',impersonate='chrome',stealthy_headers=True,timeout=35).json()
            variants=data.get('variants') or []
            expected={str(t['sku']).strip().casefold()}
            if t.get('competitor_sku'):expected.add(str(t['competitor_sku']).strip().casefold())
            exact=[v for v in variants if v.get('sku') and str(v['sku']).strip().casefold() in expected]
            if len(exact)==1:
                v=exact[0];now=dollars(v.get('price'));compare=dollars(v.get('compare_at_price'))
                if now:
                    orig=compare if compare and compare>now else None
                    result.update(status='verified_exact_sku',regular_price=fmt(orig or now),special_price=fmt(now) if orig else None,stock='in_stock' if v.get('available') is True else 'sold_out' if v.get('available') is False else 'unknown',validation_url=base+'?variant='+str(v.get('id')),method='scrapling_shopify_product_json_exact',reason='Exact SKU')
                else:result.update(status='price_not_found',reason='Missing selected-variant price')
            else:
                hints=HINTS.get(mid,[])
                candidates=[v for v in variants if hints and all(h in ' '.join(str(v.get(k) or '') for k in ('title','option1','option2','option3')).casefold() for h in hints)]
                if len(candidates)==1 or len(variants)==1:
                    v=(candidates if len(candidates)==1 else variants)[0]
                    result.update(status='candidate_needs_variant_validation',candidate_price=fmt(dollars(v.get('price'))),validation_url=base+'?variant='+str(v.get('id')),reason='SKU did not match; price is candidate only')
                else:result.update(status='variant_unresolved',reason=f'No exact match among {len(variants)} variants')
        else:
            page=Fetcher.get(url,impersonate='chrome',stealthy_headers=True,timeout=35)
            if int(getattr(page,'status',200))>=400:result.update(status='http_blocked',reason=f'HTTP {page.status}')
            else:
                docs=[]
                for raw in page.css('script[type="application/ld+json"]::text').getall():
                    try:
                        stack=[json.loads(raw)]
                        while stack:
                            obj=stack.pop()
                            if isinstance(obj,list):stack+=obj
                            if isinstance(obj,dict):
                                if obj.get('@type')=='Product':docs.append(obj)
                                for key in ('@graph','mainEntity','hasVariant'):
                                    if key in obj:stack.append(obj[key])
                    except (ValueError,TypeError):pass
                expected={str(t['sku']).strip().casefold(),str(t.get('competitor_sku') or '').strip().casefold()}
                matches=[d for d in docs if d.get('sku') and str(d['sku']).strip().casefold() in expected]
                if len(matches)==1:
                    offers=matches[0].get('offers') or []
                    if isinstance(offers,dict):offers=[offers]
                    prices=[]
                    for offer in offers:
                        try:
                            p=Decimal(str(offer.get('price')))
                            if 0<p<100000:prices.append(p)
                        except Exception:pass
                    if len(set(prices))==1:
                        result.update(status='verified_exact_sku',regular_price=fmt(prices[0]),method='scrapling_jsonld_exact_sku',reason='Exact SKU with one JSON-LD price')
                    else:result.update(status='needs_retailer_extractor',reason='Ambiguous JSON-LD offer prices')
                else:result.update(status='needs_retailer_extractor',reason='No scoped exact SKU JSON-LD price. No generic page price accepted.')
    except Exception as e:result.update(status='fetch_failed',reason=f'{type(e).__name__}: {str(e)[:250]}')
    return result
targets=json.loads(Path('novis_missing_targets.json').read_text())
targets=[t for t in targets if int(t['mapping_id']) in IDS]
assert len(targets)==62,len(targets)
results=[]
for target in targets:
    r=run(target);results.append(r)
    print(f"{r['mapping_id']}: {r['status']} {r['regular_price'] or r['candidate_price'] or ''}",flush=True)
Path('novis_remaining_45_results.json').write_text(json.dumps(results,indent=2))
with open('novis_remaining_45_results.csv','w',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
from collections import Counter
print('SUMMARY',dict(Counter(r['status'] for r in results)))
print('Read-only audit: do not import candidate/unresolved records')def scrape_nonshopify(t,out):
  url=t['competitor_url']
  mid=int(t['mapping_id'])
  page=Fetcher.get(url,impersonate='chrome',stealthy_headers=True,timeout=35)
  out['http_status']=getattr(page,'status',None)
  if out['http_status'] and out['http_status']>=400:
    out.update(status='blocked_or_http_error',reason='HTTP '+str(out['http_status']))
    return
  full=' '.join(page.css('body').get_all_text(separator=' ',strip=True).split())
  title=' '.join(page.css('h1').get_all_text(separator=' ',strip=True).split())
  expected=[str(t['sku']).strip(),str(t.get('competitor_sku') or '').strip()]
  # A SKU in the product title, URL, or explicit product-code element is stronger
  # than an incidental mention in a footer or recommendations widget.
  url_token=any(k and k.casefold() in url.casefold() for k in expected)
  product_code=' '.join(page.css('.product-info, .product_meta, [itemprop="sku"], .sku, .product-code, .product-code-value').get_all_text(separator=' ',strip=True).split())
  sku_scoped=url_token or any(k and k.casefold() in (title+' '+product_code).casefold() for k in expected)
  if not sku_scoped and any(k and k.casefold() in full.casefold() for k in expected):
    out['reason']='SKU appears in body but not in a reliable product identity area'
  # Product JSON-LD exact SKU and unambiguous offer, when available.
  objs=[]
  for raw in page.css('script[type="application/ld+json"]::text').getall():
    try:
      stack=[json.loads(raw)]
      while stack:
        obj=stack.pop()
        if isinstance(obj,list):stack.extend(obj)
        elif isinstance(obj,dict):
          if obj.get('@type')=='Product' or (isinstance(obj.get('@type'),list) and 'Product' in obj['@type']):objs.append(obj)
          for key in ('@graph','hasVariant','mainEntity'):
            if key in obj:stack.append(obj[key])
    except (ValueError,TypeError):pass
  matches=[x for x in objs if str(x.get('sku') or '').strip().casefold() in {k.casefold() for k in expected if k}]
  if len(matches)==1:
    offers=matches[0].get('offers') or []
    if isinstance(offers,dict):offers=[offers]
    prices=[]
    for offer in offers:
      try:
        v=Decimal(str(offer.get('price')))
        if 0<v<100000:prices.append(v)
      except Exception:pass
    if len(set(prices))==1:
      out.update(status='verified_exact_sku',regular_price=money(prices[0]),method='scrapling_jsonld_exact_sku',reason='Exact SKU JSON-LD offer')
      return
  # Retailer-specific price regions: excludes navigation, related-product
  # carousel prices, cart subtotal, and footer offers.
  host=urlsplit(url).hostname or ''
  selectors=[]
  if 'arthritissolutions' in host:
    selectors=['[itemprop="price"]','.product-price','.price','.productPrice','td.price']
  elif 'mobilityzone' in host:
    # Family-level pricing is never assigned to an individual signage SKU.
    out.update(status='family_variant_unresolved',reason='Four signage variants share one family URL; SKU-specific price not proven')
    return
  elif 'patienthandling' in host:
    selectors=['.productSummary .priceSection .productPrice','.productSummary .priceSection','.product-summary .price']
  elif 'astleymobility' in host or 'ilcmc' in host:
    selectors=['.ProductPrice','.product-price','.price-value','[itemprop="price"]']
  elif 'feroscare' in host or 'healthylivinghub' in host or 'gmobility' in host:
    selectors=['.summary .price','.product .summary .price','.product-price','[itemprop="price"]']
  else:
    selectors=['[itemprop="price"]','.product .summary .price','.product-price']
  candidates=[]
  for sel in selectors:
    try:
      nodes=page.css(sel)
      if not nodes:continue
      raw=' '.join(nodes.get_all_text(separator=' ',strip=True).split())
      for hit in re.findall(r'(?<!\\d)\\$\\s*([0-9][0-9,]*(?:\\.[0-9]{1,2})?)',raw):
        v=Decimal(hit.replace(',',''))
        if 0<v<100000:candidates.append((sel,v))
      if candidates:break
    except Exception:continue
  if sku_scoped and len({v for _,v in candidates})==1:
    out.update(status='candidate_scoped_price_requires_validation',candidate_price=money(candidates[0][1]),method='scrapling_retailer_scoped_price',reason='SKU identity and scoped price detected; manual confirmation required',price_selector=candidates[0][0])
  elif len({v for _,v in candidates})>1:
    out.update(status='ambiguous_product_prices',reason='Several different prices in scoped product elements; must verify regular/special relationship',price_selector=candidates[0][0])
  else:
    out.update(status='needs_retailer_extractor',reason=out.get('reason') or 'No exact-SKU scoped public price available')

