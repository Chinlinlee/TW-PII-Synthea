# Issue tracker: Local Markdown

Issues, decision tickets, and the Wayfinder map for this repo live as markdown files in `.scratch/`.

## Conventions

- One effort per directory: `.scratch/<effort-slug>/`
- The Wayfinder map is `.scratch/<effort-slug>/map.md`
- Decision tickets are one file per ticket at `.scratch/<effort-slug>/issues/NN-<slug>.md`, numbered from `01`.
- Ticket type is recorded as a `Type:` line (`research`, `prototype`, `grilling`, `task`).
- Status is recorded as a `Status:` line (`open`, `claimed`, `resolved`).
- Blocking is recorded as `Blocked by: NN, NN`. A ticket is unblocked when every listed dependency is `resolved`.
- Frontier consists of open, unblocked, unclaimed tickets.
