# Project Style Notes

This file is an example of the kind of project-local style document the skill can generate or update.

Do not treat these rules as universal Go style. Treat them as a template for extracting the conventions already present in a target repository.

## Symbol layout

Preferred order inside a Go file:

1. Package comment, if present.
2. Package declaration.
3. Imports.
4. Constants and variables.
5. Public types.
6. Constructors.
7. Public methods.
8. Public functions.
9. Private helpers.
10. Tests in `_test.go` files.

## Method order by receiver

For one receiver type, prefer:

1. Constructor-like functions, such as `NewX`.
2. Initialization and lifecycle methods: `Init`, `Start`, `Run`, `Join`.
3. Mutation methods: `Set`, `Add`, `Update`, `Remove`, `Delete`.
4. Query methods: `Get`, `Find`, `List`, `Members`, `PeerAddrs`.
5. Shutdown methods: `Close`, `Stop`, `Shutdown`.
6. Private reconciliation helpers.

This order is only a default. If the target repository already has a stronger local convention, follow the local convention.

## Receiver names

Prefer short, stable receiver names:

```go
func (m *Mesh) Join(...) error
func (s *Server) Start(...) error
func (c *Client) Do(...) error
func (d *delegate) NodeMeta(...) []byte
```

Avoid switching between receiver names for the same type unless there is a reason.

## Struct fields

For runtime state structs, a common order is:

1. Identity fields.
2. External addresses or references.
3. Configuration.
4. Runtime state.
5. Caches.
6. Channels.
7. Locks and synchronization primitives.

For wire-format structs, keep field order close to serialization order and keep tags aligned with field names.

## Error handling

Extract local rules before editing:

- Does the project wrap errors with `%w`?
- Does it use sentinel errors?
- Does it prefer direct returns?
- Does it include operation names in error messages?

Do not change error semantics in a style cleanup.

## Tests

For symmetric behavior, tests should also be symmetric:

- success and failure branch
- add and remove branch
- start and stop branch
- encode and decode branch
- local and remote branch

Prefer adding missing counterpart cases to an existing table-driven test instead of introducing a new test style.
