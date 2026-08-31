# Opening the PR to `CALLE-AI/awesome-phone-call-agents`

The submission contribution is the Agent Skill at `skills/phone-claim-verifier/` in this repo.
It goes into the CALL-E community repo as a folder + one README line. ~20 minutes.

**Do this after the demo video exists** (the SKILL.md and Devpost can reference it), and
after a final `pytest`/`ruff` pass here.

---

## Steps (I can run most of these once `gh` is available, or you do them in the browser)

### 1. Fork the repo

Open `https://github.com/CALLE-AI/awesome-phone-call-agents` → **Fork** → to your account.

### 2. Clone the fork and make a branch

```bash
git clone https://github.com/bilalhassan-567/awesome-phone-call-agents.git
cd awesome-phone-call-agents
git config core.hooksPath .githooks      # enables their pre-push validation
python3 scripts/create_branch.py feat/phone-claim-verifier
```

(`create_branch.py` validates the name against `docs/git-naming-conventions.md` and runs
`git switch -c`.)

### 3. Copy the skill in

```bash
cp -r <this-repo>/skills/phone-claim-verifier skills/phone-claim-verifier
```

The folder already matches their template: `SKILL.md` (frontmatter `name` / `description` /
`license`), `references/` (incl. the required `safety.md` and `examples.md`), `scripts/`
(stdlib only), `examples/`. No `README.md` inside the skill folder (that's forbidden).

### 4. Add the README resource-list line

In the fork's `README.md`, under the Agent Skills list, add (alphabetical order):

```markdown
- [`phone-claim-verifier`](skills/phone-claim-verifier/) - Verify claims about offline records over the phone: call each number, return MATCH / MISMATCH / UNCLEAR / NO_CONTACT for every claim with a mandatory verbatim quote as evidence, and export a corrections file. Never guesses a verdict it cannot quote.
```

### 5. Validate

```bash
python3 scripts/validate_repository.py
```

Must print no errors. (Simulated against our skill locally — it passes: slug, frontmatter,
`references/safety.md` + `references/examples.md` present, no non-example emails, every
referenced local file exists.)

### 6. Commit, push, open the PR

```bash
git add skills/phone-claim-verifier README.md
git commit -m "feat(phone-claim-verifier): add phone claim verification Agent Skill"
git push -u origin feat/phone-claim-verifier
```

Then on github.com: **Compare & pull request** from your fork's branch into
`CALLE-AI/awesome-phone-call-agents:main`.

PR title: `feat(phone-claim-verifier): add phone claim verification Agent Skill`

PR body — check every box in their `.github/pull_request_template.md`, and include:
- what it does (2–3 sentences)
- the CALL-E surface it uses (MCP: `plan_call` → `run_call` → `get_call_run`)
- the companion app + repo: `https://github.com/bilalhassan-567/GhostLine` and the live demo
- side effects: places real outbound calls; one call per number per run; no recurring jobs
- the dry-run / replay path exists (link `references/examples.md`)

### 7. Put the PR URL on the Devpost form

---

## Optional: also list under `apps/`

Their `apps/` is for runnable apps (`apps/python/<name>/`). We *could* add
`apps/python/ghostline-console/README.md` pointing at the hosted console + this repo. It costs
one README stub and covers "functional app" explicitly. Decide after the skill PR is open —
don't let it delay the skill.
