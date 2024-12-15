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
    'name': ['name', 'maiden_name', 'lname', 'fname', 'nama'],
    'address': ['address', 'city', 'state', 'alamat', 'rumah'],
    'email': ['email', 'emel'],
    'phone': ['phone', 'contact', 'nombor', 'telefon', 'no'],
    'ic': ['ic', 'id', 'passport', 'number', 'no'],
    'salary': ['salary', 'gaji'],
    'age': ['age', 'umur'],
    'cgpa': ['cgpa'],
    'date': ['birthdate', 'dob', 'date', 'expire', 'cc_expiredate', 'credit card expiration'],
    'place_of_birth': ['place of birth', 'birth place', 'city of birth'],
    'department': ['department', 'class'],
    'city': ['city', 'town', 'locality'],
    'state': ['state', 'region', 'province']
}

def preprocess_column_name(column_name):
    return column_name.strip().lower()

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
        if 'name' in column_name.lower() or 'nama' in column_name.lower() or 'maiden_name' in column_name.lower() or 'lname' in column_name.lower() or 'fname' in column_name.lower():
            return fake.name()
        elif 'address' in column_name.lower() or 'alamat' in column_name.lower() or 'rumah' in column_name.lower():
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

def mask_expiration_date(value):
    """
    Mask the expiration date in format "%d/%m/%Y" by generating a random expiration date.
    """
    if isinstance(value, str):
        try:
            value = datetime.datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return value  # If it's not in the correct format, return as is

    if isinstance(value, datetime.datetime):
        # Randomize credit card expiration dates and return in "%d/%m/%Y" format
        return fake.date_this_century(before_today=False, after_today=True).strftime("%d/%m/%Y")

    return value

def anonymize_age(value):
    """ Anonymize age by generating a random age between 18 and 100. """
    if isinstance(value, int):
        return random.randint(18, 100)  # Randomize age between 18 and 100
    return value

def mask_data(value, column_name=None):
    """ Mask data based on the type of value and column name. """
    if column_name:
        column_name = preprocess_column_name(column_name)
        print(f"Processing column: {column_name} with value: {value}")  # Debugging line
        # Explicit handling for columns that need special treatment
        if column_name == 'cc_expiredate':
            return mask_expiration_date(value)
        if column_name == 'city':
            return fake.city()  # Generate random city
        if column_name == 'state':
            return fake.state()  # Generate random state
        if column_name == 'birthdate':
            return mask_date(value)  # Handle birthdate with random dates
        
        # Process other columns based on keywords
        for key, keywords in MASK_KEYWORDS.items():
            if any(keyword in column_name for keyword in keywords):
                if key == 'name':
                    return anonymize_name_or_address(value, column_name)
                elif key == 'address':
                    return anonymize_name_or_address(value, column_name)
                elif key == 'email':
                    return mask_email(value)
                elif key == 'phone':
                    return mask_phone(value)
                elif key == 'ic':
                    return mask_numeric(value)
                elif key == 'salary':
                    return randomize_salary(value)
                elif key == 'age':
                    return anonymize_age(value)
                elif key == 'place_of_birth':
                    return anonymize_name_or_address(value, column_name)
                elif key == 'department':
                    return fake.word()  # Mask department/class with random word

    # Fallback for unmatched columns
    if isinstance(value, str):
        return fake.text(max_nb_chars=20)
    elif isinstance(value, (int, float)):
        return fake.random_int(min=1000, max=9999)
    elif isinstance(value, datetime.datetime):
        return mask_date(value)
    return fake.text(max_nb_chars=20)

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
















































































