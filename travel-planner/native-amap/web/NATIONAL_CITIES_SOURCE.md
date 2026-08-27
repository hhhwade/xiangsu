# 全国城市中心数据来源

`national-cities.js` 包含 369 个中国城市/地区中心坐标，用于：

- 目的地输入建议；
- 在高德 POI 实时返回前提供城市地图视野；
- 断网时识别用户输入的全国城市名称。

数据来源：[sunqianggg/Chinese-citys](https://github.com/sunqianggg/Chinese-citys) 的 `china-city-list.json`，该数据集说明其城市/地区名称与坐标来自和风天气城市列表。提取日期：2026-08-27。

这些中心点不是景点路线坐标。景点名称、坐标、地址、图片和概述的优先来源是应用内 AMap Search SDK 的实时 POI 搜索；若没有实时结果，界面会显示离线状态，不应把中心点当作真实景点位置。
