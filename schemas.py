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

ASK_USER_QUESTION = {
    "name": "ask_user_question",
    "description": (
        "Declare the interview question you are about to ask IN CHAT on a "
        "kanban task you are working. Records the interview position (drives "
        "the roadmap progress bar) and marks the task as waiting for the "
        "user's answer. It posts NOTHING visible — the question itself must "
        "be delivered by you in the chat conversation, which is the only "
        "place the user asks and answers questions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "The kanban task id you are working (e.g. t_063beb70).",
            },
            "question_number": {
                "type": "integer",
                "description": "This question's number in the step's interview (1-based).",
            },
            "question_total": {
                "type": "integer",
                "description": "Total questions planned for this step's interview.",
            },
            "reason_tag": {
                "type": "string",
                "description": "Unique short tag for the waiting reason, e.g. 'company size'.",
            },
        },
        "required": ["task_id", "question_number", "question_total"],
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
