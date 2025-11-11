# 支持的会议论文源 - 代码详解

## 代码位置

识别会议论文源的代码主要在两个文件中：

1. **`Chrome/background.js`** - Chrome扩展的后台脚本（右键菜单功能）
2. **`Chrome/content.js`** - Chrome扩展的内容脚本（在网页中插入链接）

---

## 1. Chrome/background.js 中的代码

### 1.1 OpenReview 支持

**代码位置**：第32行、44-49行

```javascript
// 第32行：定义正则表达式模式
var OpenReviewPattern = /(?<=openreview\.net\/.*?id=)([A-Za-z0-9]+)/g;

// 第44-49行：匹配并跳转
var paperIds = text.match(OpenReviewPattern);
if (paperIds) {
    paperIds = paperIds.map(e => e + '@OpenReview')
    var newUrl = `https://papers.cool/venue/${paperIds.join(',')}`;
    chrome.tabs.create({url: newUrl});
    return;
}
```

**功能**：
- 从URL或文本中提取OpenReview论文ID
- 格式：`{paperId}@OpenReview`
- 示例：`https://papers.cool/venue/abc123@OpenReview`

---

### 1.2 ACL Anthology 支持

**代码位置**：第34行、58-63行

```javascript
// 第34行：定义正则表达式模式
var ACLPattern = /(?<=aclanthology.org\/)([A-Za-z0-9\-\.]+)(?=(\/|\.pdf))/g;

// 第58-63行：匹配并跳转
var paperIds = text.match(ACLPattern);
if (paperIds) {
    paperIds = paperIds.map(e => e + '@ACL')
    var newUrl = `https://papers.cool/venue/${paperIds.join(',')}`;
    chrome.tabs.create({url: newUrl});
    return;
}
```

**功能**：
- 从URL中提取ACL Anthology论文ID
- 格式：`{paperId}@ACL`
- 示例：`https://papers.cool/venue/P19-1001@ACL`

---

### 1.3 IJCAI 支持

**代码位置**：第33行、51-56行

```javascript
// 第33行：定义正则表达式模式
var IJCAIPattern = /(?<=ijcai\.org\/proceedings\/)(\d+)\/(\d+)/g;

// 第51-56行：匹配并跳转
var paperIds = text.match(IJCAIPattern);
if (paperIds) {
    paperIds = paperIds.map(e => e.split('/')[1].replace(/^0+/, '') + '@' + e.split('/')[0] + '@IJCAI')
    var newUrl = `https://papers.cool/venue/${paperIds.join(',')}`;
    chrome.tabs.create({url: newUrl});
    return;
}
```

**功能**：
- 从URL中提取IJCAI论文编号和年份
- 格式：`{paperNumber}@{year}@IJCAI`
- 示例：`https://papers.cool/venue/123@2023@IJCAI`
- URL格式：`ijcai.org/proceedings/2023/123`

---

### 1.4 PMLR 支持

**代码位置**：第35行、65-70行

```javascript
// 第35行：定义正则表达式模式
var PMLRPattern = /(?<=proceedings\.mlr\.press\/)(v\d+)\/([A-Za-z0-9\-]+)(?=\.html)/g;

// 第65-70行：匹配并跳转
var paperIds = text.match(PMLRPattern);
if (paperIds) {
    paperIds = paperIds.map(e => e.split('/')[1] + '@' + e.split('/')[0] + '@PMLR')
    var newUrl = `https://papers.cool/venue/${paperIds.join(',')}`;
    chrome.tabs.create({url: newUrl});
    return;
}
```

**功能**：
- 从URL中提取PMLR论文ID和卷号
- 格式：`{paperId}@{volume}@PMLR`
- 示例：`https://papers.cool/venue/paper123@v202@PMLR`
- URL格式：`proceedings.mlr.press/v202/paper123.html`

---

## 2. Chrome/content.js 中的代码

### 2.1 OpenReview 网页注入

**代码位置**：第15-32行

