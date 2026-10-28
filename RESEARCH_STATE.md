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


## 最新未推送工作（后续心跳先查进程，勿覆盖）

- Git HEAD54b749032fa5b18839dc25d66a013ecae1190950已推送；CI40395480110六项全部success。
- 新未提交源码tools/read_visible_hud.swift、visual_prefix_host.mjs、visual_prefix_pilot.py已实际运行。generated/VisualPrefix29Retry **完整无人干预从菜单跑完首29动作**，98.075秒/259普通输入；最后508HP23A17D、G6XP29、黄2蓝1红0、1级。无观测器/游戏变量读写、无种子或时钟控制。手工查看action5/6/28图，实际2F/3F/3F。只验证三层短程（含第一笔金币商店），不是整局或破纪录。数值期望493HP，实际自然RNG508。前两次新鲜无人干预试验失败收据仍在VisualPrefix29Fresh与Foreground，不覆盖。
- HUD Swift采用真实数字白色前景清理及对齐的合成123上下文，解析时去掉123，未知保持缺失；不用学来的原版数字模板。首步漏接仅在截图仍为旧位置、九项原HUD完全一致时重发，禁止缺失读数默认0。工具还没进入CI和GitHub，需整理数值收据与说明、提交。
- 较早手动辅助开发会话VisualFeedbackPilot已主动关闭：连续同一局前28动作逐图核对，首29商店由普通输入手工辅助完成503HP23A17D G6XP29；不是无人干预实验，勿与Retry的508HP混用。图片/原版纹理都不发布。
- generated/LateDoorOmissions初版27省门失败但no-omission控制因漏F0特殊楼梯失败，不能用于排除。改版generated/LateDoorOmissionsPreserved **正对照完整28568通过**，27个源800以后门逐一省略均未接成完整固定消费顺序；25.94秒/138.13MB，有限策略失败，非全局无省门方案。源码仍generated/私有原型。
- generated/route_guidance_goal.py启发式原型加入目标战前HP缺口惩罚及200HP分桶。自然开局2048束仍失败（3.56M转移/23.52秒/1.82GB），但从源84首次F5蓝门后做正对照 **已VM打过8F首红蝙蝠**：207HP125A47D，2.21M转移/19.78秒/1.13GB，generated/RedBatGoalAfterBlueControl。原始8192束自然开局失败不是不可行证明。
- 同目标引导接GlobalEarlyBypass黄门省略前缀，最坏支持仍失败：1.67M转移/10.58秒/.83GB，准入缺57HP（1230HP136A43D）。正转向仅用于生成候选的真实Ruffle固定种子数值模拟，**不是实际游戏设种子**；需要先完整数值路线、再无指定种子的真实影片验证，任何模型结果都不能冒充纪录。当前启动generated/search_redbat_goal_yellow_bypass_fixedseed.py，输出redbat-goal-yellow-bypass-fixedseed.log与RedBatGoalYellowBypassFixedSeed；先查进程/结果，勿重复启动。原版实际最好仍28568/10088，差22。


- 最新正式工具再跑generated/VisualPrefix29MenuReady **无人干预首29动作成功**：261输入/91.281秒，最终3F493HP23A17D G6XP29钥匙2/1/0，目视复核2F/3F/终点楼层标签；公开experiments/visual-prefix-gdut-29.json。此前Retry的508HP为另一局，单独保留earlier-run收据。工具不读游戏变量，只有图像HUD/角色候选；尚无整局独立回放。
- tools/visual_prefix_pilot.py现在从可见菜单文字区域出现后才点击开始，不再假定固定18秒；移动重试仅旧位置与完整九项旧HUD均仍可见时允许。tools/read_visible_hud.swift真实数字前景清理、对齐合成123上下文，未知保持缺失，无手工原版字形模板。局部原型的早期人工辅助局不可当无人干预证据。源/收据指纹已核对；3份新工具和macOS首29步CI待提交同步。
- generated/RedBatGoalYellowBypassFixedSeed仍失败，数值模型种子128188416；准入缺31HP。只用它提取消费顺序，生成YellowBypassNearGate/proposal.json（348动作，目标红蝙蝠尚不可进入），不是候选通关。末端有可免费取的7F(7,2)ATK3及5把黄钥匙等。重分配该顺序全部23笔攻防购买得到63个最坏支持DP状态，均未直接跨首红门槛。
- 正在运行generated/continue_yellow_bypass_frontier.py（查continue-yellow-bypass-frontier.log），把这63个固定顺序分配状态作为联合起点，允许后续真实采集/战斗/经验购买，仍保留圣水/飞羽、12廉价金币/31廉价XP、禁5F(5,8)黄门。若找到，要先用所选原版字节码前缀及续程逐动作核验；结果未出前别称路线。所有当前fullgame原版整局回放均已完成，不重启。

- 63个最坏支持分配起点联合搜索已结束失败：116404转移/39632标签/.458秒/79.28MB；不能称黄门分支无解。随后在348动作近门序列里，把真实7F(7,2)ATK宝石提前到最早原版可接触时点，再做固定顺序全部23笔攻防重分配；generated/allocate_yellow_bypass_early_gem.py正运行/查allocate-yellow-bypass-early-gem.log，不重复启动。
- 首29步正式源码最后一次单局无人干预成功数据是VisualPrefix29MenuReady的493HP/91.281秒/261输入；README/L节已更新，Mac CI新增visual-prefix-macos，尚未推送新提交，下一步提交并查看新7项CI。54b7490旧6项全部success。

- 807e32a已推送；CI40432611065六项旧检查success，新增Mac视觉CI **failure**。远端单局50输入、0源动作匹配，错误Natural MT1 entry not visibly matched。数值artifact已实际下载到generated/CIVisual807e32a；公开失败收据保留，不称跨机通过。
- 开场已改为逐图确认对白/出生，出生图已出现时等待HUD完整再动；放宽橙框色相识别，并保留boot-observations/failure-observation数值到CI。新本机VisualPrefix29BootFeedback成功：97.681秒/265输入，493HP23A17D G6XP29 Y2B1R0；源码哈希与新收据对应。待提交推送修正，再查Mac CI结果。所有这些局都只29步，不是24层成绩。
- 单纯数值模型“在源84后买XP等级”因店不可达被VM拒绝，已废弃虚假正例；真实最早XP接触178，加入8廉价金币/一次真实升级的固定顺序只有17HP114A46D首红正例，仍非完整路线。调整真实左侧通路和尽早购买后，EarlyLevelASAPRed已VM过首红：最好322HP118A42D L2、G228XP43、Y5B7R1；仍缺完整后续。此路线8低金币、1廉价升级、7廉价属性，模型预算同剩余奖励条件上界10090，但不能说可达或破纪录。
- 现在运行generated/search_early_level_asap_full_potions_dp.py，提前F7原有全部药水以放宽F5左路前的可行分配，再做固定消费顺序/尽早付费的精确分配DP；查early-level-asap-full-potions-dp.log，不重复运行。若有好前缀，再实际VM续至11F/13F及完整后缀。资料和原型均未上传原版素材。

