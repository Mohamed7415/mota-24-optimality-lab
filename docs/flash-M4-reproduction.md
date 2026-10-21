# M4复现与可信计算边界

## 一键重现数值证据

```sh
python3 tools/fetch_swf.py mhhf
python3 tools/flash_milestone.py generated/private/mhhf.swf \
  --check experiments/flash-M4.json --out generated/flash-M4.json
MOTA_FLASH_SWF=generated/private/mhhf.swf \
  python3 -m unittest discover -s tests -p 'test_*.py'
```

M3复刻测试需要先运行 `npm run bootstrap`。只复现M4原版专项时，无需Node、Acorn、FFDec或JRE：

```sh
python3 tools/fetch_swf.py mhhf
python3 tools/flash_milestone.py generated/private/mhhf.swf --check experiments/flash-M4.json
MOTA_FLASH_SWF=generated/private/mhhf.swf \
  python3 -m unittest discover -s tests -p 'test_flash_integration.py'
```

原版基准来自M3已取得的同一精确文件指纹；下载器遇到哈希变化直接失败。
只有 `elapsedSeconds` 和进程峰值 `peakRSSBytes` 从跨机器基准比较中排除。其他数值、状态数、路线、帧摘要、原始段偏移/哈希均必须一致。

## 数据来源

`tools/flash_sections.py`直接读取CWS解压后的标签与AVM1动作：

- root第4346帧的初始化动作前缀，在Date构造器前停止。
- 同帧根作用域函数 `SetLineDisplay` 和 `Move_arrow`，包含其继承常量池。
- sprite453的战斗帧1、24、34、35、54。
- sprite855第1帧，在开场事件配置下解释到Date前停止。

每段的tag偏移、字节数据偏移、函数体偏移和SHA256记录于数值报告。
原始字节、反编译源码、完整地图数据不被写入公开M4报告。

## 解释器允许和拒绝什么

`src/avm1.py`只实现这批测试所需的数据、算术、比较、分支、数组、变量和成员操作。
输入必须先通过完整SWF指纹校验。未知操作码、未知构造器/原生函数/方法、无效跳转、资源上限等会失败；不存在通用脚本动态求值入口。
函数体只被提取，已知入口由测试驱动显式选择；解释器不提供任意游戏函数的自动分派。

显示/音频方法记录为数据事件。Date不被执行，不读取真实时钟；随机操作仅消费测试提供的0..199整数。
解释器本身是可信计算基的一部分，本阶段不声称已验证完整AVM1或播放器实现。

## 路线适配边界

路线从开场结束事件状态出发，实际解释一次钥匙奖励；再解释 `SetLineDisplay(1)` 得到原版位置(x=5,y=9)。
随后通过原版 `Move_arrow`逐格移动、开门、拾物、战斗准入及奖励，用原版战斗帧进行数值结算。

对话/门动画的结束被适配器明确确认；战斗结束后，适配器按原worldTick处理顺序清标志并显式调用原 `Move_arrow(100)`。
这些边界没有冒充原生播放器的动画/输入调度。上楼梯只验证到触发状态，未运行下一层加载流程。

每个交互后都比较HP、攻、防、三色钥匙、金币、经验，以及原地图目标格是否清空。
原版路线和独立逐格解还会比较最终答案。计时、保存、跨层、升级与实际PRNG不属于本次模型。

## 数值规则参考

- [Adobe SWF19格式规范](https://open-flash.github.io/mirrors/swf-spec-19.pdf)：动作、分支偏移、栈次序、随机操作0..maximum-1、混合字序双精度数。
- [Adobe ActionScript 2文档](https://open-flash.github.io/mirrors/learning-as2.pdf)：SWF6及更早标识符大小写语义。
- [Ruffle AVM1操作实现](https://github.com/ruffle-rs/ruffle/blob/dd4e73d593be11412c987a41e73701be5fab74a6/core/src/avm1/activation.rs)：除零与ToInteger的实现参考。未把Ruffle运行结果当成本阶段回放证据。

数值模型支持的输入是本作初始/局部搜索的有界整数与这些固定字节码路径，不是完整AVM1语言一致性声明。
