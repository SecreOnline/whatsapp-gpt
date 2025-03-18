import requests
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuración de APIs
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/TU_NUMERO_ID/messages"
WHATSAPP_TOKEN = "TU_TOKEN_DE_META"
OPENAI_API_KEY = "TU_OPENAI_API_KEY"

def obtener_info(categoria):
    conn = sqlite3.connect("secreonline.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contenido FROM informacion WHERE categoria = ?", (categoria,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else "No tengo información sobre eso."

def generar_prompt(mensaje):
    if "precio" in mensaje or "tarifa" in mensaje:
        info_relevante = obtener_info("tarifas")
    elif "horario" in mensaje:
        info_relevante = obtener_info("horarios")
    elif "protocolo" in mensaje:
        info_relevante = obtener_info("protocolos")
    else:
        info_relevante = "Responde de manera general sobre SecreOnline."

    prompt = f"""
    Eres el asistente de SecreOnline. Usa esta información para responder:
    {info_relevante}
    Cliente: {mensaje}
    """
    return prompt

def obtener_respuesta_gpt(mensaje_cliente):
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "system", "content": generar_prompt(mensaje_cliente)},
            {"role": "user", "content": mensaje_cliente}
        ]
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"] if response.status_code == 200 else "Error en la respuesta."

def enviar_respuesta_whatsapp(numero_cliente, respuesta):
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_cliente,
        "text": {"body": respuesta}
    }
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    requests.post(WHATSAPP_API_URL, json=payload, headers=headers)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if "messages" in data and len(data["messages"]) > 0:
        numero_cliente = data["messages"][0]["from"]
        mensaje_cliente = data["messages"][0]["text"]["body"]
        respuesta_gpt = obtener_respuesta_gpt(mensaje_cliente)
        enviar_respuesta_whatsapp(numero_cliente, respuesta_gpt)
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