## 最新接续结果（覆盖上文“正在运行/未提交”的旧描述）

- 7e39435已推送，CI40435576376完成：六项既有检查success，新Mac视觉检查failure。实际下载数值artifact至generated/CIVisual7e39435Retry；0动作/46输入/115.513秒。开场观察43角色5,1→44无角色候选→45一层出生候选但红0，44后又发送Up。boardBlackFraction始终0，**不能说黑屏检测成立**。公开失败收据visual-prefix-macos-ci-failure-7e39435.json。
- 当前修正是在序章5,1接触楼梯后停止继续Up，等待一层完整HUD/出生图；本机VisualPrefix29StairContactWait成功29动作/264输入/97.194秒，508HP23A17D L1 G6XP29 Y2B1R0，2/3/3F标签已目视核对。公开visual-prefix-gdut-29-stair-wait.json。上一过渡黑色阈值原型TransitionWait虽本机成功但黑色阈值对远端证据无效，已经移除，不要当作修正成立。新提交CI需再检查。
- EarlyLevelASAPFullPotionsRed-0..4都已完成VM；最佳509HP118A42D L2 G228XP43 keys5/7/1。8低金币/7廉价属性/1廉价升级，正式复现工具tools/search_early_level_allocation.py、experiments/early-level-allocation.json：4147labels/518购买分支，五个完整字节码正例，总13.457秒/50.58MB；mhhf与gdut --check均实际通过。只有首红前缀，**不是完整10090路线**。
- generated/continue_early_level_to_gold11.py已结束失败：4874转移/1801标签/深8，.025秒/47.0MB，未到9层，不是全局无解。没有运行中的旧Guide搜索。
- generated/search_early_level_prefix13_{asap,reordered,early_right,feather}.py均已结束，固定分支失败。**纠正此前路径推断：F8(4,5)/(4,4)药水并不能仅在黄门4,9打开后从下方免费接触**；扩展DP的368/367提前只属未核验路径放宽，不可公开为合法路线或使用其失败排除真实世界。早羽毛链在高级法师440数值处失败，也非全局界。正式首红工具不含这些未核验提前。
- 仍无新全程候选或破纪录；原版最好AD10088/HP28568；2018整局原版回放、审计、固定时序对照都已结束，不要重复启动/覆盖。已无本任务运行中的回放或搜索（下一接续仍先查进程）。
- 新工具--check最初因Python内存tuple与JSON list直接比较而误报（VM五个正例本身已全部核验）；已改为规范JSON比较，并在mhhf/gdut各完整重算通过，分别13.626/12.978秒。下一修正提交会更新CI，不能把452f44b的该检查提前称为绿色。
- 正在运行generated/search_yellow_bypass_seed_single_swaps.py：对YellowBypassNearGate做固定模型种子128188416、23个单购买攻防交换及可达额外7F宝石分支，先查yellow-bypass-seed-single-swaps.log。仅数值候选生成，不向原版游戏指定种子；即使局部正例也需完整后缀和无种子真实回放，不能宣称纪录。

## 续接最新：独立截图回放首次跨机通过，新增真实省蓝门前缀

- fd155fc已推送，CI40439012828 **七项全部success**。29步Mac远端实际成功202.901秒/204输入/518HP；452f44b的独立Mac29步也成功317.079秒/195输入/513HP（该旧提交的--check序列化问题后来已修正）。两局其余终点相同23A17D L1 G6XP29 Y2B1R0；数值artifact实际下载到CIVisualFD155FC与CIVisual452F44B。公开两份success收据；远端无图像上传，楼层另行目视未做，收据保留pending。
- 当前工具增加--actions86，本机VisualPrefix86StairWait已经 **无人干预从菜单完整86步通过**：859输入/290.565秒，5F886HP26A28D L1 G38XP107 Y3B0R0；全部12次换层和最后5F标签实际看图核验。公开experiments/visual-prefix-gdut-86.json及源码，不上传截图。86步仅本机实跑，未称远端86通过或整局。
- 黄门旧分支YellowBypassNearGate **没有省蓝门**：与原参考比较只是省5F(5,8)黄门；此前脚本注释若说省蓝，不可据此做总账。单购买交换48项数值试验结束无首红正例。固定模型RNG全23攻防分配457386labels/471062trans/.576秒仍无目标。种子1..23枚举得到seed23数值首红12HP139A43D，实际VM已过，但不是原版设种子，也不是完整可用路线。继续模型种子1..256枚举要求首红后至少350HP全部失败，均不作随机分布或全球不可行论断；对应RngSweepReserve与日志已结束。
- 新分支**真省蓝门**禁止5F黄5,8及蓝7,8，改开原参考没开的黄9,8。固定原前83动作后找右侧初级卫兵，1HP购买束搜索失败；2HP购买束搜索保存NearGuard（1733HP115A41D，准入差120），其固定顺序精确攻防DP **VM正例成功**：234动作，143HP119A37D L1 G30XP26 Y8B2R0。11低金币属性+2次800HP+9廉价XP属性，所有动作/付款/路径实证；新门9,8已开，另两门仍原封。公开experiments/blue-door-bypass-prefix.json与check_blue_bypass_prefix.py，可重放每个234资源checkpoint，不是原版实际前缀。
- 真蓝门前缀继续首红的4096束失败1295278trans/8.03秒/628MB；保存并VM核验NearRed1023HP136A43D，准入差265，generated/TrueBlueBypassNearRed/proposal.json。已有F5DEF宝石已取，F7(7,2)ATK仍可免费拿。正在运行generated/allocate_true_blue_bypass_red.py，查allocate-true-blue-bypass-red.log（实际探测最早F7宝石、固定顺序全部攻防精确重分配）。不要重复启动。新省蓝门尚未接成完整路线；省蓝钥匙如何抵消早期HP购买及缺少4属性须完整钥匙/商店总账核验，不能提前叫破纪录。
- 旧所有fullgame回放、29/86视觉会话均已结束，无运行中的整局。当前只有新数值重分配（接续先查ps/log）。正式工具与数值收据待这次提交同步；推送后的CI另查。

