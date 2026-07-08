---
name: go-symmetric-refactor
description: Use this skill when cleaning, refactoring, or reviewing Go code for symmetry, naming consistency, method ordering, receiver consistency, structure alignment, and local style preservation without changing behavior.
---

# Go Symmetric Refactor

## Goal

Clean Go code by discovering existing project conventions and applying them consistently.

This skill should make the code feel like it was written by one careful maintainer, not by several unrelated patches.

## Hard rules

- Do not invent a new architecture.
- Do not change runtime behavior unless explicitly requested.
- Do not rename exported APIs unless explicitly requested.
- Prefer small, mechanical, reviewable patches.
- Preserve public compatibility.
- Keep tests green.
- When unsure, report the ambiguity instead of editing.

## When to use

Use this skill for tasks such as:

- "clean this Go package"
- "make this code more symmetrical"
- "整理一下这段 Go 代码"
- "keep the style consistent"
- "review this refactor"
- "提炼项目里的 Go 代码风格"
- "方法顺序、receiver、命名风格统一一下"

## Workflow

### 1. Build a symbol map

First inspect the package structure before proposing edits.

Run:

```bash
python scripts/go_symbols.py .
```

Look for:

- packages
- files
- imports
- types
- constructors
- methods grouped by receiver type
- public functions
- private helpers
- test functions

### 2. Infer local symmetry rules

Infer rules from nearby code, not from generic style preferences.

Common rule categories:

- Receiver names: `Mesh` uses `m`, `Server` uses `s`, `Client` uses `c`.
- Method order: constructor -> lifecycle -> mutators -> queries -> shutdown -> private helpers.
- Visibility order: exported methods before unexported helpers.
- Struct field order: identity -> configuration -> runtime state -> synchronization primitives.
- Error style: wrap errors or return raw errors consistently.
- Test style: table-driven tests, test names, fixture naming.
- File layout: public API files, internal helpers, tests, mocks, fixtures.

Write the inferred rule explicitly before editing.

Example:

```text
Inferred rule: methods on *Mesh are ordered as constructor, lifecycle methods, query methods, shutdown, then private reconciliation helpers.
Violation: merge appears before Shutdown in mesh.go.
Patch: move merge below Shutdown without changing its body.
```

### 3. Find asymmetries

Look for drift, not just lint failures.

Useful questions:

- Does the same concept have multiple names?
- Do similar receiver types use inconsistent receiver names?
- Are public and private methods mixed randomly?
- Does a type have `Start` but no matching `Stop`, `Close`, or `Shutdown`?
- Do tests cover one symmetric branch but not its counterpart?
- Are struct fields ordered differently across equivalent types?
- Are JSON/YAML tags aligned with field names?
- Are error messages phrased consistently?

Run the lightweight checker:

```bash
python scripts/symmetry_check.py .
```

Treat script output as a hint, not as absolute truth.

### 4. Produce an edit plan

Before editing, produce a short plan:

```text
Plan:
1. Normalize receiver names for *Mesh from `mesh` to `m` in mesh.go.
2. Move private helper `merge` after the public lifecycle methods.
3. Align NodeState fields as identity, address, epoch, pools, templates.
4. Run gofmt and go test ./...
```

Skip any change that cannot be explained as local symmetry cleanup.

### 5. Apply small patches

Patch rules:

- Keep function bodies unchanged when only moving code.
- Keep comments attached to the symbols they describe.
- Avoid mixed refactors: do not rename, reorder, and redesign in the same patch unless necessary.
- Avoid changing generated files, vendored files, or third-party code.
- For exported symbols, prefer comment updates over renames unless the user requested API cleanup.

### 6. Verify

Run the strongest available checks that are reasonable for the project:

```bash
gofmt -w .
go test ./...
go vet ./...
```

If the project has its own commands, prefer them:

```bash
make test
make lint
golangci-lint run
```

Report commands that fail and do not hide failures.

### 7. Self-review the diff

After editing, review the diff and answer:

- Did behavior change?
- Did any public API change?
- Is the patch smaller than a rewrite?
- Is the symmetry rule clear?
- Are tests still passing?
- Did the refactor improve readability without adding cleverness?

## Output format

When reviewing or proposing changes, use this structure:

```text
Inferred conventions:
- ...

Asymmetries found:
- ...

Patch plan:
- ...

Verification:
- ...

Risks / skipped items:
- ...
```

## Examples of good edits

Good:

- Move helper methods below public methods.
- Normalize receiver names inside one type.
- Align method order across two similar types.
- Split a long file only when the project already uses that pattern.
- Add missing table-test cases for symmetric branches.

Bad:

- Replace the design with a new framework.
- Rename exported symbols without user approval.
- Change behavior while claiming it is a formatting cleanup.
- Apply another repository's style guide without checking local code.
- Convert straightforward Go into clever abstractions.

## Mental model

This skill is a style extractor plus a conservative refactor loop.

The agent's job is not to make the code match the agent's taste.
The agent's job is to make the code match itself.
