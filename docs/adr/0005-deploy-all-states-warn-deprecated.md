# Deploy all lifecycle states; warn on Deprecated

`mysk deploy` symlinks every skill regardless of lifecycle state. Deprecated skills are deployed with a warning rather than skipped or removed. The author may not yet have a replacement for a deprecated skill, and removing it automatically would take that choice away from them. State is surfaced in the interactive selection prompt and in the per-target summary so the author always knows what they are deploying.

## Considered options

- **Skip Deprecated during deploy** — rejected: forces authors to keep a replacement ready before they can deprecate, which conflates two independent decisions.
- **Remove Deprecated symlinks automatically** — rejected: same problem, plus it silently deletes something the author may still be relying on.
- **Warn and deploy (chosen)** — the author retains full control; the warning ensures the state is visible at deploy time.
