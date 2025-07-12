import pymupdf, fitz
import os, shutil
from PyPDF2 import PdfReader
from process_input_doc import get_image_description

def extract_images_from_pdf(pdf_path, output_folder="extracted_images"):
    """
    Extracts images from a PDF (digitally embedded) and saves them to the output folder.
    """
    doc = fitz.open(pdf_path)

    image_count = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images()
        print(f'Page {page_index+1} has {len(image_list)} image(s)')
        # print(f'len of images is {len(image_list)}  in page {page_index+1}')
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"page{page_index + 1}_img{img_index + 1}.{image_ext}"

            with open(os.path.join(output_folder, image_filename), "wb") as f:
                f.write(image_bytes)

            image_count += 1

    print(f"✅ Extracted {image_count} image(s) from {pdf_path} into {output_folder}/")


def change_ocr_doc_to_images(file_path, image_folder="extracted_images"):
    """
    Converts each page of a scanned/non-text-extractable PDF into images.
    """
    doc = fitz.open(file_path)

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_filename = f"page{page_index + 1}.png"
        image_path = os.path.join(image_folder, image_filename)

        # Save page as image

        pix.save(image_path)
        print(f"Saved {image_filename}")

    print(f"✅ Converted {len(doc)} page(s) from {file_path} to images in {image_folder}/")



def is_text_extractable(file_path):
    """
    Returns True if the PDF has selectable text (i.e., not a scanned image).
    """

    doc = pymupdf.open(file_path)
    for page in doc:
        if page.get_text():  # Returns non-empty string if text exists
            return True  # Digitally-born PDF
        return False  # Scanned PDF

def process_pdf(file_path, image_folder):
    """
    Main logic to:
    - Determine if PDF is scanned or text-based
    - Extract text or convert to images
    - Extract embedded images
    - Use VLM to generate image descriptions
    - Return combined text and image description
    """

    # Clean output folder
    shutil.rmtree(image_folder, ignore_errors=True)
    os.makedirs(image_folder)


    text = []
    
    if not is_text_extractable(file_path):
        # For scanned PDFs: convert pages to images for OCR
        change_ocr_doc_to_images(file_path, image_folder)

    else:
        # For regular PDFs: extract text and images
        reader = PdfReader(file_path)
        for page in reader.pages:
            text.append(page.extract_text())
        extract_images_from_pdf(file_path, image_folder)

    # Describe all extracted images using VLM
    image_text = get_image_description(image_folder, os.environ.get("GOOGLE_API_KEY", ""))
    text.append(f'\n\n{image_text}') # Append image summary at end

    shutil.rmtree(image_folder) # Clean up temporary image folder

    return "\n".join(text)
