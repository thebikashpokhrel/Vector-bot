from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Yayy!! The bot is still alive"}
