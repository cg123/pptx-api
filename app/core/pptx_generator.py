from io import BytesIO
from pptx import Presentation as PPTXPresentation
from pptx.util import Inches, Pt

from app.schemas.presentation import Presentation, TitleSlide, BulletSlide, BulletPoint


def create_presentation(presentation_data: Presentation) -> BytesIO:
    """Generate a PowerPoint presentation based on the provided schema."""
    prs = PPTXPresentation()
    
    for slide in presentation_data.slides:
        if slide.type == "title":
            create_title_slide(prs, slide)
        elif slide.type == "bullet":
            create_bullet_slide(prs, slide)
    
    # Save the presentation to a BytesIO object
    output = BytesIO()
    prs.save(output)
    output.seek(0)
    
    return output


def create_title_slide(prs: PPTXPresentation, slide_data: TitleSlide):
    """Create a title slide with a title and optional subtitle."""
    slide_layout = prs.slide_layouts[0]  # Title Slide layout
    slide = prs.slides.add_slide(slide_layout)
    
    # Set the title
    title = slide.shapes.title
    title.text = slide_data.title
    
    # Set the subtitle if provided
    if slide_data.subtitle:
        subtitle = slide.placeholders[1]  # Subtitle placeholder
        subtitle.text = slide_data.subtitle


def create_bullet_slide(prs: PPTXPresentation, slide_data: BulletSlide):
    """Create a bullet point slide with an optional title and multi-level bullet points."""
    slide_layout = prs.slide_layouts[1]  # Bullet point layout
    slide = prs.slides.add_slide(slide_layout)
    
    # Set the title if provided
    if slide_data.title:
        title = slide.shapes.title
        title.text = slide_data.title
    
    # Add bullet points
    shapes = slide.shapes
    body_shape = shapes.placeholders[1]  # Content placeholder
    text_frame = body_shape.text_frame
    
    # Clear any existing text
    text_frame.clear()
    
    # Add bullet points
    for point in slide_data.points:
        add_bullet_point(text_frame, point, 0)


def add_bullet_point(text_frame, point: BulletPoint, current_level: int):
    """Recursively add bullet points with proper indentation."""
    p = text_frame.add_paragraph()
    p.text = point.text
    p.level = point.level
    
    # Add child bullet points recursively
    for child in point.children:
        add_bullet_point(text_frame, child, current_level + 1)