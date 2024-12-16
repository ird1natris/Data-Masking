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
from fuzzywuzzy import fuzz

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

# Define column header keywords for IC number
IC_KEYWORDS = ['ic', 'identification', 'id', 'passport', 'ssn', 'personal id', 'national id', 'ic number', 'IC', 'mykad']

# Define column header keywords for email
EMAIL_KEYWORDS = ['email', 'email address', 'email_id', 'contact', 'e-mail', 'email address', 'contact email', 'emel']

# Define column header keywords for address
ADDRESS_KEYWORDS = ['address', 'home address', 'residence', 'location', 'street', 'city', 'place of residence', 'alamat', 'rumah']

# Define column header keywords for age
AGE_KEYWORDS = ['age', 'umur']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    return secure_filename(filename)

def preprocess_column_name(column_name):
    return column_name.strip().lower()

def generate_fake_email():
    """Generate a fake email address."""
    return fake.email()

def mask_email(email):
    """Mask the email address."""
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
    """Generate and mask a fake IC number."""
    fake_ic = generate_fake_ic_number()
    masked_ic = fake_ic[0] + '*' * (len(fake_ic) - 2) + fake_ic[-1]
    return masked_ic

def generate_fake_ic_number():
    """Generate a fake IC number in the format YYMMDD-XX-XXXX."""
    random_date = fake.date_of_birth(minimum_age=18, maximum_age=100)
    date_part = random_date.strftime("%y%m%d")
    state_code = f"{random.randint(1, 14):02d}"
    unique_identifier = f"{random.randint(0, 9999):04d}"
    return f"{date_part}-{state_code}-{unique_identifier}"

def randomize_salary(value):
    """ Randomize salary data. """
    if isinstance(value, (int, float)):
        return random.randint(2000, 10000)  # Random salary between RM2000 and RM10000
    return value

def anonymize_name_or_address(value, column_name=None):
    """ Anonymize name and address-related data by using Faker to generate random fake data. """
    if column_name:
        if 'name' in column_name.lower() or 'nama' in column_name.lower():
            return fake.name()
        elif 'address' in column_name.lower() or 'alamat' in column_name.lower():
            return fake.address()
        elif 'place of birth' in column_name.lower() or 'birth place' in column_name.lower():
            return fake.city()  # Mask place of birth with random city
        elif 'department' in column_name.lower():
            return fake.word()  # Mask department with a random word
    return value

def mask_address(address):
    """Partially mask the home address."""
    if address:
        address_parts = address.split("\n")
        masked_address = []
        for part in address_parts:
            if re.search(r'\d+', part):  # Likely a street number
                masked_part = re.sub(r'\d+', '*', part)  # Mask street numbers
            else:
                masked_part = re.sub(r'\w+', '*', part)  # Mask each word with asterisks
            masked_address.append(masked_part)
        return "\n".join(masked_address)
    return address

def mask_date(value):
    """Mask date data by replacing it with a random date."""
    if isinstance(value, str):
        try:
            value = datetime.datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            try:
                value = datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return value
    if isinstance(value, datetime.datetime):
        return fake.date_of_birth(minimum_age=18, maximum_age=100).strftime("%d/%m/%Y")
    return value

def mask_expiration_date(value):
    """Mask expiration date."""
    if isinstance(value, str):
        try:
            value = datetime.datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return value
    if isinstance(value, datetime.datetime):
        return fake.date_this_century(before_today=False, after_today=True).strftime("%d/%m/%Y")
    return value

def anonymize_age(value):
    """ Anonymize age by generating a random age between 18 and 100. """
    if isinstance(value, int):
        return random.randint(18, 100)  # Randomize age between 18 and 100
    return value

def generate_fake_age():
    """Generate a fake age between 18 and 100."""
    return random.randint(18, 100)

def mask_age_with_range(value):
    """ Mask age by generating a fake age and then masking it within a reasonable range. """
    fake_age = generate_fake_age()  # Generate a fake age
    min_age = fake_age - (fake_age % 10)  # Round down to the nearest decade (e.g., 37 -> 30)
    max_age = min_age + 9  # Mask within a range (e.g., 30-39)

    # Ensure the age is in a valid range
    min_age = max(18, min_age)  # Minimum age should be at least 18
    max_age = min(100, max_age)  # Maximum age should be at most 100

    return f"{min_age}-{max_age}"  # Return the age range (e.g., "30-40")

def generate_fake_email():
    """Generate a fake email address."""
    return fake.email()

def mask_data(value, column_name=None):
    """ Mask data based on the type of value and column name. """
    if column_name:
        column_name = preprocess_column_name(column_name)
        print(f"Processing column: {column_name} with value: {value}")  # Debugging line
        
        # Fuzzy matching to detect IC-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in IC_KEYWORDS):
            return mask_numeric(value)  # Apply the fake IC masking
        
        # Fuzzy matching to detect email-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in EMAIL_KEYWORDS):
            fake_email = generate_fake_email()
            return mask_email(fake_email)  # Mask the generated email

        # Fuzzy matching to detect address-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in ADDRESS_KEYWORDS):
            fake_address = fake.address()
            return mask_address(fake_address)  # Mask the generated address

        # Fuzzy matching to detect age-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in AGE_KEYWORDS):
            return mask_age_with_range(value)  # Apply the age masking

        # Fallback to handling other columns
        if 'name' in column_name or 'nama' in column_name:
            return anonymize_name_or_address(value, column_name)
        elif 'address' in column_name or 'alamat' in column_name:
            return anonymize_name_or_address(value, column_name)
        elif 'phone' in column_name:
            return mask_phone(value)
        elif 'salary' in column_name:
            return randomize_salary(value)
        elif 'place_of_birth' in column_name:
            return anonymize_name_or_address(value, column_name)

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








































































































