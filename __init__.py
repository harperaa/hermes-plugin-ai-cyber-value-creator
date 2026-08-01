"""AI Cyber Value Creator — hermes plugin.

The AI Cyber Value Creator methodology as a running program: the Create Value
foundation (ICP → Problems → Solutions → Offer → Elevator Pitch), then the
four-phase flywheel (Attract → Nurture → Convert → Deliver) worked in laps.

Registers:
* tools     — record_company_context, get_company_context,
              value_creator_status, start_value_step
* commands  — /value-creator, /value-step
* skills    — ai-cyber-value-creator:<slug> (playbook + step guidance +
              company-context)
* hooks     — kanban_task_claimed / completed / blocked keep the roadmap in
              sync with the kanban tasks that run each step
* dashboard — the Value Creator roadmap tab (dashboard/, loaded by the hermes
              web dashboard's plugin system)
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parent


def _on_kanban_event(status: str):
    def _cb(task_id: str = "", **kwargs) -> None:
        try:
            from . import progress
            step_id = progress.find_step_for_kanban_task(task_id)
            if step_id:
                progress.mark_step_status(step_id, status)
        except Exception:  # never break a board transition
            logger.debug("value-creator kanban hook failed", exc_info=True)
    return _cb


def register(ctx) -> None:
    from . import commands, schemas, tools

    ctx.register_tool(
        name="record_company_context",
        toolset="value_creator",
        schema=schemas.RECORD_COMPANY_CONTEXT,
        handler=tools.record_company_context,
    )
    ctx.register_tool(
        name="get_company_context",
        toolset="value_creator",
        schema=schemas.GET_COMPANY_CONTEXT,
        handler=tools.get_company_context,
    )
    ctx.register_tool(
        name="value_creator_status",
        toolset="value_creator",
        schema=schemas.VALUE_CREATOR_STATUS,
        handler=tools.value_creator_status,
    )
    ctx.register_tool(
        name="start_value_step",
        toolset="value_creator",
        schema=schemas.START_VALUE_STEP,
        handler=tools.start_value_step,
    )

    ctx.register_command(
        "value-creator",
        handler=commands.handle_value_creator,
        description="AI Cyber Value Creator roadmap status (foundation + flywheel laps)",
    )
    ctx.register_command(
        "value-step",
        handler=commands.handle_value_step,
        description="Start an AI Cyber Value Creator roadmap step as a kanban task",
        args_hint="<step-id>",
    )

    skills_dir = _PLUGIN_DIR / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                try:
                    ctx.register_skill(child.name, skill_md)
                except Exception:
                    logger.warning("Could not register skill %s", child.name, exc_info=True)

    # Roadmap ↔ kanban sync: steps complete automatically when their kanban
    # task does (the paperclip original's issue-status reconciliation).
    ctx.register_hook("kanban_task_claimed", _on_kanban_event("in-progress"))
    ctx.register_hook("kanban_task_completed", _on_kanban_event("done"))
    ctx.register_hook("kanban_task_blocked", _on_kanban_event("in-progress"))

    _sync_indexed_skills()

    # Dashboard auth: first-visit claim login (email + password) for hosted
    # deployments. No-op when the operator configured basic-auth env vars,
    # or outside a hermes dashboard context.
    try:
        from . import mentor_auth
        mentor_auth.register_mentor_auth(ctx)
    except Exception:
        logger.warning("mentor-auth registration failed", exc_info=True)


# Skills that must live in the flat ~/.hermes/skills tree: plugin-registered
# skills are opt-in explicit loads, invisible to the system prompt's
# <available_skills> index, so a router that exists to be *ambiently
# discovered* has to be materialized there. The repo copy stays the source of
# truth; this sync makes the plugin the distribution channel.
_INDEXED_SKILLS = ("marketing-pro-router",)


def _sync_indexed_skills() -> None:
    try:
        try:
            from hermes_constants import get_hermes_home
            skills_root = get_hermes_home() / "skills"
        except ImportError:  # outside hermes — nothing to sync into
            import os
            skills_root = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))) / "skills"
        for name in _INDEXED_SKILLS:
            src = _PLUGIN_DIR / "skills" / name / "SKILL.md"
            if not src.exists():
                continue
            dst_dir = skills_root / name
            dst = dst_dir / "SKILL.md"
            content = src.read_text(encoding="utf-8")
            if dst.exists() and dst.read_text(encoding="utf-8") == content:
                continue
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
            logger.info("Synced indexed skill '%s' into %s", name, dst)
    except Exception:
        logger.warning("Indexed-skill sync failed", exc_info=True)
