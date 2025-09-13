# app/scripts/document_summarizer.py

import os
import time
import fitz  # PyMuPDF for PDFs
import docx
import google.generativeai as genai

# =========================
# Gemini API Keys (Primary + Fallbacks)
# =========================
GEMINI_API_KEYS = [
    "AIzaSyCEscXcGhwjkfAAApGDqj93JlMrnBzvWow",
    "AIzaSyDSDBgtVi0GxXMYh0o48aJJkoNc3dlibXs",
    "AIzaSyBpeVnD4pVLYsv3AiAK_vAYrhjU06dR3AY"
]

current_key_index = 0
genai.configure(api_key=GEMINI_API_KEYS[current_key_index])
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")


# =========================
# File reading utilities
# =========================
def read_pdf(path: str) -> str:
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text


def read_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_document(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return read_pdf(path)
    elif ext in [".docx", ".doc"]:
        return read_docx(path)
    elif ext == ".txt":
        return read_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# =========================
# Text chunking
# =========================
def chunk_text(text: str, max_words: int = 500) -> list:
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i + max_words]))
    return chunks


# =========================
# Gemini summarization with retry + fallback
# =========================
def switch_to_next_key():
    global current_key_index, gemini_model
    if current_key_index + 1 < len(GEMINI_API_KEYS):
        current_key_index += 1
        print(f"🔑 Switching to fallback API key #{current_key_index + 1}")
        genai.configure(api_key=GEMINI_API_KEYS[current_key_index])
        gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")
        return True
    return False


def summarize_chunk(chunk: str, retries: int = 3, delay: int = 5) -> str:
    prompt = f"""
You are an expert summarizer. Summarize the following text clearly:
- Highlight key points, actions, responsibilities, and deadlines
- Provide concise bullet points

Text:
{chunk}
"""
    for attempt in range(retries):
        try:
            response = gemini_model.generate_content(
                contents=[{"role": "user", "parts": [prompt]}],
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_output_tokens": 500
                }
            )
            summary = ""
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if candidate.content.parts:
                    summary = candidate.content.parts[0].text.strip()
            if summary:
                return summary
            print(f"⚠️ LLM returned empty summary. Retrying {attempt+1}/{retries}...")
        except Exception as e:
            if "quota" in str(e).lower() and switch_to_next_key():
                continue
            print(f"❌ Error in summarize_chunk: {e}")
        time.sleep(delay)
    return "⚠️ Summary failed after retries."


# =========================
# Summarize text (used by main.py)
# =========================
def summarize_text_in_batches(text: str, chunk_size: int = 500) -> str:
    chunks = chunk_text(text, max_words=chunk_size)
    print(f"📝 Total chunks: {len(chunks)}")

    chunk_summaries = []
    for idx, chunk in enumerate(chunks):
        print(f"📝 Summarizing chunk {idx + 1}")
        chunk_summary = summarize_chunk(chunk)
        chunk_summaries.append(chunk_summary)

    merged_summary = "\n".join(chunk_summaries)

    # Final summarization pass
    final_prompt = f"""
You are an expert policy summarizer. I will provide you with a document or partial summaries of a document. Your task is to create a detailed, professional, and well-structured summary with up to 100 lines.  

Guidelines:
- Begin with a clear policy title and identifier (if available).
- Provide an overview section.
- Highlight key features, benefits, and scope of the policy.
- Break down inclusions, exclusions, claim limits, incentives, and eligibility.
- Include a section for preventive care (such as vaccinations, check-ups, etc.).
- Expand into 10–15 sections, each with bullet points or short paragraphs.
- Keep the tone professional, precise, and comprehensive.
- Ensure the output reads like an official summarized report, not just a short abstract.
- If the original text is incomplete or limited, fill in gaps logically and clearly indicate assumptions.
Here is the input text/summaries:

{merged_summary}
"""
    try:
        final_response = gemini_model.generate_content(
            contents=[{"role": "user", "parts": [final_prompt]}],
            generation_config={"temperature": 0.3, "top_p": 0.8, "max_output_tokens": 800}
        )
        final_summary = ""
        if hasattr(final_response, "candidates") and final_response.candidates:
            candidate = final_response.candidates[0]
            if candidate.content.parts:
                final_summary = candidate.content.parts[0].text.strip()
        if final_summary:
            return final_summary
    except Exception as e:
        print(f"❌ Final merge summarization failed: {e}")

    return merged_summary


# =========================
# Summarize document (file path)
# =========================
def summarize_document(path: str, chunk_size: int = 500) -> str:
    text = read_document(path)
    return summarize_text_in_batches(text, chunk_size=chunk_size)


# =========================
# Save summary
# =========================
def save_summary(summary_text: str, base_filename: str, output_folder: str) -> str:
    os.makedirs(output_folder, exist_ok=True)
    summary_path = os.path.join(output_folder, f"{base_filename}_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_text)
    return summary_path
