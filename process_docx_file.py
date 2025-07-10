import os, shutil
from docx import Document
import zipfile
from process_input_doc import get_image_description



def extract_images_from_docx(docx_path, output_folder="extracted_images"):
    
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        for ind,file in enumerate(docx_zip.namelist()):
            # print(f'{ind}')
            if file.startswith("word/media/"):
                filename = os.path.basename(file)
                with open(os.path.join(output_folder, filename), "wb") as f:
                    f.write(docx_zip.read(file))

    print(f"{len(os.listdir(output_folder))} Images extracted to: {output_folder}")



# Read docx
def process_docx(file_path,image_folder):

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    else:
        shutil.rmtree(image_folder)
        os.makedirs(image_folder)
        

    doc = Document(file_path)

    text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    
    extract_images_from_docx(file_path, image_folder)

    image_text = get_image_description(image_folder, os.environ.get("GOOGLE_API_KEY", ""))
    
    text += f'\n\n{image_text}' 
    
    shutil.rmtree(image_folder)

    return text