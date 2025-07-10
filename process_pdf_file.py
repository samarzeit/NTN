import pymupdf, fitz
import os, shutil
import ocrmypdf
from PyPDF2 import PdfReader
from process_input_doc import get_image_description

def extract_images_from_pdf(pdf_path, output_folder="extracted_images"):
    doc = fitz.open(pdf_path)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
      shutil.rmtree(output_folder)
      os.makedirs(output_folder)

    image_count = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images()
        print(f'len of images is {len(image_list)}  in page {page_index+1}')
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
    Converts each page of a PDF document to an image and saves it to a folder.

    Args:
        file_path (str): The path to the PDF document.
        image_folder (str): The folder to save the images to.
    """
    doc = fitz.open(file_path)

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    else:
        shutil.rmtree(image_folder)
        os.makedirs(image_folder)

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_filename = f"page{page_index + 1}.png"
        image_path = os.path.join(image_folder, image_filename)
        pix.save(image_path)
        print(f"Saved {image_filename}")

    print(f"✅ Converted {len(doc)} page(s) from {file_path} to images in {image_folder}/")

    # ocrmypdf.ocr(file_path, file_path, language='eng', output_type='pdf', image_folder=image_folder)
    # print(f"✅ Converted {file_path} to images in {image_folder}/")


def is_text_extractable(file_path):
    doc = pymupdf.open(file_path)
    for page in doc:
        if page.get_text():  # Check for extractable text
            return True  # Digitally-born PDF
        return False  # Scanned PDF

def process_pdf(file_path, image_folder):
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    else:
        shutil.rmtree(image_folder)
        os.makedirs(image_folder)

    text = []
    
    if not is_text_extractable(file_path):
        # ocrmypdf.ocr(file_path, file_path, language='eng')
        change_ocr_doc_to_images(file_path, image_folder)
    else:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text.append(page.extract_text())
        extract_images_from_pdf(file_path, image_folder)


    image_text = get_image_description(image_folder, os.environ.get("GOOGLE_API_KEY", ""))
    text.append(f'\n\n{image_text}') 

    shutil.rmtree(image_folder)

    return "\n".join(text)
