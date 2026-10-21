# M5 复现

需要 Node22+、Python3.12+、C11编译器、网络；Linux浏览器依赖由Playwright安装。

```sh
npm ci --ignore-scripts
npm run flash:fetch
npm run ruffle:fetch
npx playwright install --with-deps chromium
npm run ruffle:verify
MOTA_FLASH_SWF=generated/private/mhhf.swf npm test
```

验证命令重新生成探针、本机执行两组播放器检查、编译并遍历完整非零31位RNG状态，
完成两种真实地图搜索后，对比 `experiments/ruffle-M5.json` 的稳定字段。
耗时、内存、浏览器补丁版本和平台不参与跨平台相等比较；迹线、源码/运行包指纹、地图指纹、状态数量和结论参与比较。
所有输出在忽略目录 `generated/M5/`。

可用 `MOTA_RUFFLE_WEB` 指向已解压官方播放器目录，各文件仍须匹配固定SHA256。
`MOTA_CHROMIUM_EXECUTABLE` 可指定已有浏览器，实际版本会记录。
`MOTA_PLAYWRIGHT_IMPORT` 是已有Playwright模块的可选导入入口；默认使用锁文件安装的依赖。
C编译器可用 `CC` 指定。运行入口应在仓库根目录。

`ruffle-M5.json` 是可分享的数值证据。
`*-probe.swf` 含本地生成测试影片，其中战斗夹具嵌入选定原版动作体，不可随公开实验附件上传。
整个流程不运行复刻上游JavaScript；M5有意在受控独立播放器中运行原版选定数值字节码。
完整影片、原始实例层级、原生按键/计时/存档仍未验证，不能把探针通过等同于全游戏一致。
