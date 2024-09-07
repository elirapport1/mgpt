import fitz  # PyMuPDF
import os
from openai import OpenAI
import vecs
import json
import base64
from dotenv import load_dotenv
import logging

client = OpenAI()
script_dir = os.path.dirname(__file__)
load_dotenv()
DB_CONNECTION = os.getenv("DB_CONNECTION")



def extract_text_and_images(pdf_document):
    """
    Extracts text and images from each page of a PDF document, saves the text to text files and images to image files.
    
    Args:
    - pdf_document (str): Path to the PDF document to be processed.
    
    Returns:
    - list: A list of strings, each containing the text extracted from a page of the PDF.
    
    Effect:
    - Creates text files for each page containing the extracted text.
    - Creates image files for each image found in the PDF, with filenames indicating their page and order.
    """
    doc = fitz.open(pdf_document)
    script_dir = os.path.dirname(__file__)
    pdf_name = os.path.splitext(os.path.basename(pdf_document))[0]
    output_dir = os.path.join(script_dir, pdf_name)
    os.makedirs(output_dir, exist_ok=True)
    pages_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        images = page.get_images(full=True)
        text = ""
        img_text = ""
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"page_{page_num + 1}_image_{img_index + 1}.{image_ext}"
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            print(page_num)
            img_description = describe_image(base64_image)
            # print("d f")
            image_path = os.path.join(output_dir, image_filename)
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)
            img_text += f"\n[Image {image_filename}]: \n {img_description}"
        text = f"page: {page_num + 1}, manual name: {pdf_name}\n" + page.get_text() + "\n" + img_text
        file_path = os.path.join(output_dir, f"page_{page_num + 1}.txt")
        with open(file_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)
        pages_text.append(text)

    return pages_text


def describe_image(base_64_image):
    """
    Generates a text description of the given image using OpenAI's 4o

    Args:
    - base_64_image (str)

    Returns:
    - str: The generated description of the image.
    """
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this diagram from a military training manual. Make sure to include all content provided in the image do not skip data. If the image is a triangle or a similar false image return 'disregard this image' "},
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base_64_image}",
            },
            },
        ],
        }
    ],
    max_tokens=600,
    )

    return response.choices[0].message.content


def generate_and_store_embeddings_from_texts(pages_text):
    """
    Generates embeddings from the provided text pages and stores them in a vector database.

    Input:
    - pages_text (list of str): A list of strings, each containing the text extracted from a page of the PDF.

    Effect:
    - Creates embeddings for each page's text using the OpenAI API.
    - Stores the embeddings in supabase vector database using vecs (index, embedding, {})
    - Creates an index for the stored embeddings in the vector database.
    """
    embeddings = []
    vx = vecs.Client(DB_CONNECTION)
    pages = vx.get_or_create_collection(name="combined_manuals", dimension=1536)
    for i, page_text in enumerate(pages_text):
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[page_text]
        )
        embedding = response.data[0].embedding
        pages.upsert(records= [
            (
            i,           # the vector's identifier
            embedding,  # the vector. a list
            {}    # associated  metadata
            )
        ])
        pages.create_index()


# def query_similar_pages(query_input, limit=3):
#     """
#     Queries the vector database for the most similar pages to the given input query.

#     Args:
#     - query_input (str): The input query to find similar pages for.
#     - limit (int, optional): The maximum number of similar pages to return. Default is 3.

#     Returns:
#     - str: A string containing the text of the most similar pages.

#     Effect:
#     - Generates an embedding for the input query using the OpenAI API.
#     - Queries the vector database for the most similar pages based on the query embedding.
#     - Combines the text of the most similar pages into a single string.
#     - Writes the combined text of the most similar pages to a file named "query_results.txt".
#     """
#     response = client.embeddings.create(
#         model="text-embedding-ada-002",
#         input=[query_input]
#     )
#     query_embedding = response.data[0].embedding

