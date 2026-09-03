#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, time, urllib.request, xml.etree.ElementTree as ET
ITUNES='http://www.itunes.com/dtds/podcast-1.0.dtd'
def download(url,path):
    req=urllib.request.Request(url,headers={'User-Agent':'lobster-podcast-release-verifier','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=30) as r, open(path,'wb') as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            f.write(c)
def verify_audio(url,b,duration):
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'episode.mp3'); download(url+('&' if '?' in url else '?')+f'verify={int(time.time())}',p)
        if os.path.getsize(p)!=b: raise RuntimeError('public MP3 size mismatch')
        s=round(float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',p],text=True).strip())); got=f'{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}'
        if got!=duration: raise RuntimeError(f'public MP3 duration mismatch: {got}')
def verify_feed(repo,slug,url,b,duration):
    base=f'https://raw.githubusercontent.com/{repo}/main/feed.xml'; last=None
    for n in range(30):
        try:
            req=urllib.request.Request(base+f'?verify={int(time.time())}-{n}',headers={'User-Agent':'lobster-podcast-release-verifier','Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=20) as r: data=r.read()
            ch=ET.fromstring(data).find('channel'); items=[i for i in ch.findall('item') if (i.findtext('guid') or '')==slug]
            if len(items)!=1: raise RuntimeError(f'expected one live item, got {len(items)}')
            i=items[0]; e=i.find('enclosure')
            if e is None or e.attrib.get('url')!=url or int(e.attrib.get('length','-1'))!=b: raise RuntimeError('live RSS enclosure mismatch')
            if i.findtext(f'{{{ITUNES}}}duration')!=duration: raise RuntimeError('live RSS duration mismatch')
            return
        except Exception as exc: last=exc; time.sleep(4)
    raise RuntimeError(f'live RSS verification failed: {last}')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',required=True); p.add_argument('--slug',required=True); p.add_argument('--url',required=True); p.add_argument('--bytes',type=int,required=True); p.add_argument('--duration',required=True); a=p.parse_args(); verify_audio(a.url,a.bytes,a.duration); verify_feed(a.repo,a.slug,a.url,a.bytes,a.duration); print(f'PUBLIC RELEASE VERIFIED: {a.slug}')
if __name__=='__main__': main()
