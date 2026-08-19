# 龙虾故事语音工具说明

- 本目录由“龙虾头条/素材/工具/xfyun-tools”同步而来。
- 龙虾故事默认配置：`voice_profiles/lobster_story_default.json`
- 默认链路：讯飞超拟人私有接口
- 默认音色：`x6_wennuancixingnansheng_mini`
- 默认参数：speed=42, volume=52, pitch=47

## 约束
- 不使用 macOS `say`
- 出现听感异常时，先确认是否走了错误接口/错误payload结构

## 推荐执行方式（避免环境变量丢失）
- 先通过包装脚本加载环境变量，再执行 Python：
- `./with_xfyun_env.sh python3 xfyun_super_official_run.py --url ... --voice ... --text ... --out ...`
- 包装脚本会自动 source 常见 shell 配置（`.bash_profile/.zprofile/.zshrc/.bashrc`）并校验 `XFYUN_APPID/XFYUN_API_KEY/XFYUN_API_SECRET`。
