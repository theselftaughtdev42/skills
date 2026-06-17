# my-skills
Agent skills I have either made myself (less likely) or politely stolen (more likely).

## Developer setup

Install pre-commit hooks after cloning:

```sh
uv run pre-commit install
```

On each commit, two hooks run automatically:

1. **ruff-format** — reformats files in place
2. **ruff** — applies safe lint fixes

If either hook modifies a file, the commit aborts. Stage the changes and re-commit.

To run all hooks manually without committing:

```sh
uv run pre-commit run --all-files
```