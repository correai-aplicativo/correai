from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import requests
import openai
import os

app = FastAPI()

CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI')
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.get("/")
def home():
    return {"mensagem": "API integração Strava+GPT funcionando!"}

@app.get("/login")
def login():
    strava_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=activity:read_all"
    return RedirectResponse(strava_url)

@app.get("/callback")
def callback(request: Request):
    code = request.query_params.get('code')
    token_res = requests.post('https://www.strava.com/oauth/token', data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }).json()

    token = token_res.get("access_token")

    atividades = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    resumo = "\n".join([
        f"{a['name']}: {a['distance']/1000:.1f} km em {a['moving_time']//60} min"
        for a in atividades[:3]
    ])

    prompt = f"Essas são minhas últimas atividades: {resumo}. Me dê recomendações rápidas para melhorar minha corrida e evitar lesões."

    resposta = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Você é um treinador virtual especializado em corrida."},
            {"role": "user", "content": prompt}
        ]
    )

    return {
        "suas_atividades": resumo,
        "recomendacoes": resposta.choices[0].message.content
    }
