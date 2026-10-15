---
name: create-pr
description: Push the current branch and open a GitHub pull request whose description follows this repo's PR format, including a "Decisions and tradeoffs" section. Use when asked to make, create, open or push a PR for the current branch.
---

Opens a PR for the current branch with `gh`. The description matches the earlier Hangry PRs
(#3, #5, #6, #7) plus one required section, **Decisions and tradeoffs**. Paths are relative to the repo root.

## 1. Gather the facts

Run these first; the description comes from them, not from memory of the conversation.

```bash
git branch --show-current
git status --short                 # uncommitted work?
git fetch -q origin
gh pr list --state all --limit 10  # base choice, and #s of earlier PRs
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
```

- **On `main`, or a branch whose PR is already merged:** stop and say so. Offer to branch from `origin/main`
  (carrying the working tree over); don't open a PR from it.
- **Uncommitted changes:** tell the user. Don't commit unasked, and never stage `docs/` or `.claude/worktrees/`
  unless told to. If the user wants them committed, stage files by name rather than `git add -A`.
- **Base branch:** `main`, unless the branch is stacked on an open PR's branch (then use that branch and say
  "Stacked on #N, so the base is `<branch>`" under Known gaps). Check with `git merge-base` against open PR heads.
- Read the diff itself (`git diff origin/main...HEAD`), not only the commit messages.

## 2. Verify before writing checkboxes

A box is `[x]` only if you ran that check in this session and it passed; otherwise `[ ]`.
Run what the change touches (see CLAUDE.md "Commands"):

```bash
uv run python -m pytest
uv run ruff check . && uv run ruff format --check .
cd client && npm run lint && npm run build     # and `npm run gen:api` if backend/api/**/types.py changed
```

Report failures as they are. If a test is flaky, say so and name it; don't hide it or claim it passed.
Manual checks (browser, Supabase, GCP) you didn't do go in as unchecked `[ ]` items.

## 3. Write the description

Title: short and specific, no "WIP", under about 70 characters. Several changes can be listed with commas
(see #6). Use these sections, in this order, and leave out the optional ones that don't apply:

```markdown
## What this does
- 3-6 bullets: user-visible or system-visible changes, each starting with the thing that changed.

## Decisions and tradeoffs            <- REQUIRED, see below
## Design                             <- optional: diagrams, flows, state, cost notes
## Deploy steps                       <- optional, as [ ] checkboxes: migrations, secrets, GCP resources
## API changes                        <- optional: endpoints, breaking changes, regenerated openapi.json/types
## Known gaps                         <- what is not done, risks, anything stacked or unverified
## Testing
- [x] commands you ran (with counts, e.g. "Backend tests (67)")
- [ ] manual checks still to do

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Style rules taken from the earlier PRs:
- Plain, concrete sentences. Name files, endpoints, settings and env vars in backticks.
- Mark breaking changes in bold. Say when `openapi.json` / `types.gen.ts` were regenerated.
- Use a fenced ASCII diagram in Design when a flow crosses client / API / Google / DB.
- Use `Deploy steps` whenever the PR needs something done outside the code (migration, secret, Cloud Run
  setting). Missing deploy steps are the most expensive omission.
- Costs: if a change affects Google Places billing, say which SKU and why (see CLAUDE.md "Places cost").

### Decisions and tradeoffs (required)

For each significant technical choice (usually 2-5), give:
- **The choice** in bold.
- **Product driver:** the product or policy constraint behind it. Examples: the Privacy Policy promises 30-day
  deletion; candidates can't be stored outside memory because of Google's terms; the service is US-only; solo
  MVP with group sessions planned.
- **Alternative rejected**, when there was a real one.
- **Cost:** what the choice makes worse (money, complexity, coupling, a manual setup step).
- **Reversibility**, when it's cheap to undo.

Where to find the drivers: CLAUDE.md "Decisions", `docs/`, the conversation, and the PR diff's comments.
**Don't invent a product reason.** If you can't find the driver for a choice, either leave the choice out of
this section or ask the user in one short question before posting. A tradeoff written from a guess is worse
than none.

## 4. Push and open

```bash
git push -u origin "$(git branch --show-current)"
gh pr create --base <base> --title "<title>" --body "$(cat <<'EOF'
<description>
EOF
)"
```

- Use a heredoc, as above. On this Windows setup `/tmp` differs between Git Bash and Python, so for long
  bodies written by a script use the session scratchpad directory and `--body-file`.
- Never force-push, and never push to `main`.
- End the commit message (if you create one) with the attribution line from the session's reminder; the PR
  body ends with the "Generated with Claude Code" line shown above.
- Reply with the PR URL, one line on what was verified, and anything left unchecked.
