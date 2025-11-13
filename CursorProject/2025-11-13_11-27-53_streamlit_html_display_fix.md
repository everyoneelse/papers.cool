# Streamlit HTML 显示问题修复

**日期**: 2025-11-13 11:27:53  
**分支**: cursor/debug-streamlit-display-elements-af8d

## 问题描述

在运行 Streamlit 应用后，页面直接显示了 HTML 源代码（包括完整的 `<span>` 标签、style 属性、onmouseover/onmouseout 事件处理器等），而不是渲染成实际的 UI 元素。

具体表现：用户看到的是类似这样的原始 HTML 代码：
```html
<span style="background-color: #E0F7F7; color: #008B8B; border: 2px solid #4ECDC4; ...">
    <span style="font-size: 18px;">🔖</span>
    <span>cs.CL</span>
</span>
```

## 根本原因

问题出在 `render_category_pills()` 函数：

1. **函数返回 HTML 字符串**：原函数构建一个完整的 HTML 字符串并返回
2. **包含 JavaScript 事件**：HTML 中包含了 `onmouseover` 和 `onmouseout` 事件处理器
3. **复杂的 HTML 结构**：Streamlit 的 `st.markdown()` 对复杂 HTML（特别是带 JavaScript）的支持有限

虽然使用了 `unsafe_allow_html=True`，但 Streamlit 无法正确处理这种包含内联 JavaScript 事件的 HTML。

## 解决方案

### 修改前的代码

```python
def render_category_pills(categories: List[str]):
    """渲染 Pills 胶囊式分类标签"""
    pills_html = '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0;">'
    
    # 默认颜色（灰色系）
    default_colors = {"bg": "#F0F0F0", "border": "#BDBDBD", "text": "#424242"}
    
    for cat in categories:
        colors = CATEGORY_COLORS.get(cat, default_colors)
        pills_html += f'''
            <span style="...onmouseover...onmouseout...">
                <span style="font-size: 18px;">🔖</span>
                <span>{cat}</span>
            </span>
        '''
    
    pills_html += '</div>'
    return pills_html

# 调用处
pills_html = render_category_pills(st.session_state.selected_categories)
st.markdown(pills_html, unsafe_allow_html=True)
```

### 修改后的代码

```python
def render_category_pills(categories: List[str]):
    """渲染 Pills 胶囊式分类标签 - 使用Streamlit原生组件"""
    # 默认颜色（灰色系）
    default_colors = {"bg": "#F0F0F0", "border": "#BDBDBD", "text": "#424242"}
    
    # 创建列来显示pills
    cols = st.columns(len(categories))
    
    for idx, cat in enumerate(categories):
        colors = CATEGORY_COLORS.get(cat, default_colors)
        with cols[idx]:
            # 使用Streamlit的markdown显示，但不使用JavaScript事件
            st.markdown(
                f"""
                <div style="
                    background-color: {colors['bg']}; 
                    color: {colors['text']}; 
                    border: 2px solid {colors['border']};
                    padding: 8px 20px; 
                    border-radius: 25px; 
                    font-size: 15px; 
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    margin: 5px 0;
                    white-space: nowrap;
                ">
                    <span style="font-size: 18px;">🔖</span>
                    <span>{cat}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

# 调用处 - 简化为直接调用函数
render_category_pills(st.session_state.selected_categories)
```

## 关键改进

1. **移除 JavaScript 事件**：删除了 `onmouseover` 和 `onmouseout` 事件处理器（Streamlit 不支持）
2. **使用 Streamlit 列布局**：使用 `st.columns()` 创建响应式布局
3. **直接渲染**：函数不再返回 HTML 字符串，而是直接调用 `st.markdown()` 渲染
4. **简化 HTML**：每个 pill 使用更简单的 HTML 结构，仅保留样式

## 修改的文件

- `/workspace/frontend/streamlit_app.py`
  - 第 115-149 行：`render_category_pills()` 函数
  - 第 267-271 行：函数调用处

## 测试建议

运行 Streamlit 应用并验证：
```bash
cd /workspace/frontend
streamlit run streamlit_app.py
```

验证要点：
- ✅ Pills 标签正确渲染为彩色胶囊式按钮
- ✅ 不再显示原始 HTML 代码
- ✅ 每个分类使用正确的颜色主题
- ✅ 布局响应式，多个 pills 水平排列

## 经验总结

1. **Streamlit 的 HTML 限制**：`st.markdown()` 即使使用 `unsafe_allow_html=True` 也不支持内联 JavaScript
2. **优先使用原生组件**：尽可能使用 Streamlit 的原生布局组件（如 `st.columns()`）而不是自定义 HTML
3. **静态样式优先**：如果需要 HTML，只使用静态的 CSS 样式，避免 JavaScript 交互
4. **调试技巧**：如果 HTML 代码被显示为纯文本，通常是 Streamlit 拒绝渲染该 HTML
