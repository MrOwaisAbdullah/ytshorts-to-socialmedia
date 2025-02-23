import streamlit as st
from modules.slide_generator import create_carousel, create_download_zip, update_slide_content, generate_slides_content, create_style_editor, Slide, CreateLinkedInCarousel
from modules.linkedin_post import generate_linkedin_posts
from modules.x_threads import generate_thread_content
from modules.x_tweets import generate_tweet_content
from modules.youtube_helpers import extract_youtube_short_id, get_youtube_transcript_with_searchapi
from modules.ai_client import client, model_name
import streamlit.components.v1 as components
import html


# Custom Copy to Clipboard Function
def copy_to_clipboard(text):
    safe_text = html.escape(text).replace("\n", "\\n")
    components.html(
        f"""
        <html>
          <head>
            <style>
              .copy-button {{
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
              }}
            </style>
            <script>
              function copyText() {{
                navigator.clipboard.writeText("{safe_text}")
                  .then(function() {{
                    alert("Copied to clipboard!");
                  }})
                  .catch(function(err) {{
                    alert("Copy failed: " + err);
                  }});
              }}
            </script>
          </head>
          <body>
            <button class="copy-button" onclick="copyText()">Copy to Clipboard</button>
          </body>
        </html>
        """,
        height=50,
        scrolling=False,
    )

# Initialize session state
def initialize_session_state():
    if "transcript" not in st.session_state:
        st.session_state.transcript = None
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Home"
    if "linkedin_posts" not in st.session_state:
        st.session_state.linkedin_posts = None
    if "x_threads" not in st.session_state:
        st.session_state.x_threads = None
    if "x_tweets" not in st.session_state:
        st.session_state.x_tweets = None
    if "carousel_data" not in st.session_state:
        st.session_state.carousel_data = None
    if "carousel_style" not in st.session_state:
        st.session_state.carousel_style = {
            "background_color": "#FFFFFF",
            "text_color": "#000000",
            "font_style": "Professional",
            "guidelines": "Use professional tone, include statistics when available, make content scannable"
        }
    if "current_style" not in st.session_state:
        st.session_state.current_style = st.session_state.carousel_style
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

initialize_session_state()

# Sidebar Navigation
st.sidebar.title("Navigation")
if st.sidebar.button("Home"):
    st.session_state.selected_tab = "Home"
    st.rerun()
if st.sidebar.button("LinkedIn Posts"):
    st.session_state.selected_tab = "LinkedIn Posts"
    st.rerun()
if st.sidebar.button("X Tweets"):
    st.session_state.selected_tab = "X Tweets"
    st.rerun()
if st.sidebar.button("X Threads"):
    st.session_state.selected_tab = "X Threads"
    st.rerun()
if st.sidebar.button("LinkedIn Carousel"):
    st.session_state.selected_tab = "LinkedIn Carousel"
    st.rerun()

# Main Page Logic

### Home Tab
if st.session_state.selected_tab == "Home":
    st.title("YouTube Short to Social Media Content Converter")
    video_input = st.text_input("Enter YouTube Shorts URL or ID (English):", "")
    if st.button("Fetch Transcript"):
        with st.spinner("Starting transcript fetch..."):
        # Initialize progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_value = 0

            try:
                # Step 1: Validating and extracting video ID
                progress_text.text("Validating input...")
                video_id = extract_youtube_short_id(video_input)
                progress_value += 0.33  # 33% complete
                progress_bar.progress(progress_value)

                # Step 2: Fetching transcript
                progress_text.text("Fetching YouTube transcript...")
                transcript = get_youtube_transcript_with_searchapi(video_id)
                progress_value += 0.33  # 66% complete
                progress_bar.progress(progress_value)

                # Step 3: Finalizing transcript
                progress_text.text("Finalizing transcript fetch...")
                st.session_state.transcript = transcript
                progress_value += 0.34  # 100% complete
                progress_bar.progress(progress_value)
                progress_text.text("")
                st.success("Transcript fetched successfully!")
            except (ValueError, TypeError) as e:
                st.error(f"Error fetching transcript: {str(e)}")

    if st.session_state.transcript:
        st.markdown("**Transcript**")
        st.markdown(
            f'<div class="content-box">{st.session_state.transcript}</div>',
            unsafe_allow_html=True
        )
        copy_to_clipboard(st.session_state.transcript)
    else:
        st.session_state.transcript = st.text_area("Or paste your own content here:", height=200)

