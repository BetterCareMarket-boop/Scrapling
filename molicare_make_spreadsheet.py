#!/usr/bin/env python3
"""Produce the approved seven-column MoliCare export from recorded Scrapling runs.
Read-only against historical runs and product snapshot. Never writes Supabase."""
from __future__ import annotations
import io,json,os,re,urllib.request,zipfile
from pathlib import Path
import xlsxwriter

OWNER="BetterCareMarket-boop"
REPO="Scrapling"
JOB_IDS=[
 125742829726,125744119048,125745629989,125746043261,
 125748112949,125750544292,125750876067,125751733776,125752961666,
 125755938690,125756396420,125757135636,125757544636,125758264141,
 125761645861,125762072755,125763039779,125764876305,125765258929,
 125766471835,125766962136,125769779242,125770246119,125770622336,
 125774711322,125775206644,125776653068
]
SKUS=[
 "915840","915831","166014","166015","915834",
 "166029","166030","166031","915874","166041",
 "166042","915880","168100","168077","168404",
 "168405","168406","168401","168408","168519",
 "168409","168132","168044","168045","168046",
 "168051","168600","168705","168801","168066",
 "168407","915861","166000","166001","915854",
 "161065","161070","161061","165271","165272",
 "165273","165274","165374","165474","165574",
 "165371","165372","165373","165471","165472",
 "165473","165571","165572","165573","165671",
 "165672","947790","947791","947792","947793",
 "947794","947711","947712","947713","947714",
 "947715","916680","995086","995088","995075",
 "995016","915867","915868","915817","915818",
 "995089","995087","168076","947789","915827",
 "166093","915877","915870"
]
assert len(SKUS)==83
FALLBACK_NAMES={
 "916680":"MoliCare Dignity Bariatric Brief Super - Carton 32",
 "166093":"MoliCare Premium Men Pants 7 Drops Large - Carton 28"
}
ALIASES={26:("168670","168051"),23:("168634","168044"),20:("168167","168519"),25:("168682","168046"),30:("168603","168066")}
HEADERS=["Our SKU","Product Name","Price","Competitor Price","Competitor Special Price","Competitor Name","Competitor URL"]

def get_log(job_id):
    url=f"https://api.github.com/repos/{OWNER}/{REPO}/actions/jobs/{job_id}/logs"
    req=urllib.request.Request(url,headers={
       "Authorization":f"Bearer {os.environ['GH_TOKEN']}",
       "Accept":"application/vnd.github+json",
       "X-GitHub-Api-Version":"2022-11-28",
       "User-Agent":"molicare-spreadsheet"})
    with urllib.request.urlopen(req,timeout=45) as resp: raw=resp.read()
    try:
       with zipfile.ZipFile(io.BytesIO(raw)) as z:
          return "\n".join(z.read(n).decode("utf-8","replace") for n in z.namelist() if n.endswith(".txt"))
    except zipfile.BadZipFile:
       return raw.decode("utf-8","replace")

def parse_log(text):
    markers=list(re.finditer(r"(?:SCRAPLING_MOLICARE_TEST_START|B3_FOLLOWUP_START|BATCH[A-Z0-9_]*START)",text))
    if not markers:return []
    marker=markers[-1].group(0)
    name=marker[:-5]
    start=markers[-1].end()
    ending=text.find(name+"END",start)
    seg=text[start:ending if ending>start else None]
    seg="\n".join(re.sub(r"^.*?Z ","",line) for line in seg.splitlines()).strip()
    a=seg.find("[")
    if a>=0:
        b=seg.rfind("]")
        if b>a:
            try:return json.loads(seg[a:b+1])
            except json.JSONDecodeError:pass
    a=seg.find("{")
    if a>=0:
        b=seg.rfind("}")
        if b>a:
            try:return [json.loads(seg[a:b+1])]
            except json.JSONDecodeError:pass
    return []

def canonical_competitor(name):
    if name.startswith("Platinum "):return "Platinum Health Supply"
    if name=="OzMedical":return "Oz Medical"
    if name=="Vital Medical":return "Vital Medical Supplies"
    return name

