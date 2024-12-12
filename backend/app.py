from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import re
import random
import string
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Paths for uploaded and masked files
UPLOAD_FOLDER_ORIGINAL = 'uploads/original'
UPLOAD_FOLDER_MASKED = 'uploads/masked'
app.config['UPLOAD_FOLDER_ORIGINAL'] = UPLOAD_FOLDER_ORIGINAL
app.config['UPLOAD_FOLDER_MASKED'] = UPLOAD_FOLDER_MASKED

# Create directories if they do not exist
os.makedirs(UPLOAD_FOLDER_ORIGINAL, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_MASKED, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    return secure_filename(filename)

def mask_data(value, column_name=None):
    if isinstance(value, str):
        if re.match(r"[^@]+@[^@]+\.[^@]+", value):
            local, domain = value.split("@")
            local_masked = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else '*' * len(local)
            return f"{local_masked}@{domain}"
        if len(value) > 2:
            return value[0] + '*' * (len(value) - 2) + value[-1]
        else:
            return '*' * len(value)
    elif isinstance(value, (int, float)):
        num_str = str(int(value))
        return int(''.join(random.choice(string.digits) for _ in num_str))
    return value

@app.route("/detect_columns", methods=["POST"])
def detect_columns():
    file = request.files.get("file")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "No file uploaded or file format not supported"}), 400

    input_path = os.path.join(UPLOAD_FOLDER_ORIGINAL, sanitize_filename(file.filename))
    file.save(input_path)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(input_path)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(input_path)

        columns = df.columns.tolist()
        return jsonify({"columns": columns})
    except Exception as e:
        return jsonify({"error": f"Failed to process the file. Error: {str(e)}"}), 500

@app.route("/mask_data", methods=["POST"])
def mask_data_route():
    file = request.files.get("file")
    columns_to_mask = request.form.get("columns")

    if not file or not columns_to_mask:
        return jsonify({"error": "No file uploaded or columns selected for masking."}), 400

    try:
        columns_to_mask = json.loads(columns_to_mask)
        input_path = os.path.join(UPLOAD_FOLDER_ORIGINAL, sanitize_filename(file.filename))
        file.save(input_path)

        if file.filename.endswith('.csv'):
            df = pd.read_csv(input_path)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(input_path)

        for column in columns_to_mask:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: mask_data(x, column))
            else:
                print(f"Warning: Column {column} not found in DataFrame.")

        # Save the masked file in the masked folder
        masked_file_path = os.path.join(UPLOAD_FOLDER_MASKED, f"masked_{sanitize_filename(file.filename)}")
        if file.filename.endswith('.csv'):
            df.to_csv(masked_file_path, index=False)
        elif file.filename.endswith('.xlsx'):
            df.to_excel(masked_file_path, index=False)

        return jsonify({"file_path": f"/{masked_file_path.replace(os.sep, '/')}"}), 200
    except Exception as e:
        return jsonify({"error": f"Error masking data. {str(e)}"}), 500

@app.route("/uploads/masked/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER_MASKED, filename)

if __name__ == "__main__":
    app.run(debug=True)





































