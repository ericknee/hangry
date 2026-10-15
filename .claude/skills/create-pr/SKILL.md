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
- 2-5 one-line bullets: user-visible or system-visible changes, each starting with the thing that changed.

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

Keep it short. A reviewer should get the PR in under a minute:
- **Size target:** a typical PR is about 25 lines. Past about 40, cut. Size follows the change: a one-file fix
  gets What, Decisions (if any) and Testing only.
- **One line per bullet.** Say what changed and why, not how the code works; the diff shows the how.
  No restating file lists, no narrating the diff.
- **Decisions:** at most 3-4 choices, each as one bullet: choice, driver, cost (add the rejected alternative or
  reversibility only if it changes the reader's view). Skip obvious choices.
- **Optional sections only when they earn it:** Design for a flow that crosses client / API / Google / DB (use a
  small ASCII diagram instead of prose); API changes only for a changed contract; Known gaps only for real
  risks or unfinished work.
- **Deploy steps are never cut** when the PR needs something outside the code (migration, secret, Cloud Run
  setting). Missing deploy steps are the most expensive omission.
- **Testing:** one line per command, merged where possible ("Backend tests (67), ruff, eslint, build").
- Plain, concrete sentences. Name files, endpoints, settings and env vars in backticks. Mark breaking changes
  in bold and say when `openapi.json` / `types.gen.ts` were regenerated. If a change affects Google Places
  billing, name the SKU (see CLAUDE.md "Places cost").

### Decisions and tradeoffs (required)

For each significant technical choice (3-4 at most), write one bullet:
**the choice** - *driver:* the product or policy constraint behind it - *cost:* what it makes worse. Add the
rejected alternative or how reversible it is only when that changes how the reader sees it. Example drivers:
the Privacy Policy promises 30-day deletion; candidates can't be stored outside memory because of Google's
terms; the service is US-only; solo MVP with group sessions planned.

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
- Reply in three lines or fewer: the PR URL, what was verified, and what is left unchecked. Don't repeat the
  description back.
