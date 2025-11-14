# arXiv 发布节奏与日期过滤机制详解

## 📅 arXiv 的发布节奏

根据 arXiv 官方的发布机制：

### 发布时间表

```
时间: 每天 20:00 ET (美国东部时间)
内容: 昨天 14:00 ET 到今天 14:00 ET 之间提交/更新的论文

示例:
┌─────────────────────────────────────────────────────────────────┐
│ 2025-11-12 (周二) 20:00 ET 发布的论文                            │
│ 包含: 2025-11-11 14:00 ET ~ 2025-11-12 14:00 ET                │
│       之间提交/更新/cross-list的所有论文                          │
└─────────────────────────────────────────────────────────────────┘
```

### 时区对照

```
美国东部时间 (ET)      北京时间 (UTC+8)           说明
─────────────────────────────────────────────────────────────────
周二 14:00            周三 02:00 (冬令时)        提交截止 (开始)
                      周三 03:00 (夏令时)        
周二 20:00            周三 08:00 (冬令时)        公开发布时间
                      周三 09:00 (夏令时)
周三 14:00            周四 02:00 (冬令时)        提交截止 (结束)
                      周四 03:00 (夏令时)
```

**注意**: 
- ET = Eastern Time，包含 EST (东部标准时间) 和 EDT (东部夏令时)
- 美国夏令时: 3月第2个周日 ~ 11月第1个周日

## 🔍 应该查看哪个字段？

### arXiv API 返回的日期字段

arXiv API 返回多个日期字段，理解它们的区别很重要：

#### 1. `submittedDate` (提交日期)

```python
# API 中使用的字段名
submittedDate: 论文最后一次提交/更新的时间
```

**特点**:
- ✅ 包含论文的首次提交
- ✅ 包含论文的修订版本 (v2, v3, ...)
- ✅ 包含 cross-list 操作的时间
- ✅ **这是 arXiv 发布时参考的时间字段**

**用途**: 
- **获取每日新发布的论文时应该使用这个字段**
- arXiv 的 "new" 列表就是基于这个时间

#### 2. `published` / `published_date` (首次发布日期)

```python
# API XML 中的字段名
<published>2025-11-12T08:30:00Z</published>

# 我们代码中存储的字段名
published_date: "2025-11-12T08:30:00Z"
```

**特点**:
- ✅ 论文首次在 arXiv 上公开的时间
- ❌ 修订版本 (v2, v3, ...) **不会更新**这个时间
- ❌ cross-list **不会更新**这个时间
- ❌ 只记录首次发布的时间

**用途**:
- 确定论文的"首次出现"时间
- 计算论文的"年龄"

#### 3. `updated` / `updated_date` (最后更新日期)

```python
# API XML 中的字段名
<updated>2025-11-13T15:20:00Z</updated>
```

**特点**:
- ✅ 论文最后一次修改的时间
- ✅ 包含修订版本 (v2, v3, ...) 的时间
- ⚠️ 有时会因为元数据修改而更新（即使内容未变）

**用途**:
- 查找最近更新的论文
- 追踪论文的修订历史

### 对比总结

| 字段 | 首次提交 | 修订版本 | Cross-list | arXiv "New" 列表 | 建议用途 |
|-----|---------|---------|-----------|----------------|---------|
| `submittedDate` | ✅ | ✅ | ✅ | ✅ **基于此** | **获取每日新论文** ⭐ |
| `published` | ✅ | ❌ | ❌ | ❌ | 首次发布时间 |
| `updated` | ✅ | ✅ | ✅ | ❌ | 最后更新时间 |

## ✅ 正确的日期过滤方案

### 你的理解是否正确？

你说:
> "获取 20251111 的论文，应该在 20251112 获取，时间范围是 20251110 14:00 ET 到 20251111 14:00 ET"

**回答**: ✅ **基本正确！** 但需要一些调整。

### 完整的逻辑

#### arXiv 的发布逻辑

