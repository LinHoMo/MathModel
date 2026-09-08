# 问题追踪清单

**项目名称:** {{PROJECT_NAME}}
**生成日期:** {{DATE}}
**更新日期:** {{UPDATE_DATE}}

---

## 一、统计摘要

### 1.1 按级别统计

| 级别 | 数量 | 已解决 | 待处理 |
|------|------|--------|--------|
| Critical | {{CRITICAL_TOTAL}} | {{CRITICAL_RESOLVED}} | {{CRITICAL_PENDING}} |
| Important | {{IMPORTANT_TOTAL}} | {{IMPORTANT_RESOLVED}} | {{IMPORTANT_PENDING}} |
| Minor | {{MINOR_TOTAL}} | {{MINOR_RESOLVED}} | {{MINOR_PENDING}} |

### 1.2 按阶段统计

| 阶段 | 发现 | 已解决 | 遗留 |
|------|------|--------|------|
| 转换阶段 | {{TRANSLATION_FOUND}} | {{TRANSLATION_RESOLVED}} | {{TRANSLATION_PENDING}} |
| 测试阶段 | {{TEST_FOUND}} | {{TEST_RESOLVED}} | {{TEST_PENDING}} |
| 整体测试阶段 | {{OVERALL_FOUND}} | {{OVERALL_RESOLVED}} | {{OVERALL_PENDING}} |

---

## 二、问题列表

### 2.1 Critical

| ID | 发现阶段 | 文件 | 行号 | 描述 | 验证状态 | 解决状态 |
|----|----------|------|------|------|----------|----------|
{{CRITICAL_ROWS}}

### 2.2 Important

| ID | 发现阶段 | 文件 | 行号 | 描述 | 验证状态 | 解决状态 |
|----|----------|------|------|------|----------|----------|
{{IMPORTANT_ROWS}}

### 2.3 Minor

| ID | 发现阶段 | 文件 | 行号 | 描述 | 验证状态 | 解决状态 |
|----|----------|------|------|------|----------|----------|
{{MINOR_ROWS}}

---

## 三、问题详情模板

### ISSUE-{{ID}}

| 字段 | 内容 |
|------|------|
| 文件 | `{{FILE_PATH}}:{{LINE}}` |
| 发现阶段 | {{FOUND_STAGE}} |
| 问题来源 | {{ISSUE_SOURCE}} |
| 验证状态 | {{VERIFY_STATUS}} |
| 解决状态 | {{RESOLUTION_STATUS}} |
| 涉及函数 | `{{FUNCTION_NAME}}` |

**问题描述**

{{DESCRIPTION}}

**原始 MATLAB 代码**

```matlab
{{MATLAB_CODE}}
```

**建议处理方式**

{{SUGGESTED_FIX}}

**处理结果**

{{RESOLUTION}}

---

## 四、字段取值

### 发现阶段

- 转换阶段
- 测试阶段
- 整体测试阶段

### 问题来源

- 转换引入
- 原有问题
- 测试发现

### 验证状态

- 未验证
- 验证通过
- 验证失败

### 解决状态

- 待处理
- 进行中
- 已解决
- 已忽略
