# AI Cyber Value Creator — Hermes Plugin

The AI Cyber Value Creator methodology as a running program inside
[Hermes Agent](https://hermes-agent.nousresearch.com): first lay the
**Create Value foundation** (ICP → Problems → Solutions → Offer → Elevator
Pitch), then work the four-phase **value flywheel** — Attract → Nurture →
Convert → Deliver — in laps.

## What you get

- **Roadmap dashboard tab** (`/value-creator`): overall progress, the
  Foundation section, the flywheel with the clockwise-arrow hub (click the hub
  for the full process diagram), and three views — Laps / Phases / Sequence.
  Click any step to cycle To-Do → In-Progress → Done.
- **Step tasks that run themselves.** "+ Task" on any step creates a hermes
  kanban task carrying the step's executive brief and guidance skill. The
  gateway dispatcher picks it up and runs it as a normal hermes session — a
  real conversation thread you can open from the roadmap (`thread ↗`) or the
  Kanban tab. When the task completes, the roadmap step flips to Done
  automatically.
- **Shared Company Context** — who we serve & what we deliver (ICP, Problems,
  Solutions, Active Offer, Elevator Pitch). Sessions read and update it via
  the `record_company_context` / `get_company_context` tools; edit it any time
  in the roadmap's Company Context panel. Once all four fields are set, the
  elevator-pitch step auto-starts (once) — or click ✨ Generate.
- **Six methodology skills** (`ai-cyber-value-creator:<name>`): the master
  playbook, define-icp, research-problems, build-solutions, craft-offer
  (Hormozi Grand Slam + one-page dark-theme PDF spec), craft-elevator-pitch —
  plus the company-context discipline skill.
- **Slash commands**: `/value-creator` (status + next step),
  `/value-step <step-id>` (start a step).
- **Tools**: `record_company_context`, `get_company_context`,
  `value_creator_status`, `start_value_step`.

## Install

```bash
hermes plugins install harperaa/hermes-plugin-ai-cyber-value-creator --enable
```

Then restart hermes (and `hermes dashboard` for the roadmap tab). Step tasks
run via the kanban dispatcher, which lives in the gateway:

```bash
hermes gateway start
```

### Developing from a checkout

```bash
ln -s ~/code/ai-cyber-value-creator ~/.hermes/plugins/ai-cyber-value-creator
hermes plugins enable ai-cyber-value-creator
```

## Where things live

- Plugin state + the live `company-context.md`:
  `~/.hermes/plugins-data/ai-cyber-value-creator/`
- Step tasks: the standard hermes kanban board (`hermes kanban list`, the
  Kanban dashboard tab).

## Tests

```bash
python3 -m pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE).
