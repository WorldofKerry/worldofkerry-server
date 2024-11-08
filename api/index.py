from flask import Flask, request, jsonify, send_file, Response
from pymongo import MongoClient
from gridfs import GridFS
import re
import io

app = Flask(__name__)

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://readwrite:Pk1JnYa1qwo63aac@cluster0.wdytait.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['file_uploads']
fs = GridFS(db)

# HTML Template for uploading and downloading files
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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

# Endpoint to handle file upload
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
        if not re.match("^[a-zA-Z0-9]+$", custom_file_id):
            return jsonify({"error": "Invalid file ID. Only alphanumeric characters are allowed."}), 400
        if fs.exists({"_id": custom_file_id}):
            return jsonify({"error": "File ID already exists. Please choose a different ID."}), 400
        
        file_id = fs.put(file, _id=custom_file_id, filename=file.filename, content_type=file.content_type)
    else:
        file_id = fs.put(file, filename=file.filename, content_type=file.content_type)
    
    return jsonify({"message": "File uploaded successfully", "file_id": str(file_id)}), 200

# API and Web form route for file download by file_id
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

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
