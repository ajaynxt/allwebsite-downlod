from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AnalyzeRequest(StrictModel):
    url: HttpUrl = Field(max_length=2048)


class FormatOption(StrictModel):
    id: str
    kind: Literal["video", "audio"]
    label: str
    detail: str
    extension: str
    estimated_bytes: int | None = None
    recommended: bool = False


class MediaInfo(StrictModel):
    title: str
    creator: str | None = None
    platform: str
    duration_seconds: int | None = None
    thumbnail: str | None = None
    webpage_url: str
    formats: list[FormatOption]


class DownloadRequest(StrictModel):
    url: HttpUrl = Field(max_length=2048)
    mode: Literal["video", "mp3", "m4a"] = "video"
    format_id: str = Field(default="best", min_length=1, max_length=128)
    rights_confirmed: bool

    @field_validator("format_id")
    @classmethod
    def safe_format_id(cls, value: str) -> str:
        if value in {"best", "audio-best"}:
            return value
        if not all(char.isalnum() or char in "._-" for char in value):
            raise ValueError("Invalid quality selection")
        return value

    @field_validator("rights_confirmed")
    @classmethod
    def rights_must_be_confirmed(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Confirm that you own the content or have permission")
        return value

