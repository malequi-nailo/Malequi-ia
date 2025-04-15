import os
import json
from firebase_admin import credentials, firestore, initialize_app
import requests
from flask import Flask, request, jsonify

# Configuração do Firebase
cred_dict = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
cred = credentials.Certificate(cred_dict)
initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

def save_to_memory(user_id, command, response):
    """Salva conversa no Firebase."""
    db.collection('conversations').add({
        'user_id': user_id,
        'command': command,
        'response': response,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

def get_memory(user_id):
    """Recupera histórico de conversas."""
    docs = db.collection('conversations').where('user_id', '==', user_id).stream()
    return [(doc.to_dict()['command'], doc.to_dict()['response']) for doc in docs]

def search_internet(query):
    """Busca na internet usando a Wikipedia."""
    wiki_url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{query}"
    try:
        response = requests.get(wiki_url)
        data = response.json()
        return data.get('extract', 'Não encontrei informações.')
    except:
        return "Erro ao buscar na internet."

def process_command(command, user_id="user1"):
    """Processa o comando com contexto da memória."""
    if not command:
        return "Digite algo para começar!"

    history = get_memory(user_id)
    context = "\n".join([f"Usuário: {cmd}\nJARVIS: {resp}" for cmd, resp in history[-3:]])
    
    if "quem é" in command or "o que é" in command:
        query = command.replace("quem é", "").replace("o what é", "").strip()
        print(f"Buscando sobre {query}...")
        result = search_internet(query)
        save_to_memory(user_id, command, result)
        return result
    elif "sair" in command:
        return "Até mais, chefe!"
    else:
        response = f"Eu sou JARVIS. Com base no que conversamos antes: {context}\nSobre '{command}', não sei ainda. Quer que eu pesquise algo específico?"
        save_to_memory(user_id, command, response)
        return response

@app.route('/jarvis', methods=['POST'])
def jarvis():
    data = request.get_json()
    command = data.get('command')
    user_id = data.get('user_id', 'user1')
    response = process_command(command, user_id)
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
