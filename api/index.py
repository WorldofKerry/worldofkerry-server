import re
import threading
import time

import urllib
from flask import Flask, request, jsonify, Response
from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from flask import send_from_directory

load_dotenv(os.path.join(os.path.dirname(__file__), ".env.local"))

MONGODB_URI = os.getenv("MONGODB_URI")

app = Flask(__name__)

client = MongoClient(MONGODB_URI)
db = client['file_uploads']
fs = GridFS(db)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">
        <title>Upload and Download Files</title>
    </head>
    <body>
        <h2>Upload File</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <br/>
            <input type="text" name="file_id" placeholder="File ID (optional)">
            <br/>
            <button type="submit">Upload</button>
        </form>

        <h2>Download File</h2>
        <form action="/download" method="get">
            <input type="text" name="file_id" placeholder="File ID" required>
            <br/>
            <button type="submit">Download</button>
        </form>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    custom_file_id = request.form.get('file_id')
    
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    # Validate custom file ID
    if custom_file_id:
        if urllib.parse.quote(custom_file_id) != custom_file_id:
            return jsonify({"error": f"Invalid file ID. Only valid URL characters allowed. File ID `{custom_file_id}` becomes `{urllib.parse.quote(custom_file_id)}`"}), 400
        if fs.exists({"_id": custom_file_id}):
            return jsonify({"error": "File ID already exists. Please choose a different file ID."}), 400

        file_id = fs.put(file, _id=custom_file_id, filename=file.filename, content_type=file.content_type)
    else:
        file_id = fs.put(file, filename=file.filename, content_type=file.content_type)
    
    return jsonify({"message": "File uploaded successfully", "file_id": str(file_id)}), 200

@app.route('/download', methods=['GET'])
def download_file():
    file_id = request.args.get('file_id') or request.view_args.get('file_id')
    if not file_id:
        return jsonify({"error": "File ID is required"}), 400
    
    try:
        file = fs.get(file_id)
        return Response(
            file.read(),
            mimetype=file.content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{file.filename}"'
            }
        )
    except:
        return jsonify({"error": "File not found"}), 404

@app.route('/ping')
def ping():
    client.admin.command('ping')
    current_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fs.put(b'', filename=f"ping-{current_time_string}.txt", content_type="text/plain")
    return jsonify({"message": f"Ping successful at {current_time_string}"}), 200

def delete_old_files():
    while True:
        time_threshold = datetime.now() - timedelta(minutes=60)

        for file in fs.find({"uploadDate": {"$lt": time_threshold}}):
            fs.delete(file._id)
            print(f"Deleted file: {file.filename} (ID: {file._id})")

        time.sleep(60)

def start_cleanup_task():
    cleanup_thread = threading.Thread(target=delete_old_files, daemon=True)
    cleanup_thread.start()

@app.before_first_request
def before_first_request():
    start_cleanup_task()

if __name__ == '__main__':
    app.run(debug=True)