### LinkedIn Posts Tab
elif st.session_state.selected_tab == "LinkedIn Posts":
    st.title("Generate LinkedIn Posts")
    if st.session_state.transcript:
        st.subheader("Transcript:")
        st.write(st.session_state.transcript)
    context_input = None
    if st.session_state.transcript:
        context_input = st.text_area("Enter additional context or details (optional):", height=100)
    num_variations = st.slider("Number of post variations", 1, 5, 3)
    if not st.session_state.transcript:
        st.warning("No transcript found. Fetch one on the Home tab or paste your own content below.")
        st.session_state.transcript = st.text_area("Enter your custom content:", height=200)
    if st.button("Generate Posts"):
        with st.spinner("Starting post generation..."):
            # Initialize progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_value = 0

            try:
                # Step 1: Preparing post generation
                progress_text.text("Preparing LinkedIn post generation...")

                # Step 2: Generating posts
                progress_text.text("Generating LinkedIn posts...")
                posts = generate_linkedin_posts(st.session_state.transcript, client, model_name, context_input, num_variations=num_variations)
                progress_value += 0.4  # 40% complete
                progress_bar.progress(progress_value)

                # Step 3: Finalizing posts
                progress_text.text("Finalizing LinkedIn posts...")
                st.session_state.linkedin_posts = posts
                progress_value += 0.6  # 100% complete
                progress_bar.progress(progress_value)
                progress_text.text("")
                st.success("Posts generated successfully!")
            except (ValueError, TypeError) as e:
                st.error(f"Error generating posts: {str(e)}")

    if st.session_state.linkedin_posts:
        for i, post in enumerate(st.session_state.linkedin_posts, 1):
            st.markdown(f"**Post {i}**")
            st.markdown(
                f'<div class="content-box">{post}</div>',
                unsafe_allow_html=True
            )
            copy_to_clipboard(post)

### X Tweets Tab
elif st.session_state.selected_tab == "X Tweets":
    st.title("Generate X Tweets")
    context_input = None
    if st.session_state.transcript:
        st.subheader("Transcript:")
        st.write(st.session_state.transcript)
        context_input = st.text_area("Enter additional context or details (optional):", height=100)
    num_variations = st.slider("Number of tweet variations", 1, 5, 3)
    if not st.session_state.transcript:
        st.warning("No transcript found. Fetch one on the Home tab or paste your own content below.")
        st.session_state.transcript = st.text_area("Enter your custom content:", height=200)
    if st.button("Generate Tweets"):
        with st.spinner("Starting tweet generation..."):
            # Initialize progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_value = 0

            try:
                # Step 1: Preparing tweet generation
                progress_text.text("Preparing X tweet generation...")

                # Step 2: Generating tweets
                progress_text.text("Generating X tweets...")
                tweets = generate_tweet_content(
                    st.session_state.transcript,
                    context_input,
                    client,
                    model_name,
                    num_variations=num_variations
                )
                progress_value += 0.4  # 40% complete
                progress_bar.progress(progress_value)

                # Step 3: Finalizing tweets
                progress_text.text("Finalizing X tweets...")
                st.session_state.x_tweets = tweets
                progress_value += 0.6  # 100% complete
                progress_bar.progress(progress_value)
                progress_text.text("")
                st.success(f"Generated {len(tweets)} tweets successfully!")
            except (ValueError, TypeError) as e:
                st.error(f"Error generating tweets: {str(e)}")

    if st.session_state.x_tweets:
        for i, tweet in enumerate(st.session_state.x_tweets, 1):
            st.markdown(f"**Tweet Variation {i}**")
            st.markdown(
                f'<div class="content-box">{tweet}</div>',
                unsafe_allow_html=True
            )
            copy_to_clipboard(tweet)

