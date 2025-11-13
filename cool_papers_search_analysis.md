# Cool Papers 是否利用 arXiv 关键词搜索分析

## 结论

**Cool Papers 没有直接利用 arXiv 的关键词搜索 API，而是使用自己的搜索引擎搜索本地收录的 arXiv 论文数据。**

## 详细分析

### 1. Cool Papers 的搜索实现方式

#### 1.1 自己的搜索引擎

根据 `README.md`（2024.05.05 更新）：
> **增加全站论文搜索**：试上线全站论文搜索功能，搜索本地收录的所有论文，这是基于倒排索引和BM25的搜索引擎，由[tantivy](https://tantivy-py.readthedocs.io/en/latest/)搭建，目前只支持搜索title和summary两个字段，最多显示1000条搜索结果。

**关键信息：**
- 使用 **tantivy**（Rust 编写的搜索引擎库）
- 使用 **BM25** 算法（信息检索排序算法）
- 基于**倒排索引**
- 搜索**本地收录的论文**，不是实时调用 arXiv API
- 只搜索 title 和 summary 两个字段

#### 1.2 本地数据来源

根据 `README.md`（2024.10.17 更新）：
> **整合arXiv历史数据**：数据来自[Kaggle](https://www.kaggle.com/datasets/Cornell-University/arxiv)，整合其中的大部分，使得目前从Cool Papers访问大部分arXiv历史论文都不需要实时爬取了。

**关键信息：**
- Cool Papers 有自己的本地数据库
- 数据来源包括：
  - Kaggle 的 arXiv 数据集（历史数据）
  - 实时爬取 arXiv 的最新论文（用于更新）

### 2. 代码证据

#### 2.1 Chrome 扩展中的搜索跳转

在 `Chrome/background.js` 第74-76行：
```javascript
keywords = info.selectionText.match(/[\p{L}\p{N}]{2,}/gu);
if (keywords) {
    var newUrl = `https://papers.cool/arxiv/search?highlight=1&query=${keywords.join(' ')}`;
    chrome.tabs.create({url: newUrl});
}
```

**分析：**
- 当找不到论文ID时，跳转到 `https://papers.cool/arxiv/search`
- 这是 Cool Papers **自己的搜索页面**，不是 arXiv 的搜索 API
- URL 格式：`papers.cool/arxiv/search?query=关键词`

#### 2.2 没有直接调用 arXiv API

在整个代码库中：
- **没有找到**任何直接调用 `arxiv.org/search` 或 arXiv API 的代码
- **没有找到**任何 HTTP 请求到 arXiv 搜索 API 的代码
- Chrome 扩展只是重定向到 Cool Papers 自己的网站

### 3. 对比：arXiv 官方搜索 vs Cool Papers 搜索

| 特性 | arXiv 官方搜索 | Cool Papers 搜索 |
|------|---------------|------------------|
| **数据来源** | arXiv 实时数据库 | Cool Papers 本地数据库 |
| **搜索范围** | 所有 arXiv 论文（实时） | 本地收录的论文 |
| **搜索字段** | 标题、摘要、作者、全文等 | 标题和摘要（title + summary） |
| **搜索算法** | arXiv 自己的搜索引擎 | BM25 + 倒排索引（tantivy） |
| **结果数量** | 无限制 | 最多 1000 条 |
| **实时性** | 实时 | 取决于本地数据库更新频率 |

### 4. Cool Papers 搜索的优势和限制

#### 优势：
1. **更快的搜索速度**：本地搜索比调用外部 API 更快
2. **更好的搜索体验**：可以自定义搜索界面和功能
3. **离线能力**：不依赖 arXiv 服务器的可用性
4. **搜索优化**：可以使用更先进的搜索算法（BM25）

#### 限制：
1. **数据覆盖**：只搜索本地收录的论文，可能不是所有 arXiv 论文
2. **实时性**：搜索结果可能不是最新的（取决于数据库更新频率）
3. **搜索字段**：只支持标题和摘要，不支持全文搜索
4. **结果数量**：最多显示 1000 条结果

### 5. 总结

**Cool Papers 的搜索机制：**
1. ✅ **有自己的本地数据库**（包含从 arXiv 爬取/下载的论文）
2. ✅ **使用自己的搜索引擎**（基于 tantivy + BM25）
3. ✅ **搜索本地数据**，而不是实时调用 arXiv API
4. ❌ **不直接利用** arXiv 的关键词搜索 API

**工作流程：**
```
用户输入关键词 
  ↓
Cool Papers 前端接收
  ↓
Cool Papers 后端搜索引擎（tantivy + BM25）
  ↓
搜索本地数据库（包含 arXiv 论文数据）
  ↓
返回搜索结果
```

**与 arXiv 的关系：**
- Cool Papers **收集和存储** arXiv 的论文数据
- Cool Papers **不直接调用** arXiv 的搜索 API
- Cool Papers 提供**自己的搜索服务**，基于本地数据
