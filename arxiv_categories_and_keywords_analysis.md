# arXiv分类和关键词支持分析

## 1. 分类类别

### 1.1 支持的分类是arXiv官方的吗？

**是的，Cool Papers使用的分类类别完全基于arXiv官方的分类系统。**

证据：
- 在 `README.md` 中明确提到："根据arXiv官方的注释[[来源](https://arxiv.org/category_taxonomy)]，类别[cs.NA, cs.SY, math.IT, math.MP, q-fin.EC, stat.TH]实际上是[math.NA, eess.SY, cs.IT, math-ph, econ.GN, math.ST]的别名"
- 代码中使用的分类如 `cs.AI`, `cs.CL`, `cs.CV`, `cs.LG` 等都是arXiv的标准分类代码
- `Zotero/CoolPapers.js` 中第50行显示：`item.extra = subject.href.split("/").at(-1) + " - arXiv";` 表明分类信息直接来自arXiv

### 1.2 arXiv分类系统

arXiv使用标准的分类代码格式，主要包括：
- **计算机科学**：`cs.AI`, `cs.CL`, `cs.CV`, `cs.LG`, `cs.IT` 等
- **数学**：`math.NA`, `math-ph`, `math.ST` 等
- **经济学**：`econ.GN` 等
- **统计学**：`stat.TH` 等
- **电气工程与系统科学**：`eess.SY` 等

完整的分类列表可以在 [arXiv分类分类法](https://arxiv.org/category_taxonomy) 查看。

## 2. 关键词搜索

### 2.1 arXiv是否支持关键词搜索？

**是的，arXiv官方支持关键词搜索功能。**

证据：
- arXiv网站提供搜索功能，支持多种搜索字段：
  - All fields（所有字段）
  - Title（标题）
  - Author（作者）
  - Abstract（摘要）
  - Comments（评论）
  - Full text（全文）
  - 等等

- arXiv API支持搜索查询，可以通过 `query` 参数进行关键词搜索
- 示例：`https://arxiv.org/search/?query=neural+network&searchtype=all`

### 2.2 Cool Papers中的关键词搜索

在 `Chrome/background.js` 中（第74-76行），当找不到论文ID时，会使用选中的文本作为关键词进行搜索：

```javascript
keywords = info.selectionText.match(/[\p{L}\p{N}]{2,}/gu);
if (keywords) {
    var newUrl = `https://papers.cool/arxiv/search?highlight=1&query=${keywords.join(' ')}`;
    chrome.tabs.create({url: newUrl});
}
```

这表明Cool Papers实现了自己的关键词搜索功能，基于arXiv的数据进行搜索。

## 总结

1. **分类类别**：Cool Papers完全使用arXiv官方的分类系统，所有分类代码都来自arXiv的标准分类法。

2. **关键词搜索**：
   - arXiv官方支持关键词搜索（通过网站和API）
   - Cool Papers实现了自己的关键词搜索功能，基于arXiv数据
   - 支持在标题、摘要、作者等多个字段中搜索关键词
