# 全塔破纪录路线推进日志（未完成）

目标仍是找到可验证的完整24层破纪录路线。当前已完成9863攻防和的完整原生回放（见D），但没有同规则纪录超分或平台认证。各分支证据不能拼接成一次通关。

## A：原版实际回放已到十六层

固定既有Ver1.12候选SWF在官方Ruffle0.7.1中，从菜单、仙子开场开始，以普通浏览器鼠标/键盘输入执行了1586个关键动作。使用真实时钟和自然随机数，没有冻结日期、指定种子、存读档、重开或游戏变量写入。

- 普通输入28507次，最高到十六层，完成神秘宝物、隐藏结局标志及十字架剧情，随后返回序章。
- 最终3056HP、869攻、561防、17级，黄/蓝/红钥匙14/0/0，金币180、经验204。
- 原版游戏计时0→1210秒；与十六层老人交互完成时为1188秒，早于1800秒剧情门限。
- 160场战斗、964次真实抽样，逐战用独立帧级数值模型复算，全部匹配；敌人、战前资源、预伤、战后HP也与对应实际动作逐项绑定核对。
- 原版受限字节码解释器重建同一语义序列，最不利抽样199下最终588HP；每个检查点实际HP均不低于该重建值，全部非HP资源完全一致。
- 实际观察到`mt_LastGame_ID=1`、`mt_GetMoney=[1,0,0]`。这只是隐藏结局的前置条件，不能当作已完成隐藏结局。
- 只读观测器的根作用域检查始终成立。此长续程尚无无观测器对照；旧M6/M7/M8对照不能自动推广。

[十六层数值证据](../experiments/full-route-prefix16.json)包含普通输入、语义动作、资源检查点和战斗抽样，不含地图行、截图、对白或原版动作体。[此前十一层证据](../experiments/full-route-prefix11.json)保留：665动作、11777输入、107战斗、653抽样，实际最终495HP。

## B：另一数值分支已打败十九层Boss

此分支在公共的前665动作之后改良了购买安排，与A不同。它已取得十二层开路道具、完成小偷第二次开路、救出十八层公主、取得十九层两件装备并击败十九层Boss。后半段尚未在真实播放器中执行。

[候选动作](../experiments/full-route-numeric19-proposal.json)及[重新执行校验报告](../experiments/full-route-numeric19-audit.json)：

- 1880个语义动作，208场数值战斗，1459个最不利抽样；最后41152HP、1962攻、1617防、52级，钥匙5/0/0、金币563、经验490。
- 全部动作在固定原版的已审阅移动、跨层、战斗、商店和剧情字节码中重新执行，逐动作资源一致；十九层Boss后敌人变更标志已触发。
- 本机重新核验约23.41秒，进程峰值内存95191040字节，解释54645720条指令。此耗时和内存是校验器指标，不是搜索耗时或原版通关用时。
- 各分段搜索累计生成11056247条转移、存储9440602个标签；束宽256/512/2048。它们来自不同快照，不能当作全塔去重状态数。
- 例如十八层公主分段：生成1238301条转移、存储1026061标签、约7.67秒；当时整个进程历史峰值内存457490432字节，并非该分段独占内存。

所有束搜索均有裁剪，未穷尽；没有全塔最优值、全塔最优区间或破纪录保证。界面动画、对白翻页、提示关闭和时钟在数值解释器中有明确边界适配，因此数值分支不能替代真实播放器验证。抽样199是最不利输出策略，不声称对应一条可实现的固定PRNG轨迹。

### B的后续：二十三层数值前缀被排除出攻防和候选

2026-10-24，B接通二十一层剧情并进入三张显示为二十三层的地图。公开的固定[前缀](../experiments/rejected-prefix23-proposal.json)包含4130个语义动作、272场战斗、3072次最不利抽样，最后5872HP、3750攻、3407防、60级，钥匙0/2/2、金币168、经验485。[独立重执行报告](../experiments/rejected-prefix23-audit.json)逐动作资源一致：约55.53秒、169312256字节进程峰值、134350424条解释指令。这是校验开销，未在真实播放器重跑该分支，也未到最终结局。

