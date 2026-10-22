# 本地预检与有界 Colab 传输

分配超时见 [CLI 0.7.4 无分配诊断](diagnostics/README.md)：HTTP 超时与外层进程时限不同，外层超时不能判定 GET/POST 阶段。分配期间不轮询 `status`；它会同步远端 assignments 并可能改写本地会话状态。控制器没有 status 观察循环。

认证可信零会话检查仅支持已审查的 CLI **0.7.4**：复用 `usage` 已认证的只读 `ccu-info` 返回，严格核对完整 balance/rate/assignment count 三行 stdout。分配前要求 count=0 和余额为正；stop 后要求新的可信 count=0 且 stop 成功，余额无需为正。此路径不经过会吞认证退出的 `sync_sessions()`。退出码 0、旧 `sessions` 空列表、仅 stderr 的内容、重复/缺失字段、认证失败、超时或未知 CLI 版本均不能证明释放；失败记 `READBACK_UNVERIFIED` 或 `CLEANUP_FAILED`。继续保留有限清理预算与两次 stop+回读上限，无新增认证管理、API 或供应商文件修改。它依赖受信任的已安装 CLI/服务端响应，不证明回读后的并发账户状态；本地 Mock 不能代替真实端到端验收。

> [English](README.md) | 简体中文

状态：**LOCAL_VALIDATED + SCOPED LIVE_READY（CLI 0.7.4、请求 T4 的纯传输路径）**。固定源码 `8081b6e02eee0754903898d5afe5b112f1bb23d0` 的 [SAE PR #48](https://github.com/JohnnyZPiggy/SAE-Framework/pull/48) 已在真实 Colab 完成 Kernel、driver、文件哈希与 stop 后认证零会话核验；此传输试点未直接观察设备型号。[TorchYAND PR #22](https://github.com/JohnnyZPiggy/TorchYAND/pull/22) 则另行在确认的 Tesla T4 上完成单个算法科学试点，不等于通用加速承诺。基于 SAE_Test PR #3 合并提交提炼；[来源与许可证](NOTICE.md)。只需要相邻的三个 Python 文件、标准库、已有 Git 和 Colab CLI；不提供包发布、后台进程、bootstrap 或 Publisher。数学算法、安装与数值验收属于项目 driver。

未来项目按**精确 SAE 提交或 tag**复制/引用三个运行时文件并保留 MIT 声明，另行记录算法 `--source-sha`。不追踪浮动 main，不升级旧项目 `.sae/`，不强制每次实验复制 90 个协议文档。Python 3.12.14/Windows 和 3.12.3/WSL 的本地回归已运行；WSL 本地检查已有 CLI 0.7.4。初期仅接受请求 `T4`，不据此声称已验证真实硬件；CPU/TPU/XLA 与原生编译未实现。

在与实际执行相同的 shell（需要时使用已有 WSL 登录 shell）调用 `--preflight-only --repo-path path/to/project --source-sha 完整40位SHA --run-id 唯一名称 --out 新目录 --cli colab`。它只调用 `version`、本地 Git/文件系统，不认证、不查询会话、不分配资源。使用 Git blob 原始字节导出，忽略脏工作树与 CRLF 转换，临时导出排除 `.sae/`；拒绝符号链接、子模块和不安全路径。临时构建/缓存目录必须可写且位于项目与 Dropbox 外；`--temp-root` 可覆盖。默认不安装；显式 `--install-local` 只用已有 pip/构建依赖进行临时 no-deps 安装，无失败后自动安装或登录。

单独授权的计算任务可去掉 `--preflight-only`，传入项目自己的 `--driver scripts/my_driver.py --artifacts experiments/artifacts.json`。两者从项目精确提交读取，拒绝绝对/越界路径及符号链接，不执行脏文件。driver 临时放在非同步目录，收到 `SAE_CANDIDATE_SHA`；driver 与 manifest 哈希分别记录，框架不包含算法仓库地址或安装逻辑。

manifest 为 `{"artifacts":[{"name":"measurement.json"}]}`：1–16 个 JSON 文件名，禁止目录、控制报告重名、Windows 保留名或大小写重复；manifest 最大 64 KiB，driver 最大 1 MiB，每个输出最大 1 MiB，远程路径 `/content/<name>`。driver 每个文件输出一行 `ARTIFACT 文件名 字节数 SHA256`。框架核对长度、哈希、JSON 的 `source_sha` 和 `status: PASS`，拒绝重复 JSON 键。**传输 PASS 不等于科学验收**；必要输出 FAIL 会阻止传输通过，可选 NOT_RUN 信息应放在主报告内，不能伪报通过。

[示例 driver](../../examples/compute_adapter/driver.py) 与 [manifest](../../examples/compute_adapter/artifacts.json) 仅写传输样例，GPU/TPU/编译明确 NOT_RUN。`python -m unittest discover -s tools/compute/tests -v` 会在本地临时目录运行示例及故障回归，无需分配 Colab。

默认总任务 5400 秒、分配 600 秒（最多 2700）、清理保留 60 秒、Kernel 30 秒（外部最多 35 秒且受剩余预算约束）、工作执行 240 秒。每次新会话必须先做短 Kernel 探针；失败记 `KERNEL_PROBE_FAILED`，跳过 driver 并清理。工作超时后仍保留独立清理预算，最多两次 stop + 服务端零会话验证；释放不确定必须 `CLEANUP_FAILED`。既有不相关会话或未确认额度会阻止新分配。不增加购买、令牌管理、后台重试、HTTP monkeypatch 或科研审批。无法保证 OS 强制终止或服务商故障时释放成功；模拟不构成真实清理证据。

控制报告仅保存安全错误码、步骤时长与时间戳、源码与传输哈希，不记录原始输出、参数、私人根路径、OAuth URL 或环境转储；未观察的安装/CPU/发布/人工批准/交接为 null。下载 artifact 的内容由项目负责，传输层不自动删除其中秘密，独立发布前必须另行检查。工具不写 GitHub。本次真实 GPU、TPU、编译未运行，见[本地证据](../../reports/compute-issue38/summary.md)。完整参数、限制和依赖边界以英文页为准，GPT 独立审核验收与合并。
