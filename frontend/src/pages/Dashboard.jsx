import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState("");
  const [documentMessage, setDocumentMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/auth/me")
      .then((response) => {
        setUser(response.data);
        return api.get("/documents");
      })
      .then((response) => {
        setDocuments(response.data);
      })
      .catch(() => {
        setError("Unable to load dashboard. Please login again.");
        localStorage.removeItem("token");
        navigate("/", { replace: true });
      });
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setDocumentMessage("Choose a PDF before uploading.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    setIsUploading(true);
    setDocumentMessage("");

    try {
      await api.post("/documents/upload", formData);
      const response = await api.get("/documents");
      setDocuments(response.data);
      setSelectedFile(null);
      document.querySelector("#pdf-picker").value = "";
      setDocumentMessage("PDF uploaded successfully.");
    } catch (uploadError) {
      setDocumentMessage(
        uploadError.response?.data?.detail || "The PDF could not be uploaded."
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (documentId) => {
    setDocumentMessage("");
    try {
      await api.delete(`/documents/${documentId}`);
      setDocuments((currentDocuments) =>
        currentDocuments.filter((document) => document.id !== documentId)
      );
    } catch (deleteError) {
      setDocumentMessage(
        deleteError.response?.data?.detail || "The PDF could not be deleted."
      );
    }
  };

  if (error) {
    return (
      <div style={{ maxWidth: 400, margin: "auto", padding: 24 }}>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Personal knowledge base</p>
          <h1>Dashboard</h1>
        </div>
        <button className="secondary-button" onClick={handleLogout}>Logout</button>
      </header>
      {user ? (
        <>
          <p className="welcome">Welcome, {user.name}. Add a PDF to your library.</p>
          <section className="upload-panel">
            <label htmlFor="pdf-picker">PDF document</label>
            <div className="upload-controls">
              <input
                id="pdf-picker"
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => setSelectedFile(event.target.files[0] || null)}
              />
              <button onClick={handleUpload} disabled={isUploading}>
                {isUploading ? "Uploading..." : "Upload PDF"}
              </button>
            </div>
            {documentMessage && <p className="document-message">{documentMessage}</p>}
          </section>
          <section className="documents-section">
            <div className="section-heading">
              <h2>Your documents</h2>
              <span>{documents.length}</span>
            </div>
            {documents.length === 0 ? (
              <p className="empty-state">No PDFs uploaded yet.</p>
            ) : (
              <ul className="document-list">
                {documents.map((document) => (
                  <li className="document-item" key={document.id}>
                    <div>
                      <strong>{document.filename}</strong>
                      <small>{new Date(document.created_at).toLocaleString()}</small>
                    </div>
                    <button
                      className="delete-button"
                      onClick={() => handleDelete(document.id)}
                    >
                      Delete
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : (
        <p className="loading-state">Loading...</p>
      )}
    </main>
  );
}

export default Dashboard;
