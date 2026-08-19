#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import os
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode, urlparse
from wsgiref.handlers import format_date_time

import websocket

DEFAULT_URL = "wss://tts-api.xfyun.cn/v2/tts"


def build_auth(api_key: str, api_secret: str, base_ws_url: str):
    parsed = urlparse(base_ws_url)
    host = parsed.netloc
    path = parsed.path
    now = datetime.utcnow()
    date = format_date_time(mktime(now.timetuple()))
    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    signature_sha = hmac.new(api_secret.encode("utf-8"), signature_origin.encode("utf-8"), hashlib.sha256).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")
    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization_b64 = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    # Try private gateway with explicit HTTP headers (Date/Authorization).
    ws_url_with_query = base_ws_url + "?" + urlencode({"authorization": authorization_b64, "date": date, "host": host})

    headers = [
        f"Authorization: {authorization_origin}",
        f"authorization: {authorization_b64}",
        f"Host: {host}",
        f"Date: {date}",
        f"X-Date: {date}",
    ]
    return ws_url_with_query, headers


def synth(text: str, vcn: str, out_path: str, ws_base_url: str) -> None:
    appid = os.getenv("XFYUN_APPID", "")
    api_key = os.getenv("XFYUN_API_KEY", "")
    api_secret = os.getenv("XFYUN_API_SECRET", "")
    if not (appid and api_key and api_secret):
        raise RuntimeError("Missing XFYUN_APPID / XFYUN_API_KEY / XFYUN_API_SECRET")

    ws_url, headers = build_auth(api_key, api_secret, ws_base_url)
    ws = websocket.create_connection(ws_url, header=headers, timeout=20, sslopt={"cert_reqs": ssl.CERT_NONE})

    payload = {
        "common": {"app_id": appid},
        "business": {
            "aue": "lame",
            "auf": "audio/L16;rate=16000",
            "vcn": vcn,
            "tte": "UTF8",
            "speed": 50,
            "volume": 50,
            "pitch": 50,
            "sfl": 1,
            "bgs": 0,
            "reg": "0",
            "rdn": "0",
        },
        "data": {
            "status": 2,
            "text": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
        },
    }

    ws.send(json.dumps(payload))
    audio = bytearray()

    while True:
        msg = ws.recv()
        data = json.loads(msg)
        code = data.get("code", -1)
        if code != 0:
            raise RuntimeError(f"XFYUN error code={code}, message={data.get('message')}, sid={data.get('sid')}")
        chunk = data.get("data", {}).get("audio", "")
        if chunk:
            audio.extend(base64.b64decode(chunk))
        if data.get("data", {}).get("status") == 2:
            break

    ws.close()
    with open(out_path, "wb") as f:
        f.write(audio)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--voice", default="aisjinger")
    p.add_argument("--url", default=DEFAULT_URL, help="WebSocket API URL, e.g. private endpoint")
    p.add_argument("--text", default="这是超拟人语音合成的连通性测试。我们正在为播客寻找更自然的声音。")
    p.add_argument("--out", default="/Users/tangkk/Downloads/龙虾头条/试听/xfyun-humanoid-smoketest.mp3")
    args = p.parse_args()

    synth(args.text, args.voice, args.out, args.url)
    print(f"OK: wrote {args.out}")
