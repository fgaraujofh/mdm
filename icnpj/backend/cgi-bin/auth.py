# auth.py

import uuid
from datetime import datetime, timedelta

# Simulação de um armazenamento de tokens simples
active_tokens = {}
timeout_in_hour = 6
DEBUG=True

valid_credentials = [
    ("jdoe", "s3cret"),
    ("asmith", "password123"),
    ("mjackson", "thriller"),
    ("lucas", "entra@CNJ"),
    ("chico", "entra@CNJ"),
    ("augusto", "entra@CNJ")
]


def check_credentials(username, password):
    # Verifica se a combinação de username e password está na lista de credenciais válidas
    return (username, password) in valid_credentials

def generate_token():
    return str(uuid.uuid4())

def validate_token(token):
    if (DEBUG):
        return True

    token_data = active_tokens.get(token)
    if not token_data:
        return False
    
    creation_time = token_data['creation_time']  # Acessa a data de criação do token
    if datetime.now() - creation_time > timedelta(hours=timeout_in_hour):
        # Se o token já passou de 6 horas, ele é inválido e deve ser removido
        del active_tokens[token]
        return False
    return True

def create_token_for_user(username):
    token = generate_token()
    creation_time = datetime.now()
    active_tokens[token] = {'username': username, 'creation_time': creation_time}
    return token