```javascript
// 第15行：检测是否在OpenReview网站
} else if (url.match(/openreview\.net\//g)) {
    var div = document.querySelector('div.col-xs-12');
    var a = document.createElement('a');
    a.href = '';
    a.style = 'display:inline;float:right';
    a.onclick = function() {
        var url = window.location.href;
        // 第22-24行：单个论文页面
        if (url.match(/(?<=openreview\.net\/forum\?id=)([A-Za-z0-9]+)/g)) {
            var paperId = url.match(/(?<=openreview\.net\/forum\?id=)([A-Za-z0-9]+)/g)[0];
            window.open(`https://papers.cool/venue/${paperId}@OpenReview`, '_blank');
        // 第25-28行：论文列表页面
        } else if (url.match(/openreview\.net\/group/g)) {
            var content = document.querySelector('body').innerHTML;
            var paperIds = content.match(/(?<=href="\/forum\?id=)([A-Za-z0-9]+)/g).map(e => e + '@OpenReview');
            window.open(`https://papers.cool/venue/${paperIds.join(',')}`, '_blank');
        }
    };
    a.innerText = '[Cool Papers]';
    div.appendChild(a);
}
```

**功能**：
- 在OpenReview网页上插入 `[Cool Papers]` 链接
- 点击后跳转到Cool Papers的相应页面
- 支持单个论文和论文列表

---

### 2.2 ACL Anthology 网页注入

**代码位置**：第33-37行

```javascript
// 第33行：检测是否在ACL Anthology网站
} else if (url.match(/(?<=aclanthology.org\/)([A-Za-z0-9\-\.]+)(?=\/)/g)) {
    var paperId = url.match(/(?<=aclanthology.org\/)([A-Za-z0-9\-\.]+)(?=\/)/g)[0];
    var div = document.querySelector('div.acl-paper-link-block');
    // 第36行：插入Cool Papers链接按钮
    div.innerHTML += `<a class="btn btn-secondary" href="https://papers.cool/venue/${paperId}@ACL" target="_blank"><span class="pl-sm-2 d-none d-sm-inline">Cool Papers</span></a>`;
}
```

**功能**：
- 在ACL Anthology论文页面插入Cool Papers按钮
- 点击后在新标签页打开Cool Papers

---

## 3. 完整的代码流程

### 3.1 右键菜单流程（background.js）

```
用户右键点击
    ↓
chrome.contextMenus.onClicked 触发
    ↓
检查文本/URL中是否包含论文ID
    ↓
按顺序匹配：
  1. arXiv (第31行)
  2. OpenReview (第32行)
  3. IJCAI (第33行)
  4. ACL (第34行)
  5. PMLR (第35行)
    ↓
找到匹配后，跳转到 papers.cool
    ↓
如果都没找到，使用关键词搜索（第74-77行）
```

### 3.2 网页注入流程（content.js）

```
用户访问论文网站
    ↓
content.js 检测URL
    ↓
匹配网站类型：
  - arxiv.org (第3行)
  - openreview.net (第15行)
  - aclanthology.org (第33行)
    ↓
在网页中插入Cool Papers链接
    ↓
用户点击链接跳转
```

---

## 4. 代码总结

### 4.1 支持的会议源（从代码中识别）

| 会议源 | 代码文件 | 行号 | 正则表达式 | ID格式 |
|--------|---------|------|-----------|--------|
| **OpenReview** | background.js | 32, 44-49 | `/(?<=openreview\.net\/.*?id=)([A-Za-z0-9]+)/g` | `{id}@OpenReview` |
| | content.js | 15-32 | `/(?<=openreview\.net\/forum\?id=)([A-Za-z0-9]+)/g` | |
| **ACL** | background.js | 34, 58-63 | `/(?<=aclanthology.org\/)([A-Za-z0-9\-\.]+)(?=(\/|\.pdf))/g` | `{id}@ACL` |
| | content.js | 33-37 | `/(?<=aclanthology.org\/)([A-Za-z0-9\-\.]+)(?=\/)/g` | |
| **IJCAI** | background.js | 33, 51-56 | `/(?<=ijcai\.org\/proceedings\/)(\d+)\/(\d+)/g` | `{num}@{year}@IJCAI` |
| **PMLR** | background.js | 35, 65-70 | `/(?<=proceedings\.mlr\.press\/)(v\d+)\/([A-Za-z0-9\-]+)(?=\.html)/g` | `{id}@{vol}@PMLR` |

### 4.2 代码功能

1. **识别论文ID**：使用正则表达式从URL或文本中提取论文ID
2. **格式化ID**：将不同格式的ID转换为Cool Papers的统一格式
3. **跳转链接**：创建跳转到Cool Papers的URL
4. **网页注入**：在支持的网站上插入Cool Papers链接

### 4.3 代码限制

- ⚠️ **只识别ID**：代码只负责识别和跳转，不负责获取数据
- ⚠️ **前端代码**：这些代码运行在浏览器中，不涉及后端数据获取
- ⚠️ **格式固定**：如果会议网站格式改变，正则表达式可能需要更新
