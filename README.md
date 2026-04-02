<div align="center">

# 🏭 github-to-skill

**Convert any GitHub repository into a ready-to-use AI domain-expert SKILL — automatically.**

*Built for Claude Code · Codex · OpenClaw*

[![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-orange?style=flat-square)](https://github.com/anthropics/claude-code)
[![Codex](https://img.shields.io/badge/Codex-Compatible-blue?style=flat-square)](https://github.com/openai/codex)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-green?style=flat-square)](https://github.com/openclaw/openclaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-gray?style=flat-square)](LICENSE)

</div>

---

## 🎯 What this SKILL does

The open-source ecosystem has millions of powerful tools. AI agents can't use them without structured integration wrappers — and writing those by hand is slow, brittle, and doesn't scale.

`github-to-skill` automates the full pipeline: clone a repo, detect its structure, extract capabilities from docs and source code, generate a validated `SKILL.md`, and package everything an agent needs to use it fluently.

```
GitHub URL  ──→  Extract  ──→  Model  ──→  Validate  ──→  .skill
```

The output isn't a documentation summary. It's a **callable domain expert** — something the agent can invoke with natural language, knowing exactly what the tool does, how to call it, and what to expect back.

---

## 🔄 How it works

```
                   ┌────────────────────────────────────┐
                   │          github-to-skill           │
                   └────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼──────────────────────────┐
         │                           │                          │
   ① 🔍 Detect                ② 📖 Extract               ③ ⚙️  Generate
  project type & build         Wiki > README > source      type-specific template
  entry points & deps          evidence chain only         capability matrix
         │                           │                          │
         └───────────────────────────┼──────────────────────────┘
                                     │
                               ④ ✅ Validate
                            4-level progressive check
                         structure → syntax → deps → execution
                                     │
                         ┌───────────┴──────────┐
                         │                      │
                      🟢 ready             🟡 partial
                    ready to use        usable with warnings
                                        + explicit unblock steps
```

> 🔴 `blocked` — core command cannot run. No skill file is written; a diagnostic report is output instead.

---

## 📦 Generated skill layout

```
~/.claude/skills/jq/
├── 📄 SKILL.md              # capability definitions + invocation templates
├── 📁 scripts/
│   └── wrapper.py           # execution wrapper (auth, retry, output parsing)
└── 📁 references/
    ├── source-notes.md      # evidence chain (Wiki > README > source)
    └── workflow.md          # verified capability matrix
```

---

## 🚀 Installation & usage by platform

### ![Claude Code](https://img.shields.io/badge/-Claude_Code-orange?style=flat-square)

**Step 1 — Install this SKILL into Claude Code**

```bash
git clone https://github.com/zlr-zmm/github-to-skill.git ~/.claude/skills/github-to-skill
```

**Step 2 — Invoke it in a Claude Code session**

Use natural language — no flags to memorize:

```
"Turn https://github.com/user/repo into a skill"

"Package this repo: https://github.com/user/repo"

/github-to-skills https://github.com/user/repo
```

**Step 3 — The generated skill is ready immediately**

Claude Code picks up new skills in `~/.claude/skills/` automatically. The next conversation can use it:

```
"Use the {repo} skill to filter .name from my data.json"
```

---

### ![Codex](https://img.shields.io/badge/-Codex-blue?style=flat-square)

**Step 1 — Install this SKILL into your project**

```bash
mkdir -p .agents/skills
git clone https://github.com/zlr-zmm/github-to-skill.git .agents/skills/github-to-skill
```

**Step 2 — Invoke in a Codex session**

```
"Convert https://github.com/user/repo into a skill"

/github-to-skills https://github.com/user/repo
```

**Step 3 — Install the generated skill**

```bash
cp -r generated/repo-name .agents/skills/
```

Codex detects skills in `.agents/skills/` at startup. The new skill is available in the next session.

---

### ![OpenClaw](https://img.shields.io/badge/-OpenClaw-green?style=flat-square)

**Step 1 — Install this SKILL into OpenClaw**

```bash
git clone https://github.com/zlr-zmm/github-to-skill.git ~/.openclaw/plugins/github-to-skill
```

**Step 2 — Invoke in an OpenClaw session**

```
"Turn this GitHub repo into a skill: https://github.com/user/repo"

/github-to-skills https://github.com/user/repo
```

**Step 3 — Install the generated skill**

```bash
cp -r generated/repo-name ~/.openclaw/plugins/
```

Restart OpenClaw or reload plugins. The generated skill is ready to use.

---

## 🗂️ Supported project types

| Type | Detected via | Template |
|------|--------------|----------|
| 🐍 Python CLI | `[project.scripts]` in pyproject.toml | `python-cli.md` |
| 📦 Python library | `[project]` without scripts | `python-lib.md` |
| 🟨 Node.js CLI | `bin` field in package.json | `node-cli.md` |
| 🦀 Rust / Go binary | `src/main.rs` or `main.go` | `rust-cli.md` |
| 🌐 REST API | Flask / FastAPI `app.py` | `rest-api.md` |

---

## 📋 Validation levels

| Level | Check | Pass criteria |
|-------|-------|---------------|
| `L1` Structure | `SKILL.md` exists with valid frontmatter | parseable by agent runtime |
| `L2` Syntax | wrapper script has no syntax errors | `py_compile` / `eslint` passes |
| `L3` Dependencies | requirements install cleanly | `pip` / `npm install` exits 0 |
| `L4` Execution | at least one capability runs end-to-end | output file existence confirmed |

---

## 📐 Architecture

```
github-to-skill/
├── 📄 SKILL.md                    # master file read by the agent
├── src/
│   ├── pipeline.py                # main orchestration
│   ├── detector.py                # project type & entry point detection
│   ├── generator.py               # SKILL file rendering
│   └── validator.py               # 4-level validator
├── templates/                     # per-type SKILL templates
│   ├── python-cli.md
│   ├── python-lib.md
│   ├── node-cli.md
│   ├── rust-cli.md
│   └── rest-api.md
└── references/
    ├── fetch_github_info.py       # batch Wiki / README fetcher
    └── create_github_skill.py     # SKILL scaffold generator
```

---

## 🔮 Design principles

- **Evidence-first** — only capabilities verifiable in Wiki, README, or source code are written into the skill. No guessing.
- **Fail fast** — environment is validated at Phase 1. Broken setups are caught before generation, not after.
- **Transparent status** — every generated skill carries a `ready / partial / blocked` marker. `partial` always ships with an explicit unblock checklist.
- **Infinite derivation** — each generated skill can itself be used as input, enabling compound capabilities and skill chains.

---

<div align="center">
<sub>MIT License · Made for the agentic AI era</sub>
</div>