```
arXiv 在 2025-11-11 20:00 ET 发布的论文:
├─ 时间范围: 2025-11-10 14:00 ET ~ 2025-11-11 14:00 ET
├─ 论文标记: submittedDate 在这个时间段内
└─ 称为: "2025-11-11" 的论文 (按发布日命名)
```

#### 你应该何时获取？

```
选项 1: 在 2025-11-11 20:00 ET 之后立即获取 (当天)
  - 优点: 最快获取到新论文
  - 缺点: arXiv 可能有延迟，数据可能不完整

选项 2: 在 2025-11-12 (第二天) 获取 ⭐ 推荐
  - 优点: 数据已经完全稳定，保证完整性
  - 缺点: 延迟一天
```

### 正确的 API 查询方式

#### 当前代码的实现

查看现有代码:

```88:93:arxiv-paper-curator/src/services/arxiv/client.py
        if from_date or to_date:
            # Convert dates to arXiv format (YYYYMMDDHHMM) - use 0000 for start of day, 2359 for end
            date_from = f"{from_date}0000" if from_date else "*"
            date_to = f"{to_date}2359" if to_date else "*"
            # Use correct arXiv API syntax with + symbols
            search_query += f" AND submittedDate:[{date_from}+TO+{date_to}]"
```

**问题**: 
- ❌ 使用的是 `YYYYMMDD0000` 到 `YYYYMMDD2359` (UTC 时间)
- ❌ 这**不符合** arXiv 的 ET 14:00 ~ ET 14:00 机制
- ❌ 会遗漏一些论文或获取到不该获取的论文

#### 正确的实现方案

##### 方案 1: 使用 ET 时区的正确时间 (推荐) ⭐

```python
# 获取 2025-11-11 发布的论文 (在 2025-11-12 运行)
# arXiv 规则: 2025-11-10 14:00 ET ~ 2025-11-11 14:00 ET

from datetime import datetime
import pytz

def get_arxiv_date_range(publish_date: str) -> tuple[str, str]:
    """
    根据 arXiv 的发布机制，计算正确的 submittedDate 范围
    
    Args:
        publish_date: arXiv 发布日期 (格式: YYYY-MM-DD)
        
    Returns:
        (from_datetime, to_datetime) 元组
        格式: YYYYMMDDHHmm (arXiv API 格式)
    """
    et_tz = pytz.timezone('US/Eastern')
    
    # 解析发布日期
    pub_date = datetime.strptime(publish_date, "%Y-%m-%d")
    
    # 前一天 14:00 ET (提交窗口开始)
    prev_day = pub_date - timedelta(days=1)
    from_time_et = et_tz.localize(datetime(prev_day.year, prev_day.month, prev_day.day, 14, 0, 0))
    
    # 当天 14:00 ET (提交窗口结束)
    to_time_et = et_tz.localize(datetime(pub_date.year, pub_date.month, pub_date.day, 14, 0, 0))
    
    # 转换为 UTC (arXiv API 使用 UTC)
    from_time_utc = from_time_et.astimezone(pytz.UTC)
    to_time_utc = to_time_et.astimezone(pytz.UTC)
    
    # 格式化为 arXiv API 格式 (YYYYMMDDHHmm)
    from_str = from_time_utc.strftime("%Y%m%d%H%M")
    to_str = to_time_utc.strftime("%Y%m%d%H%M")
    
    return from_str, to_str

# 使用示例
from_date, to_date = get_arxiv_date_range("2025-11-11")
print(f"从: {from_date}")  # 例如: 202511101900 (冬令时 UTC)
print(f"到: {to_date}")    # 例如: 202511111900 (冬令时 UTC)

# API 查询
search_query = f"cat:cs.AI AND submittedDate:[{from_date}+TO+{to_date}]"
```

**注意事项**:
- ✅ 正确处理 ET 到 UTC 的转换
- ✅ 自动处理夏令时/冬令时切换
- ✅ 使用 `submittedDate` 字段 (arXiv 的标准)
- ✅ 符合 arXiv 的 14:00 ET ~ 14:00 ET 机制

##### 方案 2: 使用 arXiv 的日期格式 (简化版)

