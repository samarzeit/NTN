import os
from google import genai
import time




def get_image_description(image_folder,api_key):
    """
    Uploads images from a folder in batches of 3 and sends them to Gemini for vision-language description.
    Returns a list of image explanations and corresponding file paths.
    """
    image_descriptions = []
    client = genai.Client(api_key = api_key)

    # List all image files in the folder
    all_image_file_names = [
        name for name in os.listdir(image_folder)
        if name.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    # Process images in batches of 3
    for i in range(0,len(all_image_file_names),3):
        batch_filenames = all_image_file_names[i:i+3]

        # Upload each image file in the batch
        uploaded_files = [
            client.files.upload(file=os.path.join(image_folder, file_name))
            for file_name in batch_filenames
        ]

        # Prepare content for Gemini model
        contents = uploaded_files + ["Explain the images in detail"]


        # Call Gemini model
        response = client.models.generate_content(
        model = "gemini-2.5-flash-lite-preview-06-17",
        contents = contents
        )

        image_descriptions.append(response.text)
        image_descriptions.append(f"""The file names and locations are: { [os.path.join(image_folder, file_name) for file_name in all_image_file_names[i:i+3]] }""" )
        print(f"👍 Processed images")
        time.sleep(4) # Avoid hitting rate limits (15 requests per minute)

    return image_descriptions