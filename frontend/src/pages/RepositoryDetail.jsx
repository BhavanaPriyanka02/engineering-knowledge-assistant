import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

function RepositoryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [repository, setRepository] = useState(null);
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadRepository = async () => {
      try {
        const repositoryResponse = await api.get(`/repositories/${id}`);
        const filesResponse = await api.get(`/repositories/${id}/files`);
        setRepository(repositoryResponse.data);
        setFiles(filesResponse.data);
      } catch (loadError) {
        setError(loadError.response?.data?.detail || "Unable to load repository.");
      } finally {
        setLoading(false);
      }
    };

    loadRepository();
  }, [id]);

  const handleFileClick = async (fileId) => {
    try {
      const response = await api.get(`/repositories/${id}/files/${fileId}`);
      setSelectedFile(response.data);
    } catch (fileError) {
      setError(fileError.response?.data?.detail || "Unable to load the repository file.");
    }
  };

  if (loading) {
    return <p style={{ padding: 24 }}>Loading repository...</p>;
  }

  if (error) {
    return (
      <main style={{ maxWidth: 900, margin: "auto", padding: 24 }}>
        <p>{error}</p>
        <button onClick={() => navigate("/dashboard")}>Back to dashboard</button>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 1000, margin: "auto", padding: 24 }}>
      <header style={{ marginBottom: 20 }}>
        <button onClick={() => navigate("/dashboard")} style={{ marginBottom: 12 }}>
          Back to dashboard
        </button>
        <h1>{repository?.repo_name || "Repository"}</h1>
        <p>{repository?.repo_url}</p>
      </header>

      <section style={{ display: "grid", gap: 20, gridTemplateColumns: "minmax(240px, 320px) minmax(0, 1fr)" }}>
        <div>
          <h2>Files</h2>
          {files.length === 0 ? (
            <p>No files found.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {files.map((file) => (
                <li key={file.id} style={{ marginBottom: 8 }}>
                  <button onClick={() => handleFileClick(file.id)} style={{ textAlign: "left", width: "100%" }}>
                    {file.file_path}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h2>Content</h2>
          {selectedFile ? (
            <>
              <h3>{selectedFile.file_path}</h3>
              <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: 16, borderRadius: 8, overflow: "auto" }}>
                {selectedFile.content}
              </pre>
            </>
          ) : (
            <p>Select a file to view its content.</p>
          )}
        </div>
      </section>
    </main>
  );
}

export default RepositoryDetail;
