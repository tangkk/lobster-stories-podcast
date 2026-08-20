#!/usr/bin/env python3
"""Paragraph-aware long-form TTS. Canonical text is unchanged; only synthesis boundaries are controlled."""
import argparse,os,re,subprocess,tempfile
from xfyun_super_official_run import load_profile,run_once
SENTENCE=re.compile(r'(?<=[。！？!?])')
def split_text(text,max_chars=420):
    out=[]
    for p in [x.strip() for x in re.split(r'\n\s*\n+',text.strip()) if x.strip()]:
        if len(p)<=max_chars: out.append(p); continue
        buf=''
        for s in [x.strip() for x in SENTENCE.split(p) if x.strip()]:
            if buf and len(buf)+len(s)>max_chars: out.append(buf);buf=s
            else: buf+=s
        if buf: out.append(buf)
    return out
def main():
    a=argparse.ArgumentParser();a.add_argument('--text-file',required=True);a.add_argument('--out',required=True);a.add_argument('--profile',default='default');a.add_argument('--pause-ms',type=int,default=350);a.add_argument('--max-chars',type=int,default=420);args=a.parse_args()
    for k in ('XFYUN_APPID','XFYUN_API_KEY','XFYUN_API_SECRET'):
        if not os.environ.get(k): raise RuntimeError('Missing '+k)
    text=open(args.text_file,encoding='utf-8').read();segs=split_text(text,args.max_chars);p=load_profile(args.profile);v=p.get('voice','x6_wennuancixingnansheng_mini');sp=p.get('speed',42);vol=p.get('volume',52);pi=p.get('pitch',47);url=p.get('ws_url','wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6')
    with tempfile.TemporaryDirectory() as d:
        parts=[]
        for i,s in enumerate(segs):
            path=os.path.join(d,f'{i:03d}.mp3');run_once(url,path,v,s,sp,vol,pi);parts.append(path)
        sil=os.path.join(d,'silence.mp3');subprocess.run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t',str(args.pause_ms/1000),'-q:a','9',sil],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        lst=os.path.join(d,'concat.txt');f=open(lst,'w');
        for i,x in enumerate(parts): f.write("file '%s'\n"%x); f.write("file '%s'\n"%sil) if i<len(parts)-1 else None
        f.close();subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',lst,'-c:a','libmp3lame','-ar','24000','-ac','1',args.out],check=True)
    print(f'OK: {args.out} | segments={len(segs)} pause={args.pause_ms}ms')
if __name__=='__main__':main()
