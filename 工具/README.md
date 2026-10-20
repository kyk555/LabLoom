# 工具 · issue 命令行与报告生成

**定位**：让 issue 的「登记 / 回复 / 关闭」能从命令行和 AI 对话里直接完成，不用每次开浏览器点表单。
本项目用 issue 承载**验证阶段的每一条需求与内容错误**——访谈发现的问题、实验内容的学科错误、合规隐患，全部登记成 issue 再动手。

**出处**：移植自 `D:\code\allweather\工具\`（V1.0，2026-10-19），纯标准库、无第三方依赖；本项目的改动只有 UA 与示例路径。

## 一、准备（一次性，约 5 分钟）

| 缺什么 | 你要做什么 |
|---|---|
| GitHub 令牌 | 第 1、2 步 |
| Issues 功能 | 仓库已开启（`has_issues=true`），无需操作 |
| `gh` CLI | **不需要**，本工具不依赖它 |

### 第 1 步：建一个 fine-grained PAT

打开 <https://github.com/settings/personal-access-tokens/new>：

| 字段 | 填什么 |
|---|---|
| Token name | `labloom-issue-cli` |
| Expiration | 90 天（到期重生成） |
| Resource owner | 你自己的账号 |
| Repository access | **Only select repositories** → 只勾 `LabLoom` |
| Repository permissions | **Issues: Read and write**；**Metadata: Read-only**（自动勾上，必需） |
| 其余权限 | 全部 **No access** |

> 不要给 `Contents` / `Workflows`：本工具不碰代码，给了等于扩大爆炸半径。

### 第 2 步：设环境变量（不要手敲明文令牌）

PowerShell 会把每条命令记进 `ConsoleHost_history.txt`，VS Code 还会把终端状态存进 `state.vscdb`——明文令牌会一起进去。

```powershell
# 先在 GitHub 页面点 Copy，再执行：命令本身不含明文
$t = (Get-Clipboard -Raw).Trim()
[Environment]::SetEnvironmentVariable('GITHUB_TOKEN', $t, 'User')
Remove-Variable t
Set-Clipboard -Value ''

# 只在当前窗口有效（调试用）
$env:GITHUB_TOKEN = (Get-Clipboard -Raw).Trim()
```

设完**重开终端**（已开的进程读不到新变量）。

### 第 3 步：自检

```powershell
cd D:\code\LabLoom
python -B 工具/github_issue.py 自检
```

期望：`令牌来源 / 仓库 kyk555/LabLoom / 可见性 私有 / Issues 已开启 / 写入权限 True / 【就绪】`。
`写入权限：False` → PAT 少了 **Issues: Read and write**，重新生成。

### 第 4 步：跑工具自身的单测（改代码后必跑）

```powershell
python -B -m unittest 工具/测试_github_issue.py
```

**21 项，全离线**：patch 掉 `urlopen`，一个请求都不发。已做过变异验证（把标签映射改坏 → 2 项立刻失败），不是自证式测试。

## 二、命令速查

```powershell
cd D:\code\LabLoom

# 看
python -B 工具/github_issue.py 列表                      # 默认 open，最多 20 条，自动排除 PR
python -B 工具/github_issue.py 列表 --状态 all --条数 50
python -B 工具/github_issue.py 列表 --标签 bug
python -B 工具/github_issue.py 查看 3                     # 正文 + 全部评论

# 登记（正文必填，--预演 只打印不发送）
python -B 工具/github_issue.py 登记 --类型 需求 --标题 "初中化学·误差分析样本" --正文文件 $env:TEMP\需求.md
python -B 工具/github_issue.py 登记 --类型 bug  --标题 "生成的杠杆实验力矩方向画反" --正文文件 $env:TEMP\bug.md

