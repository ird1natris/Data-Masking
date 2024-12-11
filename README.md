# SecurMask-Beta

**SecurMask-Beta** is a beta version of a secure web application designed for masking and unmasking sensitive data in CSV and XLSX files. This tool is built to help organizations and individuals protect sensitive information while maintaining data usability.

## Features

- **Data Masking**: Encrypt sensitive data in specified columns of CSV or XLSX files.
- **Data Unmasking**: Decrypt previously masked data to its original state.
- **User-Friendly Interface**: Simple and intuitive web-based interface.
- **Secure Encryption**: Utilizes the `cryptography` library for robust data encryption.

## Tech Stack

- **Frontend**: React.js
- **Backend**: Python (Flask)
- **Libraries**:
  - Frontend: Material-UI for UI components, Axios for API requests
  - Backend: Flask for server-side operations, Cryptography for encryption, Pandas for file processing

## Installation and Setup

### Prerequisites

- Python 3.8 or later
- Node.js 14.x or later
- npm or yarn

### Backend Setup

1. Clone the repository and navigate to the `backend` folder:
   ```bash
   git clone https://github.com/ird1natris/SecurMask-Beta.git
   cd SecurMask-Beta/backend
   ```

2. Create and activate a virtual environment (optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate   # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the Flask server:
   ```bash
   python app.py
   ```

The backend server will run at `http://127.0.0.1:5000`.

### Frontend Setup

1. Navigate to the `frontend` folder:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```

The frontend app will run at `http://localhost:3000`.

## Usage

1. Open the frontend in your browser at `http://localhost:3000`.
2. Upload a CSV or XLSX file.
3. Specify the columns to mask or unmask.
4. Choose the action (mask or unmask) and submit the file.
5. Download the processed file with the changes applied.


