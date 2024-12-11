from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import random
import string
import json
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
import logging

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.basicConfig(level=logging.ERROR, filename="error.log", format="%(asctime)s - %(message)s")

def mask_data(value):
    if isinstance(value, str):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(len(value)))
    return value

@app.route("/detect_columns", methods=["POST"])
def detect_columns():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(input_path)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(input_path)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(input_path)
        else:
            return jsonify({"error": "File format not supported"}), 400

        columns = df.columns.tolist()
        return jsonify({"columns": columns})
    except Exception as e:
        logging.error(f"Error in detect_columns: {str(e)}")
        return jsonify({"error": f"Failed to process the file. Error: {str(e)}"}), 500

@app.route("/mask_data", methods=["POST"])
def mask_data_route():
    file = request.files.get("file")
    columns_to_mask = request.form.get("columns")

    if not file or not columns_to_mask:
        return jsonify({"error": "No file uploaded or columns selected for masking."}), 400

    try:
        columns_to_mask = json.loads(columns_to_mask)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid column selection format."}), 400

    input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(input_path)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(input_path)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(input_path)

        for column in columns_to_mask:
            if column in df.columns:
                df[column] = df[column].apply(mask_data)

        masked_file_path = os.path.join(UPLOAD_FOLDER, f"masked_{file.filename}")
        if file.filename.endswith('.csv'):
            df.to_csv(masked_file_path, index=False)
        elif file.filename.endswith('.xlsx'):
            df.to_excel(masked_file_path, index=False)

        return jsonify({"message": "File processed successfully", "file_path": f"/uploads/{os.path.basename(masked_file_path)}"})

    except Exception as e:
        logging.error(f"Error in mask_data_route: {str(e)}")
        return jsonify({"error": f"Failed to process the file. Error: {str(e)}"}), 500

@app.route('/uploads/<filename>')
def download_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        logging.error(f"Error in download_file: {str(e)}")
        return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)




















