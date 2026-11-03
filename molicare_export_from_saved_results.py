from __future__ import annotations
import base64,json,zlib,zipfile,xml.etree.ElementTree as ET
import molicare_make_spreadsheet as m

sources={}
for part in (1,2,3):
    with open(f"molicare_offers_chunk{part}.json",encoding="utf-8") as fh:
        sources.update(json.load(fh))

m.get_log=lambda jobid: jobid
m.parse_log=lambda jobid: sources.get(str(jobid),[])
m.main()

file="molicare_competitor_prices.xlsx"
ns={"x":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
with zipfile.ZipFile(file) as z:
    strings=[]
    if "xl/sharedStrings.xml" in z.namelist():
        ss=ET.fromstring(z.read("xl/sharedStrings.xml"))
        strings=["".join(node.text or "" for node in si.findall(".//x:t",ns)) for si in ss.findall("x:si",ns)]
    root=ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows=[]
    for row in root.findall(".//x:sheetData/x:row",ns):
        vals=[None]*7
        for c in row.findall("x:c",ns):
            name=c.get("r","")
            letters="".join(x for x in name if x.isalpha())
            if not letters or len(letters)!=1 or not "A"<=letters<="G":continue
            col=ord(letters)-ord("A")
            v=c.find("x:v",ns)
            if v is None:continue
            text=v.text or ""
            if c.get("t")=="s":vals[col]=strings[int(text)]
            elif c.get("t")=="inlineStr":
                t=c.find(".//x:t",ns)
                vals[col]=t.text if t is not None else ""
            elif col in (2,3,4):
                vals[col]=float(text) if text else None
            else:vals[col]=text
        rows.append(vals)
payload=base64.b64encode(zlib.compress(json.dumps(rows,separators=(",",":"),ensure_ascii=True).encode("utf-8"),9)).decode("ascii")
print("SPREADSHEET_DATA_START")
for i in range(0,len(payload),160):print(payload[i:i+160])
print("SPREADSHEET_DATA_END")
print("EXPORT_ROWS",len(rows)-1)