针对这个已领取仙子加成的固定前缀，给予所有剩余地图奖励、免除开门和一次性装备NPC费用、出售所有钥匙后，固定攻防为7282，可支配金币4266、经验3817。最有利普通商店汇率给出：

`floor(7282 + 4266/5 + 3817*17/95) = 8818`

[条件上界收据](../experiments/rejected-prefix23-ad-bound.json)绑定原版及前缀SHA256。它只界定所声明的数值模型、固定前缀和一次性奖励假设；没有证明所有原生回调和读档策略的全局上界，也没有证明该前缀不能通关或不能改善HP。它足以排除该模型下从此处冲击10088攻防和的方向。216个原版商店边界案例另外核验了相应资源势能不增。

当前正在重新安排前期战斗和购买，延后仙子加成。参考[公开10088/28590文字路线](https://www.taptap.cn/moment/544556257772569275)的资源检查点，但所有接受动作仍须在固定原版字节码中执行；没有把攻略数值当作模型真值。

## C：首条抵达最终结局跳转的完整数值路线

2026-10-24，从自然开局出发，完成神秘宝物、冰杖、晚交十字架、三杖及最终仙子剧情，击败地下最终血影。最终4863攻、5000防、6573HP，17级，金币1260、经验1077，无剩余钥匙。**攻防和9863，比公开10088低225；未破纪录；其后完整真实回放已通过，见D。**

- [原始候选](../experiments/full-route-ending-9863-proposal.json)：2462语义动作、295战斗、9990次最不利抽样。其中十九层一场无伤战斗因攻击仅高于敌防4点，需5000次普通攻击。
- [重排候选](../experiments/full-route-ending-9863-shorter-proposal.json)：把既定的15次高级经验攻击购买提前，原版逐动作执行确认当时付得起、最后全部资源相同。变为2474动作、4987次最不利抽样；增加的是实际往返楼层动作。不是改游戏变量、加资源或成绩提升。
- [独立重执行收据](../experiments/full-route-ending-9863-audit.json)：295场战斗，约32.43秒、79757312字节进程峰值、58644735条解释指令。数值终点位于26号内部地图，HP正、最终Boss格清空，并执行原版请求结局的分支。这些指标不等于原版通关用时。
- 旧原生尝试在前期终止，以验证更短战斗版本；不计作通关。新的原生尝试从菜单重新开始，真实时钟、自然随机数、普通输入；结果见D。

搜索新增跨深度资源比较：仅在地图消费集合、位置、攻击、防御、等级、钥匙、随机状态、奖励计账及购买计数都相同时，剔除HP/金币/经验全部不优于已经展开状态的候选。这样排除买钥匙再低价卖回的损耗循环；被束宽裁掉的状态不进入此表。整体仍是有裁剪的启发式搜索，失败不代表无解。

研究分支另设早期商店购买尝试上限，跨分段保留；失败购买也占尝试计数，退出不占。这是实验约束，不是原版规则，且不能误当作成功付款次数。后期若要释放上限须明确改变实验约束。已经修正商店目标未指定购买时的正常退出处理。

复算完整数值终点：

```sh
python3 tools/verify_route_proposal.py experiments/full-route-ending-9863-shorter-proposal.json generated/private/mhhf.swf --require-numeric-ending
python3 tools/reschedule_route.py experiments/full-route-ending-9863-proposal.json generated/private/mhhf.swf --before 1659 --indices '[1674,1675,1676,1677,1678,1679,1680,1681,1682,1683,1684,1685,1686,1687,1688]' --out generated/rebuilt-ending.json
```

## D：9863路线完整原生回放通过

2026-10-25复核完成：固定原版SWF、官方Ruffle0.7.1、真实时钟及自然随机数，从菜单开始执行2474关键动作、31583次普通输入，最终进入根帧4349，内部地图26、Boss格清空、6573HP存活。最终4863攻、5000防、17级，金币1260、经验1077。没有存读档、指定种子或游戏变量写入。

[公开数值收据](../experiments/full-route-native-ending-9863.json)包含输入、语义事件、资源检查点及295场战斗的4886次实际抽样。独立帧级战斗模型全部一致；原版受限字节码重建逐动作核对，实际HP始终不低于最不利模型，其余资源相同。神秘宝物在1128游戏秒取得，早于1800秒门限。游戏内计时最终停在1800；独立墙钟从菜单点击到最终截图为2267.931秒（约37分48秒），是自动化验证耗时，不能当作已按速通规则计时的人类成绩。

这次达到完整24层实际结局，但**攻防和9863仍比公开10088低225，没有破纪录**。长回放的无观测器对照仍缺失，收据重算只确认内部一致性，不能单凭公开JSON证明私有原生轨迹真实性。原始地图行、截图、完整逐帧轨迹和原版素材保留于忽略目录。

```sh
python3 tools/verify_route_progress.py experiments/full-route-native-ending-9863.json generated/private/mhhf.swf
```

## E：10088路线完整原版回放通过

2026-10-25：完整执行1656个关键动作、16647次普通输入，295场战斗和3413次自然抽样通过独立帧级模型核验。最终5056攻、5032防、19658血、17级，金币1238、经验1080、钥匙全0；地图26、根帧4349、最终Boss格清空且角色存活。墙钟1432.205秒；真实时钟、自然随机数、没有存读档或游戏变量写入。打平公开攻防和10088，尚未破纪录。完整路线的无观测器对照仍缺失。

[整局数值收据](../experiments/full-route-native-ending-10088.json)、[完整数值路线](../experiments/full-route-ending-10088-proposal.json)、[数值路线核对](../experiments/full-route-ending-10088-audit.json)均公开，不含游戏素材、地图数组或完整原版动作体。

相比9863路线，保留后期更划算的商店预算，延后会被剧情增强奖励的敌人，并使用原版飞行器从十四层右区返回，避免额外蓝门开销。飞行器由普通J、Space、数字2及Space输入完成；数值适配器执行固定SWF的对应原始按钮/菜单动作，真实播放器已走通。

固定1147动作前缀、剩余敌人/物品奖励及钥匙交易，穷举25425对购买预算、21292个货币DP单元，得到条件上界10088，路线恰好达到；耗时约0.008秒，进程峰值约26MB。放宽了购买时机、血量及位置约束，并用总攻防和的整除上界代替实际分项加成；结果不能推广到其他前缀、奖励时机、开门方案或存读档策略。[预算及假设](../experiments/full-route-ending-10088-shop-budget.json)。

```sh
python3 tools/verify_route_proposal.py experiments/full-route-ending-10088-proposal.json generated/private/mhhf.swf --require-numeric-ending
python3 tools/verify_route_progress.py experiments/full-route-native-ending-10088.json generated/private/mhhf.swf
python3 tools/fixed_suffix_shop_budget.py experiments/full-route-ending-10088-proposal.json --prefix-actions 1147 --check experiments/full-route-ending-10088-shop-budget.json
# 重新实际运行原版，需要本机官方Ruffle与Chromium路径，约24分钟
mkdir -p generated/Replay10088
cp experiments/full-route-ending-10088-proposal.json generated/Replay10088/proposal.json
python3 tools/fullgame_observer.py --directory generated/Replay10088 --compass
MOTA_REPLAY_DIR=generated/Replay10088 node tools/fullgame_replay.mjs
python3 tools/audit_fullgame.py generated/Replay10088
```

末段血量优化正在进行；数值分支不能替代整局原版验证，也不能与无攻防约束的最高血量赛道混比。

## F：10088攻防和下的28376血数值候选

前缀动态规划固定敌人/门顺序，对属性购买分配和八组血瓶延后方案搜索，共393831个DP状态、442867条转移；DP本体约0.247秒，连同两个成功候选的原版字节码重放约15.93秒，进程峰值60.8MB。兼容后缀的最佳前缀在十三层金队长后为174血、696攻、625防，保留六层两瓶大血瓶。固定该终点攻防并不表示全前缀最优。[搜索记录](../experiments/prefix-allocation-31.json)。

后段延后飞羽及可延后的血瓶，在圣水前补取所有可达剩余血瓶。原版受限字节码从自然初态重放1825动作、295战斗、3343次最不利支持抽样，存活进入最终结局：28376血、5056攻、5032防，攻防和10088。核对约14.20秒、进程峰值71.9MB。最初为数值候选；后续整局原版回放已通过（见下）。比[公开28590血路线](https://www.taptap.cn/moment/544556257772569275)低214，不能称为破纪录。

[完整候选](../experiments/full-route-hp28376-proposal.json)、[数值核对](../experiments/full-route-hp28376-audit.json)。新方案保持金币/经验总账，提前的一次廉价属性购买替代后续同类购买；不增加免费资源。搜索工具固定已审计的公开源动作哈希，不执行上游游戏源码。

```sh
python3 tools/search_prefix_shop_allocation.py
python3 tools/reorder_late_health.py
python3 tools/combine_hp_candidate.py
python3 tools/verify_route_proposal.py generated/CombinedHP/proposal.json generated/private/mhhf.swf --require-numeric-ending
python3 tools/verify_route_proposal.py experiments/full-route-hp28376-proposal.json generated/private/mhhf.swf --require-numeric-ending
```

29次前期廉价经验购买的固定顺序分支，以及束宽4096的受限搜索，都未找到过十三层金队长的候选。没有证明29次不可能。当前下一方向是改变早期战斗/血瓶顺序，进一步保存药水或减少廉价购买；不是反复优化已证10088上限的固定末段商店预算。

### F的原版整局验证

完整实际回放与独立审计已完成：1825动作、20115次普通输入、295战斗、3274次自然抽样均核验一致，最终28376血、5056攻、5032防，地图26、根帧4349、最终Boss格清空。墙钟1525.959秒。使用真实时钟、自然RNG、无存读档与游戏变量写入；仍缺完整无观测器对照。公开[原版数值收据](../experiments/full-route-native-hp28376.json)。

```sh
python3 tools/verify_route_progress.py experiments/full-route-native-hp28376.json generated/private/mhhf.swf
```

搜索补充：尝试把十三层两瓶大血瓶延后，第一瓶会阻挡通向上方的唯一路径，候选被原版路径检查拒绝；不能凭血量总账把它视为可自由挪动。更早购买经验属性和加入一次升级的固定顺序分支也已测试，失败仅针对各自限制，不构成全塔不可能证明。

## G：单事件换序与全部早期药水延后选择

2026-10-26：原版已回放最佳仍是28376血/10088攻防和，尚未破纪录。最新搜索针对能否在十三层第一只金队长前再留一瓶500血药水。

在已固定哈希的10088源动作中，枚举基准路径上当时已可接近的敌人、宝石、飞羽、钥匙等，把其中一个事件提前，共2043种换序。每个顺序重新分配原有属性购买。先用八组药水调整检查16352个方案，累计562619084次DP状态保留、632734968条转移，177.47秒，峰值54.8MB；没有留下三瓶指定大血瓶的兼容前缀。[原始范围与数值](../experiments/early-event-advancement.json)。这些是跨步骤、跨案例的累计计数，含重复状态。

为避免只试八组药水而漏掉组合，又把28瓶早期药水逐一分为原时点喝或最后白衣法师之后喝。用“攻击、防御、等级、延后补血总量”作键保留最大血量，压缩表示全部2^28种选择。固定旧顺序时，442846次状态保留、506263条转移，约0.225秒、46.6MB，没有数值存活前缀；这是固定战斗及商店时机、保留指定三瓶药水的结果。它没有覆盖其他战斗顺序、消费数量、随机数策略或全塔路线。[完整限制](../experiments/early-potion-deferral-bound.json)。

另将相同31次廉价经验购买移到商店开放且经验充足的最早时点，并结合全部早期药水选择，仍不能多保留一瓶500血药水；保留两瓶时仍得到174血前缀。[经验提前分支](../experiments/early-potion-deferral-asap-xp.json)。金币也按最早可负担时点购买的174血原版字节码正对照另已通过，并加入CI。改变消费时机的这一固定分支也没有整局提升。

同一工具只保留原来的两瓶药水作正对照时，重建了174血/696攻/625防/2级的已知前缀，并通过全部原版受限字节码动作、钥匙和货币核对。[正对照](../experiments/early-potion-deferral-control.json)。延后总量相同的药水可能位于不同路径，所以数值存活只提供候选，仍需真实路径核验；数值失败仅排除其明确限定的放宽模型。

随后把2043种单事件换序各自与全部早期药水选择结合，累计704761214次状态保留、806549881条转移，473.26秒，子进程峰值51.9MB；没有达到兼容目标696攻/625防/2级的数值分支。[批量记录](../experiments/early-event-all-deferrals.json)、[换序索引](../experiments/early-event-mutations.json)。实际没有逐一枚举2^28条路线，也没有完成全塔穷举。

保留两瓶药水的另一轮搜索，把一层(0,6)蓝宝石提前到源事件135之前，原版字节码前缀从174提高到178血。已把这个前缀接入完整28376后缀并逐动作重算，终点仍为28376血；4血差在百分比伤害中消失。因此没有把它当作整局改进或再启动相同成绩的长回放。[前缀搜索记录](../experiments/early-event-hp-search.json)。

```sh
# 以下输出目录须尚不存在；默认生成目录不含可公开授权的游戏素材
python3 tools/search_potion_deferral.py --check experiments/early-potion-deferral-bound.json
python3 tools/search_potion_deferral.py --reserve 690,721 --out generated/AllPotionDeferralsControl --check experiments/early-potion-deferral-control.json
# 从原版基准重新产生2043个可接近事件换序并检查八组药水
python3 tools/search_event_advancement.py
# 或直接使用公开的数值索引，重建每个换序的全部药水放宽结果
python3 tools/sweep_event_deferrals.py experiments/early-event-mutations.json
# 只回放比174血严格更好的前缀
python3 tools/search_event_advancement.py --reserve 690,721 --min-hp 174 --improving-only --out generated/EventAdvancementHP
```

进一步延后会掉血的战斗，按图结构保留543种、每次最多跨160个源事件的分支；购买时按实际货币优先完成12次廉价金币购买和31次廉价经验购买，高级金币购买预留早期必买红钥匙。各分支再次结合全部早期药水延后选择，累计245265477次状态保留、279474116条转移，152.70秒、子进程峰值50.7MB；没有数值兼容前缀。[结果](../experiments/early-battle-delay-search.json)、[索引](../experiments/early-battle-delay-mutations.json)。地图剪枝在对白处停止，暂未建模对白导致的新地图变化；这不是所有延后战斗的穷尽。

```sh
python3 tools/enumerate_battle_delays.py --out generated/battle-delay-mutations.json
python3 tools/sweep_battle_delays.py experiments/early-battle-delay-mutations.json
```

本轮4项Node和73项Python测试全部运行通过，未跳过原版集成测试。CI加入全部药水放宽与原版正对照重建。下一搜索必须涉及更大范围的战斗/开门顺序或消费时机，单事件提前与药水选择的这一邻域已无突破；不把这个结论扩展成原版最优性。

## H：28554血的原版完整回放

把九层左下的敌人(1,9)和药水(1,8)提前处理，使勇者可以暂时留下(2,9)药水，并保持通往后续红衣法师的路径畅通。延后五层(2,0)、九层(10,4)/(2,9)三瓶小药水到最后白衣法师之后，另把十层(10,10)的小药水和六层两瓶大药水留到圣水前。十三层首只金队长后为55血/696攻/625防，原版字节码逐动作核验通过。

新搜索给药水增加“留到本前缀以后”这一选择，以攻击、防御、等级、延后补血、保留补血为键保留最大血量。规定三个事件提前和四瓶必经药水按其事件时点喝，搜索1200血保留量；DP累计2731428次状态保留、3162434条转移，本体约1.55秒，连同原版前缀验证约9.14秒，峰值79.1MB。[前缀数值与范围](../experiments/mixed-potion-reserve-1200.json)。这里的选择数量是压缩模型的原始组合上界，包含路径上不可同时实现的选择；正例须另过实际路径核验，不能用它宣称全塔穷举或全局最优。

接上已验证后半程，完整原版字节码重算1779动作、295战斗、3349次最不利支持抽样，终点28554血/5056攻/5032防；地图26、最终Boss清空并请求结局。[完整动作](../experiments/full-route-hp28554-proposal.json)、[完整数值核对](../experiments/full-route-hp28554-audit.json)。公开完整动作保留实际回放所用文件的精确哈希；重新生成时前缀元数据不同，但完整动作列表和最终资源已逐项比对相同。

原版整局已实际完成并独立审计：19365次普通输入、295场战斗、3284次自然随机抽样逐帧模型一致。最终28554血、5056攻、5032防、17级、钥匙全0、金币1238、经验1080；地图26，根帧4349，角色存活且最终Boss格为0。菜单点击到最后观测为1497.896秒，属于程序回放墙钟。没有指定种子、改时钟、存读档或写入游戏变量。[原版收据](../experiments/full-route-native-hp28554.json)。完整无观测器对照仍未完成。

该成绩比此前28376提高178血，比[公开10088/28590文字成绩](https://www.taptap.cn/moment/544556257772569275)仍低36血；未达到破纪录条件。不同构建、结局及随机数/存读档规则的一致性尚未核实，世界纪录身份仍不能据此推定。

```sh
python3 tools/search_mixed_potion_reserve.py --advance 135,143 --extra-advance 352,353 --extra-advance 352,549 --must-eat 333,375,376,549 --target-reserve 1200 --check experiments/mixed-potion-reserve-1200.json
# 先按F节重建 LateHPGreedy；此处只使用新的前缀
python3 tools/combine_hp_candidate.py --prefix generated/MixedPotionReserve/proposal.json --directory generated/RebuiltHP28554 --expected-hp 28554
python3 tools/verify_route_proposal.py experiments/full-route-hp28554-proposal.json generated/private/mhhf.swf --require-numeric-ending
python3 tools/verify_route_progress.py experiments/full-route-native-hp28554.json generated/private/mhhf.swf
```

正在另查黄钥匙的配置：省去五层黄门，用多的一把黄钥匙取十一层另外三瓶小药水。已找到数个合法早期前缀，但续接高级商店的束搜索尚未成功；这不是完整新成绩。药水保留1300的已试固定换序分支也未得到合法候选。

## 发现并修正的问题

1. 自然开场数值初态曾扣黄钥匙却保留序章黄门，真实回放暴露了错误。现已同时清除门和出生标记；旧M8禁止返回序章，不受影响。
2. 原版道具提示框Space按钮包含实际状态修改。现静态提取并执行其原始动作，避免漏掉十字架、图鉴、飞行等标记。
3. 隐藏结局须先以未携带十字架的状态交神秘宝物取得冰杖/隐藏标志，再交十字架。提前交十字架会令仙子离开且缺少隐藏标志。A已在真实原版核对前置顺序；晚交属性加成仍需路线优化。
4. 剧情NPC可能留下无窗口的`Display_buy`标记。实际回放按窗口、剧情、按键状态判断能否移动。
5. 目标Boss必须同时满足准入门槛与最不利伤害后的存活检查，不能把走到旁边当作能击败它。
6. 十五层装备NPC不能跳过购买按钮直接领取奖励。现执行原版初始化、购买按钮及完成节点；499资源拒绝、500资源扣费并加120属性的反事实测试通过。此分支尚待真实播放器验证。
7. 世界更新可能在既有对白结算后新建Boss后续对白。现循环到对白稳定，回归测试确认二十一层楼梯真正开启后才生成下一快照。
8. 二十层上楼格初始为0，只有仙子十字架分支把它改为13。神秘宝物/冰杖剧情本身不开放该楼梯，因此加成可以延后到清理二十层之后，不能延到二十三层之后。测试同时核验了这个顺序和错误顺序的后果。
9. 搜索曾把目标商店与一次性目标一同排除，导致“在商店达到所需属性”不能在该商店购买。现保留目标商店交易转移；回归测试从30经验实际购买5攻击并核对原版扣费。
10. 分层连通分量缓存保留有向楼梯；96个真实地图/反事实已消费集合查询与原逐格遍历一致，另覆盖三杖齐全后通往最终楼层的单向边。这些反事实集合只用于算法等价测试，不作为可行路线。

新搜索以未消费奖励计入资源潜力，钥匙按回售价估值，避免把买钥匙或提前拾取物品本身当作改善。默认保留圣水，关闭付费补血和购买等级，仍允许自然取得飞羽。束搜索不完备，失败不是无解证明。原生回放新增独立墙钟时长；原游戏计时到1800秒可能停止，不能单独作为全程速通计时。

观测器旧字段`TimeRunID`在父影片的大小写敏感读取中不可用；归档没有改写，真实计时由`NowGameTime`推进及老人实际交互直接核对。新生成器补读原变量名`TimeRunId`；`--legacy-clock-field`可逐字节重建A所用旧观测器，哈希已核对一致。

## 复现

先按README取得固定SWF、依赖和官方播放器。公开收据重算只检查数值一致性，不凭收据本身证明私有轨迹真实性、无观测器等价或纪录身份。

```sh
# 重建A的数值动作，供真实播放器重新执行
python3 tools/verify_route_progress.py experiments/full-route-prefix16.json generated/private/mhhf.swf --proposal-out generated/FullRoute/proposal.json
python3 tools/fullgame_observer.py --legacy-clock-field
node tools/fullgame_replay.mjs
python3 tools/audit_fullgame.py

# 独立重算B；不是原生回放
python3 tools/verify_route_proposal.py experiments/full-route-numeric19-proposal.json generated/private/mhhf.swf

# 重新执行固定二十三层前缀并核对条件攻防和上界
python3 tools/route_resource_bound.py experiments/rejected-prefix23-proposal.json generated/private/mhhf.swf --check experiments/rejected-prefix23-ad-bound.json

# 在另一个忽略目录探索新候选，避免覆盖上面的A
python3 tools/explore_full_route.py generated/private/mhhf.swf --directory generated/FullRoute-search --width 2048
MOTA_FLASH_SWF=generated/private/mhhf.swf npm test
```

本轮4项Node与73项Python测试全部通过。CI继续回归M4—M8，并重建公开收据、重算十九层候选和二十三层条件上界。原版资源、地图数组、截图、完整对白、原版动作体仍留在忽略目录。

完整24层原生结局现已验证；下一验收是可复验的同版本同规则超纪录成绩，及完整路线无观测器对照。

## I. 2018存档、版本差异与配对宝石顺序实验（2026-10-26）

本轮实际取得另一份1856607字节的SWF，SHA256为`40926f44642f8b810caec67a80ac371080f34b7064fdf86a5dc1b4bd66101896`。下载自[yunny0保存副本](https://github.com/yunny0/magic-tower-flash-v112/tree/main/assets/flash)，Git blob SHA1为`166871fb3910734c241eb0135b485a6b2899e3ca`，与[gdut-yy在2018-07-11提交的文件](https://github.com/gdut-yy/MagicTower/blob/fdbfe273e01b008ccaa0045192d9577178e04948/%E9%AD%94%E5%A1%94V1.12.swf)一致。提交无认证签名；这是存档来源线索，仍未取得作者发布指纹或纪录视频所用文件。原文件和反编译结果只保存在忽略目录，未取得再分发许可。

静态报告见[构建比较](../experiments/swf-build-comparison.json)与[来源记录](../experiments/gdut-archive-provenance.json)。两份均为SWF6、100fps、9788根帧。标题形状455连同标签头的SHA256均为`1bb695028d1e489735571c0cf3fe8c5889a74b8b4d673e7e64f5736a5e3efcb6`，与此前目视识别的“Ver1.12”标题完全相同。103个动作脚本有99个逐字节一致，包括新游戏地图/敌人初始化和战斗帧；10个顶层DefineFunction的函数体、参数和常量池一致，包括移动、地图显示。这里没有宣称已经识别所有嵌套函数。

两份文件存在会影响规则的差异：

| 项目 | 当前mhhf回放文件 | 2018存档 |
|---|---|---|
| 存档 | 增加SharedObject跨会话存档及自动装载 | 只保留游戏内内存存档 |
| 16层限时通道 | 1800秒封闭 | 1500秒封闭 |
| 商店/飞行器选择 | 增加方向键处理 | 使用原有数字键 |
| 菜单/全屏 | 部分修改 | 保留全屏/不缩放调用 |

完整静态比较定位37284个标签，按父级/帧/类型/序号有41处差异，其中4个动作脚本、2个按钮不同。定位对齐的标签差异不等于41种游戏规则差异；不把核心脚本相同扩大为整局语义等价。

同一条公开28554路线的1779动作在2018文件的字节码数值模型中全部通过：295战斗、3349最坏支持抽样、31847107解释指令，13.09秒、69.9MB。数值终点为地图26/Boss格已清/存活/结局转场已请求；**它不验证25分钟墙钟限制，也不是该存档已真实通关的证据**。2018存档的真实时钟整局回放另行核验，结果须在实际完成后追加。

复验命令：

```
python3 tools/fetch_swf.py gdut
python3 tools/compare_swf_builds.py generated/private/mhhf.swf generated/private/gdut.swf --out generated/archive-comparison.json --check experiments/swf-build-comparison.json
python3 tools/verify_route_proposal.py experiments/full-route-hp28554-proposal.json generated/private/gdut.swf --require-numeric-ending
```

另将原有F1蓝宝石提前与31种基准可达的额外红/蓝宝石提前组合，连同未加宝石变体的对照，共32个固定顺序；继续完整分支早期药水“吃/白衣后吃/保留”及属性分配，尝试保留1300补血。全部完成，均无目标属性`696/625/2级`的1300保留解；耗时50.93秒，子进程峰值83.8MB。结果和每项状态/转移统计见[有限搜索记录](../experiments/mixed-potion-gem-sweep.json)，输入候选见[基准可达提前列表](../experiments/early-reachable-mutations.json)。这只排除声明的固定顺序，不排除其它顺序或全塔路线。

```
python3 tools/sweep_mixed_potion_gems.py --out generated/NewMixedGemSweep
```

截至这项实验，已真实回放最好成绩仍为10088/28554，比公开10088/28590低36；没有破纪录或全局最优结论。