## 2026-10-27 08:45 UTC 接续：184步原版截图前缀完成

- 新鲜本机局 `VisualPrefix184XPDirectMenu` 已结束；无相关运行中回放/搜索进程。184/184动作匹配，2234普通输入，736.319秒，终点HUD 3322HP/53ATK/60DEF，1级，27金币/29经验，黄蓝红钥匙4/5/0。最终截图单独目视确认第5层，截图不公开；发布图像SHA256指纹及数值收据 `experiments/visual-prefix-gdut-184.json`。
- 该视觉前缀没有24层通关或纪录证明；当前最好原版全程仍为28568HP/10088攻防和，公开TapTap候选仍28590HP/10088，未破纪录。版本与比赛规则是否一致仍未证实。
- `allocate_true_blue_bypass_red.py` 已结束：早取7F攻击宝石后固定路线分配DP在首红处仍无可行状态，最佳准入差264HP；这只排除该固定顺序/奖励时序，不证明其他省门路线不可行。
- 修正后的184步控制器及20分钟局部看门狗待同步；Mac CI目前只覆盖29步，不把184步称为跨机通过。证据与截图回放局限见 `docs/full-route-progress.zh-CN.md` O节。

## 2026-10-27 接续更新：360步截图前缀抵达十层

- 最新 `VisualPrefix360Extend` 无人干预截图回放成功：360/360输入计划动作匹配，4913次普通按键输入，1651.846秒。终点画面独立目视确认为第10层；终点959HP/185ATK/108DEF/1级、376金币/21经验、钥匙4/7/1。公开数值和终点截图指纹在 `experiments/visual-prefix-gdut-360.json`，图片保留本地不上传。
- 该验证只覆盖当前参考路线1–10层前缀，未抵达最终楼层；不证明完整路线/世界纪录。最终成绩基准仍28568HP/10088攻防和对公开声称28590HP/10088；版本及规则匹配、严格超越、公开排名认证仍未成立。
- `tools/visual_prefix_pilot.py`现支持动作长度29/86/184/360；本地看门狗上限升至40分钟。CI视觉工作继续只跑29步，不能称360步跨机复验。

- 426动作第一轮在动作372（五层经验商店）停止：合成数字上下文将截图中清晰可见的防御113误读成117；单独原图裁剪的OCR读为113。保留失败收据 `experiments/visual-prefix-gdut-426-initial-failure.json`，没有上传截图，不把该段算成通过。
- HUD阅读器新增首五项数值的独立原图裁剪OCR；两份本机截图回归样例分别正确读出113和360步成功局的185/108等状态。修正后正从菜单重跑426动作，目前尚在早期楼层，不能提前称其通过。

- 直接裁剪OCR第一次应用于长回放时，在动作18被拾取提示的金币栏读数2误挡（实际21）；失败收据 `experiments/visual-prefix-gdut-426-money-ocr-failure.json`。按屏幕栏位复测后，金币用4倍裁剪、其他数值栏用3倍裁剪可在该截图读对；第三次混合倍率运行正在进行，进度见 `generated/VisualPrefix426DirectCropMixed`，不要另开重复会话。

- 上述第3次426重放提前停于动作9：不同倍率的独立金币裁剪也会误读，把可见9读成6；5倍合成上下文读数则正确。`experiments/visual-prefix-gdut-426-money-scale-failure.json`保留该帧/结果；这显示直接裁剪金币不是稳健方法。
- 当前HUD读取方案采用5倍合成上下文，并以3倍直接裁剪复核生命/攻/防/经验；回测失败18帧、失败372帧及360步成功终点的HUD均符合像素读数。尚未进行通过完整426步的验证。

## 2026-10-27 最新：426步本机无干预截图回放完成

- `VisualPrefix426FiveX`：426/426源动作匹配、5726普通按键输入、2243.604秒；最终原版画面经目视确认第4层，749HP/185ATK/218DEF/1级、118金币/165经验、钥匙8/9/0。完成真实五层经验店和四层NPC对话。收据 `experiments/visual-prefix-gdut-426-dialogue.json` 仅记录数值、哈希、运行范围，截图不公开。
- 这不是全层路线：没有覆盖剩余后续到24层或通关结算，也没有破纪录；公开基准差异依旧。
- GitHub Actions 在远端截图小游戏失败，远端瞬时HUD直接裁剪将HP860误读为98；本机426仍可通过。必须先修正跨机读数并等CI验证，不能称其跨机通过。

- 跨机CI失败的原因是个别裁剪把屏幕HP860读成98；有时直接裁剪也会丢末尾数字。读数器现对主要数字保留合成上下文与两种直接裁剪，按多个视觉读数的多数决定，平票则值留空；在HP860、DEF113、Money21三张保存本机截图上逐字段核验通过。代码提交后须以新CI为准，旧CI标记保持failure。


- GitHub run `40492421126` passed its other six jobs but the screenshot job stopped at action9 on the remote instance because the new strict voting left money unknown when 5x contextual OCR read 9 and one direct crop read 6; no incorrect value was accepted. Reader now trusts the 5x-context money read and requires both direct scales to agree before they override other primary stat reads. Four pinned local screenshots were re-read successfully. Re-run CI after this change; old failure remains documented. The currently running local 600-action replay began before this last reader change and must retain its original receipt/hash.

## 2026-10-27 最新接续：600步截图回放在第432步安全停止