# 回复 / 关闭 / 重开
python -B 工具/github_issue.py 回复 3 --正文文件 $env:TEMP\回复.md
python -B 工具/github_issue.py 关闭 3 --原因 completed --评论 "已按验收标准验证，关闭" --确认
python -B 工具/github_issue.py 重开 3
```

| 行为 | 约定 |
|---|---|
| 标题前缀 | `--类型 需求` 自动加 `[需求] `，`--类型 bug` 自动加 `[Bug] `；要原样就加 `--不加上缀` |
| 默认标签 | 需求 → `enhancement`，bug → `bug` |
| 仓库 | 从 `git remote origin` 解析（不写死）；换仓库用 `--仓库 owner/repo`，**放在子命令前面** |
| 正文 | `--正文文件` 优先；空正文直接拒绝 |
| 令牌 | 只放 header，不进 URL、不打印、不落盘 |

## 三、在对话里怎么用（AI 侧固定流程）

1. **先查重**：`列表 --状态 all`，标题近似的先问「给 #N 补评论，还是新开一条？」
2. **写正文**：按 `.github/ISSUE_TEMPLATE/` 的字段顺序拼 Markdown，写到 `$env:TEMP`，**不写进仓库**
3. **先 `--预演`**：把将提交的 JSON 贴出来，确认后再发
4. **登记后**贴回 `html_url`
5. **关闭前**必须拿到明确指令，且带 `--确认`，并留一句「按哪条验收标准验证的」

## 四、安全边界

- 只调 issues 相关端点；不读代码、不改仓库设置、不碰 PR / commit
- **不读 Windows 凭据管理器**（那里有 git 凭据，挪用属越权）
- 令牌只来自环境变量；`.gitignore` 已挡 `.env`
- issue 正文里不写访谈对象的真实姓名、学校、联系方式（见 `.clinerules/01-内容准确性与合规红线.md`）

### 令牌泄露处置（顺序别跳）

1. **先 revoke**：<https://github.com/settings/personal-access-tokens> → Delete（GitHub 不能查看已建令牌，只能删了重建）
2. 环境变量仍是旧值时跑一次 `自检` → 应打印「令牌无效或已过期」（401），这是 revoke 生效的铁证
3. 清 PSReadLine 历史：`Select-String -Path "$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt" -Pattern 'github_pat_[A-Za-z0-9_]{20,}'` 应无输出
4. 清 VS Code 状态库（先关窗口）：删 `workspaceStorage\<id>\state.vscdb` 与 `.backup`
5. 查 <https://github.com/settings/security-log> 筛 `personal_access_token`
6. 重新生成，回到第 2 步

## 五、报告生成（`工具/生成调研报告.py`）

**定位**：把调研结论做成**可复现的 HTML 产物**——数字只写在脚本的 `EVIDENCE` / `DATA` 常量里，改口径改常量后重跑，不手改 HTML。

```powershell
cd D:\code\LabLoom
python -B 工具/生成调研报告.py          # 生成到 报告/
python -B 工具/生成调研报告.py --检查    # 只自检不写盘
python -B 工具/测试_生成调研报告.py      # 43 项回归测试，全离线
```

| 约定 | 说明 |
|---|---|
| 产物路径 | `报告/2026-10-20-K12实验内容工具-可行性调研与定位建议.html`（单文件，双击可开） |
| 图表 | 4 张 echarts 图，库在 `报告/assets/echarts.min.js`，**不依赖外网 CDN** |
| 幂等 | 内容未变时不重写文件（mtime 不动，不产生假 diff） |
| 生成前自检 | 证据字段完整、引用编号存在、权重和为 1、评分不越界、**第 12 节每条赛道判定至少有一条 E1 依据**、**第 13 节每个领域至少有一条 E1 且「财商」一行必须写明道德与法治**、**第 14 节每个 To C 机会点至少有一条 E1、必须写停手信号、可做行不得出现承诺性表述、标了 `evidence_gap` 的候选不得判「可试」**；任一不过直接拒绝写盘 |
| 测试守什么 | 无 CDN 引用、无占位符残留、标签闭合、图表 JSON 可解析、关键数字存在、目录锚点可解析、重复生成字节一致 |

## 六、浏览器抓取（`工具/浏览器抓取.py`）

**定位**：静态请求拿不到时（JS 渲染 / Cloudflare / 要登录）的第二级手段。用**本机已装的 Chrome**，
**有界面**、**持久化配置目录**、去掉自动化开关，形同用户自己的浏览器；撞上登录就停下来等人手动过。

| 命令 | 用途 |
|---|---|
| `python -B 工具/浏览器抓取.py --环境` | 打印 Python / Playwright 版本、Chrome 路径、登录态与留档位置 |
| `... --打开 <URL> --等 120` | 打开页面并最多等 120 秒，给人手动登录；不写留档 |
| `... --抓取 <URL> --名称 e26-主题 [--截图]` | 抓正文并留档；**撞登录 / 验证页则退出码 3、不留档、不重试** |
| `... --搜索 "关键词 site:gov.cn" --名称 s-主题` | 用真浏览器跑 Bing，留档结果页 + 链接清单，据此挑一手页面 |

规矩：

- **不入库**：配置目录 `data/浏览器配置/`、原始档 `data/raw/<日期>-<名称>/`（`page.html`、`page.txt`、`links.txt`、可选 `page.png`、`meta.json`）由 `.gitignore` 挡；
- **留痕三件套**：`meta.json` 存来源 URL、抓取时间（UTC 与北京各一行）、HTML 与正文各自 sha256；
- **不碰账号**：不猜密码、不绕验证码、不改 UA；对方明确拒绝（403 / 412 / 429、验证页）当天不再打这一家；
- 正文用 `inner_text(body)` 取，只作检索；**引用以 `page.html` 为准**。

依赖：`python -m pip install playwright`（本机 Python 3.8 装到 1.48.0）；**不需要** `playwright install`，因为走 `channel="chrome"` 用本机 Chrome。

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| **V1.6** | **2026-10-20** | 按 R0 内部讨论（`docs/验证记录/2026-10-20-R0-团队讨论-假设生成.md`）新增第 8 个 To C 候选「抽象概念『理解型』单点演示」，判「形态受限」并标 `evidence_gap`（需求侧只有 1 位会写代码的家长自述，不算证据）；§14.1 铁律三条→四条，新增「不碰别人的形象」（影视/动画美术形象受著作权保护）；`verify_data` 增加「标了证据缺口的候选不得判可试」，候选数改为脚本现算（消掉手写的「7 个」），单测 39→43，报告升 v1.5 |
| **V1.5** | **2026-10-20** | 新增 `工具/浏览器抓取.py`：有界面本机 Chrome、配置持久化、遇登录停下留给人；支持 `--环境/--打开/--抓取/--搜索`，留档 `data/raw/`（URL + 双时区时间 + 双 sha256 + 链接清单）。据本轮抓取把 E5 从「政策报道」升级为指南全文（E2→E1）并修正三处升格表述，新增 E26（课后服务 26 号函），报告升 v1.4，单测 36→39 |
| V1.4 | 2026-10-20 | 报告增第 14 节「To C：一个人能做的口子，和三个看起来像机会的坑」，筛 7 个面向家长直接收费的候选（2 可试 / 2 形态受限 / 3 别碰），证据 24→25（新增 1 条一手：教育强国建设规划纲要），单测 30→36；`verify_data` 增加「机会点须有 E1」「须写停手信号」「可做行不得含承诺性表述」三条检查 |
| V1.3 | 2026-10-20 | 报告增第 13 节「学校没教？—— 财商与其他候选领域的筛查」，证据 19→24（新增 5 条，4 条一手），单测 25→30；`verify_data` 增加「领域判定须有 E1」与「财商必须写明校内已有」两条检查；新增「只做工具」样式与 3 条数据缺口 |
| V1.2 | 2026-10-20 | 报告增第 12 节「范围外：兴趣类赛道的判定」，证据 13→19（含 6 条新增，5 条一手），单测 20→25；`verify_data` 增加「赛道判定须有 E1 依据」检查 |
| V1.1 | 2026-10-20 | 新增 `生成调研报告.py` 与对应 20 项单测；工具目录职责扩为「issue 命令行 + 报告生成」 |
| V1.0 | 2026-10-20 | 自 allweather 移植；UA 改 `labloom-issue-cli/1.0`，示例改本项目场景 |
