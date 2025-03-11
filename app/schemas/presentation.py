from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class TitleSlide(BaseModel):
    type: Literal["title"] = "title"
    title: str
    subtitle: Optional[str] = None


class BulletPoint(BaseModel):
    text: str
    level: int = 0
    children: List["BulletPoint"] = Field(default_factory=list)


class BulletSlide(BaseModel):
    type: Literal["bullet"] = "bullet"
    title: Optional[str] = None
    points: List[BulletPoint] = Field(default_factory=list)


class Presentation(BaseModel):
    slides: List[TitleSlide | BulletSlide]