import os, shutil
from docx import Document
import zipfile
from process_input_doc import get_image_description



def extract_images_from_docx(docx_path, output_folder="extracted_images"):
    """
    Extracts images from a .docx file and saves them to the output folder.
    The images are stored in the 'word/media/' folder inside the .docx zip structure.
    """    
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        for ind,file in enumerate(docx_zip.namelist()):
            # print(f'{ind}')
            if file.startswith("word/media/"):
                filename = os.path.basename(file)
                with open(os.path.join(output_folder, filename), "wb") as f:
                    f.write(docx_zip.read(file))

    print(f"{len(os.listdir(output_folder))} Images extracted to: {output_folder}")



def process_docx(file_path,image_folder):
    """
    Reads the .docx file, extracts text and images, summarizes the images using a VLM,
    and returns the combined text + image description.
    """
    # Clean output folder
    shutil.rmtree(image_folder, ignore_errors=True)
    os.makedirs(image_folder)
    
        
    # Load text content from the DOCX file
    doc = Document(file_path)
    text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    

    # Extract images embedded in the DOCX
    extract_images_from_docx(file_path, image_folder)

    # Get image-based description using a vision-language model
    image_text = get_image_description(image_folder, os.environ.get("GOOGLE_API_KEY", ""))
    
    # Append image summary to text
    text += f'\n\n{image_text}' 

    # Clean up temporary image folder 
    shutil.rmtree(image_folder)

    return text