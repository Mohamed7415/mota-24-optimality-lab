# 接续研究状态

目标：胖老鼠24层中完整、合法、可独立回放、同版本同规则严格超公开最高的路线；尚未实现。保持当前有额度时推进，定时仅作续接保障，不重复或覆盖运行中的结果。

## 最新真实完成度（2026-10-27接续）

- **当前实际最好：2018存档28568HP/5056攻/5032防/17级，AD10088，距公开28590低22。** generated/GdutNativeHP28568已完成，公开full-route-native-gdut-hp28568.json；1713动作/18045输入/295战斗/3276自然抽样，1444.232秒，审计通过。不要重启。完整无观测器对照仍失败，同纪录构建/规则未核实，绝不可称破纪录。以下28554为历史结果。

- **原版已实际完整通关28554血/5056攻/5032防/17级**，比28376提高178血，仍比公开28590低36。1779动作、19365输入、295战斗、3284自然抽样，墙钟1497.896秒，最终地图26/根帧4349/Boss格0，存活。无指定种子、改时钟、存读档和游戏变量写入。
- `generated/NativeHP28554` 原版回放已完成，`audit.log`、`public-recheck.log`全部通过。**不要重启回放**。公开 `experiments/full-route-native-hp28554.json`；完整动作 `full-route-hp28554-proposal.json` SHA256 `abc3fa2f36e64e717a10b36cf4144a98a3ac6614031f681da0660e18f6de3d26`；数值核对 `full-route-hp28554-audit.json`。
- 未完成整局无观测器对照；纪录准确构建/规则一致性未确认，绝不可称破纪录。视频页/公开view接口均412，Work浏览器空白且截图失败，没有取得视频实质内容。
- 原版候选仍为 `generated/private/mhhf.swf`，SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`，内部Ver1.12，作者发布血统未证。资源只在忽略目录。
- 本轮4项Node及73项Python测试全运行通过；原版收据独立核对通过；重建候选与公开回放输入的完整动作列表相同（顶层前缀元数据不同，文件SHA不同）。eb3bcea的五项CI已全部通过。新增2018存档比较提交后另查。

## 新路线如何复现

`tools/search_mixed_potion_reserve.py`：药水分当时吃、白衣法师后吃、留到本前缀以后。状态键为攻/防/级/延后补血/保留补血，保留最大HP；数值阶段放宽路径，正例再执行原版字节码。

命令（全在项目根目录）：
```
python3 tools/search_mixed_potion_reserve.py --advance 135,143 --extra-advance 352,353 --extra-advance 352,549 --must-eat 333,375,376,549 --target-reserve 1200 --check experiments/mixed-potion-reserve-1200.json
python3 tools/reorder_late_health.py
python3 tools/combine_hp_candidate.py --prefix generated/MixedPotionReserve/proposal.json --directory generated/RebuiltHP28554 --expected-hp 28554
```
使用不存在的新输出目录，避免覆盖既有或运行中的证据。

首13层金队长后55血/696攻/625防、78G/2314XP、钥匙3/1/3。提前1F蓝宝石，9F先杀(1,9)并吃(1,8)而留下(2,9)，解决红衣法师道路问题。延后源175/318/352三瓶小药水到最后白后，保留源623（10F小药水）及690/721（6F两大药水），总1200。

## 已跑过的限制分支，勿原样重跑

- 固定旧1147动作前缀与剩余奖励/钥匙交易的精确商店预算上界10088，不是全塔界。
- 2043单事件提前 × 全部28瓶早期药水延后选择，无额外500保留量的兼容前缀；806549881转移/473.26秒。543战斗延后（跨至多160源事件、对白处停止图剪枝）配合最早可负担购买也失败，279474116转移/152.70秒。公开early-*.json及G节保留范围。
- Prefix32早期多1廉价XP，首13金队长266血/701攻/625防且保留1500；后续卡在攻1130/防1200/XP77，无法伤害DEF1133的冥队长，95XP购买不足。不是完整候选。
- MixedPotionMacro1300 把374/375/376/385/395推迟至405并用ASAP XP失败；普通法师仍有100固定预伤害，不能把全部124伤害当可省。
- 原型 `generated/search_mixed_potion_reserve.py` 的继承元数据不适用于三分支；不要公开它。正式工具已修正，并有真实VM正例。

## 当前另一个方向：黄钥匙换600血

省5F黄门(5,8)，多的一把黄钥匙用于11F(0,3)三瓶小药水。绕门需很早杀5F(8,7)兽面人，前期损血很大；若仍可留至少700血药水至圣水前，加新增600血有望超过28590。

- `generated/EarlyYellowBypass` 已VM过5F蓝门，286HP/69A/31D，低金币购6/廉价XP购5。
- 同序DP重分配得 `EarlyBypassAllocated0`：553HP/73A/27D；排名1为519HP/77A/23D。对应全续至11F商店的宽8192束搜索均失败（约7百万转移、30秒、2.6–2.8GB）；不证明不可行。
- `GlobalEarlyBypass` 从自然开局重新搜索并避开原路线没开的门、5F黄门、早飞羽，已VM到蓝门：600HP/82A/27D、黄1/蓝0/红0、G50/XP17。7706095转移、44.37秒、3.09GB。`continue-global-bypass.log` 至11F商店失败（6020231转移、24.43秒、2.52GB）。
- `continue-global-redbat.log` 要求首红蝙蝠战后400HP失败；`continue-global-redbat-anyhp.log` 仅要求存活也已失败：6020231转移/23.66秒/2.52GB，最接近准入1203HP/117A/65D，门槛差697。黄门分支当前无运行进程，均为启发式失败。

所有束搜索都是启发式失败，无全塔不可行/最优证明。下一步必须保持真实完整路线及货币/钥匙总账，优先突破22血差或另一个已核实同规则纪录。

## 新取得2018存档与正在运行的独立版本回放

- `generated/private/gdut-v112.swf` 已实际取得，1856607字节，SHA256 `40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896`，Git blob SHA1 `166871fb3910734c241eb0135b485a6b2899e3ca`。与 gdut-yy/MagicTower 2018-07-11提交中的对象匹配；签名未认证，不能据此声称作者原始发布或与纪录视频同文件。精确来源见 `experiments/gdut-archive-provenance.json`。
- SWF6/100fps/9788帧；Ver1.12标题完整形状标签与此前目视核验者完全相同。103个动作脚本中99个相同，10个顶层DefineFunction及常量池完全相同，包括移动/地图显示。4脚本、2按钮不同，完整37,284标签定位比较见 `experiments/swf-build-comparison.json`。
- 实质差异：mhhf跨会话存档、商店/飞行器方向键扩展、1800秒限时；2018文件只内存存档，使用数字键选择，限时1500秒（超时会封16F通道）。不是两个可无条件互换的版本。
- 全1779动作在2018字节码数值模型通过，295战斗/3349最坏支持抽样，仍28554。模型不验证墙钟条件。
- **`generated/GdutNativeHP28554` 真实整局回放及独立审计均已完成，不要重启。** 1779动作/19365普通输入/295战斗/3282自然抽样，1497.448秒，仍28554/5056攻/5032防/17级。最终26层/Boss格0/根帧4349存活，真实时钟/无种子控制/无存读档/无游戏变量写入。`audit.log`、`public-recheck.log`均通过，公开 `experiments/full-route-native-gdut-hp28554.json`。整局无观测器对照及纪录版本匹配仍未完成。
- `generated/MixedGemSweep` 已完成：现有混合药水路线基础上加一次宝石提前，31变体+1对照共32固定顺序，尝试保留1300HP均无目标幸存。106065568转移/50.93秒/83.8MB（具体以公开mixed-potion-gem-sweep.json求和为准），只排除该有限范围，不是全局无解。
- 官方SRC分类/游戏API已实际取得，RTA首移动到击败血影，禁止辅助软件；本项目自动回放不能作为该RTA赛道合法成绩。证据指纹已写record-candidates.json。

## 当前运行实验（接续必须先查进程/结果）

- `generated/GdutObserverFreeHP28554`：直接顶层无观测器对照已结束并失败：19365输入全发送、播放器无报错，但 before-last-input.png 实际停在1层/1级/25HP/10A/10D/19G/18XP，不是通关。不能称对照通过。真实时钟、不加载观测器、不读写游戏变量。实际输入时序与截图保留本地。短程 `generated/GdutControlPaddedOpening` 已完成并目视检查：250输入、最小35ms间隔、长间隔+500ms；实际3层/459HP/23A/17D/25G/48XP、钥匙6/1/0、坐标10,5；非HP总账及位置匹配参考动作42（参考463HP，不同自然RNG）。仅短程证据，不是整局；公开gdut-observer-free-padded-opening.json。
- `generated/MixedBattleSweep`：已完成543单战斗延后+混合药水，目标1300HP均无兼容数值前缀。1571307050累计状态保留/1819579878转移/869.76秒/87.9MB；公开mixed-potion-battle-sweep.json，不重跑。
- `generated/Rescued32F15EarlyRed/proposal.json` 仅数值完整路线：28816HP/5056A/5025D（AD10081），不是10088条件血量超分。提前F15双攻/防宝石可跨旧中期攻击门槛；提前一笔原来晚买的红钥匙满足18F救人，延后两笔黄钥匙出售/未付得起的属性购买。预祝福少买20属性导致最终少7AD。未原版实际回放，不能称破纪录。原型 `generated/rescue_prefix32_f15_early_red.py`，日志对应同名连字符。
- `generated/MixedEconomyG11X32` / `...Fixed` 已失败，混合药水+11廉价金币/32廉价XP两个购买顺序仅能保留700HP；元数据继承旧参数，不作为公开证据。

- **`generated/GdutNativeHP28568` 实际整局及逐战审计/独立重算均已完成，不要重启。** 28568HP/5056A/5032D/17级，1713动作/18045输入/295战斗/3276自然抽样，1444.232秒；26图、根帧4349、Boss格0、存活，真实时钟、无指定种子、无存读档/游戏变量写入。公开 experiments/full-route-native-gdut-hp28568.json。最新实际最好28568，距28590低22。完整动作SHA256 `0ebe6d9c0ad9772059df35599040d80f9e09a5712759e91aa0d43fabcb9ff2a9`，tools/reorder_central_healing.py可重建。

- 预20F一笔17攻改17防、祝福前另一笔17防改17攻，消除20F普通敌人伤害，但接相同后缀最终仍28568；不要启动重复同分回放。原型generated/reorder_500_late_defense.py。
- 95a2e08的六项CI已全部通过；下一提交再检查。

- `generated/continue_28568_pipeline.py` 流水已全部结束，没有运行进程，不要重启或覆盖。`generated/GdutObserverFreeHP28568` 的35ms最小间隔/长间隔+500ms/末尾等60秒完整对照仍失败：18045输入全发，无播放器错误，但两张截图均在1层/1级/2386HP/74A/70D/35G/73XP/钥匙6,6,1。公开gdut-observer-free-hp28568-control-failure.json，不能称对照通过。
- 两颗额外宝石最早接触换序已完成66变体+对照共67项，191807432累计状态保留/222119822转移/107.62秒/87.2MB，无1300HP目标前缀。全部12颗最早宝石同时提前的放宽分支亦仅保留1200（1.64秒），各公开mixed-potion-two-gem-sweep.json及mixed-potion-all-earliest-gems.json。限定固定战斗/购买和最坏支持；非全局无解。
- 旧M4–M8报表默认仅接受mhhf指纹，防止将2018文件误标成mhhf；只有OriginalRoute显式allow_archive=True支持两份。新增5项跨存档测试全过（26.27秒）；总测试数4Node+78Python，原有73项此前已全运行通过。
- b688ffa的六项CI已全通过；下一提交再查。
- `generated/search_door_exchanges_filtered.py` 已完成394单门替换的晚期图放宽检查，无非平凡候选；预授予全部已访楼层的罗盘落点会虚假地使1F/16F红门等看似冗余，不能据此省门。不要把未真实执行的图结果叫可行路线。
- 正转向基于可见画面的无观测器控制：Swift/Vision工具生成于generated/ocr_visible_hud.swift及编译程序，已对失败图识别HP/攻/防/金币/经验正确；中文标签和部分钥匙读数不可靠，需要固定HUD数值区域识别与实际画面反馈。尚无运行中的视觉回放，不可宣称完成。


## 2026-10-27最新续接：早期金币DP与播放器音频阻塞

- 新正式工具tools/search_early_gold_allocation.py及experiments/early-gold-allocation.json：固定28568动作SHA0ebe6...，8项/365784标签/438851转移，5个真实字节码正例；总15.65秒/60.98MB。8廉价属性首红蝙蝠后100HP/119A47D，7属性+800HP后468HP/119A43D；长固定前缀分别卡源276/278（8属性+800卡308），原12属性正例仍重建13F55HP696A625D。不是完整候选，不是全局最优。原版VM正例已重放，不需反复运行；CI新增--check。
- generated/redbat-baseline-control.log：旧8192束搜索连原12金币正例都失败（14345809转移/69.41秒/5.92GB）；之前7金币+800HP、换蓝门等束失败不能作无解证据。
- generated/continue-early-gold-dp.log（7属性+800前缀）到11F商店启发式失败，4070转移/1389标签/0.02秒；8属性前缀允许小飞羽也失败861转移/325标签/0.005秒。未实际完整回放。
- generated/search_early_level{,2,3}_gold_dp.py 探索固定顺序8廉价属性+1~3早期付费等级、每级替代3次廉价XP购买，均在276失败；1级配合提前F5小药水200也失败。原型没有VM正例/正式完整枚举证书，别称全局不可能。generated/search_early_gold_advanced200_dp.py为诊断原型，继承/换序元数据不可靠，不公开其结论。
- tools/ruffle_clock_probe.mjs 已实跑默认/关闭声音输出各40秒。默认AudioContext running但currentTime固定0.005805；禁用浏览器声音输出后真实时钟推进40.182秒且片头/菜单正常。公开experiments/ruffle-audio-clock-{default,disabled}.json。游戏文件/Date/RNG/资源未改；仅被动Web Audio读数。今后播放器片头卡住先看此问题，别反复跑冻结画面。
- tools/fullgame_control.mjs新增MOTA_CONTROL_DISABLE_AUDIO_OUTPUT=1并在收据披露参数。generated/GdutAudioDisabled1000已结束：前1000输入，35ms下限/长间隔+500ms，197.335秒，实际861HP26A28D、G38XP107、1级、钥匙1/0/1、英雄10,9，外观6F右下入口；资源与参考动作不同时匹配，仍非独立对照通过。公开gdut-observer-free-audio-disabled-1000.json。不要启动同样的完整固定时序40分钟对照；要实现可见画面反馈。
- generated/visible_hud_fast.swift编译程序：固定HUD区域4倍放大、N前缀辅助识别；多数HP/攻/防/币/XP及部分钥匙可读，数字0或1偶有漏读，level需低置信阈值。保留raw/confidence，不能默认缺失为0。皮肤+蓝色像素识别heroCandidates；只在已知空格验证，不是全地图可靠识别。
- 旧VisualHostPilot2/VisualNoopHostPilot等冻结90分钟试验已按确切PID核对并关闭本任务的进程及子浏览器；其余40秒音频探针、1000输入、数值搜索均已结束。没有运行中的原版整局或后台搜索。不要重启已经结束的流水或覆盖证据。
- 新公开报告K节，README更新；接续优先突破更早战斗/金币购买时机或门成本，并完成实际画面反馈的独立控制。最新仍28568，不能把8廉价属性前缀或28816/AD10081分支称为破纪录。

- 本次新增分配工具的--check已在mhhf与gdut两份固定SWF分别通过（8项结果、5个完整字节码正例均一致）；7项商店回归通过；两份Node工具语法和Python编译及git diff检查通过。推送后的新CI需另查，不能沿用旧CI结果。
