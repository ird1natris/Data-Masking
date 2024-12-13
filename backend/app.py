import re
import os
import random
import string
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from werkzeug.utils import secure_filename
from faker import Faker
import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER_ORIGINAL = 'uploads/original'
UPLOAD_FOLDER_MASKED = 'uploads/masked'
app.config['UPLOAD_FOLDER_ORIGINAL'] = UPLOAD_FOLDER_ORIGINAL
app.config['UPLOAD_FOLDER_MASKED'] = UPLOAD_FOLDER_MASKED

os.makedirs(UPLOAD_FOLDER_ORIGINAL, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_MASKED, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# Initialize Faker
fake = Faker()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    return secure_filename(filename)

# Keywords to detect relevant columns for masking
MASK_KEYWORDS = {
    'name': ['name'],
    'address': ['address'],
    'email': ['email'],
    'phone': ['phone'],
    'ic': ['ic', 'id', 'passport'],
    'salary': ['salary'],
    'age': ['age'],
    'cgpa': ['cgpa'],
    'date': ['birthdate', 'dob'],
    'place_of_birth': ['place of birth', 'birth place', 'city of birth'],
    'department': ['department', 'class']
}

def mask_email(email):
    local, domain = email.split("@")
    local_masked = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else '*' * len(local)
    return f"{local_masked}@{domain}"

def mask_phone(phone):
    return re.sub(r'\d', '*', phone[:-2]) + phone[-2:]

def mask_text(value):
    """ Mask general text data (e.g., names, addresses) partially. """
    if len(value) > 2:
        return value[0] + '*' * (len(value) - 2) + value[-1]
    else:
        return '*' * len(value)

def mask_numeric(value):
    """ Mask numeric data (e.g., phone numbers, IC numbers) by keeping only the first and last digits visible. """
    num_str = ''.join(re.findall(r'\d', str(value)))  # Remove non-numeric characters
    if len(num_str) > 2:
        return num_str[0] + '*' * (len(num_str) - 2) + num_str[-1]
    else:
        return '*' * len(num_str)

def randomize_salary(value):
    """ Randomize salary data. """
    if isinstance(value, (int, float)):
        return random.randint(2000, 10000)  # Random salary between RM2000 and RM10000
    return value

def anonymize_name_or_address(value, column_name=None):
    """ Anonymize name and address-related data by using Faker to generate random fake data. """
    if column_name:
        if 'name' in column_name.lower():
            return fake.name()
        elif 'address' in column_name.lower():
            return fake.address()
        elif 'place of birth' in column_name.lower() or 'birth place' in column_name.lower():
            return fake.city()  # Mask place of birth with random city
        elif 'department' in column_name.lower() or 'class' in column_name.lower():
            return fake.word()  # Mask department/class with a random word
    return value

def mask_date(value):
    """
    Mask date data by replacing it with a random date within a reasonable range.
    If the value is not a valid date, it will return the original value.
    """
    if isinstance(value, str):
        # Try parsing the string as a date first
        try:
            value = datetime.datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            try:
                value = datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return value  # Return original value if it's not a valid date format

    if isinstance(value, datetime.datetime):
        # Return a random date within a reasonable range (for Birth Date column)
        return fake.date_of_birth(minimum_age=18, maximum_age=100).strftime("%d/%m/%Y")
    
    return value


def anonymize_age(value):
    """ Anonymize age by generating a random age between 18 and 100. """
    if isinstance(value, int):
        return random.randint(18, 100)  # Randomize age between 18 and 100
    return value

def mask_data(value, column_name=None):
    """ Mask data based on the type of value and column name. """
    if isinstance(value, str):
        value = value.strip()

        # Anonymize name or address if matching relevant columns
        if column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['name']):
            return anonymize_name_or_address(value, column_name)
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['address']):
            return anonymize_name_or_address(value, column_name)
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['place_of_birth']):
            return anonymize_name_or_address(value, column_name)  # Mask place of birth as a name/address
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['department']):
            return anonymize_name_or_address(value, column_name)  # Anonymize department/class with random name
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['email']):
            return mask_email(value)  # Mask email
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['phone']):
            return mask_phone(value)  # Mask phone number
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['ic']):
            return mask_numeric(value)  # Mask IC number
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['salary']):
            return randomize_salary(value)  # Randomize salary
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['date']):
            return mask_date(value)  # Mask birth date
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['age']):
            return anonymize_age(value)  # Anonymize age
        else:
            return mask_text(value)  # Generic text masking

    elif isinstance(value, (int, float)):
        # Handle numeric data for salary, CGPA, etc.
        if column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['salary']):
            return randomize_salary(value)  # Randomize salary
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['cgpa']):
            return value  # Leave CGPA unchanged
        elif column_name and any(keyword in column_name.lower() for keyword in MASK_KEYWORDS['age']):
            return anonymize_age(value)  # Anonymize age
        else:
            return mask_numeric(value)  # Mask numeric data

    elif isinstance(value, datetime.datetime):
            return mask_date(value)  # Mask date data

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







































































