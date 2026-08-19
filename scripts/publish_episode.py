#!/usr/bin/env python3
"""发布新一期播客：上传音频到 Cloudflare R2 并更新 feed.xml。

音频托管已从 GitHub audio/ 迁移到 Cloudflare R2，本脚本负责：
  1. 把本地音频上传到 R2 的 <prefix>/<slug><ext>
  2. 往 feed.xml 插入 <item>，enclosure url 指向 R2 公开地址
  3. 更新 lastBuildDate

R2 配置（全部必需，从环境变量读取；本地 ~/.bash_profile 或 GitHub Actions Secrets）：
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_ENDPOINT     e.g. https://<accountid>.r2.cloudflarestorage.com
    R2_BUCKET       e.g. tangkk-podcast
    R2_PUBLIC_URL   e.g. https://pub-xxx.r2.dev

依赖：boto3（pip install boto3）

用法示例：
  python3 publish_episode.py \
    --audio /path/to/ep030.mp3 --slug ep030-some-topic \
    --title '第30期 标题' --description '简介' --duration '00:04:32' \
    --prefix headlines
"""
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
    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        region_name='auto',
        config=Config(s3={'addressing_style': 'path'}),
    )


def upload_audio(client, bucket, prefix, slug, audio_src):
    ext = os.path.splitext(audio_src)[1].lower() or '.mp3'
    key = f"{prefix.rstrip('/')}/{slug}{ext}"
    size = os.path.getsize(audio_src)
    client.upload_file(audio_src, bucket, key, ExtraArgs={'ContentType': 'audio/mpeg'})
    return key, size


def add_episode(feed_path, enclosure_url, size, slug, title, description, duration):
    tree = ET.parse(feed_path)
    root = tree.getroot()
    ch = root.find('channel')

    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    desc = ET.SubElement(item, 'description')
    desc.text = description
    ET.SubElement(item, 'pubDate').text = format_datetime(dt.datetime.now(dt.timezone.utc))
    guid = ET.SubElement(item, 'guid', {'isPermaLink': 'false'})
    guid.text = slug
    ET.SubElement(item, 'enclosure', {
        'url': enclosure_url,
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
    p = argparse.ArgumentParser(description='Upload episode audio to R2 and append to feed.xml')
    p.add_argument('--feed', default='feed.xml')
    p.add_argument('--audio', required=True)
    p.add_argument('--slug', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--description', required=True)
    p.add_argument('--duration', default='00:05:00')
    p.add_argument('--prefix', required=True, help='R2 目录: headlines/heartvoices/bios/stories')
    args = p.parse_args()

    required_env = ['R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_ENDPOINT', 'R2_BUCKET', 'R2_PUBLIC_URL']
    missing = [v for v in required_env if v not in os.environ]
    if missing:
        raise SystemExit(f'缺少环境变量: {", ".join(missing)}')

    endpoint = os.environ['R2_ENDPOINT'].strip('"')
    bucket = os.environ['R2_BUCKET']
    public_url = os.environ['R2_PUBLIC_URL'].rstrip('/')

    client = r2_client(endpoint)
    key, size = upload_audio(client, bucket, args.prefix, args.slug, args.audio)
    enclosure_url = f"{public_url}/{key}"
    add_episode(args.feed, enclosure_url, size, args.slug, args.title, args.description, args.duration)
    print(f'OK: uploaded {key} ({size} bytes), added to {args.feed} -> {enclosure_url}')
