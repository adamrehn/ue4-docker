import multiprocessing, secrets, time, urllib.parse
from .NetworkUtils import NetworkUtils
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from functools import partial


class CredentialRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, username: str, password: str, token: str, *args, **kwargs):
        self.username = username
        self.password = password
        self.token = token
        super().__init__(*args, **kwargs)

    def log_request(self, code: str = "-", size: str = "-") -> None:
        # We do not want to log each and every incoming request
        pass

    def do_POST(self):
        query_components = parse_qs(urlparse(self.path).query)

        self.send_response(200)
        self.end_headers()

        if "token" in query_components and query_components["token"][0] == self.token:
            content_length = int(self.headers["Content-Length"])
            prompt = self.rfile.read(content_length).decode("utf-8")

            response = self.password if "Password for" in prompt else self.username
            self.wfile.write(response.encode("utf-8"))


class CredentialEndpoint(object):
    def __init__(self, username: str, password: str):
        """
        Creates an endpoint manager for the supplied credentials
        """

        # Make sure neither our username or password are blank, since that can cause `git clone` to hang indefinitely
        self.username = username if username is not None and len(username) > 0 else " "
        self.password = password if password is not None and len(password) > 0 else " "
        self.endpoint = None

        # Generate a security token to require when requesting credentials
        self.token = secrets.token_hex(16)

    def args(self) -> [str]:
        """
        Returns the Docker build arguments for creating containers that require Git credentials
        """

        # Resolve the IP address for the host system
        hostAddress = NetworkUtils.hostIP()

        # Provide the host address and security token to the container
        return [
            "--build-arg",
            "HOST_ADDRESS_ARG=" + urllib.parse.quote_plus(hostAddress),
            "--build-arg",
            "HOST_TOKEN_ARG=" + urllib.parse.quote_plus(self.token),
        ]

    def start(self) -> None:
        """
        Starts the HTTP endpoint as a child process
        """

        # Create a child process to run the credential endpoint
        self.endpoint = multiprocessing.Process(
            target=CredentialEndpoint._endpoint,
            args=(self.username, self.password, self.token),
        )

        # Spawn the child process and give the endpoint time to start
        self.endpoint.start()
        time.sleep(2)

        # Verify that the endpoint started correctly
        if not self.endpoint.is_alive():
            raise RuntimeError("failed to start the credential endpoint")

    def stop(self) -> None:
        """
        Stops the HTTP endpoint child process
        """
        self.endpoint.terminate()
        self.endpoint.join()

    @staticmethod
    def _endpoint(username: str, password: str, token: str) -> None:
        """
        Implements a HTTP endpoint to provide Git credentials to Docker containers
        """
        handler = partial(CredentialRequestHandler, username, password, token)

        server = HTTPServer(("0.0.0.0", 9876), RequestHandlerClass=handler)
        server.serve_forever()
