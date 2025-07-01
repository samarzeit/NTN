# Reference:
# https://github.com/dhkim0124/anki-mcp-server.git

import asyncio
import httpx
import json
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import pymupdf

import ocrmypdf
from PyPDF2 import PdfReader

import tkinter as tk
from tkinter import filedialog, messagebox


ANKICONNECT_URL = "http://127.0.0.1:8765"



# AnkiConnect Client
async def anki_connect(action: str, **params):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANKICONNECT_URL,
            json={"action": action, "version": 6, "params": params},
        )
        response.raise_for_status()
        return response.json()


async def create_deck(deck_name):
    try:
        response = await anki_connect("createDeck", deck=deck_name)
        print(f"✅ Created deck '{deck_name}' (or already exists).")
        return response
    except Exception as e:
        print(f"❌ Failed to create deck '{deck_name}': {e}")
        raise


# Read docx
def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

def is_text_extractable(file_path):
    doc = pymupdf.open(file_path)
    for page in doc:
        if page.get_text():  # Check for extractable text
            return True  # Digitally-born PDF
        return False  # Scanned PDF

def read_pdf(file_path):
    if not is_text_extractable(file_path):
        ocrmypdf.ocr(file_path, file_path, language='eng')

    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())

    return "\n".join(text)


def read_file(file_path):
    if file_path.endswith('.docx') or file_path.endswith('.doc'):
        return read_docx(file_path)
    elif file_path.endswith('.pdf'):
        return read_pdf(file_path)





async def generate_flashcards(text, api_key):
    system_prompt = """
You are an expert assistant for generating high-quality **Anki flashcards** from input text.

You may use light imagination to infer or expand on ideas, as long as they are clearly related to the input and remain educational and relevant to the topic. Avoid unrelated or speculative content.
If you generate questions, ensure they are clear, concise, and educational, with appropriate options, correct answers, and source references.
Any generated content should be clearly marked as AI-generated at the end of the question and not falsely attributed to the original document.


Your task:
- Analyze the provided content and identify good multiple-choice or single-choice questions.
- Generate flashcards using the Anki note type: **AllInOne (kprim, mc, sc)**.
- Use **clear**, **concise**, and **simple** language. Include examples when appropriate.
- If possible, cite the source(s) in the 'Sources' field.
- Do NOT add any explanation, commentary, or extra text — ONLY return valid JSON.

Flashcard Format:
- `Question`: The question prompt.
- `QType (0=kprim,1=mc,2=sc)`: "1" for multiple-choice, "2" for single-choice (always as **string**).
- `Q_1` to `Q_5`: Up to 5 options (at least 2 required, feel free to add upto 5).
- `Answers`: A space-separated string of binary values like `"1 0 0"` indicating correct answer(s).
- `Sources`: Comma-separated sources or leave empty.
- `Extra 1`: Leave empty unless useful.
- `Title`: Set an useful title.

Final Output Format (strict):
```json
{{
  "params": {{
    "notes": [
      {{
        "deckName": "DeckNameHere",
        "modelName": "AllInOne (kprim, mc, sc)",
        "fields": {{
          "Question": "your question here",
          "QType (0=kprim,1=mc,2=sc)": "2",
          "Q_1": "Option 1",
          "Q_2": "Option 2",
          "Q_3": "Option 3",
          "Q_4": "",
          "Q_5": "",
          "Answers": "1 0 0",
          "Sources": "Wikipedia, WHO",
          "Extra 1": "",
          "Title": "Empty title"
        }}
      }}
    ]
  }}
}}

Now generate flashcards from the following text:

{text}
"""
    try:
        os.environ["GOOGLE_API_KEY"] = api_key
        genai_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

        response = await genai_llm.ainvoke(system_prompt.format(text=text))
        llm_text_response = response.content.strip()

        if "```json" in llm_text_response:
            json_str = llm_text_response.split("```json")[1].split("```")[0].strip()
        else:
            json_str = llm_text_response

        flashcards_payload = json.loads(json_str)
        return flashcards_payload

    except json.JSONDecodeError as e:
        messagebox.showerror("LLM Error", f"Failed to parse LLM response as JSON: {e}\nRaw response:\n{llm_text_response}")
        return None
    except Exception as e:
        messagebox.showerror("LLM Error", f"An error occurred during LLM generation: {e}")
        return None

async def process_file_and_anki(file_path):
    if not file_path:
        messagebox.showwarning("No File Selected", "Please select a file first.")
        return

    try:
        status_label.config(text="Status: Reading file...")
        text = read_file(file_path)
        if text is None:
            status_label.config(text="Status: Idle")
            return
        print("✅ Extracted text from document.")
        status_label.config(text="Status: Generating flashcards with LLM...")

        flashcards_payload = await generate_flashcards(text, api_entry.get().strip())
        if flashcards_payload is None:
            status_label.config(text="Status: Idle")
            return
        print("✅ Flashcards generated from LLM.")
        status_label.config(text="Status: Sending flashcards to Anki...")

        deck_name = flashcards_payload['params']['notes'][0]['deckName']
        await create_deck(deck_name)

        response = await anki_connect("addNotes", **flashcards_payload['params'])

        print(response)
        messagebox.showinfo("Success", f"🎉 {len(response['result'])} Flashcards added successfully!")
        status_label.config(text="Status: Done!")

    except httpx.RequestError as e:
        messagebox.showerror("Connection Error", f"Could not connect to AnkiConnect. Is Anki running and AnkiConnect installed? Error: {e}")
        status_label.config(text="Status: Error")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        status_label.config(text="Status: Error")
    finally:
        status_label.config(text="Status: Idle")


def browse_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Document Files", "*.docx *.doc *.pdf")]
    )
    if file_path:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, file_path)

def start_process_gui():
    selected_file = file_path_entry.get()
    if not selected_file:
        messagebox.showwarning("No File", "Please select a file before proceeding.")
        return

    try:
        asyncio.run(process_file_and_anki(selected_file))
    except Exception as e:
        messagebox.showerror("Processing Error", f"Failed to start processing: {e}")


# GUI Setup
root = tk.Tk()
root.title("Anki Flashcard Generator")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)


# API key entry
api_label = tk.Label(frame, text="Enter Gemini API Key:")
api_label.grid(row=0, column=0, sticky="w", pady=5)

api_entry = tk.Entry(frame, width=50, show="*")  # hide input
api_entry.grid(row=0, column=1, pady=5, padx=5)


# File selection
file_label = tk.Label(frame, text="Select Document File:")
file_label.grid(row=1, column=0, sticky="w", pady=5)

file_path_entry = tk.Entry(frame, width=50)
file_path_entry.grid(row=1, column=1, pady=5, padx=5)

browse_button = tk.Button(frame, text="Browse", command=browse_file)
browse_button.grid(row=1, column=2, pady=5)

# Process button
process_button = tk.Button(frame, text="Generate Flashcards for Anki", command=start_process_gui)
process_button.grid(row=2, column=0, columnspan=3, pady=15)

# Status label
status_label = tk.Label(root, text="Status: Idle", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

root.mainloop()

