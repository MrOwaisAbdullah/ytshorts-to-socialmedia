from slide_generator import CreateLinkedInCarousel
from templates import tweet_reviewer_prompt, thread_reviewer_prompt, post_reviewer_prompt, carousel_reviewer_prompt
import streamlit as st
import json

def review_generated_tweet(generated_content, client, model_name):
    """
    Takes a single tweet and refines it using the tweet reviewer prompt.
    """
    reviewer_prompt = tweet_reviewer_prompt.format(post=generated_content)
    response = client.models.generate_content(model=model_name, contents=reviewer_prompt)
    reviewed_text = response.text.strip()
    return reviewed_text

def review_generated_thread(generated_content, client, model_name):
    """
    Takes a full thread (multiple tweets separated by "|||") and refines it using the thread reviewer prompt.
    """
    reviewer_prompt = thread_reviewer_prompt.format(post=generated_content)
    response = client.models.generate_content(model=model_name, contents=reviewer_prompt)
    reviewed_text = response.text.strip()
    
    # Ensure tweets remain separate by keeping delimiter "|||"
    if "|||" in reviewed_text:
        return [t.strip() for t in reviewed_text.split("|||") if t.strip()]
    return [reviewed_text]

def review_generated_post(generated_content, client, model_name):
    """
    Takes a single post and refines it using the post reviewer prompt.
    """
    reviewer_prompt = post_reviewer_prompt.format(post=generated_content)
    response = client.models.generate_content(model=model_name, contents=reviewer_prompt)
    reviewed_text = response.text.strip()
    return reviewed_text