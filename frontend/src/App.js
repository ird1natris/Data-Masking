import React, { useState } from "react";
import Swal from "sweetalert2";
import "sweetalert2/dist/sweetalert2.min.css";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [columnsToMask, setColumnsToMask] = useState([]);
  const [isFileUploaded, setIsFileUploaded] = useState(false);

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
            title: "File Uploaded Successfully",
            text: `Detected columns: ${data.columns.join(", ")}`,
            confirmButtonColor: "#6a1b9a",
          });
        } else {
          Swal.fire({
            icon: "error",
            title: "Error",
            text: data.error || "Failed to detect columns.",
            confirmButtonColor: "#ff4081",
          });
        }
      } catch (error) {
        console.error(error);
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "Error uploading file. Please try again later.",
          confirmButtonColor: "#ff4081",
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

  const handleMasking = async () => {
    if (columnsToMask.length > 0) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("columns", JSON.stringify(columnsToMask));

      try {
        const response = await fetch("http://localhost:5000/mask_data", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        if (data.file_path) {
          Swal.fire({
            icon: "success",
            title: "Data Masked Successfully",
            text: "Your file is ready for download.",
            confirmButtonColor: "#6a1b9a",
          }).then(() => {
            window.location.href = `http://localhost:5000${data.file_path}`;
          });
        } else {
          Swal.fire({
            icon: "error",
            title: "Error",
            text: data.error || "Error masking data.",
            confirmButtonColor: "#ff4081",
          });
        }
      } catch (error) {
        console.error(error);
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "Error masking data. Please try again later.",
          confirmButtonColor: "#ff4081",
        });
      }
    } else {
      Swal.fire({
        icon: "warning",
        title: "No Columns Selected",
        text: "Please select at least one column to mask.",
        confirmButtonColor: "#ff4081",
      });
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
      {columnsToMask.length > 0 && (
        <button className="mask-button" onClick={handleMasking}>
          Mask Data
        </button>
      )}
      <div className="footer">
        <p>Created with ❤️ by 𝐒𝐭✰𝐫𝐠𝐢𝐫𝐥</p>
        <p>&copy; 2024 SecurMask. All rights reserved.</p>
      </div>
    </div>
  );
}

export default App;









































