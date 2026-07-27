# 关于文件关系的问答

## 问题1：implementation_verification.md 和 style_mapper.py 是否重复？

### 答案：不重复，它们有不同的角色

| 文件 | 角色 | 状态 | 用途 |
|------|------|------|------|
| `affective_interaction_mapping.md` | **规范定义** | FROZEN | 定义"应该是什么"（权威规范） |
| `style_mapper.py` | **代码实现** | ACTIVE | 实现规范（可执行代码） |
| `implementation_verification.md` | **验证报告** | VERIFICATION | 验证实现是否正确（检查清单） |

### 关系图

```
规范层（FROZEN）
  ↓
affective_interaction_mapping.md  ← 这是基准！
  ↓
实现层（ACTIVE）
  ↓
style_mapper.py  ← 实现规范
  ↓
验证层（VERIFICATION）
  ↓
implementation_verification.md  ← 验证实现是否正确
```

## 问题2：可以以实施确认为基准吗？

### 答案：不可以，应该以规范文件为基准

**正确的基准层级**：

1. **第一优先级（规范基准）**：`specs/affective_interaction_mapping.md`
   - 这是冻结的规范文件
   - 定义了7-level映射的完整规范
   - 所有实现必须遵循它

2. **第二优先级（实现）**：`rstm/style_mapper.py`
   - 这是代码实现
   - 必须严格遵循规范文件
   - 不应该以验证文档为基准

3. **第三优先级（验证）**：`specs/implementation_verification.md`
   - 这是验证报告
   - 用于检查实现是否符合规范
   - 不是规范定义，不能作为基准

### 为什么不能以验证文档为基准？

1. **验证文档是检查清单**：它只说明"实现是否正确"，不定义"应该是什么"
2. **验证文档依赖规范**：它验证的是实现是否符合规范，而不是定义规范
3. **规范文件是权威来源**：只有冻结的规范文件才是权威定义

## 建议的文件引用关系

### 在代码中应该这样引用：

```python
"""
风格映射器

本实现严格遵循 specs/affective_interaction_mapping.md 规范（冻结文件）

规范基准：specs/affective_interaction_mapping.md（FROZEN）
验证文档：specs/implementation_verification.md（用于验证实现是否正确）
"""
```

### 不应该这样引用：

```python
# ❌ 错误：不应该以验证文档为基准
"""
本实现遵循 implementation_verification.md 的要求
"""
```

## 总结

1. **规范文件是基准**：`affective_interaction_mapping.md` 是权威规范
2. **实现文件遵循规范**：`style_mapper.py` 必须遵循规范文件
3. **验证文件检查实现**：`implementation_verification.md` 用于验证实现是否正确
4. **不要混淆角色**：验证文档不是规范定义，不能作为基准

## 文件维护建议

当需要更新时：

1. **规范文件（FROZEN）**：
   - 只有在研究需要时才更新
   - 更新后需要更新版本号
   - 更新后需要重新验证实现

2. **实现文件（ACTIVE）**：
   - 当规范更新时，必须同步更新
   - 确保实现符合最新规范

3. **验证文件（VERIFICATION）**：
   - 当规范或实现更新时，需要重新验证
   - 更新验证结果

