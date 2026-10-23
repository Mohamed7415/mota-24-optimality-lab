# Mota 24 Optimality Lab

研究目标：对一个精确 SWF 指纹的胖老鼠 24 层魔塔，定义优化目标、建立忠实规则，再寻找可验证的全局最优性证明。

**当前进度 M8（2026-10-23）：真实三层受限续程搜索 + 原版2150HP路线验证 + 有限性及保守上界。24层全局最优仍未证明。**

| 已完成 | 可复核结果 |
|---|---|
| 跨层真实优化搜索 | 固定M6前缀、束宽1024，展开46,408标签/293,935转移；约15.80秒/201MiB；585输入完整原版回到MT1为2150HP；受限区间[2150,13860]，未证最优 |
| 跨层真实路线见证 | 285普通输入、13战斗、115实际抽样；取铁剑、买800HP、多次往返后在MT1为905HP/23攻/9金币/31经验；无观测器对照一致 |
| 六类商店 | 216边界案例，自写数值模型/原版字节码/官方Ruffle结果全相同；升级例程未强制200级封顶 |
| 商店资源有限性 | P=金币+10黄+50蓝+100红+经验，R=P(P+1)/2+金币；每笔改变资源的交易严格降低非负整数R。外部奖励有界性仍待证明 |
| 完整原版影片回放 | 未改SWF，73个普通鼠标/键盘输入；序章、一层三场战斗、二层到达860 HP；没有界面/战斗完成替身 |
| 无观测器对照 | 原版直接顶层加载，输入顺序一致；四个资源显示区域逐像素相同 |
| 自然开局校正 | 仙子给各1把，序章黄门消耗1把，MT1实际钥匙为黄0/蓝1/红1 |
| 固定种子精确局部最优 | 种子128188416：860 HP；98标签/211转移；独立逐格3,654状态；21次实际抽样逐项一致 |
| 任意种子的条件上界 | 自然开局965 HP；372标签；独立逐格127,160状态；尚未证明真实种子可达965 |
| 固定播放器与RNG | Ruffle0.7.1，完整枚举2,147,483,647个非零状态，1级最多4连暴击；99隔离战斗/1,163快照一致 |
| 固定原版与真实数据 | SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`；内部Ver1.12；原版27地图/33敌人与静态提取一致 |
| 复刻静态数据 | 27地图对象、63敌人、50道具及事件来源；不执行其上游JS |

**此前未走完整序章，未纳入黄门消耗；自然开局基准已修正。** M4/M5固定“钥匙各1把”的995/980仍是历史条件实验，不能代表自然开局。
自然开局的独立任意抽样最好支持值为990，对抗保证为860；固定Ruffle任意种子的放宽上界为965。
指定种子局部区间 `[860,860]`，选种子的保守局部区间 `[860,965]`，两者均不代表24层全局区间。

M6保留的局部目标是MT1首次触及上楼梯时HP最大，等级1、初始1000HP/10攻/10防、钥匙0/1/1，禁止跨层绕行、商店、存读档/重开/跳随机数策略。
日期固定以确定RNG，实际时钟未验证；观测回放用只读父影片，顶层原版对照没有观测器或游戏变量读写。
M8固定M6前缀并阻挡未验证事件，受限模型有限、资源动作最多115次；束搜索裁剪91,589项，未穷尽。原版可行下界2150、模型放宽上界13860不是完整三层或全塔界限。M7的905保留为历史可行路线；二者不能与M6首次上楼梯目标混用。商店秩证明不替代全塔外部奖励审计。当前未普遍验证所有游戏路径、Adobe原生播放器、计时/剧情/商店/跨层或24层全局最优。

## 复现

需要 Node.js 22+、Python 3.12+、Git。首次获取依赖/上游及原版候选需要网络。

```sh
npm ci --ignore-scripts
npm run bootstrap
npm test
npm run experiment

# M4原版专项：下载到忽略目录，先检查完整SHA256
npm run flash:fetch
npm run flash:verify
MOTA_FLASH_SWF=generated/private/mhhf.swf npm test

# M5：需要C11编译器；下载固定独立播放器及浏览器
npm run ruffle:fetch
npx playwright install --with-deps chromium
npm run ruffle:verify

# M6：完整原版回放 + 无观测器对照 + 自然开局双算法校验
npm run game:verify

# M7：真实跨层商店路线、六类商店探针与资源秩验证
npm run crossfloor:verify

# M8：真实跨层束搜索、独立逐格路线核对、原版完整执行及对照
npm run optimization:verify
```

默认 `npm test` 为离线入口，原版相关14项集成测试会明确跳过；设置原版SWF环境变量后，4项Node与48项Python测试全运行。
M5验证执行完整RNG枚举及独立播放器探针；M6验证完整原版回放及对照，并核对稳定数值基准。CI分五个作业：Node22/24、M4原版专项、M5/M6/M7独立Ruffle、M8搜索及独立完整回放。
CI只上传数值JSON，未提交或上传原版SWF、图像、音频、完整游戏对话、完整回放截图或包含原版动作体的测试影片。

`bootstrap`固定 [arcxingye/MagicTower](https://github.com/arcxingye/MagicTower) 提交
`3bcfcc3e6dc082e8fef8ef9e62c0b70cb55d7ef9`，使用Acorn静态解析；不运行上游JS。
完整带来源数据在忽略目录 `generated/tower.json`。M4原字节码数值模型与复刻数据管线分开，可以独立运行。

## 报告和证据

- [M8详细阶段报告](docs/M8-report.zh-CN.md)
- [M8搜索与原版数值基准](experiments/optimization-M8.json)、[M8复现说明](docs/optimization-M8-reproduction.md)
- [M7详细阶段报告](docs/M7-report.zh-CN.md)
- [M7商店/跨层基准](experiments/crossfloor-M7.json)、[M7复现说明](docs/crossfloor-M7-reproduction.md)
- [M6详细阶段报告](docs/M6-report.zh-CN.md)
- [M6完整影片/自然初态/搜索基准](experiments/whole-game-M6.json)、[M6复现说明](docs/whole-game-M6-reproduction.md)
- [M5详细阶段报告](docs/M5-report.zh-CN.md)
- [M5实验基准](experiments/ruffle-M5.json)、[播放器来源指纹](experiments/ruffle-release.json)
- [M5复现与可信边界](docs/ruffle-M5-reproduction.md)
- [M4详细阶段报告](docs/M4-report.zh-CN.md)
- [M4原版验证/搜索/路线基准](experiments/flash-M4.json)
- [M4复现与可信计算边界](docs/flash-M4-reproduction.md)
- [原版指纹、内部版本图形证据](experiments/swf-evidence.json)
- [有限状态与全局证明条件](docs/proof-scope.zh-CN.md)
- [第三方资源边界](THIRD_PARTY.md)
- [M3历史阶段报告](docs/M3-report.zh-CN.md)
- [M3复刻基准](experiments/remake-baseline.json)、[M3原版静态基准](experiments/flash-mhhf-baseline.json)

已有实证表明，原版战斗准入预判和实际结算不同，不能直接套复刻伤害公式。
例如绿头怪对45HP/11攻/10防的勇士拒绝开战，尽管强制进入独立战斗例程会剩5HP。

## 下一步需要解决

已运行真实三层受限续程束搜索并验证2150HP路线。接下来收紧保守上界、建立保持完备的搜索，开放二层剧情/铁门，扩展特殊敌人/真实时钟，并继续审计全塔外部奖励、其他RNG消费与存档策略。
完整全塔模型与搜索、全局上下界证书均未完成。内部Ver1.12已取证，作者未修改发行链仍缺独立认证。
