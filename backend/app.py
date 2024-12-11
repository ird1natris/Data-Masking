from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import random
import string

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def mask_data(value):
    # Masking logic (e.g., replacing characters with asterisks or random values)
    if isinstance(value, str):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(len(value)))
    return value

@app.route("/detect_columns", methods=["POST"])
def detect_columns():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
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
        return jsonify({"error": f"Failed to process the file. Error: {str(e)}"}), 500

@app.route("/mask_data", methods=["POST"])
def mask_data_route():
    file = request.files.get("file")
    columns_to_mask = request.form.get("columns")

    if not file or not columns_to_mask:
        return jsonify({"error": "No file uploaded or columns selected for masking."}), 400

    columns_to_mask = eval(columns_to_mask)  # Convert string back to list

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(input_path)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(input_path)

        # Mask selected columns
        for column in columns_to_mask:
            if column in df.columns:
                df[column] = df[column].apply(mask_data)

        # Save the masked file
        masked_file_path = os.path.join(UPLOAD_FOLDER, f"masked_{file.filename}")
        if file.filename.endswith('.csv'):
            df.to_csv(masked_file_path, index=False)
        elif file.filename.endswith('.xlsx'):
            df.to_excel(masked_file_path, index=False)

        # Return the correct file path for download
        return jsonify({"message": "File processed successfully", "file_path": f"/{masked_file_path.split('/')[-1]}"})

    except Exception as e:
        return jsonify({"error": f"Failed to process the file. Error: {str(e)}"}), 500

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)



















