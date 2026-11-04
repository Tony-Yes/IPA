# MoviePilot + qBitController 多软件源

非官方源；IPA 直接指向原作者 GitHub Release，不镜像安装包。
采用 AltStore 风格明文 JSON，LCSign 手机导入及安装兼容性尚未验证。

## 发布步骤
1. 建立 Public GitHub 仓库 `moviepilot-source`，默认分支 `main`。
2. 解压本 ZIP，把全部文件上传仓库根目录，不是上传 ZIP 本身：
   - update.py
   - apps.json
   - test_update.py
   - source.json
   - README.md
   - .github/workflows/update.yml
3. 注意隐藏的 `.github` 文件夹。如果网页上传漏掉它，使用 Add file → Create new file，文件名输入 `.github/workflows/update.yml`，粘贴相应内容。
4. Actions → Update MoviePilot source → Run workflow。保留原工作流名称，便于旧仓库升级。
5. 运行成功后，LCSign 添加以下地址，替换用户名：
   https://raw.githubusercontent.com/YOUR_USERNAME/moviepilot-source/main/source.json
6. 确认两款软件可显示及下载。安装需自行签名；不上传证书、密码或描述文件。

已有仓库：覆盖同名文件，并新增 apps.json、test_update.py。源地址不变。
无需开启 GitHub Pages，也无需个人 Token。仓库策略或分支保护可能禁止机器人提交。

## 自动更新
每 6 小时检查两个仓库的最新正式 Release（GitHub 调度可能延迟，长期不活跃也可能停用）。
下载 IPA，核对大小，读取主 App Info.plist 的实际版本、Bundle ID 和最低系统版本。
MoviePilot 必须通过作者 SHA256SUMS 校验；qBitController 若 GitHub 提供 asset digest 则校验它。
若缺少 digest，仅计算并记录本地 SHA256，不声称独立校验通过。
单个软件失败且有旧记录时保留该软件旧记录，其余正常更新，Actions 显示警告。
无旧记录的失败、或全部软件失败时，任务失败且不覆盖 source.json。
仅提交发生变化的 source.json。

## 加软件
在 apps.json 数组加入一项，填写 name、repo、asset_pattern、icon_url、description。
asset_pattern 是完整匹配的正则表达式，必须精确选出一个 iOS IPA，避免 Android、模拟器等附件。
require_sha256sums=true 用于强制校验名为 SHA256SUMS 的附件。
软件 name 必须唯一且应保持稳定（失败时按名称寻找旧记录）。
软件需公开提供可直接下载的 IPA，登录/验证码下载不适用此脚本。

## 本次真实运行
- MoviePilot 1.1.1 / org.moviepilot.app：SHA256SUMS 校验通过。
- qBitController 2.2.1 / dev.bartuzen.qbitcontroller：GitHub asset SHA256 digest 校验通过。
- 两项单元测试通过（多软件生成、单软件失败保留旧记录）。测试使用合成 ZIP 隔离网络，不是实际 Release 数据。
- 实际两款 IPA 已下载并解析，source.json 已生成。
- 尚未在用户 GitHub 仓库运行 Actions，也未在 LCSign 手机上实测。

校验保障下载完整性，不代表独立安全审计或签名有效性。
