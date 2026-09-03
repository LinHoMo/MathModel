# Syslab Skills 安装说明

本文说明如何通过手动拷贝安装本目录下的 Syslab skills，并在安装后配置本机的 Syslab 安装目录。

本目录包含以下 skills：

- `syslab-environment`
- `syslab-mds-docs`
- `syslab-code-style`
- `syslab-testing`
- `syslab-performance-optimization`
- `syslab-matlab-to-julia`
- `syslab-julia-to-cpp`
- `syslab-digital-filter-design`

安装时需要拷贝整个 skill 目录，不能只拷贝 `SKILL.md`。

## 前提条件

无论你安装到项目级还是用户级，确保具备`SYSLAB_HOME`环境变量，该变量指向 Syslab 安装目录，例如：

```text
SYSLAB_HOME=C:/Program Files/MWORKS/Syslab 2026a 
```

*注意：必须改成你自己机器上的**真实 Syslab 安装目录**。*

## Codex

统一使用 `.codex/skills/`。

### 项目级安装

将 Syslab skills 拷贝到项目根目录下的：

```text
.codex/skills/
```

目录结构示例：

```text
<your-project>/
  .codex/
    skills/
      syslab-environment/
      syslab-mds-docs/
      syslab-code-style/
      syslab-testing/
      syslab-performance-optimization/
      syslab-matlab-to-julia/
      syslab-julia-to-cpp/
      syslab-digital-filter-design/
```

### 用户级安装

如果希望当前用户的所有项目都能使用这些 skills，就把它们拷贝到：

```powershell
~/.codex/skills/  # 对于windows环境，即 %USERPROFILE%\.codex\skills\
```

## Claude Code

统一使用 `.claude/skills/`。

### 项目级安装

把 Syslab skills 整体拷贝到项目根目录下的：

```text
.claude/skills/
```

目录结构示例：

```text
<your-project>/
  .claude/
    skills/
      syslab-environment/
      syslab-mds-docs/
      syslab-code-style/
      syslab-testing/
      syslab-performance-optimization/
      syslab-matlab-to-julia/
      syslab-julia-to-cpp/
      syslab-digital-filter-design/
```

### 用户级安装

如果希望当前用户的所有项目都能使用这些 skills，就把它们拷贝到：

```powershell
~/.claude/skills/ # 对于windows环境，即 %USERPROFILE%\.claude\skills\
```

## OpenCode

统一使用 `.opencode/skills/`。

### 项目级安装

把 Syslab skills 整体拷贝到项目根目录下的：

```text
.opencode/skills/
```

目录结构示例：

```text
<your-project>/
  .opencode/
    skills/
      syslab-environment/
      syslab-mds-docs/
      syslab-code-style/
      syslab-testing/
      syslab-performance-optimization/
      syslab-matlab-to-julia/
      syslab-julia-to-cpp/
      syslab-digital-filter-design/
```

### 用户级安装

如果希望当前用户的所有项目都能使用这些 skills，就把它们拷贝到：

```powershell
~/.config/opencode/skills/
```

## 建议

如果只是当前仓库使用，优先选项目级安装。

如果希望多个项目共用，选用户级安装。
