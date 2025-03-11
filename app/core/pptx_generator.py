import logging
from io import BytesIO

from pathlib import Path
from typing import List, Optional, Tuple

import requests
from pptx import Presentation as PPTXPresentation
from pptx.shapes.placeholder import PicturePlaceholder, SlidePlaceholder
from pptx.slide import Slide
from pptx.text.text import TextFrame
from pptx.util import Inches, Pt

from app.schemas.presentation import (
    BulletPoint,
    BulletSlide,
    ImageSlide,
    Presentation,
    SplitSlide,
    TableSlide,
    TitleSlide,
)

# Local path to broken image placeholder
BROKEN_IMAGE_PATH = (
    Path(__file__).parent.parent / "static" / "images" / "broken-image.png"
)

# Constants
IMAGE_UNAVAILABLE_TEXT = "Image unavailable"
DEFAULT_TITLE_FONT_SIZE = Pt(32)
DEFAULT_IMAGE_WIDTH = Inches(8)
DEFAULT_CONTENT_WIDTH = Inches(4.5)
DEFAULT_TITLE_HEIGHT = Inches(1)
DEFAULT_ERROR_HEIGHT = Inches(2)

# Set up logging
logger = logging.getLogger(__name__)


# Helper functions


def load_image_from_url_or_fallback(
    image_url: str,
) -> Tuple[BytesIO, str, Optional[str]]:
    """
    Attempt to load an image from a URL, with fallback to placeholder image.

    Args:
        image_url: URL of the image to load

    Returns:
        Tuple containing:
        - BytesIO object with the image data
        - String indicating source ('original' or 'placeholder')
        - Error message if any, None if successful
    """
    error_message = None

    try:
        # First try to get the requested image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img_stream = BytesIO(response.content)
        return img_stream, "original", None
    except Exception as e:
        # Log the original error
        error_message = f"Failed to load image from {image_url}: {str(e)}"
        logger.warning(error_message)

        # Use local broken image placeholder
        try:
            with open(BROKEN_IMAGE_PATH, "rb") as f:
                img_stream = BytesIO(f.read())
            return img_stream, "placeholder", error_message
        except Exception as err:
            # If broken image also fails, propagate both errors
            placeholder_error = f"Failed to load broken image placeholder: {str(err)}"
            logger.error(placeholder_error)
            return None, "error", f"{error_message}\n{placeholder_error}"


def add_presenter_notes(slide: Slide, notes_text: str) -> None:
    """
    Add or append text to the presenter notes of a slide.

    Args:
        slide: The slide to add notes to
        notes_text: The text to add to the notes
    """
    if not slide.has_notes_slide:
        slide.notes_slide

    notes_text_frame = slide.notes_slide.notes_text_frame
    existing_text = notes_text_frame.text if notes_text_frame.text else ""

    if existing_text:
        notes_text_frame.text = f"{existing_text}\n{notes_text}".strip()
    else:
        notes_text_frame.text = notes_text.strip()


def set_slide_title(slide: Slide, title: str) -> None:
    """
    Add a title to a slide.

    Args:
        slide: The slide to add the title to
        title: The title text
    """
    # For slide layouts with a title placeholder
    if hasattr(slide.shapes, "title") and slide.shapes.title:
        title_shape = slide.shapes.title
        title_shape.text = title
    else:
        # For blank slides, add a title textbox
        left = Inches(0.5)
        top = Inches(0.5)
        width = Inches(9)
        height = DEFAULT_TITLE_HEIGHT

        title_shape = slide.shapes.add_textbox(left, top, width, height)
        title_frame = title_shape.text_frame

        p = title_frame.add_paragraph()
        p.text = title
        p.font.size = DEFAULT_TITLE_FONT_SIZE
        p.font.bold = True


def create_presentation(presentation_data: Presentation) -> BytesIO:
    """Generate a PowerPoint presentation based on the provided schema."""
    prs = PPTXPresentation()

    for slide in presentation_data.slides:
        if slide.type == "title":
            create_title_slide(prs, slide)
        elif slide.type == "bullet":
            create_bullet_slide(prs, slide)
        elif slide.type == "image":
            create_image_slide(prs, slide)
        elif slide.type == "table":
            create_table_slide(prs, slide)
        elif slide.type == "split":
            create_split_slide(prs, slide)

    # Save the presentation to a BytesIO object
    output = BytesIO()
    prs.save(output)
    output.seek(0)

    return output


def create_title_slide(prs: PPTXPresentation, slide_data: TitleSlide):
    """Create a title slide with a title and optional subtitle."""
    slide_layout = prs.slide_layouts.get_by_name("Title Slide")
    slide = prs.slides.add_slide(slide_layout)
    set_slide_title(slide, slide_data.title)

    # Set the subtitle if provided
    if slide_data.subtitle:
        subtitle = slide.placeholders[1]  # Subtitle placeholder
        subtitle.text = slide_data.subtitle


def create_bullet_slide(prs: PPTXPresentation, slide_data: BulletSlide):
    """Create a bullet point slide with an optional title and multi-level bullet points."""
    slide_layout = prs.slide_layouts.get_by_name("Title and Content")
    slide = prs.slides.add_slide(slide_layout)
    set_slide_title(slide, slide_data.title)

    # Add bullet points
    body_placeholder = slide.placeholders[1]
    insert_bulleted_list(slide, body_placeholder, slide_data.points)


