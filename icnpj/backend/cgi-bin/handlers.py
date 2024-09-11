# handlers.py
import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse
from functools import cached_property
from auth import check_credentials, create_token_for_user, validate_token
from cnpj import investiga
from cnpj import compara

class WebRequestHandler(BaseHTTPRequestHandler):

    STATIC_DIR = os.path.join(os.getcwd(), 'static')  # Diretório para arquivos estáticos

    @cached_property
    def url(self):
        return urlparse(self.path)

    @cached_property
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    @cached_property
    def post_data(self):
        content_length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(content_length)

    @cached_property
    def form_data(self):
        return dict(parse_qsl(self.post_data.decode("utf-8")))

    def _set_cors_headers(self):
        """Define os cabeçalhos CORS para a resposta."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    def serve_static_file(self, filename):
        """Serve um arquivo estático localizado no diretório 'static'."""
        # Remove o prefixo '/static/' do caminho
        static_path = filename.replace("/static/", "", 1)

        # Constrói o caminho completo do arquivo
        filepath = os.path.join(self.STATIC_DIR, static_path)
        print(filepath)
        
        if not os.path.exists(filepath):
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>404 Not Found</h1></body></html>")
            return

        # Determina o tipo de conteúdo com base na extensão do arquivo
        if filepath.endswith(".js"):
            content_type = "application/javascript"
        elif filepath.endswith(".css"):
            content_type = "text/css"
        elif filepath.endswith(".html"):
            content_type = "text/html"
        else:
            content_type = "application/octet-stream"

        # Lê e serve o arquivo
        try:
            with open(filepath, 'rb') as file:
                self.send_response(200)
                self._set_cors_headers()
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_response(500)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>500 Internal Server Error</h1></body></html>")


    def handle_login(self):
        username = self.form_data.get("username")
        password = self.form_data.get("password")

        if not check_credentials(username, password):
            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return json.dumps({"error": "Permission Denied"})

        token = create_token_for_user(username)
        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        return json.dumps({"message": "Login successful", "token": token})

    def handle_search(self):
        token = self.headers.get("Authorization")

        if not token or not validate_token(token):
            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return json.dumps({"error": "Permission Denied"})

        cnpjs = self.form_data.get("cnpjs")
        if not cnpjs:
            self.send_response(400)
            self._set_cors_headers()
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return json.dumps({"error": "No CNPJs provided"})

        response_data = investiga(cnpjs)

        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        return json.dumps(response_data)

    def handle_compare(self):
        token = self.headers.get("Authorization")

        if not token or not validate_token(token):
            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return json.dumps({"error": "Permission Denied"})

        cnpjs = self.form_data.get("cnpjs")
        if not cnpjs:
            self.send_response(400)
            self._set_cors_headers()
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return json.dumps({"error": "No CNPJs provided"})

        response_data = compara(cnpjs)

        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        return json.dumps(response_data)

    def handle_homepage(self):
        # Especifica o caminho para o arquivo HTML que você deseja servir
        html_path = os.path.join(os.getcwd(), 'index.html')

        try:
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            return html_content

        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            return "<html><body><h1>404 Not Found</h1><p>The requested page was not found on this server.</p></body></html>"

    def get_response(self):
        if self.url.path == "/":
            return self.handle_homepage()
        elif self.url.path == "/login":
            return self.handle_login()
        elif self.url.path == "/search":
            return self.handle_search()
        elif self.url.path == "/compare":
            return self.handle_compare()
        elif self.url.path.startswith("/static/"):
            # Servir arquivos estáticos
            self.serve_static_file(self.url.path)
            return ""
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return json.dumps({"error": "Invalid path"})

    def do_GET(self):
        response = self.get_response()
        if response is not None:
            self.wfile.write(response.encode("utf-8"))

    def do_POST(self):
        self.do_GET()
    
    def do_OPTIONS(self):
        """Responde a requisições OPTIONS para suportar CORS pré-flights."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()