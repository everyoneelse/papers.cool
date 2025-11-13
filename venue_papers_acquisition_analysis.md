# Cool Papers 会议论文获取方式分析

## 重要说明

**这个仓库只包含前端代码（Chrome扩展和Zotero插件），不包含后端数据获取代码。**

因此，无法从这个仓库直接看到会议论文的实际获取逻辑。但可以从代码和文档中推断出相关信息。

## 1. 支持的会议论文源

根据代码分析，Cool Papers 支持以下会议论文源：

### 1.1 OpenReview
- **网站**：`openreview.net`
- **ID格式**：`{paperId}@OpenReview`
- **代码位置**：`Chrome/background.js` 第32行、44-49行
- **示例**：`https://papers.cool/venue/{paperId}@OpenReview`

### 1.2 ACL Anthology
- **网站**：`aclanthology.org`
- **ID格式**：`{paperId}@ACL`
- **代码位置**：`Chrome/background.js` 第34行、58-63行
- **示例**：`https://papers.cool/venue/{paperId}@ACL`

### 1.3 IJCAI
- **网站**：`ijcai.org/proceedings/`
- **ID格式**：`{paperNumber}@{year}@IJCAI`
- **代码位置**：`Chrome/background.js` 第33行、51-56行
- **示例**：`https://papers.cool/venue/{paperNumber}@{year}@IJCAI`

### 1.4 PMLR (Proceedings of Machine Learning Research)
- **网站**：`proceedings.mlr.press`
- **ID格式**：`{paperId}@{volume}@PMLR`
- **代码位置**：`Chrome/background.js` 第35行、65-70行
- **示例**：`https://papers.cool/venue/{paperId}@{volume}@PMLR`

## 2. 数据获取方式（根据README推断）

### 2.1 人工收集整理

根据 `README.md`（2024.02.10 更新）：
> **增加会议论文列表**：首页增加Venue栏目，收录部分会议论文；**论文由人工收集整理**，原始来源和格式都比较复杂，可能会有错漏之处，敬请谅解，如果发现请反馈。

**关键信息：**
- ✅ **人工收集整理**：不是完全自动化
- ✅ **原始来源复杂**：不同会议有不同的格式和来源
- ⚠️ **可能有错漏**：因为是人工整理

### 2.2 可能的获取方式

基于代码中支持的会议源，可以推断数据可能来自：

1. **OpenReview**
   - 通过爬取 `openreview.net` 网站
   - 提取论文ID、标题、作者、摘要等信息

2. **ACL Anthology**
   - 通过爬取 `aclanthology.org` 网站
   - ACL Anthology 是NLP领域的主要会议论文库

3. **IJCAI**
   - 通过爬取 `ijcai.org/proceedings/` 网站
   - 提取年份和论文编号

4. **PMLR**
   - 通过爬取 `proceedings.mlr.press` 网站
   - PMLR 是机器学习会议的论文集

5. **其他会议**
   - README中提到支持 `AAAI`、`ICML` 等
   - 可能通过各自的官方网站获取

## 3. Chrome扩展的作用

Chrome扩展**不负责获取数据**，而是：

1. **识别论文ID**：从用户浏览的网页中提取论文ID
2. **跳转到Cool Papers**：将用户重定向到Cool Papers的相应页面
3. **支持多个来源**：可以识别不同网站的论文ID格式

### 3.1 代码示例

```javascript
// OpenReview
var OpenReviewPattern = /(?<=openreview\.net\/.*?id=)([A-Za-z0-9]+)/g;
var paperIds = text.match(OpenReviewPattern);
if (paperIds) {
    paperIds = paperIds.map(e => e + '@OpenReview')
    var newUrl = `https://papers.cool/venue/${paperIds.join(',')}`;
    chrome.tabs.create({url: newUrl});
}

// ACL
var ACLPattern = /(?<=aclanthology.org\/)([A-Za-z0-9\-\.]+)(?=(\/|\.pdf))/g;
var paperIds = text.match(ACLPattern);
if (paperIds) {
    paperIds = paperIds.map(e => e + '@ACL')
    var newUrl = `https://papers.cool/venue/${paperIds.join(',')}`;
    chrome.tabs.create({url: newUrl});
}
```

## 4. 数据存储和访问

### 4.1 URL格式

会议论文通过以下URL格式访问：
- `https://papers.cool/venue/{会议名}` - 访问特定会议
- `https://papers.cool/venue/{会议名}.{年份}` - 访问特定年份的会议
- `https://papers.cool/venue/{paperId}@{source}` - 访问特定论文

### 4.2 订阅功能

根据 `README.md`（2024.09.02 更新）：
- 支持通过 `https://papers.cool/venue/{顶会名}/feed` 订阅会议论文
- 支持通过 `https://papers.cool/venue/latest/feed` 订阅最新会议论文

## 5. 总结

### 5.1 这个仓库的作用

这个仓库**只包含前端代码**：
- ✅ Chrome扩展：识别论文ID并跳转
- ✅ Zotero插件：导入论文到Zotero
- ❌ **不包含**后端数据获取代码

### 5.2 数据获取方式（推断）

根据README和代码分析：

1. **人工收集整理**：主要方式
2. **网站爬取**：可能从以下网站获取：
   - OpenReview (openreview.net)
   - ACL Anthology (aclanthology.org)
   - IJCAI (ijcai.org)
   - PMLR (proceedings.mlr.press)
   - 其他会议官方网站

3. **数据存储**：存储在Cool Papers的后端数据库中

4. **访问方式**：通过 `papers.cool/venue/` URL访问

### 5.3 限制

- ⚠️ **数据可能不完整**：因为是人工收集
- ⚠️ **可能有错漏**：README中明确说明
- ⚠️ **格式复杂**：不同会议有不同的格式

## 6. 建议

要了解完整的数据获取流程，需要：
1. 查看Cool Papers的后端代码仓库（如果开源）
2. 联系项目维护者（bojone@spaces.ac.cn）
3. 查看服务器端的爬虫或数据收集脚本