如果不想处理时区转换，可以使用更简单的方式：

```python
def get_arxiv_date_range_simple(publish_date: str) -> tuple[str, str]:
    """
    简化版：直接使用整天范围，可能包含一些额外的论文
    
    Args:
        publish_date: arXiv 发布日期 (格式: YYYY-MM-DD)
        
    Returns:
        (from_date, to_date) 元组
        格式: YYYYMMDD (简化格式)
    """
    pub_date = datetime.strptime(publish_date, "%Y-%m-%d")
    
    # 前一天
    prev_day = pub_date - timedelta(days=1)
    from_date = prev_day.strftime("%Y%m%d")
    
    # 当天
    to_date = pub_date.strftime("%Y%m%d")
    
    return from_date, to_date

# 使用示例
from_date, to_date = get_arxiv_date_range_simple("2025-11-11")
print(f"从: {from_date}")  # 20251110
print(f"到: {to_date}")    # 20251111

# API 查询 (使用 YYYYMMDD 格式，arXiv 会自动扩展为 0000 和 2359)
search_query = f"cat:cs.AI AND submittedDate:[{from_date}+TO+{to_date}]"
```

**优点**:
- ✅ 简单，不需要时区处理
- ✅ 会获取到所有相关论文

**缺点**:
- ⚠️ 可能包含一些不应该在这天发布的论文
- ⚠️ 时间范围不够精确

### 代码修改建议

#### 修改 1: 更新 `ArxivClient.fetch_papers()` 方法

```python
# 在 src/services/arxiv/client.py 中添加选项

async def fetch_papers(
    self,
    max_results: Optional[int] = None,
    start: int = 0,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    use_et_timezone: bool = False,  # 新增: 是否使用 ET 14:00 机制
    from_time: Optional[str] = None,  # 新增: 精确时间 (HHmm)
    to_time: Optional[str] = None,    # 新增: 精确时间 (HHmm)
) -> ArxivSearchResult:
    """
    Args:
        from_date: 开始日期 (格式: YYYYMMDD)
        to_date: 结束日期 (格式: YYYYMMDD)
        use_et_timezone: 是否使用 arXiv 的 ET 14:00 机制
        from_time: 开始时间 (格式: HHmm, UTC), 如 "1900" 表示 19:00
        to_time: 结束时间 (格式: HHmm, UTC)
    """
    
    if from_date or to_date:
        if use_et_timezone:
            # 使用 arXiv 的标准: 前一天 14:00 ET ~ 当天 14:00 ET
            from_datetime, to_datetime = self._convert_to_et_range(from_date, to_date)
        elif from_time and to_time:
            # 使用精确时间
            date_from = f"{from_date}{from_time}" if from_date else "*"
            date_to = f"{to_date}{to_time}" if to_date else "*"
        else:
            # 使用默认: 00:00 ~ 23:59
            date_from = f"{from_date}0000" if from_date else "*"
            date_to = f"{to_date}2359" if to_date else "*"
        
        search_query += f" AND submittedDate:[{date_from}+TO+{date_to}]"
```

#### 修改 2: 添加时区转换工具函数

```python
# 在 src/services/arxiv/client.py 中添加

import pytz
from datetime import datetime, timedelta

def _convert_to_et_range(
    self, 
    from_date: str, 
    to_date: str
) -> tuple[str, str]:
    """
    将日期转换为 arXiv 的 ET 14:00 ~ ET 14:00 时间范围
    
    Args:
        from_date: 开始日期 (YYYYMMDD)
        to_date: 结束日期 (YYYYMMDD)
        
    Returns:
        (from_datetime, to_datetime) 格式为 YYYYMMDDHHmm (UTC)
    """
    et_tz = pytz.timezone('US/Eastern')
    utc_tz = pytz.UTC
    
    # 解析日期
    from_dt = datetime.strptime(from_date, "%Y%m%d")
    to_dt = datetime.strptime(to_date, "%Y%m%d")
    
    # ET 14:00 (下午2点)
    from_et = et_tz.localize(datetime(from_dt.year, from_dt.month, from_dt.day, 14, 0, 0))
    to_et = et_tz.localize(datetime(to_dt.year, to_dt.month, to_dt.day, 14, 0, 0))
    
    # 转换为 UTC
    from_utc = from_et.astimezone(utc_tz)
    to_utc = to_et.astimezone(utc_tz)
    
    # 格式化
    return from_utc.strftime("%Y%m%d%H%M"), to_utc.strftime("%Y%m%d%H%M")
```

