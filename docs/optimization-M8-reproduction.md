# M8复现

需要Node22+、Python3.12+、依赖安装、固定原版及Ruffle0.7.1、Chromium。原始第三方素材始终保留在忽略目录。

```sh
npm ci --ignore-scripts
npm run flash:fetch
npm run ruffle:fetch
npx playwright install chromium
npm run optimization:verify
MOTA_FLASH_SWF=generated/private/mhhf.swf npm test
```

完整入口重新运行宽1024/深140的搜索、独立逐格路线校验、原版普通输入回放、无观测器对照和显示区域比较。CI不复用本地生成结果。输入来源绑定SWF SHA及初始化地图/敌人表SHA；标准结果在 `experiments/optimization-M8.json`。生成的 `generated/M8/game-plan.json` 含实际地图，仅本地使用。

仅运行搜索：

```sh
python3 tools/search_crossfloor.py generated/private/mhhf.swf
```

探索其他束宽/深度会生成不同数值或路线；不能用不同参数的数据替换标准基准而不更新说明。

本机已有浏览器时可指定 `MOTA_CHROMIUM_EXECUTABLE`；Ruffle文件可用 `MOTA_RUFFLE_WEB` 指定，程序仍检查全部发布文件哈希。`--reuse-local`仅用于本地汇总已有回放，不是独立复现，不用于CI。

基准比较移除耗时、进程峰值、平台、浏览器版本、输入等待时间、截图像素哈希等环境差异。四个显示区域在同一次环境内必须逐像素相等，路线/资源/抽样/计数/输入顺序及规范检查点指纹必须匹配。

本阶段固定M6前缀并阻挡未验证事件。保守区间[2150,13860]只属于该受限续程模型；束搜索丢弃候选，`complete=false`。不会发布原版素材或完整截图。
