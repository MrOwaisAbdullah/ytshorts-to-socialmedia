from templates import prompt_short_to_post
from review_content import review_generated_post

def generate_linkedin_posts(transcript, client, model_name, context_input, num_variations=3):
    posts = []
    for i in range(num_variations):
        prompt =f"{prompt_short_to_post}\n\nTranscript:\n{transcript}, here is some more context/details:\n{context_input}, variation {i+1}"
        response = client.models.generate_content(
        model=model_name,
        contents=prompt
        )
        post_text = response.candidates[0].content.parts[0].text
        reviewed_post = review_generated_post(post_text, client, model_name)
        posts.append(reviewed_post)
    return posts