#### 修改 3: 更新 `fetch_daily_papers.py` 脚本

```python
# 在 src/scripts/fetch_daily_papers.py 中

async def fetch_papers_for_date(
    self,
    date: datetime,
    categories: Optional[List[str]] = None,
    use_arxiv_schedule: bool = True,  # 新增: 使用 arXiv 的发布时间表
) -> tuple[Dict[str, List[Dict]], Dict[str, str]]:
    """
    获取特定日期的论文
    
    Args:
        date: 论文的发布日期 (arXiv 发布日)
        use_arxiv_schedule: 是否使用 arXiv 的 ET 14:00 机制
    """
    
    if use_arxiv_schedule:
        # 使用 arXiv 的标准时间范围
        # 例如: 获取 2025-11-11 发布的论文
        # 实际时间范围: 2025-11-10 14:00 ET ~ 2025-11-11 14:00 ET
        prev_day = date - timedelta(days=1)
        from_date = prev_day.strftime("%Y%m%d")
        to_date = date.strftime("%Y%m%d")
        
        # 使用 ET 时区转换
        settings = ArxivSettings(search_category=category)
        client = ArxivClient(settings)
        papers, results = await client.fetch_all_papers_in_date_range(
            from_date=from_date,
            to_date=to_date,
            use_et_timezone=True,  # 启用 ET 时区
        )
    else:
        # 使用简单的日期范围 (当天 00:00 ~ 23:59)
        date_str = date.strftime("%Y%m%d")
        papers, results = await client.fetch_all_papers_in_date_range(
            from_date=date_str,
            to_date=date_str,
        )
```

## 🎯 最佳实践建议

### 推荐方案

```python
# 方案 A: 精确匹配 arXiv 发布机制 (最准确) ⭐⭐⭐
# 获取 2025-11-11 发布的论文
# 在 2025-11-12 (或之后) 运行

from datetime import datetime, timedelta
import pytz

def fetch_arxiv_daily_papers(publish_date: str):
    """
    获取指定日期发布的 arXiv 论文
    
    Args:
        publish_date: arXiv 发布日期，格式 YYYY-MM-DD
                      例如 "2025-11-11" 表示 2025-11-11 20:00 ET 发布的论文
    """
    et_tz = pytz.timezone('US/Eastern')
    pub_date = datetime.strptime(publish_date, "%Y-%m-%d")
    
    # 前一天 14:00 ET
    prev_day = pub_date - timedelta(days=1)
    from_time_et = et_tz.localize(datetime(prev_day.year, prev_day.month, prev_day.day, 14, 0, 0))
    
    # 当天 14:00 ET
    to_time_et = et_tz.localize(datetime(pub_date.year, pub_date.month, pub_date.day, 14, 0, 0))
    
    # 转换为 UTC
    from_time_utc = from_time_et.astimezone(pytz.UTC)
    to_time_utc = to_time_et.astimezone(pytz.UTC)
    
    # 格式化为 arXiv API 格式
    from_datetime = from_time_utc.strftime("%Y%m%d%H%M")
    to_datetime = to_time_utc.strftime("%Y%m%d%H%M")
    
    # 构建查询
    search_query = f"cat:cs.AI AND submittedDate:[{from_datetime}+TO+{to_datetime}]"
    
    return from_datetime, to_datetime, search_query

# 使用示例
from_dt, to_dt, query = fetch_arxiv_daily_papers("2025-11-11")
print(f"查询时间范围: {from_dt} ~ {to_dt}")
print(f"查询语句: {query}")

# 输出 (冬令时):
# 查询时间范围: 202511101900 ~ 202511111900
# 查询语句: cat:cs.AI AND submittedDate:[202511101900+TO+202511111900]
```

