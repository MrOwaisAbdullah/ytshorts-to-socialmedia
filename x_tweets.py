# In x_tweets.py
from clean_output import clean_output
from review_content import review_generated_tweet
from templates import prompt_tweet, tweet_template_1, tweet_template_2, tweet_template_3, tweet_template_4, tweet_template_5

def generate_tweet_content(transcript, context, client, model_name, num_variations=3):
    """
    Generate a specified number of tweet variations from a transcript and optional context.
    Each tweet uses a different template and is limited to one tweet per variation.
    """
    tweet_variations = []
    templates = [
        tweet_template_1,
        tweet_template_2,
        tweet_template_3,
        tweet_template_4,
        tweet_template_5
    ]
    
    # Generate exactly num_variations tweets
    for i in range(num_variations):
        # Cycle through templates
        template = templates[i % len(templates)]
        # Use the template in the prompt
        prompt = prompt_tweet.format(content=transcript, context=context, post_template=template)
        
        # Generate the initial tweet
        response = client.models.generate_content(model=model_name, contents=prompt)
        raw_tweet = response.text.strip()
        raw_tweet = clean_output(raw_tweet)  # Remove unwanted formatting
        
        # Ensure only one tweet (take first if multiple lines are generated)
        single_tweet = raw_tweet.split('\n\n')[0] if '\n\n' in raw_tweet else raw_tweet
        
        # Review the tweet
        reviewed_tweet = review_generated_tweet(single_tweet, client, model_name)
        
        # Verify character limit (optional safeguard)
        if len(reviewed_tweet) > 280:
            reviewed_tweet = reviewed_tweet[:277] + "..."  # Truncate if needed
        tweet_variations.append(reviewed_tweet)
    
    return tweet_variations