- `VisualPrefix600To9F` 已退出。该局从菜单实际发送5737次普通输入，运行2722.618秒；432/600动作匹配后，在动作432暂停。失败截图显示第5层商店，实际HUD为776HP/185ATK/224DEF、200经验、60金币、钥匙8/9/1，与购买红钥匙后的预期资源相符；角色被商店弹窗遮挡，未确认预期坐标，故动作432不记为匹配。原收据的 `finalVisibleHUD` 来自最后已匹配动作431，160金币/红钥匙0不是购买后的状态，不能据此推断交易恢复或回滚；已补充失败截图的独立核验说明。
- 可复核的无图像收据在 `experiments/visual-prefix-gdut-600-failure.json`；固定截图无上传。该前缀只到第五层，既非24层通关，也非破纪录证据。保留失败收据，不从当前状态续跑或重启相同600动作序列；需先修正角色定位/商店反馈同步，再考虑新的独立回放。
- 该600步回放使用旧HUD源哈希 `69f4e6af…cc512c1c`，其启动早于最新OCR修正；必须按收据所记代码版本描述，不能把后续改动归因到此失败。
- 检查失败截图后发现购买后的HUD/商店弹窗符合预期；被弹窗遮挡的角色坐标导致原控制器误判未完成。已修正为商店中间态要求“弹窗仍开且购买后资源精确匹配”，普通地图动作仍要求坐标可见；新增3项边界测试，`npm test`通过（4 Node、81 Python，36跳过）。`VisualPrefix600ShopConfirm` 实际在初始化阶段退出（未发送游戏输入），因默认播放器路径不存在，不能称其正在回放。随后找到已存在的 `../private/ruffle-web.zip`，SHA256与固定官方归档完全匹配，通过环境参数复用其解压目录，避免重新下载。
- 远端 `40495799017` 的失败收据确认：两种直接裁剪都把HP860误读98，而合成上下文原始字符串为 `123860`。这说明两倍率错误相关，多数票不保证正确。已限制直接裁剪覆盖仅用于曾实证存在上下文错误的DEF；HP/攻/金币/经验保留上下文读数。四张保存失败/成功截图回归核验通过。GitHub `40500490035` 的视觉检查仍失败，其他检查以实际结束状态为准。
- `VisualPrefix600ShopContext` 亦在初始化退出（没有游戏输入），因为Playwright默认的1234浏览器不存在。本机已有1248浏览器，已用 `MOTA_CHROMIUM_EXECUTABLE` 显式选择。新的 `generated/VisualPrefix600Recovered` 已确认真实运行并匹配到动作43；日志 `generated/visual-prefix600-recovered.log`。播放器复用 `MOTA_RUFFLE_WEB=../private/ruffle-web` 的已核实资源，冗余的网络下载已经终止。接续先查进程与收据，不要重复启动或覆盖。该局绑定上述HUD及商店确认修正的源哈希，尚未完成整段验证。
- 当前最佳仍为2018存档28568HP/AD10088，比公开声称28590HP低22；没有破纪录路线或版本/规则同一性证明。

## 2026-10-27 独立CI恢复与步行性能优化

- `addc195` 的 GitHub Actions `40502596514` **七项全部success**。远端29/29动作、187普通输入、417.690秒，终点503HP/23攻/17防、1级、6金币/29经验、钥匙2/1/0。数值artifact已下载到 `generated/CIVisualADDC195`，公开 `experiments/visual-prefix-macos-ci-success-addc195.json`。没有截图上传，远端终点楼层标签仍未另行目视确认。
- 新的像素模式仅用于普通行走格的位置/弹窗检查，跳过不需要的数字OCR；每个源动作的成功判定和任何重新发出方向键之前仍需完整HUD。四张保存截图的角色/弹窗结果与完整模式逐项一致，暖态读取中位数0.02392秒，相对完整模式0.21412秒；这是读取器微基准，不能称整局加速9倍。新模式与4项控制器测试通过；完整 `npm test` 为4 Node +82 Python（36跳过）。新代码的跨机CI须另查。
- **当前600局仍是 `VisualPrefix600Recovered`，使用此前90a8fc0f… HUD和6ce663b8…控制器的完整OCR版本，不受后续源文件编辑影响。** 像素模式没有应用到这份已运行的证据中，不能混用性能或成功结论。接续检查该目录进度/最终收据，别重启。
- 新的数值分支 `generated/search_true_blue_paid_level.py` 检查真省蓝门固定顺序，增加实际可达的5F兽面人和7F攻击宝石，允许至多12金币属性/2次800血/11经验属性/1次付费升级。审计版 `generated/TrueBluePaidLevelAudited` 完成264事件、266519累计标签/952903购买转移、8.098秒/56.4MB；这一个顺序下没有付费升级的首红蝙蝠正例，最佳差399HP。保留并原版VM重放了未升级正对照：1131HP/125攻/57防、68金币/16经验、钥匙4/8/0，仍未打红蝙蝠。只是该固定顺序的失败，不是全局无解；无新全程候选。

## 2026-10-27 最新：退出选项回归已修正，实际运行918步局

- `VisualPrefix600Recovered` 已结束，392/600匹配、5334输入、2439.502秒。失败截图实际显示第11层、937HP/185攻/118防/1级、471金币/44经验、钥匙7/7/1，角色(5,9)，弹窗已关闭：源动作392的商店选项4本已正常退出。上一轮“弹窗必须仍开”的修正错误地应用到了退出选项，造成检查器误停。公开 `experiments/visual-prefix-gdut-600-shop-exit-failure.json`，不把未接受动作记作通过。
- 新控制器对选项1–3要求购买后的开窗资源确认，然后退出；对选项4直接等待关窗/资源/位置确认。状态化商店测试覆盖3种商店×4种选项，避免多买或退出后继续发输入；相关5项测试通过。918动作已离线编译，最后为14F(8,9)，包含392/788/828三次退出，尚不含首次罗盘动作918。
- **当前实际运行的是 `generated/VisualPrefix918FastWalk`，日志 `generated/visual-prefix918-fast-walk.log`。** 从菜单新鲜启动，像素步行/完整动作HUD版本，已实际匹配超过100个动作。以前600局均已结束，不要重启或覆盖。检查进程和该目录最终收据后再启动下一局。
- `8111d07` 的CI `40505686606` 七项全success，远端29动作像素步行实际通过：181输入/363.524秒、518HP；公开 `experiments/visual-prefix-macos-ci-success-8111d07.json`。这份跨机正例不含392退出选项，最新退出修正仍待更长实际回放和新CI。
- 双战斗共同延后搜索 `generated/MixedBattlePairSweep` 已完整结束：由543个单延后候选派生的305组同插入点配对，目标1300保留补血，全部没有数值正例；897973920累计标签/1040046064转移、578.030秒/87.65MB。公开工具 `tools/sweep_mixed_potion_battle_pairs.py` 与 `experiments/mixed-potion-battle-pair-sweep.json`。仅排除这些固定顺序和购买策略的放宽模型，不是全塔无解或最优性结论。原目录不可覆盖。
- `generated/MiddlePotionDeferrals` 的7组中期补血/邻接道具延后尝试亦已结束，均在原版VM的真实路径检查失败。13F源809药水挡住左上路径；816药水挡住通往14F的楼梯；12F源1010药水挡住1011项链，连项链一起延后则在18F路径条件失败。只是固定其余门/事件顺序的结果，未证明所有替代路线不可行。无新完整超分候选。

## 2026-10-27 新取得真实公开榜首，而非近期游玩列表

