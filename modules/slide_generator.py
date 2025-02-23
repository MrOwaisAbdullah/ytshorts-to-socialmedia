from datetime import datetime
import streamlit as st
import json
import io
import os
from PIL import Image, ImageDraw, ImageFont
from modules.ai_client import client, model_name
import textwrap
from zipfile import ZipFile
import tempfile
from typing import List
from pydantic import BaseModel
from data.templates import sample_templates_carousel

# Pydantic models
class Slide(BaseModel):
    title: str  
    points: List[str]

class CreateLinkedInCarousel(BaseModel):
    caption: str
    slides: List[Slide]

# Session State Initialization
if 'slides_data' not in st.session_state:
    st.session_state.slides_data = None
if 'slides_images' not in st.session_state:
    st.session_state.slides_images = None
if 'current_slide' not in st.session_state:
    st.session_state.current_slide = 1
if 'editing_mode' not in st.session_state:
    st.session_state.editing_mode = False
if 'edited_slides' not in st.session_state:
    st.session_state.edited_slides = None
if 'current_style' not in st.session_state:
    st.session_state.current_style = {
        "font_family": "NotoSans-Regular",
        "letter_spacing": 0.0,
        "background_type": "Gradient",
        "background_color": None,
        "background_gradient": ("#8E2DE2", "#4A00E0"),
        "background_image": None,
        "text_color": "#FFFFFF",
        "font_style": "Professional",
        "guidelines": "Use professional tone, include statistics when available, make content scannable"
    }

# Helper Functions
def create_download_zip(slides_images):
    """Create a ZIP file containing all slides"""
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, img in enumerate(slides_images, 1):
            img_path = os.path.join(temp_dir, f'slide_{i}.png')
            img.save(img_path, 'PNG')
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            for i in range(1, len(slides_images) + 1):
                img_path = os.path.join(temp_dir, f'slide_{i}.png')
                zip_file.write(img_path, f'slide_{i}.png')
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

def update_slide():
    """Update current slide based on slider value"""
    st.session_state.current_slide = st.session_state.slide_navigator
    
def generate_slides_content(transcript, style):
    # Enhanced prompt with explicit JSON structure
    prompt = f"""
    You are an expert in creating engaging LinkedIn carousel posts.

    Generate a LinkedIn carousel post as JSON with EXACTLY this structure:
{{
    "caption": "3-5 engaging sentences with emojis 🚀",
    "slides": [
        {{
            "title": "Short title under 60 chars",
            "points": ["Point 1", "Point 2", "Point 3"]
        }},
        // 4-6 more slides
    ]
}}

Rules:
1. Use simple, relatable language for easy understanding.
2. Create exactly 5 to 7 slides, each with a title under 60 characters and 3 concise bullet points.
3. Emphasize storytelling with personal experiences, lessons, or steps.
4. Make the caption short, engaging, and include emojis and hashtags.
5. Use these sample templates for inspiration:
{sample_templates_carousel}

6. Follow these style guidelines: {style['guidelines']}

Content to transform:
{transcript}
"""

    try:
        # Generate initial response
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        
        # Clean and validate initial response
        raw_text = response.text.strip()
        cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        # Debugging output
        # st.write("Initial Gemini Response:", repr(raw_text))

        # First parse attempt
        try:
            initial_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Handle array responses
            if cleaned_text.startswith("["):
                initial_data = {"slides": json.loads(cleaned_text)}
            else:
                # Attempt to fix common formatting issues
                cleaned_text = cleaned_text.replace("'", '"')
                initial_data = json.loads(cleaned_text)

        # Ensure required fields exist
        initial_data.setdefault("caption", "🔥 Valuable Insights #CareerGrowth")
        initial_data.setdefault("slides", [])

        # Validate and sanitize slides
        valid_slides = []
        for slide in initial_data.get("slides", []):
            if isinstance(slide, dict):
                valid_slide = {
                    "title": str(slide.get("title", "Key Point"))[:60],
                    "points": [str(p)[:120] for p in slide.get("points", [])][:3]
                }
                valid_slides.append(valid_slide)
        
        # Fallback if no valid slides
        if not valid_slides:
            valid_slides = [{
                "title": "Important Insights",
                "points": ["Valuable content coming soon", "Check back later", "We're working on it"]
            }]

        # Ensure slide count constraint
        valid_slides = valid_slides[:7]  # Maximum 7 slides
        if len(valid_slides) < 5:
            st.warning(f"Only {len(valid_slides)} slides generated. Adding placeholder slides.")
            while len(valid_slides) < 5:
                valid_slides.append({
                    "title": f"Bonus Tip {len(valid_slides)+1}",
                    "points": ["Great content coming soon"]
                })

        return CreateLinkedInCarousel(
            caption=initial_data["caption"],
            slides=[Slide(**s) for s in valid_slides]
        )

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        st.error(f"Critical Generation Error: {str(e)}")
        return CreateLinkedInCarousel(
            caption="⚠️ Let's Try Again Together!",
            slides=[
                Slide(title="Oops! Something Went Wrong", points=["We're refreshing the system", "Try again in 30 seconds"]),
                Slide(title="Your Content Matters", points=["We're working hard", "To deliver your carousel"]),
                Slide(title="Pro Tip While You Wait", points=["Double-check your input", "Clear, specific content", "Works best!"])
            ]
        )
    
