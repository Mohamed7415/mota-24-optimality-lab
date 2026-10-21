# Mota 24 Optimality Lab

研究目标：对一个精确 SWF 指纹的胖老鼠 24 层魔塔，定义优化目标、建立忠实规则，再寻找可验证的全局最优性证明。

**当前进度 M4（2026-10-22）：原版字节码子集验证 + 原版一层条件模型精确搜索。原版 24 层全局最优仍未证明。**

| 已完成 | 可复核结果 |
|---|---|
| 固定原版候选 | SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`；内部标题 Ver 1.12，SWF格式6 |
| 原版数据 | 字节码初始化恢复的27张地图、33个敌人五元组，与M3静态提取全部一致 |
| 原版规则验证 | 596个战斗案例、4976个帧快照、124个准入案例、16个拾物/门案例；开场钥匙仅发一次 |
| 原版MT1最有利支持模型 | 精确995 HP；416标签；独立逐格27734状态；原字节码数值路线回放一致 |
| 原版MT1对抗支持模型 | 精确860 HP；416标签；独立逐格43756状态；原字节码数值路线回放一致 |
| 实际搜索输入再验证 | 两种模型各123个不同战斗输入，全部用原字节码检查准入，47个可进入案例再检查结算 |
| M3复刻数据/实验 | 27地图对象、63敌人定义、50道具定义及事件来源；复刻MT1局部860 HP |

**995 的含义有严格限制**：模型允许每次攻击独立选择0..199中的随机输出；见证路线给定了21次抽样。
真实 Flash 播放器的 PRNG 算法、种子和该序列可达性尚未核实，因此995不是“真实原版已实现的最优”。
860是指定对抗支持模型的最优保证值；两者都禁止其他楼层绕行、固定初始1级、以首次触及上楼梯时HP为目标。

字节码数值回放使用项目自己的受限 AVM1 测试解释器，显示/音频为替身、界面结束有显式适配边界。
尚未进行原生 Flash Player 或 Ruffle 集成回放，也未建模时钟、完整剧情、商店、全塔和真实PRNG。

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
```

默认 `npm test` 为离线测试入口，原版集成类会明确跳过7项；最后一条命令包含全部27项测试方法。
CI中两组复刻/基础测试（Node22/24）与原版专项作业共同覆盖全部测试，原版专项重新下载并校验SWF。
CI只上传数值JSON，未提交或上传原版SWF、图像、音频或完整游戏对话。

`bootstrap`固定 [arcxingye/MagicTower](https://github.com/arcxingye/MagicTower) 提交
`3bcfcc3e6dc082e8fef8ef9e62c0b70cb55d7ef9`，使用Acorn静态解析；不运行上游JS。
完整带来源数据在忽略目录 `generated/tower.json`。M4原字节码数值模型与复刻数据管线分开，可以独立运行。

## 报告和证据

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

优先加入独立播放器的确定输入回放、固定播放器版本及RNG/初态规则，继而验证时钟、跨层、商店和剧情。
完整全塔模型与搜索、全局上下界证书均未完成。内部Ver1.12已取证，作者未修改发行链仍缺独立认证。
