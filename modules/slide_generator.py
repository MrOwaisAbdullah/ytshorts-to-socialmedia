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
        "background_color": "#FFFFFF",
        "text_color": "#000000",
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

def create_slide_image(title, points, style):
    width = 1080
    height = 1080
    img = Image.new('RGB', (width, height), style['background_color'])
    draw = ImageDraw.Draw(img)
    try:
        # Use Noto Sans or Segoe UI Emoji for emoji support
        title_font = ImageFont.truetype("NotoSans-Regular.ttf", 60)
        body_font = ImageFont.truetype("NotoSans-Regular.ttf", 40)
    except OSError:
        try:
            # Fallback to Segoe UI Emoji (Windows)
            title_font = ImageFont.truetype("seguiemj.ttf", 60)
            body_font = ImageFont.truetype("seguiemj.ttf", 40)
        except OSError:
            # Last resort: default font (may not support emojis)
            st.warning("Emoji-supporting font not found. Emojis may appear as squares.")
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
    
    title_wrapped = textwrap.fill(title, width=30)
    title_bbox = draw.multiline_textbbox((0, 0), title_wrapped, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) / 2
    title_y = 100
    draw.multiline_text((title_x, title_y), title_wrapped, font=title_font, fill=style['text_color'], align='center')
    y_position = 300
    for point in points:
        wrapped_point = textwrap.fill(point, width=40)
        point_bbox = draw.multiline_textbbox((0, 0), wrapped_point, font=body_font)
        point_height = point_bbox[3] - point_bbox[1]
        draw.text((60, y_position), "•", font=body_font, fill=style['text_color'])
        draw.multiline_text((120, y_position), wrapped_point, font=body_font, fill=style['text_color'])
        y_position += point_height + 40
    return img

def update_slide_content():
    if st.session_state.edited_slides:
        slides_images = []
        for slide in st.session_state.edited_slides:
            slide_img = create_slide_image(slide.title, slide.points, st.session_state.current_style)
            slides_images.append(slide_img)
        st.session_state.slides_images = slides_images

def edit_slide_content(index):
    slide = st.session_state.edited_slides[index]
    new_title = st.text_input("Edit Title", value=slide.title, key=f"title_{index}")
    new_points = []
    for i, point in enumerate(slide.points):
        new_point = st.text_input(f"Point {i+1}", value=point, key=f"point_{index}_{i}")
        new_points.append(new_point)
    st.session_state.edited_slides[index] = Slide(title=new_title, points=new_points)

def create_style_editor():
    st.sidebar.subheader("Edit Style")
    background_color = st.sidebar.color_picker("Background Color", st.session_state.current_style.get("background_color", "#FFFFFF"), key="style_editor_bg_color")
    text_color = st.sidebar.color_picker("Text Color", st.session_state.current_style.get("text_color", "#000000"), key="style_editor_text_color")
    font_style = st.sidebar.selectbox("Style", ["Professional", "Creative", "Minimalist", "Bold"], index=0, key="style_editor_font_style")
    st.session_state.current_style = {
        "background_color": background_color,
        "text_color": text_color,
        "font_style": font_style,
        "guidelines": "Use professional tone, include statistics when available, make content scannable"
    }

def create_carousel(slides_images):
    if not slides_images:
        return
    col1, col2, col3 = st.columns([1, 8, 1])
    with col1:
        if st.button("◀") and st.session_state.current_slide > 1:
            st.session_state.current_slide -= 1
    with col2:
        st.image(slides_images[st.session_state.current_slide - 1],
                 caption=f"Slide {st.session_state.current_slide}/{len(slides_images)}",
                 use_container_width=True)
        if st.button("Edit Current Slide"):
            st.session_state.editing_mode = not st.session_state.editing_mode
    with col3:
        if st.button("▶") and st.session_state.current_slide < len(slides_images):
            st.session_state.current_slide += 1
    if st.session_state.editing_mode:
        edit_slide_content(st.session_state.current_slide - 1)
        if st.button("Apply Changes"):
            update_slide_content()
    st.slider("Navigate slides", min_value=1, max_value=len(slides_images),
              value=st.session_state.current_slide, key="slide_navigator", on_change=update_slide)
    
def main():
    st.title("LinkedIn Slides Generator")
    if not st.session_state.slides_data:
        input_text = st.text_area("Paste your content here (article, video script, etc.)", height=200, key="input_text_area")
        st.subheader("Customize Your Slides")
        col1, col2, col3 = st.columns(3)
        with col1:
            background_color = st.color_picker("Background Color", "#FFFFFF", key="initial_bg_color")
        with col2:
            text_color = st.color_picker("Text Color", "#000000", key="initial_text_color")
        with col3:
            font_style = st.selectbox("Style", ["Professional", "Creative", "Minimalist", "Bold"], index=0, key="initial_font_style")
        style = {
            "background_color": background_color,
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
        with col1:
            zip_data = create_download_zip(st.session_state.slides_images)
            st.download_button(label="📥 Download All Slides", data=zip_data, file_name="linkedin_slides.zip", mime="application/zip", help="Download all slides as a ZIP file", key="download_all_button")
        with col2:
            if st.button("Show Individual Downloads", key="show_individual_downloads"):
                for i, img in enumerate(st.session_state.slides_images, 1):
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(label=f"Download Slide {i}", data=buf.getvalue(), file_name=f"slide_{i}.png", mime="image/png", key=f"download_slide_{i}")

if __name__ == "__main__":
    main()