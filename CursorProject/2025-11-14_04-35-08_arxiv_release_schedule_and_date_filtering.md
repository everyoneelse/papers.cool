# arXiv 发布节奏与日期过滤机制详解

## 📅 arXiv 的发布节奏

根据 arXiv 官方的发布机制：

### 发布时间表

```
时间: 工作日每天 20:00 ET (美国东部时间)
内容: 上一个工作日 14:00 ET 到当前工作日 14:00 ET 之间提交/更新的论文

⚠️ 重要: arXiv 在周末 (周六、周日) 不发布新论文！
```

### 详细的每周发布时间表

```
┌─────────────────────────────────────────────────────────────────────┐
│ 周日 (Sunday)                                                        │
│ - 无发布                                                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 周一 (Monday) 20:00 ET 发布 ⭐ 特殊情况！                            │
│ - 包含: 周五 14:00 ET ~ 周一 14:00 ET (跨越 3 天)                   │
│ - 原因: 周末不发布，周一要把周六日的论文一起发布                      │
│ - 论文数量: 通常是平时的 3 倍                                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 周二 (Tuesday) 20:00 ET 发布                                         │
│ - 包含: 周一 14:00 ET ~ 周二 14:00 ET (1 天)                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 周三 (Wednesday) 20:00 ET 发布                                       │
│ - 包含: 周二 14:00 ET ~ 周三 14:00 ET (1 天)                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 周四 (Thursday) 20:00 ET 发布                                        │
│ - 包含: 周三 14:00 ET ~ 周四 14:00 ET (1 天)                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 周五 (Friday) 20:00 ET 发布                                          │
│ - 包含: 周四 14:00 ET ~ 周五 14:00 ET (1 天)                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 周六 (Saturday)                                                      │
│ - 无发布                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 实际示例

```
2025-11-10 (周一) 20:00 ET 发布:
├─ 时间范围: 2025-11-07 (周五) 14:00 ET ~ 2025-11-10 (周一) 14:00 ET
├─ 跨越天数: 3 天 (周五下午 + 周六全天 + 周日全天 + 周一上午)
├─ 论文数量: ~1500 篇 (约为平时的 3 倍)
└─ 称为: "2025-11-10" 的论文

2025-11-11 (周二) 20:00 ET 发布:
├─ 时间范围: 2025-11-10 (周一) 14:00 ET ~ 2025-11-11 (周二) 14:00 ET
├─ 跨越天数: 1 天
├─ 论文数量: ~500 篇 (正常数量)
└─ 称为: "2025-11-11" 的论文

2025-11-12 (周三) 20:00 ET 发布:
├─ 时间范围: 2025-11-11 (周二) 14:00 ET ~ 2025-11-12 (周三) 14:00 ET
├─ 跨越天数: 1 天
├─ 论文数量: ~500 篇
└─ 称为: "2025-11-12" 的论文
```

### 时区对照

```
美国东部时间 (ET)      北京时间 (UTC+8)           说明
─────────────────────────────────────────────────────────────────
周五 14:00            周六 02:00 (冬令时)        周末提交窗口开始
                      周六 03:00 (夏令时)        
周一 14:00            周二 02:00 (冬令时)        周末提交窗口结束
                      周二 03:00 (夏令时)
周一 20:00            周二 08:00 (冬令时)        周一发布 (包含周末)
                      周二 09:00 (夏令时)
```

**注意**: 
- ET = Eastern Time，包含 EST (东部标准时间) 和 EDT (东部夏令时)
- 美国夏令时: 3月第2个周日 ~ 11月第1个周日
- arXiv 在美国节假日也可能不发布，需要特殊处理

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

#### 修改 2: 添加时区转换工具函数（支持周末逻辑）⭐

```python
# 在 src/services/arxiv/client.py 中添加

import pytz
from datetime import datetime, timedelta

