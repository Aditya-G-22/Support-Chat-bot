from langdetect import detect, LangDetectException

# Map language codes to full language names
# The LLM needs the full name to reply in the correct language
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh-cn": "Chinese",
    "zh-tw": "Chinese",
    "ar": "Arabic",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "it": "Italian",
    "nl": "Dutch",
    "tr": "Turkish",
}


#=========================================================================================
def detect_language(text: str) -> str:
    # Returns full language name like "Hindi" or "Spanish"
    # Falls back to English if detection fails

    if not text or len(text.strip()) < 3:
        return "English"

    try:
        language_code = detect(text)
        full_name = LANGUAGE_MAP.get(language_code, "English")
        return full_name

    except LangDetectException:
        print("Warning: Could not detect language, defaulting to English")
        return "English"