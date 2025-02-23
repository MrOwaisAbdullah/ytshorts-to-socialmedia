from clean_output import clean_output
from review_content import review_generated_thread  # Use thread reviewer
from templates import prompt_thread, sample_templates_thread

def generate_thread_content(transcript, context, num_tweets, client, model_name):
    """
    Generate a Twitter thread with exactly num_tweets tweets from a transcript and context.
    """
    # Format the prompt with explicit instructions
    prompt = prompt_thread.format(
        content=transcript,
        context=context,
        num_tweets=num_tweets,
        sample_templates=sample_templates_thread
    )
    
    # Generate the initial thread
    response = client.models.generate_content(model=model_name, contents=prompt)
    raw_thread = response.text.strip()
    raw_thread = clean_output(raw_thread)  # Remove unwanted formatting
    
    # Review the thread
    reviewed_tweets = review_generated_thread(raw_thread, client, model_name)
    
    # Ensure we have exactly num_tweets
    if len(reviewed_tweets) == num_tweets:
        return reviewed_tweets
    elif len(reviewed_tweets) > num_tweets:
        return reviewed_tweets[:num_tweets]  # Truncate if too many
    else:
        # Generate additional tweets if too few
        missing_count = num_tweets - len(reviewed_tweets)
        additional_prompt = prompt + f"\n\nGenerate {missing_count} more tweets to complete the thread."
        additional_response = client.models.generate_content(model=model_name, contents=additional_prompt)
        additional_raw = clean_output(additional_response.text.strip())
        additional_tweets = review_generated_thread(additional_raw, client, model_name)
        return reviewed_tweets + additional_tweets[:missing_count]  # Add only what's needed