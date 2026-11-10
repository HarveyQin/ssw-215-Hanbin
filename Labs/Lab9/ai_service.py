import os
from typing import List

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


class AIRefusalError(Exception):
    pass


class AIServiceUnavailableError(Exception):
    pass


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def extract_project_details(notes):
    if client is None:
        raise AIServiceUnavailableError("OPENAI_API_KEY is not configured")

    schema = (
        ProjectDetails.model_json_schema()
        if hasattr(ProjectDetails, "model_json_schema")
        else ProjectDetails.schema()
    )
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "project_details",
            "strict": True,
            "schema": schema,
        },
    }

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract project details from the notes. Return a concise "
                        "title, a summary in one or two sentences, and the "
                        "technologies as a list of strings. Do not invent details."
                    ),
                },
                {"role": "user", "content": notes},
            ],
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
        return ProjectDetails.parse_raw(message.content)
    except ValidationError as error:
        raise AIServiceUnavailableError(
            "The provider returned invalid project details"
        ) from error
