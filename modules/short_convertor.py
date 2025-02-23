import streamlit as st
from data.templates import post_reviewer_prompt, templates_1, templates_2, templates_3, templates_5, prompt_short_to_post
import youtube_helpers
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Set up the Gemini client using the environment variable
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
client = genai.Client(api_key=api_key)
model_name = "gemini-2.0-flash" 

st.title("YouTube Short to LinkedIn Post Converter")

# Video ID Input
video_id = st.text_input("Enter YouTube Video ID:", "CYTwGx43SzY")

if st.button("Generate Posts"):
    with st.spinner('Fetching YouTube content...'):
        content = youtube_helpers.get_youtube_transcript_with_searchapi(video_id)
        # Prepare prompts
        prompt_template_1 = prompt_short_to_post.format(video=content, post_templates=templates_1)
        prompt_template_2 = prompt_short_to_post.format(video=content, post_templates=templates_2)
        prompt_template_3 = prompt_short_to_post.format(video=content, post_templates=templates_3)
        prompt_template_5 = prompt_short_to_post.format(video=content, post_templates=templates_5)
        st.success('Content fetched successfully!')
    
    progress = st.progress(0)
    progress_value = 0
    progress_text = st.empty()
    
    # Generate responses directly with the client
    gemini_responses = []
    for idx, template in enumerate([prompt_template_1, prompt_template_2, prompt_template_3, prompt_template_5]):
        # Generate initial response
        progress_text.text(f'Generating Response {idx + 1} (initial)...')
        initial_response = client.models.generate_content(
            model=model_name,
            contents=template
        ).text
        
        # Generate reviewed response
        progress_text.text(f'Generating Response {idx + 1} (reviewed)...')
        reviewed_prompt = post_reviewer_prompt.format(post=initial_response)
        checked_response = client.models.generate_content(
            model=model_name,
            contents=reviewed_prompt
        ).text
        
        gemini_responses.append(checked_response)
        progress_value += 0.25  # Increment after each template is fully processed
        progress.progress(progress_value)
    
    progress_text.text('All responses generated!')
    st.success('All responses generated successfully!')

    # Display results
    st.subheader("Gemini Responses")
    for idx, response in enumerate(gemini_responses):
        st.markdown(f"**Response {idx + 1}:**")
        st.info(response)