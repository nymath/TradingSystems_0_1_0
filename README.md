# 事件驱动的交易系统

[![version](https://img.shields.io/badge/version-0.1.0-green.svg)]([{linkUrl}](https://github.com/nymath/TradingSystems_0_1_0)) [![Version](https://img.shields.io/badge/python-3.9-blue.svg)]([{linkUrl}](https://github.com/nymath/TradingSystems_0_1_0))
等后边有时间了再写一下完整的介绍。

---

## Installation

- Unix

```{shell}
cd ~
git clone git@github.com:nymath/TradingSystems_0_1_0.git
```

- Test

```{shell}
cd {your root work space}
python ./examples/mac.py
```

## 文件介绍

- **study_materials**:
    关于数据获取方式, 量化社区的一些总结.
- **pytrade**:
    回测系统的核心部分，我写成了一个module.
- **data**:
    用于存放下载的数据.
- **examples**:
    一些常见策略的实现.

## 运行逻辑

1. 事件驱动, 程序是在bar上run的, bar的timestamp是整个bar的开端.
2. 在每个交易日当天, 程序会根据是否继续回测(该信息包含在datahandler里), 更新一个bar(更新bar的同时会加入一个MarketEvent), 这个bar的timestamp是上一个交易"日".

> 该回测系统基于两个while循环, 外层while循环用于更新bar, 如果无bar可更则跳出循环。内层循环则用于处理上一个bar的期间内产生的一系列"事件", 当事件队列为空时, 跳 出内层循环.

## 定义

[详细介绍](https://www.notion.so/nymath/Terminology-67f949ecd34b4455b2a550509d3ae7e1)

- **事件**

| 类 | 描述 |
| --- | --- |
| `MarketEvent`| |
| `SignalEvent`| |
| `OrderEvent`| |
| `FillEvent`| |

- **事件队列**

所有的事件类全部放在queue容器中.

- **算子**

| 类 | 描述 |
| --- | --- |
| `DataHandler`|读数据, 并保存为bar |
| `Strategy`|接受市场事件， 产生信号事件 |
| `Portfolio`| |
| `ExecutionHandler`| |

---

## 其他注意事项

1. 时区
2. 交易费用

<!-- [![GitHub version](https://badge.fury.io/nymath/TradingSystems_0_1_0.svg)](https://github.com/nymath/TradingSystems_0_1_0) -->

<!-- [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) -->

---

Bibliography:

[1] Hall-Moore, M.(2014). Successful Algorithmic Trading.
[2] 
