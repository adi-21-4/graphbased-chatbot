# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot import handle_input, speak_text
from cypher_generator import generate_cypher_query
from graph_query import run_cypher_query
import threading

app = Flask(__name__)
CORS(app)


def format_record_to_string(rec):
    """
    Convert a single record (dict-like or other) to a friendly string.
    Prioritizes s.name, o.name, desc.text, t.name, or the first available value.
    """
    try:
        # If it's already a string
        if isinstance(rec, str):
            return rec

        # Mapping-like (neo4j.Record or dict)
        if hasattr(rec, "items") or hasattr(rec, "keys"):
            # try dict-style access
            items = None
            try:
                items = list(rec.items())
            except Exception:
                # if rec is neo4j.Record, convert via keys()
                try:
                    items = [(k, rec[k]) for k in rec.keys()]
                except Exception:
                    items = []

            # build quick lookup
            kv = {str(k): v for k, v in items}

            # helper to find key by substring
            def find_key(subs):
                for k in kv.keys():
                    if subs in k.lower():
                        return k
                return None

            s_key = find_key("s.name") or find_key(".name") or find_key("name")
            o_key = find_key("o.name") or find_key("objective") or find_key("o")
            desc_key = find_key("desc.text") or find_key("description") or find_key("desc")
            tag_key = find_key("t.name") or find_key("tag")

            s_val = kv.get(s_key) if s_key else None
            o_val = kv.get(o_key) if o_key else None
            desc_val = kv.get(desc_key) if desc_key else None
            tag_val = kv.get(tag_key) if tag_key else None

            # prefer objective
            if s_val is not None and o_val is not None:
                return f"{s_val}: {o_val}"
            if s_val is not None and desc_val is not None:
                return f"{s_val}: {desc_val}"
            if s_val is not None:
                return str(s_val)
            # fallback to first value
            if items:
                return str(items[0][1])
            return ""
        # If it's list/tuple, join values
        if isinstance(rec, (list, tuple)):
            return ", ".join(map(str, rec))
        # fallback
        return str(rec)
    except Exception as e:
        print("format_record_to_string error:", e)
        try:
            return str(rec)
        except:
            return ""


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    # compatibility: frontend may send speech_mode, speech_output, etc.
    speech_output = data.get("speech_output", data.get("speech_mode", False))
    # optional language hint (not required)
    speech_lang = data.get("speech_lang", "en-IN")

    if not question:
        return jsonify({"error": "Empty question"}), 400

    try:
        # Extract the base language code (e.g., 'mr' from 'mr-IN')
        base_lang = speech_lang.split('-')[0] if speech_lang else None

        # Process text-only input (frontend handles speech->text)
        # Pass the explicit language to bypass langdetect guessing
        original_q, translated_q, lang = handle_input(question, explicit_lang=base_lang)
        
        if original_q == "exit":
            return jsonify({"answer": "Goodbye!", "type": "text"})

        # Generate Cypher using the translated question
        cypher = generate_cypher_query(translated_q)
        print("\n📝 User Question:", original_q)
        print("📝 Translated Question:", translated_q)
        print("🔎 Generated Cypher Query:\n", cypher)

        # Run query
        answer_data = run_cypher_query(cypher)

        # Format the response depending on what run_cypher_query returned
        if isinstance(answer_data, list):
            # Try to convert each record to friendly string
            answer_list = [format_record_to_string(rec) for rec in answer_data]
            response_payload = {
                "question": original_q,
                "cypher": cypher,
                "answer": answer_list,
                "type": "list",
                "lang": lang,
            }
        else:
            # if it's a plain string or count
            response_payload = {
                "question": original_q,
                "cypher": cypher,
                "answer": str(answer_data),
                "type": "text",
                "lang": lang,
            }

        # Kick off TTS in background (non-blocking). Join list into a speakable string if needed.
        if speech_output:
            speak_text_arg = (
                response_payload["answer"]
                if isinstance(response_payload["answer"], str)
                else ", ".join(response_payload["answer"])
            )
            t = threading.Thread(
                target=speak_text,
                args=(speak_text_arg, "mr" if str(lang).startswith("mr") else "en"),
                daemon=True,
            )
            t.start()

        # Return result immediately
        return jsonify(response_payload)

    except Exception as e:
        # return trace for debugging (you can remove traceback in production)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)