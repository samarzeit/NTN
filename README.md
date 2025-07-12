# Notes-To-Neurons 🧠✨  
> AI-powered Anki flashcard generator that turns your notes into spaced-repetition-ready memory bites.

---

## 🚀 What is this?

**Notes-To-Neurons** (NTN) is a tool that takes your documents (`.pdf`, `.docx`) as input, uses **Google Gemini 2.5 Pro and Flash** to understand the content, and generates intelligent **Anki flashcards** — with optional **images**, **AI-inferred questions**, and direct integration with Anki via **[AnkiConnect](https://ankiweb.net/shared/info/2055492159)** and
**[Multiple Choice for Anki](https://ankiweb.net/shared/info/1566095810)**

It supports:
- 👁️ Document + Vision-Language description
- 🧠 AI-generated questions grounded in your notes
- 📤 Direct push to Anki via AnkiConnect
- 💻 Easy GUI built with **Tkinter**

---

## 🖼️ Features

✅ Gemini API Key input through GUI  
✅ Extracts **text & images** from scanned or native PDFs  
✅ Uses a **Multimodal Model** to describe embedded images  
✅ Smartly distinguishes questions as:
- `"From Content"` (verbatim from notes)
- `"AI-generated"` (intelligently related)  

✅ Sends cards directly to Anki using `AnkiConnect`.     
✅ Cross-platform support (Windows, Mac, Linux with Python)

---

## 📝 Document Tips

📄 **Split large PDFs** before uploading — this helps produce higher-quality flashcards.

🔍 **OCR-enabled PDFs** (scanned files) are automatically split into **one image per page** to preserve layout and boost model understanding.

🧠 Combining extracted text with Gemini's **visual reasoning** lets the system interpret charts, figures, and complex visual cues.


---

## 🛠️ Setup Instructions

### 1. Clone this repo
```bash
git clone https://github.com/samarzeit/NTN.git
cd NTN 
```

### 2. Install dependencies
Make sure you have Python 3.10+ and AnkiConnect installed in Anki.

```bash
python -m venv venv
venv\Scripts\activate # on Windows
pip install -r requirements.txt
```

### 3. Set up Gemini API access
Get your key from https://aistudio.google.com/app/apikey  
No need to export — you’ll enter it in the app GUI.

---

## 🧪 How to Run
```bash
python main.py
```


This will open a GUI window where you can:

- Paste your Gemini API key

- Upload a .pdf or .docx

- Click “Generate Flashcards for Anki”

You’ll see results in Anki automatically (if Anki is open with AnkiConnect enabled).

## 📷 Image-aware Notes?
If your document includes illustrations, figures, diagrams — NTN uses Gemini 2.5 Flash Model to interpret them and include their meaning in the flashcard context.


## 🤖 Models Used

Google Gemini 2.5 Flash

https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash-lite


Google Gemini 2.5 Pro

https://ai.google.dev/gemini-api/docs/models#gemini-2.5-pro



## ⚠️ Notes
Requires Anki to be open and running locally

Make sure `AnkiConnect` and `Multiple Choice for Anki` plugins are installed in Anki

Does not yet support bulk file uploads (1 file at a time)

## 🧠 Tagline
**From notes to neurons — build memory with meaning.**