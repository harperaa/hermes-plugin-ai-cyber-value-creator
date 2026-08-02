"""Tool schemas — what the LLM sees."""

from .methodology import ALL_TASK_IDS, CONTEXT_FIELD_KEYS, ELEVATOR_PITCH_KEY

RECORD_COMPANY_CONTEXT = {
    "name": "record_company_context",
    "description": (
        "Record/update the shared Company Context — who the company serves and "
        "what it is delivering. Call this whenever you confirm or refine the ICP, "
        "the problems, candidate solutions, the active offer, or the elevator "
        "pitch with the user. It updates the context every session reads."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "field": {
                "type": "string",
                "enum": [*CONTEXT_FIELD_KEYS, ELEVATOR_PITCH_KEY],
                "description": (
                    "Which part of the context to set: icp | problems | solutions "
                    "| offer | elevatorPitch"
                ),
            },
            "content": {
                "type": "string",
                "description": "The confirmed content for that field (markdown allowed).",
            },
        },
        "required": ["field", "content"],
    },
}

GET_COMPANY_CONTEXT = {
    "name": "get_company_context",
    "description": (
        "Read the shared Company Context (ICP, problems, candidate solutions, "
        "active offer, elevator pitch). Read this before acting on any AI Cyber "
        "Value Creator work so it stays aligned with the current ICP and offer."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

VALUE_CREATOR_STATUS = {
    "name": "value_creator_status",
    "description": (
        "Get the AI Cyber Value Creator roadmap status: every phase and step "
        "with its completion state, plus overall progress. The foundation "
        "(Create Value) gates the four flywheel phases (Attract, Nurture, "
        "Convert, Deliver) worked in laps."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

RECORD_USER_ANSWER = {
    "name": "record_user_answer",
    "description": (
        "Record an answer the user just gave IN THIS CHAT THREAD to an open "
        "question card on a kanban task you are working. Posts the answer onto "
        "the task thread (so the roadmap card and kanban board stay in sync) "
        "and resets the board's stuck-loop counter. The task stays blocked — "
        "you are already here working it, so keep the interview going in this "
        "conversation. Only for answers given in chat; card answers arrive as "
        "task comments on their own."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "The kanban task id you are working (e.g. t_063beb70).",
            },
            "answer": {
                "type": "string",
                "description": "The user's answer, verbatim.",
            },
        },
        "required": ["task_id", "answer"],
    },
}

START_VALUE_STEP = {
    "name": "start_value_step",
    "description": (
        "Start a roadmap step: creates a kanban task carrying the step's "
        "executive brief and guidance skill; the gateway dispatcher runs it as "
        "a normal hermes session. Use value_creator_status first to pick the "
        "next step."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "step_id": {
                "type": "string",
                "enum": ALL_TASK_IDS,
                "description": "The roadmap step to start.",
            },
        },
        "required": ["step_id"],
    },
}
