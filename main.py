from fastapi import FastAPI
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
    # Access the message from the InputData model
    relevant_pages = query_similar_pages(data.message)
    chat_response = generate_response(data.message, relevant_pages)
    return {"chat_response": chat_response}