def _get_arxiv_submission_window(
    self,
    publish_date: str
) -> tuple[str, str]:
    """
    根据 arXiv 的发布机制，计算论文提交窗口的时间范围
    自动处理周末逻辑：周一需要回溯到周五
    
    Args:
        publish_date: arXiv 发布日期 (YYYYMMDD)
                      例如 "20251110" 表示 2025-11-10 20:00 ET 发布的论文
        
    Returns:
        (from_datetime, to_datetime) 格式为 YYYYMMDDHHmm (UTC)
        
    Examples:
        # 周二到周五 (正常情况)
        _get_arxiv_submission_window("20251111")  # 周二
        # 返回: 周一 14:00 ET ~ 周二 14:00 ET
        
        # 周一 (特殊情况：包含周末)
        _get_arxiv_submission_window("20251110")  # 周一
        # 返回: 周五 14:00 ET ~ 周一 14:00 ET (跨越 3 天)
    """
    et_tz = pytz.timezone('US/Eastern')
    utc_tz = pytz.UTC
    
    # 解析发布日期
    pub_date = datetime.strptime(publish_date, "%Y%m%d")
    
    # 获取星期几 (0=Monday, 1=Tuesday, ..., 6=Sunday)
    weekday = pub_date.weekday()
    
    # 计算提交窗口的开始日期
    if weekday == 0:  # Monday (周一)
        # 周一发布的论文，窗口从上周五 14:00 ET 开始
        days_back = 3  # 回到周五
        logger.info(f"Monday detected: {publish_date}, going back 3 days to Friday")
    elif weekday in [1, 2, 3, 4]:  # Tuesday to Friday (周二到周五)
        # 正常情况：前一天 14:00 ET
        days_back = 1
    elif weekday in [5, 6]:  # Saturday or Sunday (周六或周日)
        # arXiv 不在周末发布！这应该是错误的日期
        logger.warning(f"arXiv does not publish on weekends! Date: {publish_date}")
        # 如果是周六，回到周五；如果是周日，回到周五
        days_back = weekday - 4  # 周六->1天, 周日->2天
    else:
        days_back = 1  # 默认回退1天
    
    # 计算窗口开始时间 (前 N 个工作日的 14:00 ET)
    from_date = pub_date - timedelta(days=days_back)
    from_et = et_tz.localize(datetime(from_date.year, from_date.month, from_date.day, 14, 0, 0))
    
    # 计算窗口结束时间 (当天 14:00 ET)
    to_et = et_tz.localize(datetime(pub_date.year, pub_date.month, pub_date.day, 14, 0, 0))
    
    # 转换为 UTC
    from_utc = from_et.astimezone(utc_tz)
    to_utc = to_et.astimezone(utc_tz)
    
    # 格式化
    from_str = from_utc.strftime("%Y%m%d%H%M")
    to_str = to_utc.strftime("%Y%m%d%H%M")
    
    logger.info(
        f"arXiv submission window for {publish_date} ({_get_weekday_name(weekday)}): "
        f"{from_str} ~ {to_str} UTC (span: {days_back} days)"
    )
    
    return from_str, to_str

def _get_weekday_name(weekday: int) -> str:
    """获取星期几的名称"""
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[weekday]

