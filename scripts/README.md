# scripts/ —— 过程脚本归档

这里的脚本都是**探索过程的一次性工具**，结论已经固化进 `gui/wxcore.py` 和
`tools/wcdb_key_tool_windows.py`。保留它们是为了说明「为什么最后选这条路线」，
日常使用不需要运行。脚本里引用的输入路径（`mem/`、`decrypted/`、`out/`）
现在位于 `wx_export_local/`（见仓库上级目录），按需改路径即可。

```
scripts/
├─ reverse/                 逆向：把密钥从微信进程里挖出来的全过程
│  ├─ memory/               内存转储、密钥候选扫描、AES 验证
│  ├─ hook/                 Frida attach / spawn 注入抓 passphrase
│  └─ static/               Weixin.dll 静态分析、定位 KDF 调用点
├─ probe/                   探针：确认「界面在哪、库里有什么」
│  ├─ window/               窗口枚举、UIA 树、点击、截图
│  └─ db/                   解密后 SQLite 的表/字段/发送者核对
└─ analysis/                导出之后的内容分析（私人用途，与工具本身无关）
```

## reverse/memory

| 脚本 | 作用 |
|---|---|
| `dump_mem.py` | 遍历 Weixin.exe 可读内存区域并转储（产出 `mem/pid_*.bin`） |
| `findkey.py` | v1：内存里直接搜 `x'<96hex>'` 原始密钥缓存 |
| `findkey2.py` | v2：结构化定位，按 salt / 库路径字符串邻域枚举候选 |
| `findkey3.py` | v3：先统计命中再限窗验证，带预算防爆 |
| `findkey4.py` | v4：扫十六进制字符串候选 + `PRAGMA key` 上下文 |
| `scan96.py` | 只搜 `x'(96hex)` 形态（4.0.x ~ 4.1.9 时代有效） |
| `scan_pass.py` | `Config.Cipher` 邻域枚举 passphrase（PBKDF2 验证） |
| `scan_key.c` / `test_aes.c` | 自研 AES-NI 枚举器与 NIST 自测（需自行编译，不含二进制） |
| `memcheck.py` / `memcarve1.py` / `probe2.py` | 在转储里找表名 / 聊天片段，判断哪块内存有货 |
| `ana.py` | 统计 `wx_hits*.jsonl` 的命中分布 |

## reverse/hook

| 脚本 | 作用 |
|---|---|
| `frida_smoke.py` / `frida_smoke2.py` | Frida 可用性冒烟测试（hook 记事本） |
| `api_test.py` / `test_dump.py` | Frida attach 微信、试读内存 |
| `hook_weixin.py` | attach 后在 WCDB cipher 配置点下断，抓 passphrase |
| `spawn_hook.py` / `spawn_hook2.py` | spawn 模式注入，抓启动瞬间的 passphrase 候选 |
| `validate_hits.py` / `validate3.py` | 校验抓到的内存窗口里是否真有 passphrase / enc_key |

## reverse/static

| 脚本 | 作用 |
|---|---|
| `exp.py` | 导出 PE 结构（节表 / 导入导出） |
| `xref.py` / `xref2.py` | 找关键字符串的 RIP 相对引用点（hook 目标候选） |
| `kdfscan.py` | 在 `256000`（KDF 迭代数）常量附近找引用 |
| `kdf_xref.py` | 找 PBKDF2 调用者 |
| `pdata.py` | 解析 `.pdata` 得函数边界，筛 codec/pragma 附近函数 |
| `kdf_targets.json` / `hook_funcs.json` | 上述脚本的中间结果（函数地址清单） |

## probe/window

| 脚本 | 作用 |
|---|---|
| `wins2.py` ~ `wins5.py`、`win_enum.py`、`kids.py` | 枚举窗口 / 子窗口，定位微信各层 HWND |
| `uia_dump.ps1`、`uia_tree.txt` | 导出 UIA 树，评估控件可读性 |
| `click_login.py`、`click_login.ps1`、`click_login2.ps1` | 点「进入微信」 |
| `post_click.ps1`、`click_prepare*.py`、`click_export.py` | 用窗口消息 / 鼠标点界面按钮（绕过前台锁） |
| `cap_win.py`、`cap_win2.py`、`cap_hwnd.py`、`cap2.py`、`shot_gui.py`、`dbg.py` | PrintWindow / 屏幕截图，检查界面状态 |
| `t_shot.py`、`ui_probe.py` | 开发期截图与控件尺寸探针（调界面用） |

## probe/db

`chk_sender.py`、`find_contact.py`、`find_tables.py`、`stats.py`、`stats2.py`、
`peek.py` ~ `peek4.py`、`perchk.py`、`dupcheck.py`、`dist.py`、
`export_messages.py`（早期导出脚本，已被 `gui/wxcore.py` 取代）。

## analysis

`person.py`、`deep1.py`、`deep2.py`、`nodes.py`、`conflict_scan.py`、`episode_stats.py`、
`moran_sample.py`、`moran_stats2.py`、`moran_style.py`、`gender_probe.py`、`whois.py`、
`split_segments.py`、`find_moran.py`、`probe_moran.py`

读导出结果做统计与抽样，属于「导出之后怎么用」，不是工具的一部分。
