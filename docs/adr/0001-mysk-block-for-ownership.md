# mysk frontmatter block as the ownership signal

A skill is owned by `mysk` if its `SKILL.md` contains a `mysk:` frontmatter block. The presence of this block is the canonical signal — not the symlink target path, not a separate manifest. All mysk-specific metadata (`source`, `modified`, `experimental`, `deprecated`) lives inside this block; generic fields (`name`, `description`) remain at the top level for any agent to read.

## Considered options

- **Symlink path inference** — check whether the symlink in a Deployment Target points into the mysk repo. Rejected because it breaks when symlinks are replaced with hard copies or when the CLI is distributed independently of the repo.
- **External manifest** — maintain a lockfile of deployed skills. Rejected because it introduces a second source of truth that can drift.

## Consequences

All skills managed by `mysk` must have a `mysk:` block in their frontmatter. Skills without it are invisible to `mysk` and will not be deployed, cleaned up, or otherwise managed.
