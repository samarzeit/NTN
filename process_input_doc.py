
import os
from google import genai
import time




def get_image_description(image_folder,api_key):

    image_descriptions = []
    client = genai.Client(api_key = api_key)

    all_image_file_names = os.listdir(image_folder)

    for i in range(0,len(all_image_file_names),3):
        contents = []
        batch_contents = [client.files.upload(file=os.path.join(image_folder, file_name)) for file_name in all_image_file_names[i:i+3] if file_name.lower().endswith(('.png', '.jpg', '.jpeg'))]
        contents.append(batch_contents)
        contents.append("Explain the images in detail")  

        response = client.models.generate_content(
        # model="gemini-2.5-pro",
        model = "gemini-2.5-flash-lite-preview-06-17",
        contents = contents
        )

        image_descriptions.append(response.text)
        image_descriptions.append(f"""The file names and locations are: { [os.path.join(image_folder, file_name) for file_name in all_image_file_names[i:i+3]] }""" )
        print(f"👍 Processed images \n{image_descriptions} ")
        time.sleep(4)

    return image_descriptions