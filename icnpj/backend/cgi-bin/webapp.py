import argparse
import socketserver
from http.server import HTTPServer, ThreadingHTTPServer
from handlers import WebRequestHandler

class CustomHTTPServer(ThreadingHTTPServer):
    """Custom HTTPServer with increased timeout and threaded handling."""

    protocol_version = "HTTP/1.1"
    def __init__(self, server_address, RequestHandlerClass, timeout=300):
        super().__init__(server_address, RequestHandlerClass)
        self.timeout = timeout
        self.request_queue_size = 100  # Ajusta tamanho da fila de requisições

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a simple HTTP server.")
    parser.add_argument('--port', type=int, default=8080, help='Port to run the HTTP server on')
    args = parser.parse_args()

    server = CustomHTTPServer(("0.0.0.0", args.port), WebRequestHandler, timeout=300)
    print(f"Starting threaded server on port {args.port} with timeout {server.timeout} seconds...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()