from fastapi import FastAPI
import time
from pydantic import BaseModel
from extracttext import query_similar_pages, generate_response


app = FastAPI()


# Define a Pydantic model for the expected data structure
class InputData(BaseModel):
    message: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application"}

@app.post("/chat_input")


async def receive_input(data: InputData):
    start_time = time.time()
    
    # Access the message from the InputData model
    relevant_pages = query_similar_pages(data.message)
    query_time = time.time()
    print(f"query_similar_pages took {query_time - start_time} seconds")
    
    chat_response = generate_response(data.message, relevant_pages)
    response_time = time.time()
    print(f"generate_response took {response_time - query_time} seconds")
    
    total_time = response_time - start_time
    print(f"Total time for receive_input: {total_time} seconds")
    
    return {"chat_response": chat_response}
