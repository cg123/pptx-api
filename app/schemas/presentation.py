from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class TitleSlide(BaseModel):
    type: Literal["title"] = "title"
    title: str
    subtitle: Optional[str] = None


class BulletPoint(BaseModel):
    text: str
    children: List["BulletPoint"] = Field(default_factory=list)


class BulletSlide(BaseModel):
    type: Literal["bullet"] = "bullet"
    title: Optional[str] = None
    points: List[BulletPoint] = Field(default_factory=list)


class ImageSlide(BaseModel):
    type: Literal["image"] = "image"
    title: Optional[str] = None
    url: str  # URL to the image
    alt: Optional[str] = None  # Alt text/description of the image


class TableSlide(BaseModel):
    type: Literal["table"] = "table"
    title: Optional[str] = None
    headers: List[str]  # Column headers
    rows: List[List[str]]  # Table data (rows of cells)


class ContentSection(BaseModel):
    """Content that can be placed in a section of a split slide."""

    type: Literal["bullet", "image", "table"]

    # For bullet section
    points: Optional[List[BulletPoint]] = Field(default_factory=list)

    # For image section
    url: Optional[str] = None
    alt: Optional[str] = None

    # For table section
    headers: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None


class SplitSlide(BaseModel):
    type: Literal["split"] = "split"
    title: Optional[str] = None
    layout: Literal["left-right"] = "left-right"  # Future: could add more layouts
    sections: List[ContentSection] = Field(
        min_items=2, max_items=2
    )  # Currently supports exactly 2 sections


# Update the presentation model to include all slide types
class Presentation(BaseModel):
    slides: List[Union[TitleSlide, BulletSlide, ImageSlide, TableSlide, SplitSlide]]
    filename: Optional[str] = "presentation.pptx"


# Add forward reference for BulletPoint's recursive definition
BulletPoint.model_rebuild()