def _convert_to_et_range(
    self, 
    from_date: str, 
    to_date: str
) -> tuple[str, str]:
    """
    将日期转换为 arXiv 的 ET 14:00 ~ ET 14:00 时间范围
    ⚠️ 这个方法不处理周末逻辑，建议使用 _get_arxiv_submission_window()
    
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
# 方案 A: 精确匹配 arXiv 发布机制 (最准确，支持周末逻辑) ⭐⭐⭐⭐⭐
# 自动处理周一的特殊情况

from datetime import datetime, timedelta
import pytz

def get_arxiv_submission_window(publish_date: str) -> tuple[str, str, str]:
    """
    根据 arXiv 的发布机制，计算论文提交窗口的时间范围
    自动处理周末逻辑：周一需要回溯到周五
    
    Args:
        publish_date: arXiv 发布日期，格式 YYYY-MM-DD
                      例如 "2025-11-11" 表示 2025-11-11 20:00 ET 发布的论文
        
    Returns:
        (from_datetime, to_datetime, search_query) 元组
    """
    et_tz = pytz.timezone('US/Eastern')
    pub_date = datetime.strptime(publish_date, "%Y-%m-%d")
    
    # 获取星期几 (0=Monday, 1=Tuesday, ..., 6=Sunday)
    weekday = pub_date.weekday()
    
    # 计算提交窗口的开始日期
    if weekday == 0:  # Monday (周一)
        # 周一发布的论文，窗口从上周五 14:00 ET 开始
        days_back = 3  # 回到周五
        print(f"⚠️ Monday detected! Going back 3 days to Friday (includes weekend)")
    elif weekday in [1, 2, 3, 4]:  # Tuesday to Friday (周二到周五)
        # 正常情况：前一天 14:00 ET
        days_back = 1
    elif weekday in [5, 6]:  # Saturday or Sunday (周六或周日)
        # arXiv 不在周末发布！
        raise ValueError(f"arXiv does not publish on weekends! Invalid date: {publish_date}")
    else:
        days_back = 1  # 默认
    
    # 计算窗口开始时间
    from_date = pub_date - timedelta(days=days_back)
    from_time_et = et_tz.localize(datetime(from_date.year, from_date.month, from_date.day, 14, 0, 0))
    
    # 计算窗口结束时间 (当天 14:00 ET)
    to_time_et = et_tz.localize(datetime(pub_date.year, pub_date.month, pub_date.day, 14, 0, 0))
    
    # 转换为 UTC
    from_time_utc = from_time_et.astimezone(pytz.UTC)
    to_time_utc = to_time_et.astimezone(pytz.UTC)
    
    # 格式化为 arXiv API 格式
    from_datetime = from_time_utc.strftime("%Y%m%d%H%M")
    to_datetime = to_time_utc.strftime("%Y%m%d%H%M")
    
    # 构建查询
    search_query = f"submittedDate:[{from_datetime}+TO+{to_datetime}]"
    
    return from_datetime, to_datetime, search_query

# 使用示例 1: 周二 (正常情况)
print("=" * 60)
print("Example 1: Tuesday (Normal case)")
from_dt, to_dt, query = get_arxiv_submission_window("2025-11-11")  # 周二
print(f"发布日期: 2025-11-11 (Tuesday)")
print(f"查询时间: {from_dt} ~ {to_dt}")
print(f"跨越天数: 1 天")
print(f"查询语句: {query}")

# 输出 (冬令时):
# 发布日期: 2025-11-11 (Tuesday)
# 查询时间: 202511101900 ~ 202511111900
# 跨越天数: 1 天
# 查询语句: submittedDate:[202511101900+TO+202511111900]

# 使用示例 2: 周一 (特殊情况 - 包含周末)
print("\n" + "=" * 60)
print("Example 2: Monday (Special case - includes weekend)")
from_dt, to_dt, query = get_arxiv_submission_window("2025-11-10")  # 周一
print(f"⚠️ Monday detected! Going back 3 days to Friday (includes weekend)")
print(f"发布日期: 2025-11-10 (Monday)")
print(f"查询时间: {from_dt} ~ {to_dt}")
print(f"跨越天数: 3 天 (周五下午 + 周六全天 + 周日全天 + 周一上午)")
print(f"查询语句: {query}")

# 输出 (冬令时):
# 发布日期: 2025-11-10 (Monday)
# 查询时间: 202511071900 ~ 202511101900
# 跨越天数: 3 天 (周五下午 + 周六全天 + 周日全天 + 周一上午)
# 查询语句: submittedDate:[202511071900+TO+202511101900]

# 使用示例 3: 完整的 API 查询
print("\n" + "=" * 60)
print("Example 3: Complete API query")

from_dt, to_dt, date_query = get_arxiv_submission_window("2025-11-10")  # 周一
category = "cs.AI"
complete_query = f"cat:{category} AND {date_query}"
print(f"完整查询: {complete_query}")

# 输出:
# 完整查询: cat:cs.AI AND submittedDate:[202511071900+TO+202511101900]
```

### 周末的完整示例

```python
# 一周的完整示例（2025-11-10 到 2025-11-16）

from datetime import datetime, timedelta

base_date = datetime(2025, 11, 10)  # 周一

print("=" * 80)
print("arXiv 一周的发布时间表 (2025-11-10 ~ 2025-11-16)")
print("=" * 80)

for i in range(7):
    date = base_date + timedelta(days=i)
    date_str = date.strftime("%Y-%m-%d")
    weekday = date.weekday()
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_name = weekday_names[weekday]
    
    print(f"\n{date_str} ({weekday_name})")
    
    if weekday in [5, 6]:  # Weekend
        print("  ❌ No publication (Weekend)")
    else:
        try:
            from_dt, to_dt, _ = get_arxiv_submission_window(date_str)
            
            # 计算跨越天数
            from_date = datetime.strptime(from_dt[:8], "%Y%m%d")
            to_date = datetime.strptime(to_dt[:8], "%Y%m%d")
            days_span = (to_date - from_date).days
            
            if weekday == 0:  # Monday
                print(f"  ⭐ Publication at 20:00 ET (includes weekend!)")
                print(f"  📅 Window: {from_dt} ~ {to_dt} UTC")
                print(f"  ⏱️  Span: {days_span} days (Friday 14:00 ET ~ Monday 14:00 ET)")
                print(f"  📊 Expected papers: ~1500 (3x normal)")
            else:
                print(f"  ✅ Publication at 20:00 ET")
                print(f"  📅 Window: {from_dt} ~ {to_dt} UTC")
                print(f"  ⏱️  Span: {days_span} day")
                print(f"  📊 Expected papers: ~500")
        except ValueError as e:
            print(f"  ❌ {e}")

# 输出示例:
# ================================================================================
# arXiv 一周的发布时间表 (2025-11-10 ~ 2025-11-16)
# ================================================================================
#
# 2025-11-10 (Monday)
#   ⭐ Publication at 20:00 ET (includes weekend!)
#   📅 Window: 202511071900 ~ 202511101900 UTC
#   ⏱️  Span: 3 days (Friday 14:00 ET ~ Monday 14:00 ET)
#   📊 Expected papers: ~1500 (3x normal)
#
# 2025-11-11 (Tuesday)
#   ✅ Publication at 20:00 ET
#   📅 Window: 202511101900 ~ 202511111900 UTC
#   ⏱️  Span: 1 day
#   📊 Expected papers: ~500
#
# 2025-11-12 (Wednesday)
#   ✅ Publication at 20:00 ET
#   📅 Window: 202511111900 ~ 202511121900 UTC
#   ⏱️  Span: 1 day
#   📊 Expected papers: ~500
#
# ... (以此类推)
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

> "这个时间要根据星期来变化，因为 arXiv 在周末是不更新的，所以周一要将周六周日的加上"

✅ **非常正确！** 这是关键点！周一需要特殊处理。

### 关键要点

1. **使用 `submittedDate` 字段** - 这是 arXiv 发布时使用的字段
2. **时间范围**: 
   - **周二到周五**: 前一天 14:00 ET ~ 当天 14:00 ET (1天)
   - **周一 (特殊!)**: 上周五 14:00 ET ~ 周一 14:00 ET (3天) ⭐
   - **周末**: 不发布
3. **运行时机**: 建议在第二天运行，保证数据完整性
4. **时区转换**: 需要将 ET 转换为 UTC (arXiv API 使用 UTC)
5. **周末处理**: 必须根据星期几计算回退天数 (周一=3天，其他=1天)

### 代码修改清单

- [ ] 添加时区处理 (`pytz`)
- [ ] 修改 `ArxivClient.fetch_papers()` 支持 ET 时区
- [ ] 添加 `_get_arxiv_submission_window()` 方法 ⭐ **支持周末逻辑**
- [ ] 添加周末检测逻辑 (周一回退3天，其他回退1天)
- [ ] 更新 `fetch_daily_papers.py` 使用新机制
- [ ] 添加 `use_arxiv_schedule` 选项
- [ ] 更新文档说明新的日期过滤机制

## 🎊 关于节假日的额外说明

### 美国联邦节假日

arXiv 在美国联邦节假日也不发布论文。主要节假日包括：

```
1月1日        - New Year's Day (元旦)
1月第3个周一   - Martin Luther King Jr. Day
2月第3个周一   - Presidents' Day
5月最后一个周一 - Memorial Day (阵亡将士纪念日)
7月4日        - Independence Day (美国独立日)
9月第1个周一   - Labor Day (劳动节)
10月第2个周一  - Columbus Day
11月11日      - Veterans Day (退伍军人节)
11月第4个周四  - Thanksgiving (感恩节)
12月25日      - Christmas Day (圣诞节)
```

### 节假日后的发布

如果节假日在工作日，那么节假日后的第一个工作日会包含更多天的论文。

```
示例 1: 周一是节假日 (例如 Labor Day)
─────────────────────────────────────────
周五 (9月1日): 正常发布 (周四 14:00 ~ 周五 14:00)
周六 (9月2日): 无发布
周日 (9月3日): 无发布
周一 (9月4日): 节假日，无发布 ❌
周二 (9月5日): 发布，包含 4 天！ ⭐
                (周五 14:00 ~ 周二 14:00)

示例 2: 周四周五是节假日 (例如 Thanksgiving 周四 + 周五)
─────────────────────────────────────────
周三 (11月22日): 正常发布 (周二 14:00 ~ 周三 14:00)
周四 (11月23日): Thanksgiving，无发布 ❌
周五 (11月24日): Black Friday，通常也无发布 ❌
周六 (11月25日): 无发布
周日 (11月26日): 无发布
周一 (11月27日): 发布，包含 5 天！ ⭐⭐
                (周三 14:00 ~ 周一 14:00)
```

### 代码实现建议

```python
# 可以添加节假日检测
from datetime import date
import holidays

def get_arxiv_submission_window_with_holidays(publish_date: str):
    """
    考虑美国节假日的 arXiv 发布窗口计算
    """
    us_holidays = holidays.US()
    pub_date = datetime.strptime(publish_date, "%Y-%m-%d")
    
    # 往前找最近的工作日 (非周末、非节假日)
    current = pub_date - timedelta(days=1)
    while current.weekday() in [5, 6] or current in us_holidays:
        current -= timedelta(days=1)
    
    # current 就是上一个工作日
    from_date = current
    
    # ... 继续计算时间范围
```

**注意**: 目前的实现只处理周末，不处理节假日。如果需要完整的节假日支持，需要添加 `holidays` 库。

## 📋 快速参考表

### 每日发布时间窗口速查表

| 发布日 | 星期 | 提交窗口开始 | 提交窗口结束 | 回退天数 | 预期论文数量 | 说明 |
|-------|------|-----------|-----------|---------|------------|------|
| 11月10日 | 周一 | 11月07日 14:00 ET | 11月10日 14:00 ET | 3天 | ~1500篇 | ⭐ 包含周末 |
| 11月11日 | 周二 | 11月10日 14:00 ET | 11月11日 14:00 ET | 1天 | ~500篇 | 正常 |
| 11月12日 | 周三 | 11月11日 14:00 ET | 11月12日 14:00 ET | 1天 | ~500篇 | 正常 |
| 11月13日 | 周四 | 11月12日 14:00 ET | 11月13日 14:00 ET | 1天 | ~500篇 | 正常 |
| 11月14日 | 周五 | 11月13日 14:00 ET | 11月14日 14:00 ET | 1天 | ~500篇 | 正常 |
| 11月15日 | 周六 | - | - | - | - | ❌ 无发布 |
| 11月16日 | 周日 | - | - | - | - | ❌ 无发布 |

### API 查询格式速查

```python
# 格式: cat:{category} AND submittedDate:[{from}+TO+{to}]

# 周二 (2025-11-11) - 正常情况
cat:cs.AI AND submittedDate:[202511101900+TO+202511111900]

# 周一 (2025-11-10) - 包含周末
cat:cs.AI AND submittedDate:[202511071900+TO+202511101900]
```

### 常见问题速查

| 问题 | 答案 |
|-----|------|
| 使用哪个日期字段？ | `submittedDate` ⭐ |
| 周一的时间范围？ | 周五 14:00 ET ~ 周一 14:00 ET (3天) |
| 周二到周五的时间范围？ | 前一天 14:00 ET ~ 当天 14:00 ET (1天) |
| 周末发布吗？ | ❌ 不发布 |
| 节假日发布吗？ | ❌ 不发布 |
| ET 与 UTC 的时差？ | 冬令时 -5h，夏令时 -4h |
| 何时获取最稳定？ | 第二天运行 ⭐ |

### 代码片段速查

```python
# 1. 检测星期几
weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday

# 2. 计算回退天数
days_back = 3 if weekday == 0 else 1  # 周一回退3天，其他回退1天

# 3. ET 转 UTC
et_tz = pytz.timezone('US/Eastern')
from_et = et_tz.localize(datetime(2025, 11, 10, 14, 0, 0))
from_utc = from_et.astimezone(pytz.UTC)
```

### 下一步

如果需要，我可以帮你：
1. ✅ 实现完整的时区转换代码（已提供）
2. ✅ 实现周末逻辑支持（已提供）
3. ✅ 添加节假日检测功能
4. ✅ 修改现有的 ArxivClient 类
5. ✅ 更新 fetch_daily_papers.py 脚本
6. ✅ 添加单元测试
7. ✅ 更新文档

只需告诉我你想要哪些修改！🚀
