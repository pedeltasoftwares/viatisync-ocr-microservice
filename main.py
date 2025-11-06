from fastapi import FastAPI, UploadFile, File
from ocr_service import procesar_documento

app = FastAPI()

@app.post("/ocr/extract")
async def extract(file: UploadFile = File(...)):
    file_bytes = await file.read()
    data = procesar_documento(file_bytes, file.filename)
    return {"ok": True, "data": data}