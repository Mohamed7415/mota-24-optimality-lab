# M7 复现

```sh
npm ci --ignore-scripts
npm run flash:fetch
npm run ruffle:fetch
npx playwright install --with-deps chromium
npm run crossfloor:verify
MOTA_FLASH_SWF=generated/private/mhhf.swf npm test
```

需要Node22+、Python3.12+和浏览器运行环境。M5完整RNG枚举另需C11编译器。
`crossfloor:verify`重新生成真实地图计划、六类原版商店隔离探针和只读观测器，
实际执行216商店案例及两轮完整原版菜单→三层→一层路线，比较HUD、115抽样、资源和23格持久化，最后核对稳定基准。
CI还先执行M5/M6以覆盖原有回归。

输入顺序、数值检查点、散列来源、消费格和结论必须相等；等待毫秒、瞬时切层旗标、采样帧数、
浏览器版本、硬件计时/内存和平台像素散列不参与跨平台相等比较。
每次运行仍要求本机有/无观测器的四个资源区域逐像素相同。

结果在忽略目录 `generated/M7/`，可分享的是 `crossfloor-M7.json`。
原版画面、探针SWF和含完整地图的私有计划不得作为公开附件。
`--reuse-local`仅用于汇总已完成的本机原始回放输出；CI不使用这个选项，会从头运行全部探针和回放。

可用 `MOTA_RUFFLE_WEB` 与 `MOTA_CHROMIUM_EXECUTABLE` 指定已有运行环境，播放器仍校验固定文件指纹。
M7驱动会将原版路径及回放目录传给其子进程，不改动原版游戏字节或变量。
秩证明仅覆盖商店自身的非负精确整数资源域；外部奖励有限性和跨层最优仍待证明。
