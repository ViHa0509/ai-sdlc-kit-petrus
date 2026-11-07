# Spec Delta

## ADDED Requirements

### Requirement: Deny writes that contain a likely secret
Before a Write, Edit, MultiEdit or NotebookEdit tool call, the kit SHALL scan the new content and deny the call when it contains a likely secret: an Anthropic, OpenAI, AWS, GitHub, Google or Slack key or token, a PEM private key block, or a long random value assigned to a name containing key, secret, token or password. The deny reason MUST name only the secret type and the line number, never the secret text.

#### Scenario: API key written into a file
- **WHEN** an agent writes a file whose line 3 holds an Anthropic API key
- **THEN** the write is denied with a reason naming "Anthropic API key" and line 3
- **AND** the reason does not contain the key

#### Scenario: Private key block
- **WHEN** an agent writes a PEM private key block
- **THEN** the write is denied

### Requirement: Placeholders and allow-lists pass
The guard SHALL allow obvious placeholders: values with `...`, `<...>`, `xxxx`, `your`, `example`, `changeme`, `placeholder`, `dummy`, `redacted`, a very low variety of characters, and empty values. A line carrying `sdlc:allow-secret` or `pragma: allowlist secret` passes. `.sdlc/gates.json` MAY list `secrets.allow` regular expressions (matched against the finding's line) and `secrets.ignore_paths` globs; matching findings or paths pass.

#### Scenario: Placeholder in an example env file
- **WHEN** an agent writes `.env.example` with `ANTHROPIC_API_KEY=` and `OPENAI_API_KEY=sk-...`
- **THEN** the write is allowed

#### Scenario: Configured allow pattern
- **GIVEN** `secrets.allow` contains a pattern matching a test fixture line
- **WHEN** an agent writes that line
- **THEN** the write is allowed

### Requirement: Staged secrets block a commit
Before a Bash call that runs `git commit`, the kit SHALL scan the added lines of the staged diff (and, when the command also stages files or uses `-a`, the unstaged and untracked changes) and deny the commit when a likely secret is found, naming the file, line and type only.

#### Scenario: Secret staged
- **GIVEN** a staged file adds a GitHub token
- **WHEN** an agent runs `git commit -m "x"`
- **THEN** the commit is denied with the file name, line number and "GitHub token"
