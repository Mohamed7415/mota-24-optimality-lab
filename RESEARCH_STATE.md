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
