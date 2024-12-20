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
from collections import defaultdict

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

# Dictionary to store gender pseudonym mappings
gender_pseudonym_mapping = defaultdict(lambda: None)
gender_counter = 1  # Counter for pseudonymized values

# Dictionary to store religion pseudonym mappings
religion_pseudonym_mapping = defaultdict(lambda: None)
religion_counter = 1  # Counter for pseudonymized values

# Dictionary to store race pseudonym mappings
race_pseudonym_mapping = defaultdict(lambda: None)
race_counter = 1  # Counter for pseudonymized values

# Define column header keywords for IC number
IC_KEYWORDS = ['ic', 'identification', 'id', 'passport', 'ssn', 'personal id', 'national id', 'ic number', 'IC', 'mykad']

# Define column header keywords for email
EMAIL_KEYWORDS = ['email', 'email address', 'email_id', 'contact', 'e-mail', 'email address', 'contact email', 'emel']

# Define column header keywords for address
ADDRESS_KEYWORDS = ['address', 'home address', 'residence', 'location', 'street', 'city', 'place of residence', 'alamat', 'rumah']

# Define column header keywords for age
AGE_KEYWORDS = ['age', 'umur']

# Define column header keywords for name
NAME_KEYWORDS = ['name', 'full name', 'first name', 'last name', 'first', 'surname', 'nama', 'penuh', 'given name', 'fname', 'lname']

# Define column header keywords for phone numbers
PHONE_KEYWORDS = ['phone', 'mobile', 'contact', 'telephone', 'cell', 'telefon', 'tel']

# Define column header keywords for Place of Birth
PLACE_OF_BIRTH_KEYWORDS = ['place', 'origin', 'tempat', 'state']

# Define column header keywords for Birth Date
BIRTH_DATE_KEYWORDS = ['date', 'dob', 'b-day', 'd.o.b.', 'tarikh']

GENDER_KEYWORDS = ['gender', 'sex', 'jenis kelamin', 'j.k.', 'sex/gender', 'gen', 'jantina']

HEALTH_STATUS_KEYWORDS = ['health', 'status', 'health status', 'medical condition', 
                          'condition', 'health state', 'state of health', 'tahap kesihatan']

# Define column header keywords for Religion
RELIGION_KEYWORDS = ['religion', 'faith', 'religious', 'religion type', 'belief', 'agama', 'kepercayaan']

# Define column header keywords for Race
RACE_KEYWORDS = ['race', 'ethnicity', 'ethnic group', 'race/ethnicity', 'bangsa', 'kaum']

# Define column header keywords for Race
SALARY_KEYWORDS = ['salary', 'income', 'gaji', 'pendapatan', 'source']

CREDIT_CARD_KEYWORDS = ['credit card', 'cc', 'kredit', 'debit']

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

def mask_credit_card(value):
    """Mask credit card numbers by keeping the last four digits."""
    if len(value) > 4:
        return '*' * (len(value) - 4) + value[-4:]
    return value

def generate_fake_health_status():
    """Generate a fake health status."""
    statuses = ["Healthy", "Under Observation", "Critical", "Recovering", "Needs Attention"]
    return random.choice(statuses)

def generate_fake_salary():
    """Generate a fake salary within a range."""
    return random.randint(2000, 15000)  # Random salary between 2,000 and 15,000

def mask_salary_with_range(value):
    """Mask salary by generating a fake salary and then masking it within a reasonable range."""
    fake_salary = generate_fake_salary()  # Generate a fake salary
    min_salary = fake_salary - (fake_salary % 1000)  # Round down to the nearest 1000 (e.g., 5500 -> 5000)
    max_salary = min_salary + 999  # Mask within a range (e.g., 5000-5999)

    # Ensure salary is within valid range
    min_salary = max(2000, min_salary)  # Minimum salary should be at least 2000
    max_salary = min(15000, max_salary)  # Maximum salary should be at most 15,000

    return f"{min_salary}-{max_salary}"  # Return the salary range (e.g., "5000-6000")

def pseudonymize_religion(value):
    """Pseudonymize religion as Religion1, Religion2, etc."""
    global religion_counter

    # Normalize the religion value for consistency
    normalized_value = value.strip().lower() if isinstance(value, str) else str(value)

    # Check if the value already has a pseudonym
    if religion_pseudonym_mapping[normalized_value] is None:
        pseudonym = f"Religion{religion_counter}"
        religion_pseudonym_mapping[normalized_value] = pseudonym
        religion_counter += 1

    return religion_pseudonym_mapping[normalized_value]

def pseudonymize_race(value):
    """Pseudonymize race as Race1, Race2, etc."""
    global race_counter

    # Normalize the race value for consistency
    normalized_value = value.strip().lower() if isinstance(value, str) else str(value)

    # Check if the value already has a pseudonym
    if race_pseudonym_mapping[normalized_value] is None:
        pseudonym = f"Race{race_counter}"
        race_pseudonym_mapping[normalized_value] = pseudonym
        race_counter += 1

    return race_pseudonym_mapping[normalized_value]

