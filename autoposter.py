# San Antonio Abad, ora pro nobis
# San Carlo Acutis, ora pro nobis
import os
import requests
from bs4 import BeautifulSoup
import datetime as dt
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# 📌 Configura tus datos aquí:
PARROQUIA_PAGE_ID = os.getenv('PARROQUIA_PAGE_ID')
PARROQUIA_TOKEN = os.getenv('PARROQUIA_TOKEN')
FACEBOOK_API_URL = f"https://graph.facebook.com/{PARROQUIA_PAGE_ID}/feed"


def get_dominicos_content():
    url = "https://www.dominicos.org/predicacion/evangelio-del-dia/hoy/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    contenido = {}

    lecturas_div = soup.find_all("div", class_="lectura")
    if lecturas_div:
        contenido['lecturas'] = "\n\n".join([l.get_text(strip=True, separator="\n") for l in lecturas_div])

    evangelio_div = soup.find("div", class_="evangelio")
    if evangelio_div:
        contenido['evangelio'] = evangelio_div.get_text(strip=True, separator="\n")

    audio_tag = soup.find("audio")
    if audio_tag and audio_tag.find("source"):
        contenido['audio_url'] = audio_tag.find("source").get("src")

    comentario_div = soup.find("div", class_="comentario")
    if comentario_div:
        contenido['comentario'] = comentario_div.get_text(strip=True, separator="\n")

    return contenido


def build_message(data):
    mensaje = f"📖 *Lecturas del día* 📖\n\n{data.get('lecturas', '')}\n\n"
    mensaje += f"📖 *Evangelio* 📖\n\n{data.get('evangelio', '')}\n\n"
    if 'audio_url' in data:
        mensaje += f"🎧 *Escúcha el Evangelio aquí:* {data['audio_url']}\n\n"
    mensaje += f"💬 *Comentario:* 💬\n\n{data.get('comentario', '')}\n"
    return mensaje.strip()


def schedule_facebook_post(msg, schedule_time):
    payload = {
        'access_token': PARROQUIA_TOKEN,
        'message': msg,
        'published': False,
        'scheduled_publish_time': int(schedule_time.timestamp())
    }
    response = requests.post(FACEBOOK_API_URL, data=payload)
    print(f"{dt.datetime.now()}: Scheduled - {response.status_code} - {response.text}")


app = Flask(__name__)


@app.route('/')
def home():
    return "⛪ Bot parroquial activo."


@app.route('/programar')
def programar():
    print("⛪ Publicador Parroquial iniciado...")
    datos = get_dominicos_content()
    status = datos
    if datos:
        mensaje = build_message(datos)

        # 🕕 Programar para 6:00am hora de Puerto Rico (UTC-4)
        today = dt.datetime.utcnow().date()
        scheduled_time = dt.datetime(today.year, today.month, today.day, 10, 0, tzinfo=dt.timezone.utc)  # 10:00 UTC = 6:00 PR

        status = schedule_facebook_post(mensaje, scheduled_time)
    else:
        print("⚠️ No se pudo extraer contenido desde dominicos.org")
    return f"🕒 Publicación programada con status: {status}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
