from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from gridfs import GridFS
import os

app = Flask(__name__)

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://readwrite:Pk1JnYa1qwo63aac@cluster0.wdytait.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # Replace with your MongoDB Atlas URI
db = client['your_database_name']               # Replace with your database name
fs = GridFS(db)

# HTML Template for uploading files
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload File</title>
    </head>
    <body>
        <h2>Upload File to MongoDB</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Upload</button>
        </form>
    </body>
    </html>
    '''

# Endpoint to handle file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    # Store file in GridFS
    file_id = fs.put(file, filename=file.filename, content_type=file.content_type)
    
    return jsonify({"message": "File uploaded successfully", "file_id": str(file_id)}), 200

# Endpoint to download file by ID
@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        file = fs.get(file_id)
        return file.read(), 200, {
            'Content-Type': file.content_type,
            'Content-Disposition': f'attachment; filename="{file.filename}"'
        }
    except:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