def pseudonymize_gender(value):
    """Pseudonymize gender as Gender1, Gender2, etc."""
    global gender_counter

    # Normalize the gender value for consistency
    normalized_value = value.strip().lower() if isinstance(value, str) else str(value)

    # Check if the value already has a pseudonym
    if gender_pseudonym_mapping[normalized_value] is None:
        pseudonym = f"Gender{gender_counter}"
        gender_pseudonym_mapping[normalized_value] = pseudonym
        gender_counter += 1

    return gender_pseudonym_mapping[normalized_value]

def generate_fake_place_of_birth():
    """Generate a fake state for place of birth."""
    states = ["Kuala Lumpur", "Sarawak", "Johor Darul Ta'zim", "Penang", "Sabah", "Selangor", "Perak", "Negeri Sembilan", "Kedah", "Kelantan", "Pahang", "Terengganu", "Perlis", "Malacca"]
    return random.choice(states)

def mask_place_of_birth(value):
    """Partially mask the place of birth."""
    fake_state = generate_fake_place_of_birth()
    if len(fake_state) > 2:
        return fake_state[0] + '*' * (len(fake_state) - 2) + fake_state[-1]
    else:
        return '*' * len(fake_state)

def generate_fake_phone_number():
    """Generate a fake phone number with a randomized area code in the format (XXX-XXXXXXX)."""
    # List of possible area codes (you can expand this list)
    area_codes = ['010', '011', '012', '013', '014', '015', '016', '017', '018', '019']
    
    # Randomly choose an area code
    area_code = random.choice(area_codes)
    
    # Generate a random 7-digit number
    number = ''.join(random.choices(string.digits, k=7))  # e.g., 3456789
    
    # Combine area code and number into the desired format
    return f"({area_code})-{number}"

def mask_phone(phone):
    """Mask phone number except the last two digits."""
    # Ensure phone follows the pattern (012-3456789)
    match = re.match(r'\((\d{3})\)-(\d{7})', phone)
    if match:
        area_code = match.group(1)  # Extract random area code
        number = match.group(2)     # Extract random 7-digit number
        
        # Mask all digits except for the last two
        masked_number = '*' * (len(number) - 2) + number[-2:]  # Mask all but the last two digits
        
        # Combine area code and masked number into the desired format
        return f"({area_code})-{masked_number}"
    
    # Return phone unchanged if it doesn't match the pattern
    return phone

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
    """Generate a fake name and mask it partially."""
    if column_name:
        if 'name' in column_name.lower() or 'nama' in column_name.lower():
            fake_name = fake.name()
            # Mask the name by keeping the first and last letters and replacing others with asterisks
            name_parts = fake_name.split()
            masked_name = " ".join([part[0] + '*' * (len(part) - 2) + part[-1] if len(part) > 2 else '*' * len(part) for part in name_parts])
            return masked_name
        elif 'address' in column_name.lower() or 'alamat' in column_name.lower():
            return fake.address()
        # Further anonymization logic for other types can follow
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

def mask_data(value, column_name=None):
    """ Mask data based on the type of value and column name. """
    if column_name:
        column_name = preprocess_column_name(column_name)
        print(f"Processing column: {column_name} with value: {value}")  # Debugging line
        
        # Fuzzy matching to detect race-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in RACE_KEYWORDS):
            return pseudonymize_race(value)
        
        # Fuzzy matching to detect salary-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in SALARY_KEYWORDS):
            return mask_salary_with_range(value)  # Apply the salary masking

        # Fuzzy matching to detect religion-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in RELIGION_KEYWORDS):
            return pseudonymize_religion(value)

        # Fuzzy matching for Health Status-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in HEALTH_STATUS_KEYWORDS):
            return generate_fake_health_status()

        # Fuzzy matching for gender-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in GENDER_KEYWORDS):
            return pseudonymize_gender(value)

        # Fuzzy matching to detect Birth Date-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in BIRTH_DATE_KEYWORDS):
            return mask_date(value)

        # Fuzzy matching to detect Place of Birth-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in PLACE_OF_BIRTH_KEYWORDS):
            return mask_place_of_birth(value)

 	    # Fuzzy matching to detect phone number-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in PHONE_KEYWORDS):
            fake_phone = generate_fake_phone_number()  # Generate a fake phone number
            return mask_phone(fake_phone)  # Mask the generated phone number
        
        # Fuzzy matching to detect name-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in NAME_KEYWORDS):
            return anonymize_name_or_address(value, column_name)  # Mask the generated name
        
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
        
        # Fuzzy matching to detect credit card-related columns
        if any(fuzz.partial_ratio(column_name, keyword) > 80 for keyword in CREDIT_CARD_KEYWORDS):
            return mask_credit_card(value)

    # Fallback for unmatched columns
    if isinstance(value, str):
        return 'XXXXXX'
    elif isinstance(value, (int, float)):
        return '*****'
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
















































































































