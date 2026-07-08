# go-symmetric-refactor

A reusable Agent Skill for cleaning Go code by discovering and applying existing project symmetry.

This skill is intentionally conservative. It does **not** ask the agent to invent a new architecture. It asks the agent to extract the conventions already present in the repository, find asymmetries, make small mechanical patches, and verify that behavior remains unchanged.

## What it is good at

- Grouping Go methods by receiver type.
- Checking receiver-name consistency.
- Finding method-order drift.
- Keeping public methods, private helpers, constructors, and lifecycle methods organized.
- Detecting naming inconsistencies across similar concepts.
- Producing a reviewable edit plan before touching files.
- Running `gofmt`, `go test`, and optional static checks after edits.

## What it should avoid

- Large architecture rewrites.
- Behavior changes hidden inside formatting refactors.
- Public API changes unless explicitly requested.
- Renaming exported symbols without a migration plan.
- Applying style rules from another project without first checking the local codebase.

## Suggested installation

Clone this repository into an agent skill directory:

```bash
git clone https://github.com/luojiyin1987/go-symmetric-refactor.git \
  ~/.claude/skills/go-symmetric-refactor
```

Or copy it into a project-local agent directory:

```text
.agent/skills/go-symmetric-refactor/
  SKILL.md
  scripts/
  references/
```

## Basic usage

Ask the agent to use this skill when you want a Go cleanup pass:

```text
Use the go-symmetric-refactor skill to inspect this package, infer the local style, and propose a small refactor plan. Do not change behavior.
```

For a stricter pass:

```text
Use go-symmetric-refactor. First run scripts/go_symbols.py and scripts/symmetry_check.py. Then propose a patch plan. Only apply changes that are mechanical, local, and covered by tests.
```

## Repository layout

```text
SKILL.md                         # Main skill instruction file
scripts/go_symbols.py             # Deterministic Go symbol scanner
scripts/symmetry_check.py          # Lightweight symmetry heuristics
references/project-style.md        # Example conventions document
examples/agent-prompt.md           # Example prompt for invoking the skill
```

## Design principle

Good refactoring starts from the codebase, not from the model's taste.

The workflow is:

1. Extract local structure.
2. Infer existing rules.
3. Identify asymmetry.
4. Explain the intended patch.
5. Apply small changes.
6. Verify with tooling.
7. Review the diff for behavior changes.
