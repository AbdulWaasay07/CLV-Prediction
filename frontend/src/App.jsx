import { useState } from 'react';
import Dashboard from './Dashboard';
import MLDashboard from './MLDashboard';
import './App.css';

const schemas = {
  customers: ["customer_id", "name", "email", "phone", "location", "sign_up_date"],
  transactions: ["transaction_id", "customer_id", "product_id", "transaction_date", "amount", "quantity", "payment_method", "status"],
  products: ["product_id", "product_name", "price"],
  customer_behavior: ["behavior_id", "customer_id", "log_date", "website_visits", "app_sessions", "page_views", "avg_session_duration"],
  support: ["ticket_id", "customer_id", "issue_date", "resolution_date", "category", "severity", "status", "csat_score"],
  marketing: ["customer_id", "campaign_id", "channel", "send_date", "opened", "clicked", "converted"]
};

function App() {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload', 'dashboard', or 'ml'
  
  const [datasetType, setDatasetType] = useState('customers');
  const [file, setFile] = useState(null);
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [mapping, setMapping] = useState({});
  const [uploadStatus, setUploadStatus] = useState(null);

  // Handle File Selection & Parse Headers
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setUploadStatus(null);
    setMapping({});

    if (selectedFile) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        const firstLine = text.split('\n')[0];
        const headers = firstLine.split(',').map(h => h.trim().replace(/['"]/g, '').toLowerCase());
        setCsvHeaders(headers);
        
        // Auto-map exact matches for better UX
        const initialMapping = {};
        const requiredCols = schemas[datasetType];
        headers.forEach(header => {
          if (requiredCols.includes(header)) {
            initialMapping[header] = header;
          }
        });
        setMapping(initialMapping);
      };
      reader.readAsText(selectedFile.slice(0, 5000)); // Read just the beginning of the file
    } else {
      setCsvHeaders([]);
    }
  };

  const handleDatasetTypeChange = (e) => {
    setDatasetType(e.target.value);
    setMapping({}); // Reset mapping on type change
  };

  const handleMappingChange = (requiredCol, csvCol) => {
    setMapping(prev => {
      const newMapping = { ...prev };
      
      // If they selected "-- Ignore --", we need to remove any existing mapping for this required col
      if (!csvCol) {
        Object.keys(newMapping).forEach(key => {
          if (newMapping[key] === requiredCol) delete newMapping[key];
        });
        return newMapping;
      }
      
      // Otherwise, map the chosen csvCol to the requiredCol
      newMapping[csvCol] = requiredCol;
      return newMapping;
    });
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploadStatus("Uploading...");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("column_mapping", JSON.stringify(mapping));

    try {
      const response = await fetch(`http://localhost:8000/api/upload/${datasetType}`, {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        if (data.rows_inserted === 0 && data.errors && data.errors.length > 0) {
          setUploadStatus(`Failed. 0 rows inserted. Database Error: ${data.errors[0].issue}`);
        } else {
          setUploadStatus(`Success! Inserted ${data.rows_inserted} rows. Health Score: ${data.dataset_health_score}`);
        }
      } else {
        setUploadStatus(`Error: ${JSON.stringify(data.detail)}`);
      }
    } catch (error) {
      setUploadStatus(`Error connecting to server: ${error.message}`);
    }
  };

  const requiredColumns = schemas[datasetType];

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h2>ChurnX</h2>
        </div>
        <nav className="sidebar-nav">
          <button 
            className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Data Importer
          </button>
          <button 
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            EDA Dashboard
          </button>
          <button 
            className={`nav-btn ${activeTab === 'ml' ? 'active' : ''}`}
            onClick={() => setActiveTab('ml')}
          >
            AI & Recommendations
          </button>
        </nav>
      </aside>

      <main className="main-content">
        {activeTab === 'dashboard' ? (
          <Dashboard />
        ) : activeTab === 'ml' ? (
          <MLDashboard />
        ) : (
          <div className="container">
            <header className="header">
              <h1>Universal Data Importer</h1>
              <p>Map your CSV files directly into the platform</p>
            </header>

            <div className="upload-card">
        <div className="form-group">
          <label>1. Select Dataset Type</label>
          <select value={datasetType} onChange={handleDatasetTypeChange}>
            {Object.keys(schemas).map(type => (
              <option key={type} value={type}>{type.toUpperCase()}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>2. Upload CSV File</label>
          <input type="file" accept=".csv" onChange={handleFileChange} />
        </div>

        {csvHeaders.length > 0 && (
          <div className="mapping-section">
            <h3>3. Map Your Columns</h3>
            <p className="subtitle">Match our required database columns to your CSV headers.</p>
            
            <div className="mapper-grid">
              <div className="mapper-header">Required DB Column</div>
              <div className="mapper-header">Your CSV Column</div>
              
              {requiredColumns.map(reqCol => {
                // Find what CSV header is currently mapped to this required column
                const mappedCsvHeader = Object.keys(mapping).find(key => mapping[key] === reqCol) || "";
                
                return (
                  <div key={reqCol} className="mapper-row">
                    <div className="req-col-name">{reqCol} <span className="asterisk">*</span></div>
                    <select 
                      value={mappedCsvHeader}
                      onChange={(e) => handleMappingChange(reqCol, e.target.value)}
                    >
                      <option value="">-- Ignore / Use Default --</option>
                      {csvHeaders.map(header => (
                        <option key={header} value={header}>{header}</option>
                      ))}
                    </select>
                  </div>
                );
              })}
            </div>

            <button 
              className="upload-button" 
              onClick={handleUpload}
              disabled={uploadStatus === "Uploading..."}
            >
              {uploadStatus === "Uploading..." ? "Processing..." : "Run Upload & Process Pipeline"}
            </button>
            
            {uploadStatus && (
              <div className={`status-message ${uploadStatus.includes("Error") ? "error" : "success"}`}>
                {uploadStatus}
              </div>
            )}
          </div>
        )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
