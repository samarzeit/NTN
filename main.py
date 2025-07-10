# Reference:
# https://github.com/dhkim0124/anki-mcp-server.git

# === Imports ===


import asyncio
import httpx
import json
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from process_docx_file import process_docx
from process_pdf_file import process_pdf



import tkinter as tk
from tkinter import filedialog, messagebox


# === Constants ===
ANKICONNECT_URL = "http://127.0.0.1:8765"  # Localhost URL for AnkiConnect


# === AnkiConnect helper functions ===
async def anki_connect(action: str, **params):
    """Send an action request to AnkiConnect API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANKICONNECT_URL,
            json={"action": action, "version": 6, "params": params},
        )
        response.raise_for_status()
        return response.json()

async def check_anki_connection():
    """Ensure Anki and AnkiConnect are available before proceeding."""
    try:
        await anki_connect("version")
        return True
    except Exception as e:
        messagebox.showerror("Anki Error", f"AnkiConnect is not available. Please ensure Anki is running and the add-on is installed.\n\nError: {e}")
        return False

async def create_deck(deck_name):
    """Create a deck in Anki (or verify it exists)."""
    try:
        response = await anki_connect("createDeck", deck=deck_name)
        print(f"✅ Created deck '{deck_name}' (or already exists).")
        return response
    except Exception as e:
        print(f"❌ Failed to create deck '{deck_name}': {e}")
        raise

# === File Reader ===
def process_file(file_path, image_folder="extracted_images"):
    """Decide whether to process a DOCX or PDF file."""

    if file_path.endswith('.docx') or file_path.endswith('.doc'):
        return process_docx(file_path, image_folder)
    elif file_path.endswith('.pdf'):
        return process_pdf(file_path, image_folder)



# === Flashcard Generation ===
async def generate_flashcards(text):
    """Use Gemini API to generate flashcards in Anki JSON format."""

    system_prompt = """
You are an expert assistant for generating high-quality **Anki flashcards** from input text.

Your task:
- Read the input content and generate a balanced set of flashcards.
- Include **both**:
  1. Questions taken directly from the input content (clearly marked as "From Content").
  2. Related questions **inferred by the AI** that are relevant but not directly present in the text (clearly marked as "AI-generated"). Do not generate AI questions if unsure.
- Ensure AI-generated questions are grounded, educational, and do not speculate.

Requirements:
- Avoid hallucination — keep AI-generated content clearly **connected** to the source topic.
- Avoid giving away the correct answer by making it **much longer** or more specific than the incorrect options. Keep all options similar in tone and length.
- Always cite the relevant **text snippet** from the content in the `Sources` field for "From Content" questions.
- For AI-generated questions, include a brief explanation in the `Extra 1` field justifying the correct answer.
- If no meaningful AI-generated question can be made, skip it — don’t guess.
- Use **simple, clear, and concise** language. Add examples where helpful.

Format:
- `Question`: The actual question, ending with either “(From Content)” or “(AI-generated)”
- `QType (0=kprim,1=mc,2=sc)`: use "1" or "2" as a **string**
- `Q_1` to `Q_5`: answer options (min. 2, max. 5)
- `Answers`: a string like "1 0 0 0 0" marking correct answers
- `Sources`: paste the part of the content that inspired the question (or leave blank if AI-generated)
- `Extra 1`: leave blank for "From Content", or add explanation if "AI-generated"
- `Title`: short and meaningful for the card

Final output must be valid **JSON only**, no extra commentary.

```json
{{
  "params": {{
    "notes": [
      {{
        "deckName": "<suitable deck name>",
        "modelName": "AllInOne (kprim, mc, sc)",
        "fields": {{
          "Question": "your question here (From Content or AI-generated)",
          "QType (0=kprim,1=mc,2=sc)": "2",
          "Q_1": "Option 1",
          "Q_2": "Option 2",
          "Q_3": "Option 3",
          "Q_4": "",
          "Q_5": "",
          "Answers": "1 0 0",
          "Sources": "Paste relevant content or leave empty if AI",
          "Extra 1": "Explanation if AI-generated, else leave blank",
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


# === Full Process Controller ===
async def process_file_and_anki(file_path):
    """Complete processing: extract → generate flashcards → send to Anki."""
    if not api_entry.get().strip():
        messagebox.showwarning("No API-key", "Please provide an API key.")
        return    
    
    if not file_path:
        messagebox.showwarning("No File Selected", "Please select a file first.")
        return

    os.environ["GOOGLE_API_KEY"] = api_entry.get().strip()

    # Check if Anki is available before any processing
    if not await check_anki_connection():
        status_label.config(text="Status: Anki not available.")
        return
    
    try:

        status_label.config(text="Status: Reading file...")
        
        text = process_file(file_path)
        
        if text is None:
            status_label.config(text="Status: Idle")
            return
        
        print("✅ Extracted text from document.")
        
        status_label.config(text="Status: Generating flashcards with LLM...")

        flashcards_payload = await generate_flashcards(text)
        
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
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            error_json = e.response.json()
            if error_json.get('error', {}).get('message') == 'API key not valid. Please pass a valid API key.':
                messagebox.showerror("Invalid API Key", "Please enter a valid Gemini API key.")
            else:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        else:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        status_label.config(text="Status: Error")

    finally:
        status_label.config(text="Status: Idle")


# === GUI: File and API Input ===
def browse_file():
    """Open file picker and load selected file into entry field."""
    file_path = filedialog.askopenfilename(
        filetypes=[("Document Files", "*.docx *.doc *.pdf")]
    )
    if file_path:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, file_path)

def start_process_gui():
    """Start the async flashcard generation process from GUI."""
    selected_file = file_path_entry.get()
    if not selected_file or not api_entry.get().strip():
        messagebox.showwarning("Missing data", "Please provide the necessary data to proceed.")
        return
    if not os.path.isfile(selected_file):
        messagebox.showerror("File Error", f"The selected file does not exist:\n{selected_file}")
        return
    try:
        asyncio.run(process_file_and_anki(selected_file))
    except Exception as e:
        messagebox.showerror("Processing Error", f"Failed to start processing: {e}")


# === GUI Layout ===
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

# Start GUI loop
root.mainloop()