- 已HTTPS取得 `https://h5mota.com/tower/?name=24` 的SSR JSON，当前H5版24层结局有13类公开榜首；全部行验证码为-1。已下载并核对该站固定前端 `VerdictIcon-ntIqIgAy.js`，-1明确表示“录像验证成功”，0/8才是未验证。公开 `experiments/h5mota24-leaderboards-20261027.json` 与 `tools/extract_h5mota24_records.py`；没有独立重放他人录像，没有破纪录。
- 真实目标包括：攻防10088、生命251602、攻击7293、等级200、金币6660、经验7140、金币商店购买870、经验老人购买554、留怪62，以及最低金币购买161、经验购买49、防御365、攻防6227。最低类别已用真实结局事件的整数编码整除还原，不能将大整数原始分数当属性值。详见 `docs/h5-24-record-targets.zh-CN.md`。
- 当前计榜是2026新版H5的无暴击极速模式；经典模式不计榜。2023年的H5 10090视频包含暴击/存读档，不能直接与这版比较；两份Flash SWF与之也未建立构建一致性。Mota Mod近期124次经验购买并非全局纪录，不能用作“破世界纪录”靶值。
- 两站实际工程的物品和结局文件逐字节相同，但配置、敌人字段、帮助事件存在差异；运行时、插件及另外26张地图未比对，不能声称整塔同版本。原始来源仅存 `generated/MotaModFresh20261027`，数值指纹在 `experiments/h5mota-motamod-build-probe.json`。官方普通界面不提供他人录像下载，完整成绩构建SHA仍未知；不尝试绕过权限。
- 当前仍实际运行 `VisualPrefix918FastWalk`；已越过392退出与432商店遮挡旧故障点，后续检查进程/收据，不开重复局。原版完整最好仍28568/10088；新榜单发现没有改变该完成度。

## 2026-10-27 当前执行入口：1170动作罗盘局

- `VisualPrefix918FastWalk` **已结束失败，不再运行**：714/918动作匹配、10051普通输入、2993.039秒；源动作714拾取红钥匙后，画面实际为11F/4009HP/450攻/505防/2级、65金币/1064经验、钥匙13/3/2、角色(6,2)，但上下文OCR把2读成Z（原始文本123Z），红钥匙值留空，安全停止。最后自动匹配的713号动作仍为红钥匙1。公开 `experiments/visual-prefix-gdut-918-key-ocr-failure.json`，不得称918完成。
- 不用计划值补读数：仅在钥匙值缺失时，尝试原图多倍率裁剪；若上下文出现Z/2歧义，至少还要有直接裁剪得到字面数字2，且所有直接数字一致。失败帧实际得到上下文123Z与3倍裁剪2，已正确恢复2；6张保存原图回归通过。公开 `experiments/hud-key-corroboration-regression.json`，不上传字形模板/截图。仍非通用OCR正确性证明。
- `VisualPrefix29Walk50` 已结束成功：29/29、239输入、97.101秒，实际目视3F/515HP/23攻/17防。普通步行键后等待由150改50ms（键间隔仍35ms，交互仍150ms），全程保留位置检查、每源动作完整HUD和重发前完整HUD检查。公开 `experiments/visual-prefix-gdut-29-walk50.json`。旧918局没有使用50ms改动；600动作图显示游戏计时18:06，714失败图21:03，尚未通过16F限时条件，不能外推长局一定来得及。
- 已加入原版J/Space/数字2选择的罗盘输入，目标只允许1..20，先确认弹窗，再按源计划选择，落地须重新核对HUD/角色。只通过状态化菜单单测，尚无无观测器罗盘实际正例。1170动作已由原版VM离线编译通过，含12次罗盘，首个源918飞13F，末尾20F；**不是1170步实跑完成**。
- 当前新鲜局 **`generated/VisualPrefix1170Compass50`** 已启动；日志 **`generated/visual-prefix1170-compass50.log`**。参数：`--swf generated/private/gdut-v112.swf --actions 1170`；环境复用 `MOTA_RUFFLE_WEB=../private/ruffle-web`、已有1248 headless-shell浏览器。先查ps/该目录进度或最终收据，禁止开重复局或覆盖。以前600/918/29局及数值搜索均已结束。
- 新控制器追加host源码哈希及两种键后等待时间到收据。相关7项控制器测试、6张HUD回归、节点语法检查、完整4 Node+85 Python测试（36跳过）通过；新提交CI须另查。
- 补看旧 `GdutNativeHP28568/fullroute-native.png` 为结束切换黑帧，旧完整成绩的依据是原版观察器结束谓词/root4349/Boss格0及逐战审计；这张黑图本身不能作为独立目视结局证据。未来截图整局必须另等并检查实际结局画面。
- H5广场当前工程37份源码/页面已实际GET取得，全部成功；只在 `generated/H5Mota24Project20261027` 保留，逐文件URL/SHA见该目录provenance。尚未执行这些工程函数或将Flash路线称作H5可行路线；全套地图/插件可用于后续静态对照。公开资源身份与纪录快照已同步，未上传该游戏源码或素材。

## H5真实数据静态导入已完成（仍未执行H5路线）

- `tools/import_h5_24_json.py` 对37个已取文件逐一校验SHA/字节数，严格解析33个JSON赋值；拒绝重复键、非JSON数值及赋值外的可执行代码，代码文本只保留为数据。4项有意义的解析边界测试和真实导入均通过。
- 输出 `generated/H5Mota24ImportedChecked20261027/structured-private.json`：27张13×13内部地图（24层游戏含序章和23层三分支）、4563格、66敌人定义、62道具定义、6商店，方块编号均可解析，101个不透明函数/效果字符串。不能把这些不透明效果填成空操作或称完整H5模拟器。公开 `experiments/h5mota24-static-import.json` 不含原始地图/工程代码。
- `tools/compare_h5_flash_grid.py` 已实际对照2018 SWF与H5初始内部图1..26，坐标偏移明确x+1/y+1：可比2895格、分类相符2887、8处初始差异；另206特殊格和45铁门格未分类。33基础敌人五项数值匹配（4个名称别名经完整五数值核验），不含特殊攻击/变异机制等价证明。公开 `experiments/h5-flash-static-grid-comparison.json`。
- 明确差异包含3层红蓝宝石互换、23层角落攻击宝石移位及18/20层初始楼梯；不能盲用Flash路线作为H5见证。公开下载/导入/校验工具均不执行H5函数，不取媒体，真实源码仍只在忽略目录。
- 37文件重新GET指纹复验 **已完成且全部相符**：`generated/H5Mota24FetchReproduction`。对新副本再次严格导入、再次初始图分类，两个完整summary与发布版本逐字段完全一致；公开 `experiments/h5-source-reproduction.json`。原始37文件、完整结构化工程仍不上传。完整4 Node+89 Python测试通过（36跳过），其中4项新静态解析边界测试均通过。
- 当前唯一长程游戏回放仍是 `VisualPrefix1170Compass50`，不要被旧918行的历史状态误导。原版完整实际最好28568/10088不变；静态H5导入、榜单核验和菜单单测均不能算作破纪录路线。

