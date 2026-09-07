# 模板变更记录

## [2026-07-18] cumcmthesis v2.6 → v2.7
- 新增 microtype/mathtools/algorithm/algpseudocode/natbib 预加载
- 修复 \setCJKmonofont{KaiTi} → \setCJKfamilyfont{zhkai}
- normalsize 12.05pt → 12pt
- 新增 biblatex GB/T 7714 可选入口（gbt7714 选项）

## [2024-01-25] mcmthesis v6.3 → v6.3.2
- 新增 subcaption/caption/algorithm/algpseudocode/natbib 预加载
- 新增 \supercite/\upcite 上标引用命令
- 新增 \aiacknowledgment 命令（2024 美赛 AI 引用）

## [2026-07-18] typst 模板修复
- 修复 gray.with-key(0.9) → luma(230)（Typst 0.11+ API 变更）
- 修复下划线内换行符
- typst.toml 补全 minimum-typst-version
