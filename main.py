import os
import subprocess
import sys
import threading
import time
import requests
from flask import Flask, Response, request

app = Flask(__name__)
node_process = None
NODE_PORT = 3000

def start_node_server():
    global node_process
    if node_process is None:
        print("Starting Node.js server...")
        # Set the NODE_PORT environment variable for the Node.js process
        env = os.environ.copy()
        env['NODE_PORT'] = str(NODE_PORT)
        node_process = subprocess.Popen(['node', 'main.js'], env=env, stdout=sys.stdout, stderr=sys.stderr)
        # Give Node.js server time to start
        time.sleep(2)
        print("Node.js server started on port", NODE_PORT)

# Start Node.js server in a separate thread when Gunicorn loads
def start_node_thread():
    thread = threading.Thread(target=start_node_server)
    thread.daemon = True
    thread.start()

start_node_thread()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Proxy all traffic to the Node.js app
    node_url = f"http://localhost:{NODE_PORT}/{path}"
    
    # Forward the request to the Node.js server
    resp = requests.request(
        method=request.method,
        url=node_url,
        headers={key: value for key, value in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True
    )
    
    # Create a Flask response from the Node.js response
    response = Response(resp.content, resp.status_code)
    
    # Copy headers from Node.js response
    for key, value in resp.headers.items():
        if key.lower() != 'content-length':  # Exclude content-length which will be set automatically
            response.headers[key] = value
            
    return response

# For local testing
if __name__ == '__main__':
    start_node_server()
    app.run(host='0.0.0.0', port=5000)