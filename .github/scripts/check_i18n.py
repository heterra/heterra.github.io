#!/usr/bin/env python3
"""Check the website's translations: python3 .github/scripts/check_i18n.py

English and Simplified Chinese are written in the pages. The other six languages are in
assets/i18n/<code>.js, { English html: translated html }; the page's script puts each translation
in the place of the English text, and a text without one stays in English. This lists, for each
language, the English texts of index.html and index-stats.html without a translation, the
translations no longer used, and translations whose HTML tags differ from the English.
With --strings it prints the English texts as JSON, to give to a translator.
"""
import json
import pathlib
import re
import sys
from html.parser import HTMLParser
VOID={'img','br','meta','link','input','hr','source'}
def k(h): return re.sub(r'\s+',' ',h).strip()
class P(HTMLParser):
    def __init__(s,src):
        super().__init__(convert_charrefs=False); s.src=src; s.lines=[0]
        for l in src.split('\n'): s.lines.append(s.lines[-1]+len(l)+1)
        s.stack=[]; s.out=[]; s.inbody=False
    def off(s): l,c=s.getpos(); return s.lines[l-1]+c
    def handle_starttag(s,tag,attrs):
        if tag in VOID: return
        a=dict(attrs); cls=(a.get('class') or '').split()
        if tag=='body': s.inbody=True
        par=s.stack[-1] if s.stack else None
        want=False
        if s.inbody and a.get('lang')=='en' and 'zoom' not in cls and 'subscribe' not in cls: want=True
        if par and par['sub'] and tag in('h3','p'): want=True
        if 'copy' in cls and any(x['sub'] for x in s.stack): want=True
        s.stack.append({'tag':tag,'want':want,'start':s.off()+len(s.get_starttag_text()),'sub':('subscribe' in cls and a.get('lang')=='en'),'lang':a.get('lang')})
    def handle_endtag(s,tag):
        if tag in VOID: return
        while s.stack:
            e=s.stack.pop()
            if e['tag']==tag:
                if e['want']: s.out.append(k(s.src[e['start']:s.off()]))
                break
ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT_TEXTS = ["Copied", "total", "new that day"]  # put in by scripts, through window.heterraText


def strings():
    out = []
    for f in ("index.html", "index-stats.html"):
        path = ROOT / f
        if not path.exists():
            continue
        src = path.read_text(encoding="utf-8")
        p = P(src)
        p.feed(src)
        for x in [re.search(r"<title>(.*?)</title>", src).group(1)] + p.out + SCRIPT_TEXTS:
            if x not in out:
                out.append(x)
    return out


def tags(html):
    return sorted(re.findall(r"<[^>]+>", html))


def main():
    texts = strings()
    if "--strings" in sys.argv:
        json.dump(texts, sys.stdout, ensure_ascii=False, indent=1)
        return 0
    bad = 0
    for path in sorted((ROOT / "assets" / "i18n").glob("*.js")):
        # the file is one assignment of a JSON object
        source = path.read_text(encoding="utf-8")
        table = json.loads(source[source.index("] = {") + 4:].rstrip().rstrip(";"))
        missing = [t for t in texts if not table.get(t)]
        unused = [t for t in table if t not in texts]
        wrong = [t for t in texts if table.get(t) and tags(table[t]) != tags(t)]
        print(f"{path.stem}: {len(texts)} texts, {len(missing)} missing, {len(unused)} unused, {len(wrong)} with other tags")
        for name, group in (("missing", missing), ("unused", unused), ("other tags", wrong)):
            for t in group:
                print(f"  {name}: {t[:90]}")
        bad += len(missing) + len(wrong)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
