from extracttext import describe_image
import base64

# Path to a local image file
image_path = "riflecarbine/page_75_image_1.jpeg"


# Function to convert image to base64
# def convert_image_to_base64(image_path):
with open(image_path, "rb") as image_file:
    bmage = base64.b64encode(image_file.read()).decode('utf-8')

description = describe_image(bmage)
print(description)