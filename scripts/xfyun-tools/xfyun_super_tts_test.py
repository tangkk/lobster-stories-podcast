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


def build_ws_url(ws_base_url: str, api_key: str, api_secret: str) -> str:
    p = urlparse(ws_base_url)
    host = p.netloc
    path = p.path
    date = format_date_time(mktime(datetime.utcnow().timetuple()))
    sign_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    sign_sha = hmac.new(api_secret.encode(), sign_origin.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(sign_sha).decode()
    auth_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(auth_origin.encode()).decode()
    return ws_base_url + "?" + urlencode({"authorization": authorization, "date": date, "host": host}), date, auth_origin


def run(text: str, vcn: str, ws_base_url: str, out_path: str):
    appid = os.getenv("XFYUN_APPID", "")
    api_key = os.getenv("XFYUN_API_KEY", "")
    api_secret = os.getenv("XFYUN_API_SECRET", "")
    if not (appid and api_key and api_secret):
        raise RuntimeError("Missing XFYUN_APPID/XFYUN_API_KEY/XFYUN_API_SECRET")

    ws_url, date, auth_origin = build_ws_url(ws_base_url, api_key, api_secret)
    host = urlparse(ws_base_url).netloc
    headers = [
        f"Date: {date}",
        f"Host: {host}",
        f"Authorization: {auth_origin}",
    ]
    ws = websocket.create_connection(ws_url, header=headers, timeout=20, sslopt={"cert_reqs": ssl.CERT_NONE})

    req = {
        "header": {"app_id": appid, "status": 2},
        "parameter": {
            "oral": {"oral_level": "mid", "spark_assist": 1, "stop_split": 0, "remain": 0},
            "tts": {
                "vcn": vcn,
                "speed": 50,
                "volume": 50,
                "pitch": 50,
                "bgs": 0,
                "reg": 0,
                "rdn": 0,
                "audio": {"encoding": "lame", "sample_rate": 24000, "channels": 1, "bit_depth": 16, "frame_size": 0},
            },
        },
        "payload": {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 2,
                "seq": 0,
                "text": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
            }
        },
    }

    ws.send(json.dumps(req, ensure_ascii=False))
    audio = bytearray()
    while True:
        msg = ws.recv()
        data = json.loads(msg)
        code = data.get("header", {}).get("code", -1)
        if code != 0:
            raise RuntimeError(f"code={code} msg={data.get('header', {}).get('message')} sid={data.get('header', {}).get('sid')}")
        a = data.get("payload", {}).get("audio", {})
        if a.get("audio"):
            audio.extend(base64.b64decode(a["audio"]))
        if a.get("status") == 2:
            break

    ws.close()
    with open(out_path, "wb") as f:
        f.write(audio)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--text", default="你好，这是一段超拟人语音测试。")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    run(args.text, args.voice, args.url, args.out)
    print("OK", args.out)
