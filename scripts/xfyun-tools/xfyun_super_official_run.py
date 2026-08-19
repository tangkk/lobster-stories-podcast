# -*- coding:utf-8 -*-
import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os


class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Text, Voice, Speed=50, Volume=50, Pitch=50):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text
        self.Voice = Voice
        self.CommonArgs = {"app_id": self.APPID, "status": 2}
        self.BusinessArgs = {
            "tts": {
                "vcn": self.Voice,
                "volume": int(Volume),
                "rhy": 0,
                "speed": int(Speed),
                "pitch": int(Pitch),
                "bgs": 0,
                "reg": 0,
                "rdn": 0,
                "audio": {
                    "encoding": "lame",
                    "sample_rate": 24000,
                    "channels": 1,
                    "bit_depth": 16,
                    "frame_size": 0,
                },
            }
        }
        self.Data = {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 2,
                "seq": 0,
                "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8"),
            }
        }


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    path = host[edidx:]
    host = host[:edidx]
    return Url(host, path, schema)


def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    date = format_date_time(mktime(datetime.now().timetuple()))
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    values = {"host": host, "date": date, "authorization": authorization}
    return requset_url + "?" + urlencode(values)


def run_once(requrl, out_path, voice, text, speed=50, volume=50, pitch=50):
    appid = os.environ.get("XFYUN_APPID", "")
    apisecret = os.environ.get("XFYUN_API_SECRET", "")
    apikey = os.environ.get("XFYUN_API_KEY", "")
    if not (appid and apikey and apisecret):
        raise RuntimeError("Missing XFYUN_APPID/XFYUN_API_KEY/XFYUN_API_SECRET")

    wsParam = Ws_Param(APPID=appid, APISecret=apisecret, APIKey=apikey, Text=text, Voice=voice, Speed=speed, Volume=volume, Pitch=pitch)
    wsUrl = assemble_ws_auth_url(requrl, "GET", apikey, apisecret)

    if os.path.exists(out_path):
        os.remove(out_path)

    done = {"ok": False, "err": None}

    def on_message(ws, message):
        try:
            msg = json.loads(message)
            code = msg["header"].get("code", -1)
            if code != 0:
                done["err"] = f"code={code}, msg={msg['header'].get('message')}, sid={msg['header'].get('sid')}"
                ws.close()
                return
            if "payload" in msg and "audio" in msg["payload"]:
                audio_b64 = msg["payload"]["audio"].get("audio", "")
                if audio_b64:
                    with open(out_path, 'ab') as f:
                        f.write(base64.b64decode(audio_b64))
                if msg["payload"]["audio"].get("status") == 2:
                    done["ok"] = True
                    ws.close()
        except Exception as e:
            done["err"] = str(e)
            ws.close()

    def on_error(ws, error):
        done["err"] = str(error)

    def on_close(ws, *_):
        return

    def on_open(ws):
        def _run(*args):
            d = {"header": wsParam.CommonArgs, "parameter": wsParam.BusinessArgs, "payload": wsParam.Data}
            ws.send(json.dumps(d, ensure_ascii=False))
        thread.start_new_thread(_run, ())

    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    if done["err"]:
        raise RuntimeError(done["err"])
    if not done["ok"]:
        raise RuntimeError("TTS did not complete")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6")
    ap.add_argument("--voice", default="x6_wennuancixingnansheng_mini")
    ap.add_argument("--text", default="你好，这是一段超拟人语音测试。")
    ap.add_argument("--speed", type=int, default=42)
    ap.add_argument("--volume", type=int, default=52)
    ap.add_argument("--pitch", type=int, default=47)
    ap.add_argument("--out", default="/Users/tangkk/Downloads/龙虾故事/试听/xfyun-x6_wennuancixingnansheng_mini-official.mp3")
    args = ap.parse_args()

    run_once(args.url, args.out, args.voice, args.text, speed=args.speed, volume=args.volume, pitch=args.pitch)
    print("OK:", args.out)
