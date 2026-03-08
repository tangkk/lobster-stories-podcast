#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import shutil
import xml.etree.ElementTree as ET
from email.utils import format_datetime


def ensure_namespaces():
    ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')


def add_episode(feed_path, base_url, audio_src, slug, title, description, duration):
    tree = ET.parse(feed_path)
    root = tree.getroot()
    ch = root.find('channel')

    audio_dir = os.path.join(os.path.dirname(feed_path), 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    ext = os.path.splitext(audio_src)[1].lower() or '.mp3'
    audio_name = f"{slug}{ext}"
    dst = os.path.join(audio_dir, audio_name)
    shutil.copy2(audio_src, dst)
    size = os.path.getsize(dst)

    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    desc = ET.SubElement(item, 'description')
    desc.text = description
    ET.SubElement(item, 'pubDate').text = format_datetime(dt.datetime.now(dt.timezone.utc))
    guid = ET.SubElement(item, 'guid', {'isPermaLink': 'false'})
    guid.text = slug
    ET.SubElement(item, 'enclosure', {
        'url': f"{base_url}/audio/{audio_name}",
        'length': str(size),
        'type': 'audio/mpeg'
    })
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = duration
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'

    first_item = ch.find('item')
    if first_item is not None:
        idx = list(ch).index(first_item)
        ch.insert(idx, item)
    else:
        ch.append(item)

    lb = ch.find('lastBuildDate')
    if lb is not None:
        lb.text = format_datetime(dt.datetime.now(dt.timezone.utc))

    tree.write(feed_path, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    ensure_namespaces()
    p = argparse.ArgumentParser(description='Append new episode to feed.xml and copy audio')
    p.add_argument('--feed', default='feed.xml')
    p.add_argument('--base-url', required=True)
    p.add_argument('--audio', required=True)
    p.add_argument('--slug', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--description', required=True)
    p.add_argument('--duration', default='00:05:00')
    args = p.parse_args()
    add_episode(args.feed, args.base_url.rstrip('/'), args.audio, args.slug, args.title, args.description, args.duration)
    print('OK: episode added')
