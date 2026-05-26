from typing import Literal

from pydantic import BaseModel, Field, model_validator


SaveMode = Literal["full", "summary", "main-idea"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=50_000)


class SaveRequest(BaseModel):
    mode: SaveMode = "full"
    chat_url: str
    title: str = Field(default="ChatGPT conversation", max_length=200)
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_total_content_size(self) -> "SaveRequest":
        total_chars = sum(len(message.content) for message in self.messages)
        if total_chars > 250_000:
            raise ValueError("Conversation is too large to save in one request.")
        return self


class SaveResponse(BaseModel):
    ok: bool
    filename: str
    path: str
