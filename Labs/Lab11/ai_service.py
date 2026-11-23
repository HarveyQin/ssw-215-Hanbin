import os
import uuid
from typing import List, Literal

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

load_dotenv()


class ProjectDetails(BaseModel):
    title: str = Field(description="A concise project title")
    summary: str = Field(description="A one- or two-sentence project summary")
    technologies: List[str] = Field(
        description="A list of technologies used by the project"
    )

    class Config:
        extra = "forbid"


class ProjectDraft(BaseModel):
    title: str = Field(description="A concise project title of at most 120 characters")
    summary: str = Field(description="A one- or two-sentence summary")
    technologies: List[str] = Field(
        description="A list of technologies used by the project"
    )
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]

    class Config:
        extra = "forbid"


class AIRefusalError(Exception):
    pass


class AIServiceUnavailableError(Exception):
    pass


sessions = {}

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def _serialize_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _request_structured_response(messages, response_model):
    if client is None:
        raise AIServiceUnavailableError("OPENAI_API_KEY is not configured")

    schema = (
        response_model.model_json_schema()
        if hasattr(response_model, "model_json_schema")
        else response_model.schema()
    )
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": response_model.__name__.lower(),
            "strict": True,
            "schema": schema,
        },
    }

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            response_format=response_format,
            temperature=0.1,
        )
    except OpenAIError as error:
        raise AIServiceUnavailableError("The OpenAI provider request failed") from error

    if not response.choices:
        raise AIServiceUnavailableError("The provider returned no choices")

    message = response.choices[0].message
    if message.refusal:
        raise AIRefusalError("The provider refused the request")
    if not message.content:
        raise AIServiceUnavailableError("The provider returned no project details")

    try:
        parsed_response = response_model.parse_raw(message.content)
    except ValidationError as error:
        raise AIServiceUnavailableError(
            "The provider returned invalid project details"
        ) from error
    if isinstance(parsed_response, ProjectDraft):
        title = parsed_response.title.strip()
        summary = parsed_response.summary.strip()
        if not title or len(title) > 120 or not summary or len(summary) > 500:
            raise AIServiceUnavailableError(
                "The provider returned an invalid project draft"
            )
    return parsed_response, message.content


def extract_project_details(notes):
    messages = [
        {
            "role": "system",
            "content": (
                "Extract project details from the notes. Return a concise "
                "title, a summary in one or two sentences, and the "
                "technologies as a list of strings. Do not invent details."
            ),
        },
        {"role": "user", "content": notes},
    ]
    details, _ = _request_structured_response(messages, ProjectDetails)
    return details


def verify_api_key():
    if client is None:
        raise AIServiceUnavailableError("OPENAI_API_KEY is not configured")

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": "Say OK and nothing else."}],
            temperature=0.1,
        )
    except OpenAIError as error:
        raise AIServiceUnavailableError("The OpenAI provider request failed") from error

    if not response.choices or not response.choices[0].message.content:
        raise AIServiceUnavailableError("The provider returned no response")
    return response.choices[0].message.content


def start_draft_session(text):
    messages = [
        {
            "role": "system",
            "content": (
                "Create a project draft from the supplied text. Return a concise "
                "title, a one- or two-sentence summary, a list of technologies, "
                "and difficulty exactly as Beginner, Intermediate, or Advanced. "
                "Keep the title under 120 characters. Do not invent details."
            ),
        },
        {"role": "user", "content": text},
    ]
    draft, assistant_message = _request_structured_response(messages, ProjectDraft)
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "messages": messages + [{"role": "assistant", "content": assistant_message}],
        "draft": _serialize_model(draft),
    }
    return session_id, get_draft_session(session_id)


def refine_draft_session(session_id, feedback):
    session = sessions.get(session_id)
    if session is None:
        return None

    messages = session["messages"] + [{"role": "user", "content": feedback}]
    draft, assistant_message = _request_structured_response(messages, ProjectDraft)
    session["messages"] = messages + [
        {"role": "assistant", "content": assistant_message}
    ]
    session["draft"] = _serialize_model(draft)
    return get_draft_session(session_id)


def refine_draft_blind(feedback):
    draft, _ = _request_structured_response(
        [{"role": "user", "content": feedback}],
        ProjectDraft,
    )
    return _serialize_model(draft)


def get_draft_session(session_id):
    session = sessions.get(session_id)
    if session is None:
        return None
    return {
        "title": session["draft"]["title"],
        "summary": session["draft"]["summary"],
        "technologies": list(session["draft"]["technologies"]),
        "difficulty": session["draft"]["difficulty"],
    }


def discard_draft_session(session_id):
    sessions.pop(session_id, None)
