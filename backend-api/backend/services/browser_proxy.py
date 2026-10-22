"""A loopback CONNECT proxy: browser traffic may reach public HTTPS only.

DNS is resolved and pinned before connecting, including redirects/subresources.
No TLS interception, cookies, credential forwarding or certificate exceptions.
"""
import ipaddress
import select
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def public_addresses(host, port):
    if port != 443:
        raise ValueError('Only HTTPS is allowed')
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Non-public address')
    return list(dict.fromkeys(item[4][0] for item in addresses))


class PublicProxy:
    def __init__(self):
        self.active = threading.Event()
        self.active.set()
        self.lock = threading.Lock()
        self.bytes = 0
        self.requests = 0
        self.deadline = time.monotonic() + 65

    def __enter__(self):
        guard = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_error(403)

            def do_CONNECT(self):
                upstream = None
                try:
                    with guard.lock:
                        guard.requests += 1
                        if guard.requests > 500 or guard.bytes > 40_000_000:
                            raise ValueError('Network budget exceeded')
                    host, port = self.path.rsplit(':', 1)
                    addresses = public_addresses(host.strip('[]'), int(port))
                    for address in addresses[:3]:
                        try:
                            upstream = socket.create_connection((address, int(port)), timeout=3)
                            break
                        except OSError:
                            continue
                    if upstream is None:
                        raise OSError('Connection failed')
                    self.send_response(200, 'Connection established')
                    self.end_headers()
                    self.wfile.flush()
                    self.connection.setblocking(False)
                    upstream.setblocking(False)
                    while guard.active.is_set() and time.monotonic() < guard.deadline:
                        ready, _, _ = select.select([self.connection, upstream], [], [], 1)
                        for source in ready:
                            chunk = source.recv(32768)
                            if not chunk:
                                return
                            with guard.lock:
                                guard.bytes += len(chunk)
                                if guard.bytes > 40_000_000:
                                    return
                            target = upstream if source is self.connection else self.connection
                            target.settimeout(3)
                            target.sendall(chunk)
                            target.setblocking(False)
                except (OSError, ValueError):
                    if upstream is None:
                        try:
                            self.send_error(403)
                        except OSError:
                            pass
                finally:
                    if upstream is not None:
                        upstream.close()
                    self.close_connection = True

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f'http://127.0.0.1:{self.server.server_port}'

    def __exit__(self, *args):
        self.active.clear()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
