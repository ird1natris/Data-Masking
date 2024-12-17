import React, { useState } from "react";
import "./App.css";
import Swal from "sweetalert2";
import { ClipLoader } from "react-spinners"; // Import the spinner

function App() {
  const [file, setFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [columnsToMask, setColumnsToMask] = useState([]);
  const [isFileUploaded, setIsFileUploaded] = useState(false);
  const [isMaskingInProgress, setIsMaskingInProgress] = useState(false); // To track masking progress
  const [loadingMessage, setLoadingMessage] = useState(""); // Optional: Add message during loading
  const [selectAll, setSelectAll] = useState(false); // To track the Select All checkbox state

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      try {
        const response = await fetch("http://localhost:5000/detect_columns", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        if (data.columns) {
          setFile(uploadedFile);
          setColumns(data.columns);
          setIsFileUploaded(true);
          Swal.fire({
            icon: "success",
            title: "File uploaded!",
            text: "Columns detected successfully.",
          });
        } else {
          Swal.fire({
            icon: "error",
            title: "Error",
            text: data.error || "Failed to detect columns.",
          });
        }
      } catch (error) {
        console.error(error);
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "Error uploading file.",
        });
      }
    }
  };

  const handleColumnSelection = (column) => {
    if (columnsToMask.includes(column)) {
      setColumnsToMask(columnsToMask.filter((item) => item !== column));
    } else {
      setColumnsToMask([...columnsToMask, column]);
    }
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setColumnsToMask([]); // Deselect all
    } else {
      setColumnsToMask(columns); // Select all
    }
    setSelectAll(!selectAll); // Toggle Select All checkbox state
  };

  const handleMasking = async () => {
    if (columnsToMask.length === 0) {
      Swal.fire({
        icon: "warning",
        title: "No columns selected",
        text: "Please select at least one column to mask.",
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("columns", JSON.stringify(columnsToMask));

    setIsMaskingInProgress(true); // Show progress indicator
    setLoadingMessage("Masking data... Please wait!"); // Optional message

    try {
      const response = await fetch("http://localhost:5000/mask_data", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (response.ok && data.file_path) {
        Swal.fire({
          icon: "success",
          title: "Data Masked!",
          text: "Your masked file is ready for download.",
          confirmButtonText: "Download",
        }).then(() => {
          window.location.href = `http://localhost:5000${data.file_path}`;
        });
      } else {
        Swal.fire({
          icon: "error",
          title: "Error",
          text: data.error || "Error masking data.",
        });
      }
    } catch (error) {
      console.error(error);
      Swal.fire({
        icon: "error",
        title: "Error",
        text: "Error masking data.",
      });
    } finally {
      setIsMaskingInProgress(false); // Hide progress indicator
      setLoadingMessage(""); // Clear loading message
    }
  };

  return (
    <div className="container">
      <h1>SecurMask</h1>
      <p>Upload your file and securely mask sensitive data.</p>
      <div className="upload-section">
        <input type="file" accept=".csv, .xlsx" onChange={handleFileUpload} />
      </div>
      {isFileUploaded && (
        <div className="checkbox-list">
          <h3>Select columns to mask:</h3>
          {/* "Select All" checkbox */}
          <div className="checkbox-item">
            <input
              type="checkbox"
              id="select-all"
              checked={selectAll}
              onChange={handleSelectAll}
            />
            <label htmlFor="select-all">Select All</label>
          </div>

          {columns.map((column, index) => (
            <div key={index} className="checkbox-item">
              <input
                type="checkbox"
                id={column}
                checked={columnsToMask.includes(column)}
                onChange={() => handleColumnSelection(column)}
              />
              <label htmlFor={column}>{column}</label>
            </div>
          ))}
        </div>
      )}
      {isFileUploaded && (
        <button
          className="mask-button"
          onClick={handleMasking}
          disabled={isMaskingInProgress} // Disable the button while masking
        >
          {isMaskingInProgress ? (
            <div className="spinner-container">
              <ClipLoader color="#ffffff" size={30} />
              <span>{loadingMessage}</span>
            </div>
          ) : (
            "Mask Data"
          )}
        </button>
      )}
      <div className="footer">
        <p>&copy; 2024 SecurMask. All rights reserved.</p>
      </div>
    </div>
  );
}

export default App;

























































