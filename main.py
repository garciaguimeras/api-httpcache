import threading
import httpcache
from flask import Flask, request

app = Flask(__name__)

@app.route("/health")
def health():
    return "v1.0.0", 200

@app.route("/")
def get():
    q = request.args.get("q")
    if q is None:
        return "Missing url param: 'q'", 400
    
    try:
        content = httpcache.get_url_content(q)
        if content is None:
            return "Page content not found", 404

        return content, 200
    except Exception as e:
        return "Internal error getting page content: " + e.args, 500

@app.route("/update")
def update():
    try: 
        t = threading.Thread(target=httpcache.update_content)
        t.start()
            
        return "Thread started. Follow httpcache.log to get update results", 200
    except Exception as e:
        return "Internal error starting thread to update content: " + e.args, 500
