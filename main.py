from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()
# --- SEGURIDAD DE TU APP ---
API_KEY_APP = "mi_super_secreto_123"  # La llave que pondrás en Flutter
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verificar_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY_APP:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return api_key


# --- CONEXIÓN A GROQ ---
# Pega aquí la llave que te dio la página de Groq (gsk_...)
api_key = os.getenv("GROQ_API_KEY")
cliente_groq = Groq(api_key=api_key)

app = FastAPI(title="Mi API con Groq")


class SolicitudIA(BaseModel):
    pregunta: str
    # Groq usa modelos diferentes. Llama 3 de 8B es súper rápido y excelente.
    modelo: str = "llama-3.3-70b-versatile"


@app.post("/generar/")
async def generar_respuesta(solicitud: SolicitudIA, key: str = Depends(verificar_api_key)):
    # Esta función va soltando las palabras poco a poco (Streaming)
    def generador_stream():
        try:
            stream = cliente_groq.chat.completions.create(
                messages=[{"role": "user", "content": solicitud.pregunta}],
                model=solicitud.modelo,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    pedacito = chunk.choices[0].delta.content
                    # Lo empaquetamos en JSON para que Flutter lo entienda fácil
                    yield json.dumps({"respuesta": pedacito}) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    # Retornamos la respuesta en formato stream
    return StreamingResponse(generador_stream(), media_type="application/x-ndjson")