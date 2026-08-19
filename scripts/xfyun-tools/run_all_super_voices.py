#!/usr/bin/env python3
import subprocess
from pathlib import Path

BASE = Path('/Users/tangkk/Downloads/龙虾头条')
SCRIPT = BASE / 'xfyun-tools' / 'xfyun_super_official_run.py'
OUT_DIR = BASE / '试听' / 'xfyun-super-all'
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = 'wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6'
TEXT = '你好，这里是龙虾头条声音盲听测试。'

voices = [
    'x6_wennuancixingnansheng_mini','x6_xiaonaigoudidi_mini','x6_shibingnvsheng_mini','x6_kongbunvsheng_mini',
    'x6_yulexinwennvsheng_mini','x6_wenrounansheng_mini','x6_jingqudaolannvsheng_mini','x6_daqixuanchuanpiannansheng_mini',
    'x6_cuishounvsheng_pro','x6_yingxiaonv_pro','x6_huanlemianbao_pro','x6_xiangruiyingyu_pro','x6_taiqiangnuannan_pro',
    'x6_wumeinv_pro','x6_lingbosong_pro','x6_dudulibao_pro','x6_huajidama_pro','x6_huoposhaonian_pro','x6_lingxiaoli_pro',
    'x6_xiaoqiChat_pro','x6_lingfeiyi_pro','x6_feizheChat_pro','x6_lingxiaoyue_pro','x6_lingxiaoxuan_pro','x6_lingyuyan_pro',
    'x6_pangbainan1_pro','x6_pangbainv1_pro','x6_lingfeihan_pro','x6_lingfeihao_pro','x6_gufengpangbai_pro','x6_lingyuaner_pro',
    'x6_ganliannvxing_pro','x6_ruyadashu_pro','x6_lingyufei_pro','x6_lingxiaoshan_pro','x6_lingxiaoyun_pro','x6_lingyouyou_pro',
    'x6_lingxiaoying_pro','x6_lingxiaozhen_pro','x6_lingfeibo_pro','x6_waiguodashu_pro','x6_gaolengnanshen_pro','x6_dongmanshaonv_pro',
    'x5_lingxiaotang_flow','x5_lingyuzhao_flow','x4_zijin_oral','x4_ziyang_oral','x5_EnUs_Grant_flow','x5_EnUs_Lila_flow'
]

ok, fail = [], []
for v in voices:
    out = OUT_DIR / f'{v}.mp3'
    cmd = [
        'python3', str(SCRIPT), '--url', URL, '--voice', v, '--text', TEXT, '--out', str(out)
    ]
    p = subprocess.run(['bash', '-lc', 'source ~/.bash_profile && ' + ' '.join([subprocess.list2cmdline([c]) for c in cmd])], capture_output=True, text=True)
    if p.returncode == 0 and out.exists() and out.stat().st_size > 0:
        ok.append(v)
        print(f'OK   {v}')
    else:
        fail.append((v, (p.stderr or p.stdout)[-220:]))
        print(f'FAIL {v}')

summary = OUT_DIR / '_summary.txt'
with open(summary, 'w', encoding='utf-8') as f:
    f.write('=== OK voices ===\n')
    for v in ok:
        f.write(v + '\n')
    f.write('\n=== FAIL voices ===\n')
    for v, e in fail:
        f.write(f'{v}\t{e}\n')

print(f'\nDone. OK={len(ok)} FAIL={len(fail)}')
print(f'Summary: {summary}')
