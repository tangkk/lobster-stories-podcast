#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import xml.etree.ElementTree as ET
from email.utils import format_datetime


def ensure_namespaces():
    ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')


def r2_client(endpoint):
    import boto3
    from botocore.config import Config
    return boto3.client('s3', endpoint_url=endpoint,
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        region_name='auto', config=Config(s3={'addressing_style': 'path'}))


def ensure_key_absent(client, bucket, key):
    try:
        client.head_object(Bucket=bucket, Key=key)
    except Exception as exc:
        response = getattr(exc, 'response', {}) or {}
        code = str(response.get('Error', {}).get('Code', ''))
        status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
        if code in {'404', 'NoSuchKey', 'NotFound'} or status == 404:
            return
        raise
    raise SystemExit(f'R2 object already exists: {key}')


def add_episode(feed_path, enclosure_url, size, slug, title, description, duration):
    tree = ET.parse(feed_path)
    root = tree.getroot()
    ch = root.find('channel')
    if ch is None:
        raise SystemExit('Missing RSS channel')
    if any((item.findtext('guid') or '') == slug for item in ch.findall('item')):
        raise SystemExit(f'GUID already exists: {slug}')

    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = format_datetime(dt.datetime.now(dt.timezone.utc))
    ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = slug
    ET.SubElement(item, 'enclosure', {'url': enclosure_url, 'length': str(size), 'type': 'audio/mpeg'})
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = duration
    ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'

    first = ch.find('item')
    if first is not None:
        ch.insert(list(ch).index(first), item)
    else:
        ch.append(item)
    lb = ch.find('lastBuildDate')
    if lb is not None:
        lb.text = format_datetime(dt.datetime.now(dt.timezone.utc))
    tree.write(feed_path, encoding='utf-8', xml_declaration=True)


def main():
    ensure_namespaces()
    p = argparse.ArgumentParser(description='Upload approved episode audio to R2 and update feed.xml')
    p.add_argument('--feed', default='feed.xml')
    p.add_argument('--audio', required=True)
    p.add_argument('--slug', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--description', required=True)
    p.add_argument('--duration', required=True)
    p.add_argument('--prefix', required=True)
    args = p.parse_args()

    required = ['R2_ACCESS_KEY_ID','R2_SECRET_ACCESS_KEY','R2_ENDPOINT','R2_BUCKET','R2_PUBLIC_URL']
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise SystemExit('Missing env: ' + ', '.join(missing))
    if not os.path.isfile(args.audio) or os.path.getsize(args.audio) <= 0:
        raise SystemExit('Audio missing or empty')

    endpoint = os.environ['R2_ENDPOINT'].strip('"')
    bucket = os.environ['R2_BUCKET']
    public = os.environ['R2_PUBLIC_URL'].rstrip('/')
    ext = os.path.splitext(args.audio)[1].lower() or '.mp3'
    key = f"{args.prefix.rstrip('/')}/{args.slug}{ext}"
    client = r2_client(endpoint)
    ensure_key_absent(client, bucket, key)
    size = os.path.getsize(args.audio)
    client.upload_file(args.audio, bucket, key, ExtraArgs={'ContentType': 'audio/mpeg'})
    add_episode(args.feed, f'{public}/{key}', size, args.slug, args.title, args.description, args.duration)
    print(f'uploaded {key} ({size} bytes); feed updated')


if __name__ == '__main__':
    main()