## 2026-10-27 接续：首次实际罗盘通过，16F长战斗超时已定位

- `VisualPrefix1170Compass50` **已结束**：930/1170源动作匹配（索引0..929）、12273次输入、2747.949秒。源918实际罗盘落地13F已目视核验：1308HP/1006攻/1020防、2级、652金币/499经验、钥匙6/1/3、(1,10)，游戏计时22:21。源714红钥匙OCR补读在这次实跑中真正通过。
- 第930号源动作在16F的战斗仍进行时触及25秒检查期限；独立查看失败帧，怪物剩3261HP/1000攻/1000防，勇士1308HP/1091攻/1020防，大部分地图HUD被遮挡。不能把这场战斗、16F限时条件或剩余路线记为通过。公开 `experiments/visual-prefix-gdut-1170-battle-timeout.json` 保存失败和首罗盘抽样核验，截图仍私有。
- 控制器现在依据离线原版VM的逐战随机调用数量设置保守轮询期限 `min(600,max(25,10+2*drawCount))`；这只改变等候预算，实际接受仍须截图HUD/位置完整匹配。该战165次调用，预算340秒。8项控制器测试通过，完整4 Node+90 Python测试通过（36跳过）。新鲜局 **`generated/VisualPrefix1170LongBattle`** 已实际启动，日志 **`generated/visual-prefix1170-long-battle.log`**，exec会话89976。不要重启旧1170局或覆盖结果；先查当前进程与收据。
- `ce7b20d` 的远端CI `40522223401` 已completed/success；新改动须另查。

## H5实际压缩发布数据已静态比对

- 网站main.js实际启用压缩、cache版本5767；不能仅因未压缩源文件可取就假定浏览器使用它。实际GET得到 `project.min.js?v=5767`、`floors.min.js?v=5767`、`libs.min.js?v=5767`，URL/字节/SHA留在忽略目录 `generated/H5Mota24ActiveBundles/provenance.json`。三个文件均未被离线执行。
- 新工具 `tools/compare_h5_active_bundles.mjs` 使用Acorn静态解析：只读顶层数据声明/地图字面量赋值；编译器辅助函数跳过不执行，函数体保持不透明。六项工程输入(data/enemys/icons/maps/items/events)与27张地图共9343个叶值逐项完全相同。公开 `experiments/h5-active-bundle-literal-comparison.json`。functions/plugins与libs行为未比较；这不是历史纪录提交构建指纹或H5全行为等价证明。
- 官方页面正常加载探针曾停在92.11%，未进入游戏，尚无H5通关实跑。正在 `generated/H5NetworkDiagnosis` 做一次普通页面网络诊断，记录未结束请求/HTTP错误；不绕过加载器或改写游戏变量。
- 最好完整原版成绩仍28568HP/AD10088，没有破纪录。
- 接续补充：新局 `VisualPrefix1170LongBattle` PID36055，已真实匹配源122（不是完成1170）。H5第一次50秒诊断已退出：503出现在`/reload`，资源请求后续才发出，不能据此把503认定为游戏加载失败的唯一原因。新的普通页面最长300秒诊断 `generated/H5NetworkLongWait`/`generated/h5-network-long-wait.log`，PID37243、exec29406，120秒时仍有多项素材请求未结束；其结束后读取receipt，不重复启动。浏览器只正常加载页面，无游戏输入/变量改写。
- 额外离线编译完整1713源动作已成功，草案保留 `generated/full-visual-plan-draft.json`；最终为26内部图Boss188动作，28568HP/5056攻/5032防。仅说明规划器支持输入，不是全程截图回放成功；结局切换画面仍需专门验证，当前实跑仍只请求1170。
- 状态文档已纠正旧28554/差36和旧H5暴击规则的过期主描述。`581a888`新CI `40525362519`仍in_progress，勿称已通过；此前`ce7b20d` CI成功。最新文档提交8afcb8c已同步。

## 2026-10-28 当前：1170步视觉验证完成，完整1713步新局进行中

- `VisualPrefix1170LongBattle` **1170/1170通过**：15558普通输入、3676.005秒。终点原图目视20F、2103HP/2040攻/1693防/5级、2232金币/1973经验、钥匙5/8/4，(2,0)。源930的16F长战斗已实际完成，全部12次罗盘通过资源/角色检查。公开 `experiments/visual-prefix-gdut-1170-success.json`。只到20F，不是24F结局，也非破纪录。
- 新控制器支持1713动作。最后1712号Boss攻击仅采集0/2/5/10/20/40/80/120/180秒画面，不发Space、不把黑帧或数值仍相符自动判胜；因此即使走到此处，收据仍等待独立结局核验。host有界会话由90增至180分钟。9项控制器测试通过。
- 第一份完整新局 `VisualFull1713EndingSamples` **已失败并退出**，178/1713匹配、2075输入、539.000秒；178号实际5F/3323HP/43攻/45防/1级、27金币/179经验/钥匙4/5/0，而上下文OCR1234丢了末尾3，两种原始裁剪均读43。公开 `experiments/visual-full-gdut-1713-atk-ocr-failure.json`；最后匹配177仍为DEF42，不把178记为通过。
- 新OCR仅在ATK上下文值是完整直接数值的严格前缀、且两种直接裁剪一致时修复截断；不放开HP直接覆盖、不读取期望计划。7张历史失败/成功原图逐一回归通过，含新的43例。公开 `experiments/hud-atk-truncation-regression.json`。
- **当前唯一原版长局 `generated/VisualFull1713ATK43`**，日志 **`generated/visual-full1713-atk43.log`**，exec87523。实际已超过源187、越过旧178故障点，先查进程/收据，不重启之前已退出的1713/1170局。环境仍复用固定Ruffle和1248浏览器；没有观测器、游戏变量读写、种子或时钟控制。完整测试4 Node、94 Python（36跳过）通过。最近已推送3c1f61a/8afcb8c/581a888的三份CI均已success；本轮新代码CI须另查。

## H5普通界面实跑至5F，已用正常存档界面保存