### 运行时机建议

```python
# 建议 1: 在 arXiv 发布后几小时运行 (最及时)
# 时间: 当天 20:00 ET 之后 (北京时间次日 08:00-09:00)
# 优点: 最快获取新论文
# 缺点: 可能有延迟，数据不一定完全稳定

# 建议 2: 第二天运行 (最稳定) ⭐ 推荐
# 时间: 第二天任意时间
# 优点: 数据完全稳定，保证完整性
# 缺点: 延迟一天

# 建议 3: 使用持续运行模式 (最可靠)
# 每 6-24 小时检查一次，自动获取新论文
# 既保证及时性，又保证完整性

# 推荐的 cron 配置
# 每天北京时间 10:00 运行，获取昨天的论文
0 10 * * * cd /path/to/project && python -m src.scripts.fetch_daily_papers --date yesterday
```

## 📊 各种方案对比

### 日期范围方案对比

| 方案 | from_date | to_date | 准确性 | 复杂度 | 推荐度 |
|-----|-----------|---------|-------|--------|--------|
| **A. ET 14:00 机制** | 前一天 14:00 ET | 当天 14:00 ET | ⭐⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐⭐ |
| B. 整天范围 | 前一天 00:00 | 当天 23:59 | ⭐⭐⭐ | 低 | ⭐⭐⭐ |
| C. 单天范围 | 当天 00:00 | 当天 23:59 | ⭐⭐ | 低 | ⭐⭐ |
| D. 不过滤日期 | - | - | ⭐ | 极低 | ⭐ |

### 字段选择对比

| 字段 | 匹配 arXiv "New" | 包含修订版本 | 包含 Cross-list | 推荐度 |
|-----|-----------------|------------|----------------|--------|
| **submittedDate** | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| published | ❌ | ❌ | ❌ | ⭐⭐ |
| updated | ⚠️ | ✅ | ✅ | ⭐⭐⭐ |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pytz  # 用于时区转换
```

### 2. 使用修改后的代码

```python
from src.services.arxiv.client import ArxivClient
from src.config import ArxivSettings
from datetime import datetime, timedelta

# 获取昨天发布的论文 (推荐)
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

settings = ArxivSettings(search_category="cs.AI")
client = ArxivClient(settings)

# 使用 ET 时区机制
papers, results = await client.fetch_all_papers_in_date_range(
    from_date=yesterday.replace("-", ""),  # YYYYMMDD
    to_date=yesterday.replace("-", ""),
    use_et_timezone=True,  # 启用 arXiv 标准时间
)

print(f"获取到 {len(papers)} 篇论文")
```

## ✅ 总结

### 你的理解

> "获取 20251111 的论文，在 20251112 获取，时间范围 20251110 14:00 ET 到 20251111 14:00 ET"

✅ **完全正确！** 这正是 arXiv 的标准机制。

### 关键要点

1. **使用 `submittedDate` 字段** - 这是 arXiv 发布时使用的字段
2. **时间范围**: 前一天 14:00 ET ~ 当天 14:00 ET
3. **运行时机**: 建议在第二天运行，保证数据完整性
4. **时区转换**: 需要将 ET 转换为 UTC (arXiv API 使用 UTC)

### 代码修改清单

- [ ] 添加时区处理 (`pytz`)
- [ ] 修改 `ArxivClient.fetch_papers()` 支持 ET 时区
- [ ] 添加 `_convert_to_et_range()` 方法
- [ ] 更新 `fetch_daily_papers.py` 使用新机制
- [ ] 添加 `use_arxiv_schedule` 选项
- [ ] 更新文档说明新的日期过滤机制

### 下一步

如果需要，我可以帮你：
1. ✅ 实现完整的时区转换代码
2. ✅ 修改现有的 ArxivClient 类
3. ✅ 更新 fetch_daily_papers.py 脚本
4. ✅ 添加单元测试
5. ✅ 更新文档

只需告诉我你想要哪些修改！🚀
