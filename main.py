from typing import Union
from api_sample import generate_move
from fastapi import FastAPI

app = FastAPI()

@app.post("/items")
async def send_moves(moves: list[str]):
	return generate_move(moves)