#     vx = vecs.Client(DB_CONNECTION)
#     pages = vx.get_or_create_collection(name="combined_manuals", dimension=1536)
#     # query the collection for the most similar page
#     results = pages.query(
#         data=query_embedding,
#         limit=limit,
#         include_value=True
#     )
#     combined_relevant_pages = ""
#     json_file_path = os.path.join(script_dir, "pages_text_array.json")
#     with open(json_file_path, "r", encoding="utf-8") as json_file:
#         combined_pages_text = json.load(json_file)
#     for i in range(limit):
#         combined_relevant_pages += combined_pages_text[int(results[i][0])] + "\n"

#     output_file_path = os.path.join(script_dir, "query_results.txt")
#     with open(output_file_path, "w", encoding="utf-8") as output_file:
#         output_file.write(combined_relevant_pages)
#     return combined_relevant_pages

# def generate_response(query, relevant_pages):
#     """
#     Generate a response based on the relevant pages using the OpenAI API.

#     Args:
#     - relevant_pages (str): A string containing the text of the relevant pages.

#     Returns:
#     - str: The generated response from the OpenAI API.
#     """
#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant who can answer a military training question based only on the provided text."},
#             {"role": "user", "content": "here is the user's question that you need to answer: "+query+" And here are the relevant pages of the manual you need to read and pull from to answer the question - make sure to include the page numbers of all the pages given: "+relevant_pages}
#         ]
#     )
#     # return response.choices[0].message['content']
#     return response.choices[0].message.content






# Initialize logging
logging.basicConfig(level=logging.INFO)

def query_similar_pages(query_input, limit=3):
    """
    Queries the vector database for the most similar pages to the given input query.

    Args:
    - query_input (str): The input query to find similar pages for.
    - limit (int, optional): The maximum number of similar pages to return. Default is 3.

    Returns:
    - str: A string containing the text of the most similar pages.

    Effect:
    - Generates an embedding for the input query using the OpenAI API.
    - Queries the vector database for the most similar pages based on the query embedding.
    - Combines the text of the most similar pages into a single string.
    - Writes the combined text of the most similar pages to a file named "query_results.txt".
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[query_input]
        )
        query_embedding = response.data[0].embedding

        vx = vecs.Client(DB_CONNECTION)
        pages = vx.get_or_create_collection(name="combined_manuals", dimension=1536)
        # query the collection for the most similar page
        results = pages.query(
            data=query_embedding,
            limit=limit,
            include_value=True
        )
        combined_relevant_pages = ""
        json_file_path = os.path.join(script_dir, "pages_text_array.json")
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            combined_pages_text = json.load(json_file)
        for i in range(limit):
            combined_relevant_pages += combined_pages_text[int(results[i][0])] + "\n"

        output_file_path = os.path.join(script_dir, "query_results.txt")
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(combined_relevant_pages)
        return combined_relevant_pages
    except Exception as e:
        logging.error(f"Error querying similar pages: {e}")
        return ""

def generate_response(query, relevant_pages):
    """
    Generate a response based on the relevant pages using the OpenAI API.

    Args:
    - relevant_pages (str): A string containing the text of the relevant pages.

    Returns:
    - str: The generated response from the OpenAI API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who can answer a military training question based only on the provided text."},
                {"role": "user", "content": "here is the user's question that you need to answer: "+query+" And here are the relevant pages of the manual you need to read and pull from to answer the question - make sure to include the page numbers of all the pages given: "+relevant_pages}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return ""
    





# To process the pdfs and initialize the vector DB in supabase uncomment below:
# riflecarbine_path = os.path.join(script_dir, "riflecarbine.pdf")
# riflecarbine_pages = extract_text_and_images(riflecarbine_path)


# iwq_path = os.path.join(script_dir, "iwq.pdf")
# iwq_pages = extract_text_and_images(iwq_path)
# combined_pages_text = riflecarbine_pages + iwq_pages
# # Define the path for the JSON file
# json_file_path = os.path.join(script_dir, "pages_text_array.json")
# # Save the combined_pages_text as a JSON file
# with open(json_file_path, "w", encoding="utf-8") as json_file:
#     json.dump(riflecarbine_pages, json_file, ensure_ascii=False, indent=4)
# generate_and_store_embeddings_from_texts(riflecarbine_pages)