def draw_text_with_spacing(draw, position, text, font, fill, spacing, center=False):
    x, y = position
    if isinstance(font, ImageFont.FreeTypeFont):
        if center:
            # Calculate total width including spacing
            total_width = sum(font.getbbox(char)[2] for char in text) + spacing * (len(text) - 1)
            x -= total_width / 2  # Adjust x to center the text
        for char in text:
            draw.text((x, y), char, font=font, fill=fill)
            char_width = font.getbbox(char)[2]  # Get width from bounding box
            x += char_width + spacing
    else:
        # Fallback for non-TrueType fonts
        draw.text((x, y), text, font=font, fill=fill)
        st.warning("Letter spacing not applied due to unavailable TrueType font.")

def create_slide_image(title, points, style):
    width = 1080
    height = 1080
    img = Image.new('RGB', (width, height), (255, 255, 255))  # White background
    draw = ImageDraw.Draw(img)
    
    # Apply background (unchanged from your logic)
    if style['background_type'] == "Solid" and style['background_color']:
        img.paste(style['background_color'], (0, 0, width, height))
    elif style['background_type'] == "Gradient" and style['background_gradient']:
        start_color = tuple(int(style['background_gradient'][0][i:i+2], 16) for i in (1, 3, 5))
        end_color = tuple(int(style['background_gradient'][1][i:i+2], 16) for i in (1, 3, 5))
        for y in range(height):
            r = int(start_color[0] + (end_color[0] - start_color[0]) * (y / height))
            g = int(start_color[1] + (end_color[1] - start_color[1]) * (y / height))
            b = int(start_color[2] + (end_color[2] - start_color[2]) * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    elif style['background_type'] == "Image" and style['background_image']:
        bg_image = Image.open(style['background_image']).resize((width, height))
        img.paste(bg_image)

    # Load fonts with fallback (unchanged)
    try:
        font_path = os.path.join(os.getcwd(), "fonts", f"{style['font_family']}.ttf")
        title_font = ImageFont.truetype(font_path, 60)
        body_font = ImageFont.truetype(font_path, 40)
    except OSError:
        st.warning(f"Font {style['font_family']} not found. Using Arial as fallback.")
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            body_font = ImageFont.truetype("arial.ttf", 40)
        except OSError:
            st.error("No TrueType fonts available. Using default font without spacing.")
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

    # Draw title (centered)
    title_wrapped = textwrap.fill(title, width=30)
    lines = title_wrapped.split('\n')
    y = 100
    for line in lines:
        draw_text_with_spacing(draw, (width // 2, y), line, title_font, style['text_color'], 
                              style['letter_spacing'], center=True)
        y += 60  # Line height

    # Draw points (unchanged)
    y_position = 300
    for point in points:
        wrapped_point = textwrap.fill(point, width=40)
        lines = wrapped_point.split('\n')
        for line in lines:
            draw_text_with_spacing(draw, (120, y_position), line, body_font, style['text_color'], 
                                  style['letter_spacing'])
            y_position += 40  # Line height
        y_position += 20  # Space between points

    return img

def apply_text_changes():
    current_index = st.session_state.current_slide - 1
    slide = st.session_state.edited_slides[current_index]
    slide_img = create_slide_image(slide.title, slide.points, st.session_state.current_style)
    st.session_state.slides_images[current_index] = slide_img
    st.session_state.editing_mode = False

def update_slide_content():
    if st.session_state.edited_slides:
        slides_images = []
        for slide in st.session_state.edited_slides:
            slide_img = create_slide_image(slide.title, slide.points, st.session_state.current_style)
            slides_images.append(slide_img)
        st.session_state.slides_images = slides_images

def edit_slide_content(index):
    """Edit the title and points of a specific slide."""
    slide = st.session_state.edited_slides[index]
    new_title = st.text_input("Edit Title", value=slide.title, key=f"title_{index}")
    new_points = []
    for i, point in enumerate(slide.points):
        new_point = st.text_input(f"Point {i+1}", value=point, key=f"point_{index}_{i}")
        new_points.append(new_point)
    st.session_state.edited_slides[index] = Slide(title=new_title, points=new_points)

def create_style_editor():
    st.sidebar.subheader("Edit Style")
    
    # Get current style from session state
    current_style = st.session_state.current_style
    
    font_options = ["NotoSans-Regular", "Arial", "Times New Roman", "Courier New"]
    font_family = st.sidebar.selectbox("Font Family", font_options, 
                                     index=font_options.index(current_style["font_family"]) if current_style["font_family"] in font_options else 0, 
                                     key="style_editor_font_family")
    
    letter_spacing = st.sidebar.slider("Letter Spacing", min_value=0.0, max_value=5.0, 
                                     value=current_style["letter_spacing"], 
                                     step=0.1, key="style_editor_letter_spacing")
    
    background_type = st.sidebar.selectbox("Background Type", ["Solid", "Gradient", "Image"], 
                                         index=["Solid", "Gradient", "Image"].index(current_style["background_type"]),
                                         key="style_editor_background_type")
    
    if background_type == "Gradient":
        gradient_start = st.sidebar.color_picker("Gradient Start Color", 
                                               current_style["background_gradient"][0] if current_style["background_gradient"] else "#FFFFFF", 
                                               key="style_editor_gradient_start")
        gradient_end = st.sidebar.color_picker("Gradient End Color", 
                                             current_style["background_gradient"][1] if current_style["background_gradient"] else "#000000", 
                                             key="style_editor_gradient_end")
        background_color = None
        background_gradient = (gradient_start, gradient_end)
        background_image = None
    elif background_type == "Solid":
        background_color = st.sidebar.color_picker("Background Color", 
                                                 current_style["background_color"] or "#FFFFFF", 
                                                 key="style_editor_bg_color")
        background_gradient = None
        background_image = None
    else:  # Image
        background_image = st.sidebar.file_uploader("Upload Background Image", 
                                                  type=["png", "jpg", "jpeg"], 
                                                  key="style_editor_bg_image")
        background_color = None
        background_gradient = None
    
    text_color = st.sidebar.color_picker("Text Color", 
                                       current_style["text_color"], 
                                       key="style_editor_text_color")
    
    font_style = st.sidebar.selectbox("Style", ["Professional", "Creative", "Minimalist", "Bold"], 
                                    index=["Professional", "Creative", "Minimalist", "Bold"].index(current_style["font_style"]),
                                    key="style_editor_font_style")
    
    # Update both current_style and carousel_style
    updated_style = {
        "font_family": font_family,
        "letter_spacing": letter_spacing,
        "background_type": background_type,
        "background_color": background_color,
        "background_gradient": background_gradient,
        "background_image": background_image,
        "text_color": text_color,
        "font_style": font_style,
        "guidelines": current_style["guidelines"]
    }
    
    st.session_state.current_style = updated_style
    st.session_state.carousel_style = updated_style.copy()  # Keep carousel_style in sync

def create_carousel(slides_images):
    if not slides_images:
        return
    
    st.markdown("""
        <style>
        .carousel-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            gap: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():

        col1, col2, col3 = st.columns([1, 8, 1], vertical_alignment="center")
        with col1:
            if st.button("◀", key="prev_slide"):
                if st.session_state.current_slide > 1:
                    st.session_state.current_slide -= 1
        with col2:
            st.image(slides_images[st.session_state.current_slide - 1],
                     caption=f"Slide {st.session_state.current_slide}/{len(slides_images)}",
                     use_container_width=True)
        with col3:
            if st.button("▶", key="next_slide"):
                if st.session_state.current_slide < len(slides_images):
                    st.session_state.current_slide += 1

        # st.slider("Navigate slides", min_value=1, max_value=len(slides_images),
        #           value=st.session_state.current_slide, key="slide_navigator",
        #           on_change=update_slide)
        
        with st.expander("Edit Current Slide", expanded=False):
            edit_slide_content(st.session_state.current_slide - 1)
            if st.button("Apply Text Changes"):
                apply_text_changes()
    
def main():
    st.title("LinkedIn Slides Generator")

    if not st.session_state.slides_data:
        input_text = st.text_area("Paste your content here (article, video script, etc.)", height=200, key="input_text_area")
        st.subheader("Customize Your Slides")
        col1, col2, col3 = st.columns(3)
        with col1:
            gradient_start = st.sidebar.color_picker("Gradient Start Color", "#FFFFFF", 
                                                    key="style_editor_gradient_start")
            gradient_end = st.sidebar.color_picker("Gradient End Color", "#000000", 
                                                key="style_editor_gradient_end")
        with col2:
            text_color = st.color_picker("Text Color", "#000000", key="initial_text_color")
        with col3:
            font_style = st.selectbox("Style", ["Professional", "Creative", "Minimalist", "Bold"], index=0, key="initial_font_style")
            style = {
                "font_family": "NotoSans-Regular", 
                "letter_spacing": 0.0,             
                "background_type": "Gradient",        
                "background_color": None,
                "background_gradient": (gradient_start, gradient_end),
                "background_image": None,
                "text_color": text_color,
                "font_style": font_style,
                "guidelines": "Use professional tone, include statistics when available, make content scannable"
            }
        if st.button("Generate Slides", key="generate_button"):
            if input_text:
                with st.spinner("Generating slides..."):
                    try:
                        slides_data = generate_slides_content(input_text, style)
                        if slides_data and slides_data.caption and slides_data.slides:
                            st.session_state.slides_data = slides_data
                            st.session_state.edited_slides = slides_data.slides
                            st.session_state.current_style = style
                            update_slide_content()
                            st.success("Slides generated successfully!")
                        else:
                            st.error("Failed to generate slides")
                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                        st.error(f"An error occurred: {str(e)}")
            else:
                st.error("Please enter some content to generate slides.")
    if st.session_state.slides_data and st.session_state.slides_images:
        create_style_editor()
        st.subheader("LinkedIn Caption")
        st.text_area("Caption (copy this to your LinkedIn post)", st.session_state.slides_data.caption, height=100, key="caption_display")
        st.subheader("Preview Slides")
        create_carousel(st.session_state.slides_images)
        if st.sidebar.button("Apply Style Changes", key="apply_style_button"):
            update_slide_content()
        col1, col2 = st.columns(2)
        file_name = f"linkedin_slides_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with col1:
            zip_data = create_download_zip(st.session_state.slides_images)
            st.download_button(label="📥 Download All Slides", data=zip_data, file_name=file_name, mime="application/zip", key="download_all_button")
        with col2:
            if st.button("Show Individual Downloads", key="show_individual_downloads"):
                for i, img in enumerate(st.session_state.slides_images, 1):
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(label=f"Download Slide {i}", data=buf.getvalue(), file_name=f"{file_name}_{i}.png", mime="image/png", key=f"download_slide_{i}")

if __name__ == "__main__":
    main()