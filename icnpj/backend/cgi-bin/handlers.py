# handlers.py
import os
import json
import logging
import gzip
from io import BytesIO
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse
from functools import cached_property
from auth import check_credentials, create_token_for_user, validate_token
from cnpj import investiga
from cnpj import compara

DEBUG=False

class WebRequestHandler(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"  # Definir a versão correta aqui

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
        # print(filepath)
        
        if not os.path.exists(filepath):
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
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
                file_content = file.read()

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(file_content)))  # 🔹 Adiciona Content-Length
            self.send_header("Connection", "close")  # 🔹 Fecha corretamente a conexão
            self.end_headers()
            self.wfile.write(file_content)
            self.wfile.flush()  # 🔹 Garante que os dados são enviados imediatamente

        except Exception as e:
            self.send_response(500)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()


    def handle_login(self):
        username = self.form_data.get("username")
        password = self.form_data.get("password")

        # Imprime diretamente no log do servidor
        self.log_message("Login | user: %s", username)

        if not check_credentials(username, password):
            error_response = json.dumps({"error": "Permissão Negada"}).encode("utf-8")

            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")  # ✅ Fecha corretamente a conexão
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()
            return

        # Gera o token e prepara a resposta JSON
        token = create_token_for_user(username)
        response_data = json.dumps({"Mensagem": "Login realizado com sucesso", "token": token}).encode("utf-8")

        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_data)))  # ✅ Define Content-Length
        self.send_header("Connection", "close")  # ✅ Fecha corretamente a conexão
        self.end_headers()
        self.wfile.write(response_data)
        self.wfile.flush()

    def handle_search(self):
        token = self.headers.get("Authorization")

        if not token or not validate_token(token):
            error_response = json.dumps({"error": "Permissão negada"}).encode("utf-8")

            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()
            return

        cnpjs = self.form_data.get("cnpjs")
        cpfs  = self.form_data.get("cpfs")
        self.log_message("search | CNPJ: %s CPF: %s", cnpjs, cpfs)
        
        if not cnpjs:
            error_response = json.dumps({"error": "Nenhum CNPJ informado"}).encode("utf-8")

            self.send_response(400)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()
            return 

        try:
            response_data = investiga(cnpjs, cpfs)
            response_json = json.dumps(response_data).encode("utf-8")

            if DEBUG:
                print("Voltei da investigacao", flush=True)

            # 🔹 Compacta a resposta JSON com Gzip
            buffer = BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb') as gzip_file:
                gzip_file.write(response_json)

            compressed_data = buffer.getvalue()

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Encoding", "gzip")  # ✅ Indica compactação
            self.send_header("Content-Length", str(len(compressed_data)))  # ✅ Define Content-Length correto
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(compressed_data)
            self.wfile.flush()

            return
            
        except ValueError as e:
            # Captura a exceção e retorna como resposta JSON
            error_response = json.dumps({"error": str(e)}).encode("utf-8")

            self.send_response(400)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()
            
    def handle_compare(self):
        token = self.headers.get("Authorization")

        if not token or not validate_token(token):
            error_response = json.dumps({"error": "Permissão negada"}).encode("utf-8")

            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()
            return

        cnpjs = self.form_data.get("cnpjs")
        self.log_message("compare | %s", cnpjs)
        
        if not cnpjs:
            error_response = json.dumps({"error": "CNPJs não fornecidos"}).encode("utf-8")

            self.send_response(400)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()
            return

        try: 
            response_data = compara(cnpjs)
            response_json = json.dumps(response_data).encode("utf-8")
        
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_json)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()

            self.wfile.write(response_json)
            self.wfile.flush()  # ✅ Garante envio completo
        
        except ValueError as e:
            error_response = json.dumps({"error": str(e)}).encode("utf-8")

            self.send_response(400)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()

    def handle_homepage(self):
        # Especifica o caminho para o arquivo HTML que você deseja servir
        html_path = os.path.join(os.getcwd(), 'index.html')

        try:
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            response_data = html_content.encode("utf-8")  # Converte para bytes

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(response_data)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")  # ✅ Fecha corretamente a conexão
            self.end_headers()
            self.wfile.write(response_data)
            self.wfile.flush()  # ✅ Garante que os dados são enviados imediatamente

        except FileNotFoundError:
            error_response = b"<html><body><h1>404 Not Found</h1><p>The requested page was not found on this server.</p></body></html>"
        
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()

    def handle_log_acao(self):
        """Recebe os cliques de Like/Dislike e imprime no log do servidor."""
        try:
            # Lê os dados enviados via POST
            dados = json.loads(self.post_data)
            acao = dados.get("acao")
            cnpjs = dados.get("cnpjs")

            # Imprime diretamente no log do servidor
            self.log_message("%s | CNPJs: %s", acao, cnpjs)

            # Prepara a resposta JSON
            response_data = json.dumps({"status": "Log registrado"}).encode("utf-8")

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_data)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(response_data)
            self.wfile.flush()

        except (json.JSONDecodeError, ValueError) as e:
            error_response = json.dumps({"error": str(e)}).encode("utf-8")

            self.send_response(400)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))  # ✅ Define Content-Length
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(error_response)
            self.wfile.flush()

    def handle_favicon(self):
        """Serve o favicon.ico se solicitado."""
        favicon_path = os.path.join(self.STATIC_DIR, "favicon.ico")
        
        if not os.path.exists(favicon_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            return

        try:
            with open(favicon_path, "rb") as file:
                file_content = file.read()
                
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", str(len(file_content)))  # 🔹 Define o tamanho do favicon
            self.send_header("Connection", "close")  # 🔹 Garante que a conexão seja fechada corretamente
            self.end_headers()
            self.wfile.write(file_content)
            self.wfile.flush()  # 🔹 Garante que os dados são enviados imediatamente
        
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>500 Internal Server Error</h1></body></html>")


    def get_response(self):
        if self.url.path == "/":
            return self.handle_homepage()
        elif self.url.path == "/login":
            return self.handle_login()
        elif self.url.path == "/search":
            return self.handle_search()
        elif self.url.path == "/compare":
            return self.handle_compare()
        elif self.url.path == "/log_acao":  
            return self.handle_log_acao()
        elif self.url.path == "/favicon.ico":  # Nova rota para favicon
            return self.handle_favicon()
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