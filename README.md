# Mota 24 Optimality Lab

研究目标：对一个精确 SWF 指纹的胖老鼠 24 层魔塔，定义优化目标、建立忠实规则，再寻找可验证的全局最优性证明。

**当前进度 M5（2026-10-22）：独立 Ruffle 数值验证 + 完整 RNG 状态枚举 + 原版一层条件上界980 HP。24层全局最优仍未证明。**

| 已完成 | 可复核结果 |
|---|---|
| 固定原版候选 | SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`；内部标题 Ver1.12，SWF格式6 |
| 独立播放器 RNG 验证 | 官方 Ruffle0.7.1，1,000次抽样与算法移植全相等；C/Python另校验5种种子各1,000次 |
| 独立播放器原版战斗验证 | 99案例，1,163条数值快照全相等；隔离原版动作体，尚非整部游戏回放 |
| 完整 RNG 状态枚举 | 2,147,483,647个非零状态；1级最多连续4次暴击 |
| 原版 MT1 收紧上界 | 禁止5连暴击的放宽模型精确980 HP；2,032标签/12,278转移；独立逐格727,668状态一致 |
| M4原版子集 | 596战斗案例/4,976帧快照；独立抽样支持模型995、对抗支持模型860 |
| 真实数据及来源 | 原版27地图/33敌人与静态提取一致；复刻27地图对象、63敌人、50道具及事件来源 |

**980 是上界，真实种子可达性尚未建立。** 这项结论仅针对固定 Ruffle0.7.1、M4的MT1局部规则、战斗之间不插入其他RNG抽样的条件模型。
初始1000HP/10攻/10防、1级、三色钥匙各1，以首次触及上楼梯为终点，禁止跨层绕行和商店。
M4的995仍是允许每次独立任意抽样时的精确值；M5在更具体的条件模型中将其排除，对所有局部路线成立。
保守保证860与上界980均不能当成24层全局答案。

M5播放器探针执行原版战斗数值动作体，替换音效、显式调度各段并采集数值；未验证原始实例层级、完整时间轴和按键回放。
时钟、剧情、商店、跨层、保存/等待/种子策略与原版全塔搜索仍未完成，作者原始发行链未独立认证。

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
```

默认 `npm test` 为离线入口，原版相关8项集成测试会明确跳过；设置原版SWF环境变量后，4项Node与29项Python测试全运行。
M5验证还执行完整RNG枚举及独立播放器探针，并核对稳定基准。CI分四个作业：Node22/24、M4原版专项、M5独立Ruffle。
CI只上传数值JSON，未提交或上传原版SWF、图像、音频、完整游戏对话或包含原版动作体的测试影片。

`bootstrap`固定 [arcxingye/MagicTower](https://github.com/arcxingye/MagicTower) 提交
`3bcfcc3e6dc082e8fef8ef9e62c0b70cb55d7ef9`，使用Acorn静态解析；不运行上游JS。
完整带来源数据在忽略目录 `generated/tower.json`。M4原字节码数值模型与复刻数据管线分开，可以独立运行。

## 报告和证据

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

固定版本的RNG和隔离战斗例程已实测。接下来需要整部未改原版影片的确定按键回放，明确其他RNG消费、种子/等待/存档约定，再验证时钟、跨层、商店和剧情。
完整全塔模型与搜索、全局上下界证书均未完成。内部Ver1.12已取证，作者未修改发行链仍缺独立认证。
