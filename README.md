# Google One / Google AI Billing 研究脚本

[English README](README.en.md) · [安全说明](SECURITY.md) · [静态测试](tests/test_static.py)

> **非 Google 官方项目。** 此项目用于研究 Android Play Billing 查询和结算界面的行为，并非免费获得 Google AI Pro 的保证。查询到某个 offer 不代表账号具备资格；打开结算界面也不代表订阅成功。

## 功能与限制

- 通过 ADB、Frida 和 Google One 应用进程查询 Android Play Billing 的商品与 offer。
- 只读查询模式不会打开订阅结算界面。
- 在结算模式下，脚本只打开并读取结算页面，**不会自动点击订阅**；任何真实购买必须由账号持有人在 Google Play 界面手动审查并确认。
- 历史版本提到的“12 + 6 + 6 个月”叠加并未在本版本经过真实账号验证，不能保证可用性、优惠长度或后续收费金额。

## 环境要求

- Python 3.10+，ADB，具备所需权限的 Android 测试设备/模拟器。
- 测试设备中需安装 Google Play 和 Google One。
- `frida==16.5.9`（请先检查下载的工具和附带 DEX 模块的可信度）。
- **不要在文本文件中存放真实密码、TOTP 密钥或支付卡信息。**

## 安全检查

```bash
python -m pip install -r requirements.txt
python ultra0.py --check
python ultra0.py --account current@device --no-add --list --plan pro12
python -m unittest discover -s tests -v
```

`--check` 会尝试启动检测所需的 Android/Frida 环境，不是完全无副作用的操作。默认不会清除代理或终止网络应用；只有指定 `--reset-network` 才允许更改网络设置。

结算操作必须验证当前 Google Play 账号；`--force` 只允许用于只读 `--list`。任何真实付款及续费条款均以 Google Play 实际页面为准。

## 文件

- `ultra0.py`: ADB/Frida 主脚本、offer 查询与结算界面观察。
- `setup_env.py`: Windows 环境安装及检测。
- `query_sku.py`: 商品查询辅助脚本。
- `0_环境自检.bat`, `1_查看offer列表.bat`: 环境和只读查询。
- `2_Pro_*.bat` 至 `5_Pro_*.bat`: 保留的实验性步骤，不保证优惠资格或时间叠加。
- `README.en.md`: 完整英文说明。
- `SECURITY.md`: 安全边界、已知限制及报告建议。
- `tests/test_static.py`: 不连接设备、无需真实账号的自动化静态测试。

## 注意事项

- 仅使用自己拥有或获得授权的设备和账号。请遵守 Google Play 服务和促销条款。
- 已打开结算窗口的状态为 `checkout_opened_manual_verification_required`，**不是成功购买**。
- 任何订阅结果都应当在 Google Play 的正式订阅页面核对实际到期/续订日期。
- 本项目内嵌的 DEX 为预编译代码，尚未完成独立安全审计；不要在主力设备或主要 Google 账号上直接执行。

详细英文说明请阅读 [README.en.md](README.en.md)。
