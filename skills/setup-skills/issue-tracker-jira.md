# Issue tracker: Jira

Issues and PRDs for this repo live in Jira. Use the Atlassian CLI (`acli`) for all operations.

## Conventions

- **Create an issue**:
  ```bash
  acli jira workitem create \
    --project "PROJ" \
    --type "Task" \
    --summary "..." \
    --description "..."
  ```
  Use a heredoc for multi-line descriptions.

- **Read an issue**:
  ```bash
  acli jira workitem view PROJ-123
  ```
  Use `--json` for machine-readable output.

- **List issues**:
  ```bash
  acli jira workitem search \
    --jql 'project = PROJ AND status != Done'
  ```
  Use `--json` when the output will be processed programmatically.

- **Comment on an issue**:
  ```bash
  acli jira workitem comment create \
    --key PROJ-123 \
    --body "..."
  ```

- **Update fields**:
  ```bash
  acli jira workitem edit --key PROJ-123 --summary "..." --yes
  ```
  Use field-specific flags (`--summary`, `--description` etc.). Add `--yes` to skip confirmation.

- **Apply / remove labels**:
  ```bash
  acli jira workitem edit --key PROJ-123 --labels "label1,label2" --yes
  ```
  Use `--remove-labels` to remove specific labels.

- **Transition / close an issue**:
  ```bash
  acli jira workitem transition --key PROJ-123 --status "..." --yes
  ```
  `acli` cannot list available transitions — always ask the user which status to transition to before running this command. Valid transitions depend on the project's workflow and the issue's current status. Post a comment before transitioning if an explanation is required. DO NOT close issues without explicit permission!

## Conventions for search

Use JQL (Jira Query Language) when listing or searching issues.

Examples:

```bash
project = PROJ
project = PROJ AND status != Done
assignee = currentUser()
labels = backend
summary ~ "authentication"
```

## Repository / project discovery

Do not infer the Jira project unless the user has mentioned a specific project already. More than one project could work on this repo. You can use `acli jira project list --limit 50` to determine what is available and ask the user which one to use.

## When a skill says "publish to the issue tracker"

Create a Jira work item using:

```bash
acli jira workitem create ...
```

## When a skill says "fetch the relevant ticket"

Run:

```bash
acli jira workitem view PROJ-123
```

If only search criteria are known, use:

```bash
acli jira workitem search --jql '...'
```
