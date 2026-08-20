#!/usr/bin/env python3
"""Conservatively derive a TTS transcript from canonical Markdown/plain text."""
import argparse, json, re
from pathlib import Path
DIGITS = str.maketrans("0123456789", "零一二三四五六七八九")
def prepare(text, d):
    text=re.sub(r"!\[[^]]*\]\([^)]*\)","",text); text=re.sub(r"\[([^]]+)\]\([^)]*\)",r"\1",text); text=re.sub(r"https?://\S+","",text)
    text=re.sub(r"^\s{0,3}#{1,6}\s*","",text,flags=re.M); text=re.sub(r"[*_`]+","",text); text=re.sub(r"^\s*>\s?","",text,flags=re.M)
    text=re.sub(r"(\d+(?:\.\d+)?)\s*%",r"百分之\1",text); text=re.sub(r"\b((?:19|20)\d{2})(?=\s*年)",lambda m:m.group(1).translate(DIGITS),text)
    for k in sorted(d,key=len,reverse=True): text=text.replace(k,d[k])
    return re.sub(r"\n{3,}","\n\n",re.sub(r"[ \t]+"," ",text)).strip()+"\n"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("-o","--output"); ap.add_argument("--dict",dest="dict_path"); a=ap.parse_args(); base=Path(__file__).resolve().parent
    p=Path(a.dict_path) if a.dict_path else base/"pronunciation.json"; d=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}; out=prepare(Path(a.input).read_text(encoding="utf-8"),d)
    Path(a.output).write_text(out,encoding="utf-8") if a.output else print(out,end="")
if __name__=="__main__": main()