def main():
    products={x["sku"]:x for x in json.loads(Path("molicare_export_our_prices.json").read_text())}
    approved={}
    problems=[]
    for jobid in JOB_IDS:
        try: records=parse_log(get_log(jobid))
        except Exception as exc:
            problems.append(f"{jobid}: {exc}")
            continue
        for r in records:
            try: index=int(r.get("row",0))
            except:continue
            if not 1<=index<=83 or r.get("status")!="success":continue
            try:competitor_price=float(r["price"])
            except:continue
            competitor=str(r.get("retailer") or "").strip()
            url=str(r.get("variant_url") or r.get("url") or "").strip()
            if not competitor or not url.startswith("https://"):continue
            source_sku=str(r.get("manufacturer_sku") or r.get("product_sku") or r.get("reference_sku") or r.get("sku") or "")
            our_sku=SKUS[index-1]
            # Preserve historically accepted retailer alias variants; omit documented wrong carton for row 30.
            if index==30 and source_sku=="168603":continue
            # Earlier batch scripts sometimes stored the supplier's old SKU. Where both differ,
            # match must be approved by the earlier batch review.
            if source_sku and source_sku!=our_sku:
                if index==81 and source_sku in ("915828","166093"):pass
                elif index in ALIASES and source_sku in ALIASES[index]:pass
                elif index in (3,4,7,8,9,23,25,32,33,34):pass
                elif re.search(r"(?<!\d)"+re.escape(our_sku)+r"(?!\d)",source_sku):pass
                else:continue
            if r.get("special_price") is not None:
                try:special=float(r["special_price"])
                except:special=None
            else:special=None
            if special is not None and special>=competitor_price:special=None
            name=canonical_competitor(competitor)
            key=(index,name)
            # Later targeted workflow supersedes initial extraction for same competitor/product.
            approved[key]=(competitor_price,special,url)
    book=xlsxwriter.Workbook("molicare_competitor_prices.xlsx")
    ws=book.add_worksheet("Competitor Prices")
    dark=book.add_format({"bold":True,"font_color":"#FFFFFF","bg_color":"#18324C","valign":"vcenter","border":0})
    txt=book.add_format({"font_name":"Aptos","font_size":10,"valign":"vcenter"})
    currency=book.add_format({"font_name":"Aptos","font_size":10,"num_format":"$#,##0.00","valign":"vcenter"})
    urlfmt=book.add_format({"font_name":"Aptos","font_size":10,"font_color":"#1672BB","underline":1})
    for c,h in enumerate(HEADERS):ws.write(0,c,h,dark)
    ws.set_row(0,28)
    ws.set_column("A:A",16)
    ws.set_column("B:B",70)
    ws.set_column("C:E",23)
    ws.set_column("F:F",30)
    ws.set_column("G:G",80)
    ws.freeze_panes(1,0)
    rownum=1
    product_covered=set()
    for idx,sku in enumerate(SKUS,1):
        product=products.get(sku,{})
        name=product.get("product_name") or FALLBACK_NAMES.get(sku) or f"MoliCare product {idx}"
        price=product.get("our_price")
        price=float(price) if price is not None and str(price).strip() else None
        offers=sorted(((ret,*detail) for (num,ret),detail in approved.items() if num==idx),key=lambda x:x[0].lower())
        if not offers:offers=[("",None,None,"")]
        else:product_covered.add(idx)
        for retailer,regular,special,url in offers:
            ws.write_string(rownum,0,sku,txt)
            ws.write_string(rownum,1,name,txt)
            if price is not None:ws.write_number(rownum,2,price,currency)
            if regular is not None:ws.write_number(rownum,3,regular,currency)
            if special is not None:ws.write_number(rownum,4,special,currency)
            if retailer:ws.write_string(rownum,5,retailer,txt)
            if url:ws.write_url(rownum,6,url,urlfmt,url)
            rownum+=1
    ws.autofilter(0,0,rownum-1,6)
    book.close()
    print(json.dumps({"file":"molicare_competitor_prices.xlsx","rows":rownum-1,
       "unique_products":len(SKUS),"products_with_competitors":len(product_covered),
       "offers":len(approved),"errors":problems}))
if __name__=="__main__":main()
