from flask import Flask, render_template, request, jsonify
from run import Chat, initialize_llm
import threading
import uuid
import os

app = Flask(__name__)

chain, memory = initialize_llm()

results = {}
results_lock = threading.Lock() 

def process_chat_request(task_id, youtube_url, user_query):
    try:
        response = Chat(youtube_url, user_query, chain, memory)
        with results_lock:
            results[task_id] = {"status": "complete", "response": response}
    except Exception as e:
        with results_lock:
            results[task_id] = {"status": "error", "response": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    youtube_url = data.get('youtube_url')
    user_query = data.get('query')
    
    task_id = str(uuid.uuid4())
    
    thread = threading.Thread(
        target=process_chat_request,
        args=(task_id, youtube_url, user_query)
    )
    thread.start()
    
    return jsonify({"task_id": task_id})

@app.route('/status/<task_id>')
def get_status(task_id):
    with results_lock:
        if task_id in results:
            result = results[task_id]
            if result["status"] in ("complete", "error"):
                response = results.pop(task_id)
                return jsonify(response)
    return jsonify({"status": "processing"})

if __name__ == '__main__':
    # قراءة متغير PORT من البيئة، واستخدام 5000 إذا لم يتوفر
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
