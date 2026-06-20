# ============================================================
# image.py — Image Generation Placeholder for Bharat.ai
# Status: Feature coming soon
# BCA 6th Semester | Dibrugarh University
# Built by Harsh Raut & Shanu Das
# ============================================================


def generate_image(prompt: str) -> dict:
    """
    Image generation is currently unavailable.
    Returns a friendly message indicating the feature is coming soon.
    """
    return {
        "success": False,
        "error": "🎨 Image generation feature is coming soon! Stay tuned for updates.",
        "image_url": None,
        "prompt": prompt
    }


def is_image_request(message: str) -> bool:
    """Check if user message is requesting image generation."""
    message = message.lower()
    keywords = [
        "generate image", "generate images", "create image",
        "create images", "make image", "make images",
        "draw", "draw me", "image of", "picture of",
        "photo of", "generate picture", "create picture",
        "show image", "can you generate", "can u generate",
        "make a picture", "make a photo", "generate a photo",
        "create a photo", "show me a picture", "show me an image",
        "paint", "illustrate",
    ]
    return any(keyword in message for keyword in keywords)


def extract_image_prompt(message: str) -> str:
    """Extract clean image prompt from user message."""
    message = message.lower()
    remove_words = [
        "can you generate image of", "can u generate image of",
        "can you generate a image of", "can u generate a image of",
        "please generate image of", "generate image of",
        "generate images of", "generate a image of",
        "generate an image of", "create image of",
        "create images of", "create a image of",
        "create an image of", "make image of",
        "make images of", "make a image of",
        "make an image of", "draw me a", "draw me an",
        "draw me", "draw a", "draw an", "draw",
        "show image of", "show me a picture of",
        "show me an image of", "generate picture of",
        "create picture of", "make a picture of",
        "make a photo of", "generate a photo of",
        "picture of", "image of", "photo of",
        "paint a", "paint an", "paint", "illustrate",
        "generate image", "create image", "make image",
        "generate", "create", "please", "can you", "can u",
    ]
    prompt = message
    for word in remove_words:
        prompt = prompt.replace(word, "")

    prompt = prompt.strip()
    for article in ["a an ", "an a ", "a a ", "an an ", "a ", "an ", "the "]:
        if prompt.startswith(article):
            prompt = prompt[len(article):]
            break

    return prompt.strip()