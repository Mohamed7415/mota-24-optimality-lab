# M6 复现：完整原版影片及自然初态

需要Node22+、Python3.12+、C11编译器（M5枚举用）、网络与Playwright浏览器运行环境。

```sh
npm ci --ignore-scripts
npm run flash:fetch
npm run ruffle:fetch
npx playwright install --with-deps chromium
npm run ruffle:verify
npm run game:verify
MOTA_FLASH_SWF=generated/private/mhhf.swf npm test
```

`game:verify`重新生成只读父影片与真实地图计划，运行两轮完整原版影片，再比较数值区域，
核对21次实际抽样、开场资源、事件结算、固定种子与任意种子放宽上界的双算法结果。
与 `experiments/whole-game-M6.json` 比较时，保留输入顺序、数值检查点、来源指纹、抽样、搜索量和结论；
忽略等待毫秒、总帧采样数、瞬时切层旗标、硬件计时/内存、浏览器版本以及各平台的像素散列值。
每次运行仍严格要求本机有/无观测器的四个数值显示区域逐像素一致。

M6读取M5证书的文件指纹，完整RNG枚举由前一条 `ruffle:verify` 重新验证。
CI也按此顺序运行，并重新获取两个固定公共下载。

输出位于忽略目录 `generated/M6/`：
- `whole-game-M6.json` 为可分享数值证据，含输入顺序及规范化检查点。
- `native-traces.json` 为本机完整数值抽样记录；帧数受调度影响，不要求逐帧跨平台一致。
- `native-MT2.png`、`control-MT2.png` 含游戏原版画面，供本机校验，不公开上传。
- `observer.swf` 是实验自己的只读父影片；原版 `mhhf.swf` 字节未修改。
- `game-plan.json` 是从固定原版数据导出的本地地图/路线计划；不随数值附件上传。

日期被固定以确定RNG，帧率保持原版100，菜单、对话、门、战斗和切层照常运行。
顶层原版对照复用输入顺序并增加等待余量，未使用观测器或读写游戏变量。
此流程不验证真实1800秒事件、不操作已有存档，也不证明Adobe原生播放器或24层全局最优。

`MOTA_RUFFLE_WEB`、`MOTA_CHROMIUM_EXECUTABLE` 可指定已有播放器/浏览器；播放器文件仍须匹配发行指纹。
M6直接使用锁文件中的Playwright。完整回放通常约一分钟，较慢机器需要更长；CI使用各语义条件的有界超时。
