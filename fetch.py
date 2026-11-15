import re, subprocess, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
B="https://raw.githubusercontent.com/chadwickbureau/retrosheet/master/"
def get(url, tries=3):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r: return r.read()
        except Exception as e: err=e
    return None
def season_files(y):
    h=get(f"https://github.com/chadwickbureau/retrosheet/tree/master/seasons/{y}")
    if not h: return []
    s=set(re.findall(rf'seasons/{y}/({y}[A-Z]{{3}}\.EV[AN])', h.decode()))
    return sorted(s)
def dl(args):
    y,f=args
    p=f"raw/{f}"
    if os.path.exists(p): return 1
    d=get(B+f"seasons/{y}/{f}")
    if d: open(p,"wb").write(d); return 1
    return 0
years=range(2010,2026)
jobs=[]
for y in years:
    fs=season_files(y); print(y,len(fs),flush=True)
    jobs+=[(y,f) for f in fs]
with ThreadPoolExecutor(12) as ex: r=list(ex.map(dl,jobs))
print(sum(r),len(r))
for y in years:
    p=f"raw/GL{y}.TXT"
    if not os.path.exists(p):
        d=get(B+f"gamelog/GL{y}.TXT")
        if d: open(p,"wb").write(d)