### X Threads Tab
elif st.session_state.selected_tab == "X Threads":
    st.title("Generate X Threads")
    st.subheader("Transcript:")
    st.write(st.session_state.transcript)
    context_input = None
    if st.session_state.transcript:
        context_input = st.text_area("Enter additional context or details (optional):", height=100)
    num_tweets = st.slider("Number of tweets in thread", 2, 10, 5)
    if not st.session_state.transcript:
        st.warning("No transcript found. Fetch one on the Home tab or paste your own content below.")
        st.session_state.transcript = st.text_area("Enter your custom content:", height=200)
    if st.button("Generate Thread"):
        with st.spinner("Starting thread generation..."):
            # Initialize progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_value = 0

            try:
                # Step 1: Preparing thread generation
                progress_text.text("Preparing X thread generation...")

                # Step 2: Generating thread
                progress_text.text("Generating X thread...")
                threads = generate_thread_content(
                    st.session_state.transcript,
                    context_input,
                    num_tweets,
                    client,
                    model_name
                )
                progress_value += 0.4  # 40% complete
                progress_bar.progress(progress_value)

                # Step 3: Finalizing thread
                progress_text.text("Finalizing X thread...")
                st.session_state.x_threads = threads
                progress_value += 0.6  # 100% complete
                progress_bar.progress(progress_value)
                progress_text.text("")
                st.success(f"Generated {len(threads)} tweets in thread!")
            except (ValueError, TypeError) as e:
                st.error(f"Error generating thread: {str(e)}")

    if st.session_state.x_threads:
        for i, tweet in enumerate(st.session_state.x_threads, 1):
            st.markdown(f"**Tweet {i} in Thread**")
            st.markdown(
                f'<div class="content-box">{tweet}</div>',
                unsafe_allow_html=True
            )
            copy_to_clipboard(tweet)

### LinkedIn Carousel Tab
elif st.session_state.selected_tab == "LinkedIn Carousel":
    st.title("Generate LinkedIn Carousel")
    if st.session_state.transcript:
        st.subheader("Transcript:")
        st.write(st.session_state.transcript)
    # Style customization in sidebar
    create_style_editor()
    
    if not st.session_state.transcript:
        st.warning("No transcript found. Fetch one on the Home tab or paste your own content below.")
        st.session_state.transcript = st.text_area("Enter your custom content:", height=200)
    
    if st.button("Generate Carousel"):
        with st.spinner("Starting carousel generation..."):
            # Initialize progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_value = 0

            try:
                # Step 1: Preparing carousel generation
                progress_text.text("Preparing carousel generation...")

                # Step 2: Generating initial carousel
                progress_text.text("Generating initial carousel...")
                carousel_data = generate_slides_content(st.session_state.transcript, st.session_state.carousel_style, client, model_name)
                progress_value += 0.4  # 40% complete
                progress_bar.progress(progress_value)

                # Step 3: Finalizing carousel
                progress_text.text("Finalizing carousel content...")
                if carousel_data:
                    st.session_state.carousel_data = carousel_data
                    st.session_state.edited_slides = carousel_data.slides
                    st.session_state.current_style = st.session_state.carousel_style
                    update_slide_content()
                    progress_value += 0.6  # 100% complete
                    progress_bar.progress(progress_value)
                    progress_text.text("")
                    st.success("Carousel generated successfully!")
                else:
                    st.error("Failed to generate carousel")

            except (ValueError, TypeError) as e:
                st.error(f"Error generating carousel: {str(e)}")
                st.session_state.carousel_data = CreateLinkedInCarousel(
                    caption="⚠️ Oops! Let's try that again...",
                    slides=[
                        Slide(title="Temporary Issue", points=["Please try again", "Check your input", "Refresh the page"]),
                        Slide(title="We're On It", points=["Our team has been notified", "Working on a fix", "Thanks for your patience"])
                    ]
                )
                update_slide_content()

    if st.session_state.carousel_data and st.session_state.get("slides_images"):
        st.markdown("**Caption**")
        st.markdown(
            f'<div class="content-box">{st.session_state.carousel_data.caption}</div>',
            unsafe_allow_html=True
        )
        copy_to_clipboard(st.session_state.carousel_data.caption)
        create_carousel(st.session_state.slides_images)
        if st.sidebar.button("Apply Style Changes"):
            st.session_state.current_style = st.session_state.carousel_style
            update_slide_content()
        zip_data = create_download_zip(st.session_state.slides_images)
        st.download_button("Download All Slides", zip_data, "linkedin_slides.zip", "application/zip")

# CSS for content boxes
st.markdown("""
    <style>
    .content-box {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-family: Arial, sans-serif;
        color: inherit;
    }
    </style>
""", unsafe_allow_html=True)