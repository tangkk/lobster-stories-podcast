#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import xml.etree.ElementTree as ET
from email.utils import format_datetime

ITUNES='http://www.itunes.com/dtds/podcast-1.0.dtd'
ATOM='http://www.w3.org/2005/Atom'
CONTENT='http://purl.org/rss/1.0/modules/content/'

def ensure_namespaces():
    ET.register_namespace('itunes',ITUNES); ET.register_namespace('atom',ATOM); ET.register_namespace('content',CONTENT)

def r2_client(endpoint):
    import boto3
    from botocore.config import Config
    return boto3.client('s3',endpoint_url=endpoint,aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(s3={'addressing_style':'path'}))

def set_node(parent,tag,text=None,attrs=None):
    n=parent.find(tag)
    if n is None: n=ET.SubElement(parent,tag)
    if attrs is not None: n.attrib.clear(); n.attrib.update(attrs)
    n.text=text; return n

def upsert_episode(feed,url,size,slug,title,description,duration):
    t=ET.parse(feed); ch=t.getroot().find('channel')
    if ch is None: raise SystemExit('Missing RSS channel')
    matches=[i for i in ch.findall('item') if (i.findtext('guid') or '')==slug]
    if len(matches)>1: raise SystemExit(f'Duplicate RSS GUID already present: {slug}')
    now=format_datetime(dt.datetime.now(dt.timezone.utc))
    if matches: item=matches[0]
    else:
        item=ET.Element('item'); first=ch.find('item'); ch.insert(list(ch).index(first),item) if first is not None else ch.append(item); set_node(item,'pubDate',now)
    set_node(item,'title',title); set_node(item,'description',description)
    if item.find('pubDate') is None: set_node(item,'pubDate',now)
    set_node(item,'guid',slug,{'isPermaLink':'false'}); set_node(item,'enclosure',None,{'url':url,'length':str(size),'type':'audio/mpeg'}); set_node(item,f'{{{ITUNES}}}duration',duration); set_node(item,f'{{{ITUNES}}}episodeType','full'); set_node(item,f'{{{ITUNES}}}explicit','false')
    lb=ch.find('lastBuildDate')
    if lb is not None: lb.text=now
    t.write(feed,encoding='utf-8',xml_declaration=True)

def main():
    ensure_namespaces(); p=argparse.ArgumentParser(); p.add_argument('--feed',default='feed.xml'); p.add_argument('--audio',required=True); p.add_argument('--slug',required=True); p.add_argument('--title',required=True); p.add_argument('--description',required=True); p.add_argument('--duration',required=True); p.add_argument('--prefix',required=True); a=p.parse_args()
    req=['R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY','R2_ENDPOINT','R2_BUCKET','R2_PUBLIC_URL']; missing=[v for v in req if not os.environ.get(v)]
    if missing: raise SystemExit('Missing env: '+', '.join(missing))
    if not os.path.isfile(a.audio) or os.path.getsize(a.audio)<=0: raise SystemExit('Audio missing or empty')
    key=f"{a.prefix.rstrip('/')}/{a.slug}{os.path.splitext(a.audio)[1].lower() or '.mp3'}"; size=os.path.getsize(a.audio); public=os.environ['R2_PUBLIC_URL'].rstrip('/')
    r2_client(os.environ['R2_ENDPOINT'].strip('"')).upload_file(a.audio,os.environ['R2_BUCKET'],key,ExtraArgs={'ContentType':'audio/mpeg'})
    url=f'{public}/{key}'; upsert_episode(a.feed,url,size,a.slug,a.title,a.description,a.duration); print(url)

if __name__=='__main__': main()
