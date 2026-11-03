"""Read-only Scrapling audit of 62 unmapped NOVIS prices."""
import csv,json,re
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from scrapling.fetchers import Fetcher
IDS={345,346,347,350,351,352,357,358,359,360,362,368,369,370,371,372,377,378,379,384,388,389,390,391,392,393,401,402,403,418,419,421,424,425,435,437,438,439,440,442,443,444,463,464,465,466,469,473,474,476,482,483,487,488,489,490,491,495,496,497,500,501}
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
Path('novis_remaining_62_results.json').write_text(json.dumps(results,indent=2))
with open('novis_remaining_62_results.csv','w',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
from collections import Counter
print('SUMMARY',dict(Counter(r['status'] for r in results)))
print('Read-only audit: do not import candidate/unresolved records')