- 原先HTTP/2连接出现资源协议错误/长等待；正常浏览器切换HTTP/1传输且复用缓存后，成功打开原站。没有绕过加载器、改写游戏变量或执行抽出的H5函数。新工具 `tools/h5_ui_host.mjs` 只发送普通键/开始按钮，读被动状态与截图；它使用独立私有profile `generated/private/h5-browser-profile`。
- 从普通开始菜单选择观看片头、极速模式，实际读取开启暴击=false；仙子对话后自然进入MT1。前三层29源动作结束493HP/23攻/17防，公开 `experiments/h5-normal-ui-prefix29.json`。23号先得到ATK23/DEF10（H5红宝石在前），24号两版总属性回到23/13。初版检查器正负号写反已保留误停，原游戏同一局修正检查后继续，没有改状态/重载。
- 同一H5游戏继续完成 **184源动作**，终点目视5F/3318HP/53攻/60防/1级、27金币/29经验、钥匙4/5/0。源139书本弹出说明，旧检查器只看不变资源而过早接受；源140因此误停。已改为consume的已知文本弹窗必须用普通Enter关完、无未关闭事件才通过；同一局接着验证140..183。公开 `experiments/h5-normal-ui-prefix184.json`，不是无人干预从菜单一次性执行，也不是H5全程/纪录。
- `tools/h5_prefix_pilot.py` 和 `tools/h5_route_adapter.py` 保存可复用的窄范围适配；只走实际空格、逐次检查资源/位置、处理信息文本、按实际商店光标选择。3项边界测试包括不穿过未计划门、接触前停止、宝石差异方向与不修改原数据。
- 正常按S、Enter保存 **槽1**，再开存档页目视槽1为3318/53/60，图片私有 `H5NormalUI20261028/frame-00208.png`。这次只保存没有读取；旧自动存档仍43攻/42防，不要误选。截图和IndexedDB只在私有profile。H5host已正常关闭释放资源；没有H5长局仍在跑。下一接续可用同一profile正常开站，先从读取菜单用D/Enter取槽1，再核查5F资源及历史route；如需要全程无读取证据则重新从菜单跑，不能把分段接续冒充无存档通关。
- 浏览器读数声明 `gameVariableReads=true`，与原版截图控制严格分开。缓存号5767不是完整运行文件指纹；原始工程/压缩包静态一致不等于历史榜单提交构建一致。所有原始地图/图像/游戏源码仍不上传。

## 另一真实优化目标：保留经验的数值分支

