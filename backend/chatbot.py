# chatbot.py
from deep_translator import GoogleTranslator
from langdetect import detect
import pyttsx3

def speak_text(text, lang="en"):
    """
    Synchronous TTS function (kept simple).
    app.py will call this in a background thread so it does not block responses.
    """
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        # Default to first voice
        selected_voice = voices[0].id if voices else None

        if lang == "mr":
            # try to find a Marathi/Hindi voice
            for v in voices:
                if "marathi" in v.name.lower() or "hindi" in v.name.lower():
                    selected_voice = v.id
                    break
        else:
            # prefer Indian English if available
            for v in voices:
                if "english" in v.name.lower() and "india" in v.name.lower():
                    selected_voice = v.id
                    break

        if selected_voice:
            engine.setProperty("voice", selected_voice)
        engine.setProperty("rate", 170)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("⚠️ Text-to-speech failed:", e)


def handle_input(user_input: str, explicit_lang: str = None):
    """
    Handle text input (typed or frontend-transcribed speech).
    Returns (original_question, translated_question, lang)
    - original_question: the original text from frontend
    - translated_question: English text to feed into cypher generator (if needed)
    - lang: detected language code ('en' or 'mr', etc.)
    """
    if not user_input or not isinstance(user_input, str):
        return None, None, None

    question = user_input.strip()
    if not question:
        return None, None, None

    # exit shortcut
    if question.lower() == "exit" or "बाहेर पडा" in question:
        return "exit", None, None

    # 👈 FIX: Use the explicitly provided language from the frontend
    lang = explicit_lang
    if not lang:
        try:
            lang = detect(question)
        except Exception:
            lang = "en"

    # If Marathi is selected, translate to English for the LLM
    if lang.startswith("mr"):  
        try:
            translated_q = GoogleTranslator(source="mr", target="en").translate(question)
        except Exception as e:
            print("⚠️ Translation failed:", e)
            translated_q = question
    else:
        translated_q = question

    return question, translated_q, lang