def insert_bulleted_list(
    _slide: Slide, placeholder: SlidePlaceholder, points: List[BulletPoint]
):
    """Insert a bulleted list into a placeholder on a slide."""
    text_frame = placeholder.text_frame

    # Clear any existing text
    text_frame.clear()

    # Add bullet points
    for point in points:
        add_bullet_point(text_frame, point, 0)


def add_bullet_point(text_frame: TextFrame, point: BulletPoint, current_level: int):
    """Recursively add bullet points with proper indentation."""
    p = text_frame.add_paragraph()
    p.text = point.text
    p.level = current_level  # Use the current nesting level

    # Add child bullet points recursively
    for child in point.children:
        add_bullet_point(text_frame, child, current_level + 1)


def insert_image(
    slide: Slide,
    placeholder: SlidePlaceholder,
    url: str,
    alt_text: Optional[str] = None,
):
    """Insert an image into a placeholder on a slide."""
    img_stream, image_source, error_message = load_image_from_url_or_fallback(url)

    if image_source == "error":
        # If both original image and placeholder failed
        left = placeholder.left
        top = placeholder.top
        width = placeholder.width
        height = placeholder.height

        err_shape = slide.shapes.add_textbox(left, top, width, height)
        err_frame = err_shape.text_frame

        p = err_frame.add_paragraph()
        p.text = IMAGE_UNAVAILABLE_TEXT

        # Add presenter notes with error details
        add_presenter_notes(slide, f"Image placeholder error: {error_message}")
        return

    try:
        if isinstance(placeholder, PicturePlaceholder):
            # Add the image to the placeholder
            pic = placeholder.insert_picture(img_stream)
        else:
            pic = slide.shapes.add_picture(
                img_stream,
                placeholder.left,
                placeholder.top,
                width=placeholder.width,
                height=placeholder.height,
            )
    except Exception as e:
        combined_error = f"Failed to add image to placeholder: {str(e)}"
        logger.error(combined_error)
        add_presenter_notes(slide, combined_error)
    else:
        if alt_text:
            pic.name = alt_text
    # Add presenter notes with error details if we used the placeholder
    if image_source == "placeholder":
        add_presenter_notes(
            slide, f"Warning: Image could not be loaded. {error_message}"
        )


def insert_table(
    slide: Slide,
    placeholder: SlidePlaceholder,
    headers: List[str],
    rows: List[List[str]],
):
    """Insert a table into a placeholder on a slide."""
    if not headers or not rows:
        return

    # Calculate table dimensions
    num_rows = len(rows) + 1  # +1 for header row
    num_cols = len(headers)

    # Add the table
    try:
        table = slide.shapes.add_table(
            num_rows,
            num_cols,
            placeholder.left,
            placeholder.top,
            placeholder.width,
            placeholder.height,
        ).table

        # Add headers
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.bold = True

        # Add data rows
        for i, row in enumerate(rows):
            for j, cell_text in enumerate(row):
                if j < num_cols:  # Ensure we don't exceed the column count
                    cell = table.cell(i + 1, j)  # +1 to skip header row
                    cell.text = cell_text
    except Exception as e:
        error_message = f"Failed to create table: {str(e)}"
        logger.error(error_message, exc_info=True)
        add_presenter_notes(slide, error_message)


def create_image_slide(prs: PPTXPresentation, slide_data: ImageSlide):
    """Create a slide with an image."""
    slide_layout = prs.slide_layouts.get_by_name("Title and Content")
    slide = prs.slides.add_slide(slide_layout)
    set_slide_title(slide, slide_data.title)

    # Add the image
    body_placeholder = slide.placeholders[1]
    insert_image(slide, body_placeholder, slide_data.url, slide_data.alt)


def create_table_slide(prs: PPTXPresentation, slide_data: TableSlide):
    """Create a slide with a table."""
    slide_layout = prs.slide_layouts.get_by_name("Title and Content")
    slide = prs.slides.add_slide(slide_layout)
    set_slide_title(slide, slide_data.title)

    # Add the table
    body_placeholder = slide.placeholders[1]
    insert_table(slide, body_placeholder, slide_data.headers, slide_data.rows)


def create_split_slide(prs: PPTXPresentation, slide_data: SplitSlide):
    """Create a slide with split content (two sections side by side)."""
    slide_layout = prs.slide_layouts.get_by_name("Two Content")
    slide = prs.slides.add_slide(slide_layout)
    set_slide_title(slide, slide_data.title)

    left_placeholder = slide.placeholders[1]
    right_placeholder = slide.placeholders[2]
    if len(slide_data.sections) > 2:
        add_presenter_notes(
            slide,
            f"Warning: Only the first two of {len(slide_data.sections)} sections are displayed.",
        )
    for ph, section in zip(
        [left_placeholder, right_placeholder], slide_data.sections[:2]
    ):
        if section.type == "bullet":
            insert_bulleted_list(slide, ph, section.points)
        elif section.type == "image":
            insert_image(slide, ph, section.url, section.alt)
        elif section.type == "table":
            insert_table(slide, ph, section.headers, section.rows)
        else:
            add_presenter_notes(
                slide, f"Warning: Unsupported section type: {section.type}"
            )
            continue