- `tools/search_xp_suffix.py` 实际重放固定2018原版字节码，省去源1616..1666最后51次大经验属性购买，其余消费/行走/战斗不变。**1662动作完整数值重放通过**：28568HP/4189攻/5032防/17级、1238金币/**5925经验**，26内部图最后Boss位置已执行。12.248秒/66.95MB。公开 `experiments/xp-suffix-no-last-purchases.json`，工具重新从文件重放得到相同全部非性能字段。
- 这是新目标的数值基线，尚无该分支原版或H5实跑；不能把5925与当前H5榜首7140作同版本超分比较，更不能称破纪录。原版已实际完整最好仍28568HP/AD10088；目标未完成。

## 2026-10-28 关键纠正：旧1292局实际进入21F普通结局

- 原版 `VisualFull1713ATK43` 已退出：1292个HUD/位置谓词匹配、16436输入、3971.588秒。失败后图片不是单纯OCR缺数：frame-15680显示击败21F魔王及312金币/275经验；frame-15700明确显示勇士公主共同生活的普通结局文字；frame-15782是胖老鼠工作室片尾。没有24F结局。公开 `experiments/visual-full-gdut-1713-normal21-ending.json`。
- 发现重要检查器漏洞：资源不变的dialogue929只凭数值/位置不变就被接受，无须证明曾打开对话。该局929的16F图上(4,4)商人位置已是墙，因此不能宣称取得神秘宝物。固定2018源码的1500秒条件会移除此NPC；该帧没有显示计时，不能仅靠它定量归因。未来必须证明对话实际打开、并观察“得到神秘宝物”弹窗，不能只继续改OCR。
- 旧1170的20F画面及数值仍真实，但1170计数仅代表旧检查谓词，并不证明每个隐藏事件。已给 `experiments/visual-prefix-gdut-1170-success.json` 补充明确语义限制。全24F的旧观测器回放证据与此次无观测器普通结局严格分开。

## H5实跑360动作与录像导出

- 正常从槽1读取5F后，公共工具实跑184..359，**360动作前缀完成**，该续接段696.976秒；终点目视10F、856HP/185攻/108防/1级、376金币/21经验、钥匙4/7/1。已普通保存到**槽2**并在新浏览器正常读取核验，槽1保留5F。公开 `experiments/h5-normal-ui-prefix360.json`。
- 在R菜单“下载当前录像”正常导出自有文件 `generated/H5ReplayExport360/24_20261028041522.h5route`，SHA256 `523c54a9f70cffd9b321b860f5b7cd54cdf587adce9b6e0c581d42b3f1cd6bfb`，对应4164条引擎动作。只含自有录像，不含游戏地图或图像。
- 导出会话实际浏览器响应的main.js及project/floors/libs三个压缩包SHA已记录，后3个与此前静态取得的包完全一致。仍没有历史榜单各提交的全构建指纹。
- 第一次独立空profile导入录像后，官方startReplay默认pausing=true；当时只消费开场两个选择，未按Space开始移动。被动监测25分钟超时，后120分钟host正常关闭。**这不是成功重放，也不能据此说录像无效**。旧所有H5host/监测均已退出，不要复用过期endpoint。下一步应新开普通回放，等开场结束、按Space开始；可以正常数字6选择官方24倍回放速度。勿直接写replay.pausing或速度变量。

## 少金币购买的真实数值分支

- `tools/search_gold_shop_stat_candidate.py` 从固定源更改7次早期金币攻击为防御、省去54次末段金币防御、把最后51次经验攻击改防御，字节码重放到源1711通过：**164次金币购买，28568HP/4002攻/5005防/6638金币/1080经验**。最后Boss仅用同SHA旧原版实测敌人数值和独立公式检查，需50000击、零伤害；没有执行最后一战完整字节码/影片，不能称完整路线。公开 `experiments/gold-shop164-stat-prefix.json`，公有工具再运行得到相同非性能结果。
- `tools/search_gold_shop_level_trials.py` 的3种160次购买目标方案均被固定顺序的中途战斗阻挡；公开 `experiments/gold-shop160-level-trials.json`。仅3策略失败，非全局下界。详细范围/复验命令在 `docs/low-gold-shop-branch.zh-CN.md`。
- 164/6638本身未超过H5的161/6660，且构建/规则比较仍未成立。无破纪录结果。

## H5自有360前缀录像真正独立回放成功

- 新空profile generated/private/h5-replay-check2-profile、新host generated/H5IndependentReplay360Started，仅通过开始菜单录像回放、正常文件选择器导入自有文件。开场后按Space开始、数字6选择官方24倍速度，没有直接修改replay或英雄变量。
- 实际完成100%/4164条输入，终点MT10、856HP/185攻/108防/1级、376金币/21经验、钥匙4/7/1，与原局一致。引擎remaining=0、failed=false，frame-00000目视显示“录像播放完毕”、4164/4164、100%。这是被动状态读取加目视检查，不是纯截图控制；录像正常使用文件中原局自然种子。
- 已公开1864字节自有文件 experiments/h5-prefix360-own.h5route、收据 experiments/h5-prefix360-independent-replay.json 与复验步骤 docs/h5-prefix-replay.zh-CN.md。导出/验证会话实际JS四项响应SHA全部相同，历史榜单各提交构建身份仍未知。只验证十层前缀，没有成绩提交/破纪录。
- 私有监测elapsed0.015是开始监测时已完成后的观察耗时，绝不是回放耗时。公共收据只列Space至最终截图36.946秒上界（含代理等候），不作速度基准/RTA。相关H5导出、独立验证host均已关闭。

## 当前原版长局：宝物严格检查与空步批次

- 唯一原版长局 generated/VisualFull1713QuestGuardBatched，日志 generated/visual-full1713-quest-guard-batched.log，PID17755/exec92934，已实际超过源325。不要重启或覆盖，原1292局已退出且是普通21层结局。
- 已启动版本对所有dialogue先要求实际弹窗，16F宝物还要求OCR看到“得到神秘宝物”；没有计划数字输入到读数器。真实缺失NPC帧orangeMaxRun26且无授予文本不能满足该条件；7个旧数字回归通过，公开 experiments/hud-scene-reader-regression.json。
- 空步至多8个同方向一批，批末核对角色；只有完整实际HUD不变且角色明确落在早期格才重发剩余步，不把事件接触键并入。多键gap75ms、单键gap35ms、批后50ms，未改游戏时钟/帧率。首29动作从首次输入至终点图79.194秒，旧单格样本85.238秒，不能外推全程或保证25分钟门槛。
- 后续公有源码把宝物绑定16F(4,4)的26号NPC而非固定动作号，增加校验SHA的自有proposal入口；这些文件编辑不会改变已运行进程。14个控制器边界测试和完整4 Node+99 Python（36跳过）通过。继续以运行收据记录的源码SHA为准。

## 提前宝物访问的具体数值备选

- tools/search_early_treasure_detour.py 检查一个固定消费顺序中的前缀，源912后首次可完成宝物绕行。插入走楼层/红门/小偷/宝物访问，略去旧927..929后，1717动作完整数值续程通过，仍28568HP/5056攻/5032防。原试验和公共工具共同非计时字段全部一致，公开 experiments/early-hidden-treasure-detour.json。
- 没有模拟1500秒期限，也未实际看到宝物弹窗；不能把模型标志当真实时钟通关。方案已实际通过新版compile_plan离线编译，宝物定位917、最终Boss1716。这是批次速度仍不足时可尝试的具体备选，不是破纪录改进。

## 当前H5实际续程至600局

- 当前H5唯一续程 generated/H5Prefix600Resumed，日志 generated/h5-prefix600-resumed.log，exec80353；host generated/H5Resume10FTo600/exec66321，原私有profile，从普通槽2读取十层/360前缀，已实际超过源508。不要开同profile第二浏览器。
- 步行只保留100ms逐键间隔，不再额外固定等130ms；位置未稳时只空等，不盲重发。当前版本源425在条件text循环实际发14次Enter并继续，后加的明确text开窗截图要求不会改变已启动版本。
- 若600完成，先目视终点、保存槽3（保留槽1五层/184、槽2十层/360），再整理收据、导出/独立回放。不得把此续程称无存读档游戏；无需重复验证已经成功的360录像。

## 2026-10-28 最新续接点（覆盖上述“当前”状态）

- 旧宝物严格检查局 `VisualFull1713QuestGuardBatched` 已停止在664：6F(9,2)接触(10,2)敌人未触发，旧金币45/经验804不变；尚未到宝物。原始截图与收据一致，公开 `experiments/visual-full-gdut-664-untriggered-contact.json`。实际部署控制器014fa159与Swift e1591f21已以提交c96e44b保留，便于准确复验。
- 新原版唯一长局 `generated/VisualFull1717EarlyQuestGap25`，日志 `generated/visual-full1717-early-quest-gap25.log`，PID32320/exec93884，正在运行。采用已数值复算的提前宝物绕行proposal SHA10a13c4327fb65f3bfc4283c6a4e4303e3f93896cc39b0a07d5544afc289568f，宝物917/最终Boss1716；gap25ms，模态期间像素轮询，未改游戏时钟或帧率。战斗重试仅允许完整HUD不变、角色原位、无弹窗且有非HP奖励进展信号，最多3次，避免双重购买。授予检查要求完整“得到神秘宝物”行，不把“你可以得到…”当授予。15个控制器测试通过。
- H5 `H5Prefix600Resumed` 已实际完成600，9F/614HP/355攻/404防/104金币/524经验、钥匙16/8/1，续段606.219秒。正常槽3保存，目视frame-00268并导出自有录像a681b902…；公开 `experiments/h5-normal-ui-prefix600.json` 和 `experiments/h5-prefix600-own.h5route`。此600录像尚待独立回放；360录像已独立成功。600不等于楼层9以下全清，更非通关。
- 同一H5普通存读档局已启动 `generated/H5Prefix918Resumed`，exec73963，日志 `generated/h5-prefix918-resumed.log`，host仍 `generated/H5Resume10FTo600`/exec66321。从600继续至918（源918首个飞行道具之前），不要重复启动。另开独立空profile `generated/private/h5-replay600-profile`/host `generated/H5IndependentReplay600`/exec13669，专用于600自有录像复验，不共享正在游玩profile。
- 两组HP数值网格公有工具复跑均已结束；65+127个固定配方（后127排除前65），全部非性能字段与原实验一致。最好150540HP/5056攻/3612防/L17，仅数值完整1713动作，不含原版1500秒宝物期限；不存在该分支实际24F结局/已认证成绩。不能与AD10088约束下HP纪录混为一谈。公开 coarse/refined 收据并附复跑命令与私有收据SHA。
- 完整测试100项Python（36因缺私有资源跳过）通过，Node4项通过。没有已验证破纪录路线，继续以24F真实完整回放和同规则比较为完成条件。
