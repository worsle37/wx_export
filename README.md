# wx_export —— 微信聊天记录导出（Windows）

从**正在运行**的微信 4.x 里取 SQLCipher 密钥 → 本地逐页解密 → 选会话 → 导出
**Markdown / CSV / HTML**。单文件 exe，全程离线。

![界面预览](gui/preview_dark.png)

**不想看代码、只想用？** 直接去 [Releases](https://github.com/worsle37/wx_export/releases) 下载
`微信聊天导出.exe`（约 14 MB，免安装），然后照 **[使用教程](docs/使用教程.md)** 点四下就出结果。

- 使用教程（截图 + 四步上手 + FAQ）：[`docs/使用教程.md`](docs/使用教程.md)
- 界面与开发说明：[`gui/README.md`](gui/README.md)
- 逆向过程与实测结论：[`docs/微信聊天记录导出-技术方案.md`](docs/微信聊天记录导出-技术方案.md)
- 目录归档说明：[`docs/项目结构说明.md`](docs/项目结构说明.md)

## 特性

| | |
|---|---|
| 取密钥 | 读 `Weixin.exe` 内存里的 `com.Tencent.WCDB.Config.Cipher` 对象，XOR 解码后用第一页 HMAC 校验 |
| 解密 | SQLCipher 4（AES-256-CBC + HMAC-SHA512，PBKDF2 256000 次，页 4096 / 保留区 80）逐页解成标准 SQLite |
| 导出 | MD（按天分组）/ CSV（Excel 友好，带 BOM）/ HTML（单文件深色），文本 + 图片语音视频表情文件等元信息 |
| 界面 | Tkinter 自绘深色主题，圆角卡片、虚拟列表、多选、实时搜索、分级日志、进度线；Win11 深色标题栏 |
| 打包 | PyInstaller 单文件、无控制台，约 15 MB，Win10/11 x64 |

## 快速开始

1. 登录微信桌面端并保持运行
2. 运行从 [Releases](https://github.com/worsle37/wx_export/releases) 下载的 `微信聊天导出.exe`
   （建议右键「以管理员身份运行」；源码跑法是 `python gui/app.py`）
3. 点右上角 **① 读取密钥并解密**（首次 1–3 分钟）
4. 选中会话 → 勾格式 → **② 导出选中**（默认输出到 `桌面\微信导出`）

完整图文步骤见 **[使用教程](docs/使用教程.md)**。

命令行批量导出：

```powershell
.\微信聊天导出.exe --cli --all --out D:\导出
.\微信聊天导出.exe --cli --name "好友A" --out D:\导出
```

## 目录

```
wx_export/
├─ gui/                 ★ 交付物：界面程序（app.py / wxcore.py / spec / README / assets）
│  └─ legacy/           美化前的旧界面备份
├─ tools/               取密钥 + 批量解密 的独立命令行工具（不依赖 GUI）
├─ scripts/             过程脚本归档：逆向（内存/hook/静态）、探针（窗口/数据库）、内容分析
├─ docs/                使用教程 + 技术方案 + 项目结构说明
├─ README.md            本文件
└─ .gitignore
```

## 开发

```powershell
pip install pycryptodome zstandard pillow pyinstaller
python gui/app.py                      # 跑源码
$env:WXGUI_DEMO="1"; python gui/app.py # 演示模式：示例数据，不读真实微信
python gui/selftest.py                 # 自检：列出已解密会话并试导出一个
python -m PyInstaller gui/微信聊天导出.spec --noconfirm --distpath dist --workpath build
```

运行数据写在 `%LOCALAPPDATA%\WxDumpGUI\`（`work/` 解密中间件、`config.json` 界面配置），
不写微信自己的目录，随时可删。细节见 [`gui/README.md`](gui/README.md)。

## 隐私

密钥、内存转储、解密后的 SQLite 和导出成品**都不会入库**（见 `.gitignore`）。
仓库里只有源码与文档，没有任何聊天内容或密钥材料。

仅用于导出你自己账号在本机的聊天记录；取密钥依赖读取微信进程内存，请只在自己的机器、
对自己的数据使用。
