# Example Agent Prompt

Use this when you want an agent to run a conservative Go cleanup pass.

```text
Use the go-symmetric-refactor skill on this repository.

Goal:
- Infer the local Go style from the current package.
- Find method-order, receiver-name, naming, and structure asymmetries.
- Propose a small patch plan before editing.
- Do not change behavior.
- Do not rename exported APIs unless I explicitly approve it.

Required steps:
1. Run `python scripts/go_symbols.py .`.
2. Run `python scripts/symmetry_check.py .`.
3. Summarize inferred conventions.
4. List asymmetries found.
5. Propose a patch plan.
6. Apply only mechanical changes.
7. Run `gofmt -w .` and `go test ./...`.
8. Review the diff and explain what changed.
```

For a review-only pass:

```text
Use go-symmetric-refactor in review-only mode. Do not edit files. Produce inferred conventions, asymmetries, risks, and a suggested patch plan.
```

For generating a project-local style file:

```text
Use go-symmetric-refactor to inspect this repository and generate `PROJECT_STYLE.md`. The file should document only conventions that are actually visible in this codebase.
```
