import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [repositories, setRepositories] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [repositoryType, setRepositoryType] = useState("project");
  const [error, setError] = useState("");
  const [documentMessage, setDocumentMessage] = useState("");
  const [repositoryMessage, setRepositoryMessage] = useState("");
  const [searchQuestion, setSearchQuestion] = useState("");
  const [topK, setTopK] = useState("5");
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAddingRepository, setIsAddingRepository] = useState(false);
  const [processingDocumentId, setProcessingDocumentId] = useState(null);
  const [processingRepositoryId, setProcessingRepositoryId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState({});
  const navigate = useNavigate();

  const loadDashboardData = async () => {
    try {
      const [userResponse, documentsResponse, repositoriesResponse] = await Promise.all([
        api.get("/auth/me"),
        api.get("/documents"),
        api.get("/repositories"),
      ]);

      setUser(userResponse.data);
      setDocuments(documentsResponse.data);
      setRepositories(repositoriesResponse.data);
    } catch (loadError) {
      setError("Unable to load dashboard. Please login again.");
      localStorage.removeItem("token");
      navigate("/", { replace: true });
    }
  };

  useEffect(() => {
    loadDashboardData();
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

  const handleAddRepository = async (event) => {
    event.preventDefault();
    setRepositoryMessage("");

    if (!repoUrl.trim()) {
      setRepositoryMessage("Enter a GitHub repository URL.");
      return;
    }

    setIsAddingRepository(true);

    try {
      await api.post("/repositories", {
        repo_url: repoUrl.trim(),
        repository_type: repositoryType,
      });
      setRepoUrl("");
      setRepositoryType("project");
      setRepositoryMessage("Repository added successfully.");
      const response = await api.get("/repositories");
      setRepositories(response.data);
    } catch (repositoryError) {
      setRepositoryMessage(
        repositoryError.response?.data?.detail || "The repository could not be added."
      );
    } finally {
      setIsAddingRepository(false);
    }
  };

  const handleDeleteRepository = async (repositoryId) => {
    setRepositoryMessage("");

    try {
      await api.delete(`/repositories/${repositoryId}`);
      setRepositories((currentRepositories) =>
        currentRepositories.filter((repository) => repository.id !== repositoryId)
      );
    } catch (repositoryError) {
      setRepositoryMessage(
        repositoryError.response?.data?.detail || "The repository could not be deleted."
      );
    }
  };

  const handleProcessDocument = async (documentId) => {
    setProcessingDocumentId(documentId);
    setProcessingStatus((current) => ({ ...current, [documentId]: "Processing..." }));

    try {
      const response = await api.post(`/knowledge/process/documents/${documentId}`);
      setProcessingStatus((current) => ({
        ...current,
        [documentId]: `Processed: ${response.data.chunks_created} chunks`,
      }));
    } catch (processError) {
      setProcessingStatus((current) => ({
        ...current,
        [documentId]: "Processing failed.",
      }));
    } finally {
      setProcessingDocumentId(null);
    }
  };

  const handleProcessRepository = async (repositoryId) => {
    setProcessingRepositoryId(repositoryId);
    setProcessingStatus((current) => ({ ...current, [repositoryId]: "Processing..." }));

    try {
      const response = await api.post(`/knowledge/process/repositories/${repositoryId}`);
      setProcessingStatus((current) => ({
        ...current,
        [repositoryId]: `Processed: ${response.data.chunks_created} chunks`,
      }));
    } catch (processError) {
      setProcessingStatus((current) => ({
        ...current,
        [repositoryId]: "Processing failed.",
      }));
    } finally {
      setProcessingRepositoryId(null);
    }
  };

  const handleKnowledgeSearch = async (event) => {
    event.preventDefault();

    if (!searchQuestion.trim()) {
      setSearchError("Enter a question to search your knowledge base.");
      return;
    }

    setIsSearching(true);
    setSearchError("");

    try {
      const sanitizedTopK = Number(topK) || 5;
      const response = await api.post("/knowledge/search", {
        query: searchQuestion.trim(),
        top_k: Math.max(1, sanitizedTopK),
      });
      setSearchResults(response.data?.results || []);
    } catch (searchError) {
      setSearchError(searchError.response?.data?.detail || "Knowledge search failed.");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
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

          <section className="upload-panel search-panel">
            <h2>Search Knowledge</h2>
            <form onSubmit={handleKnowledgeSearch} className="knowledge-search-form">
              <div className="search-input-row">
                <input
                  type="text"
                  value={searchQuestion}
                  onChange={(event) => setSearchQuestion(event.target.value)}
                  placeholder="Ask a question about your saved knowledge"
                />
                <div className="top-k-control">
                  <label htmlFor="knowledge-top-k">Top K</label>
                  <input
                    id="knowledge-top-k"
                    type="number"
                    min="1"
                    max="20"
                    value={topK}
                    onChange={(event) => setTopK(event.target.value)}
                  />
                </div>
              </div>
              <button type="submit" disabled={isSearching}>
                {isSearching ? "Searching..." : "Search"}
              </button>
            </form>
            {searchError && <p className="document-message search-error">{searchError}</p>}

            <div className="search-results">
              {searchResults.length === 0 && !isSearching && !searchError ? (
                <p className="empty-state">No results yet. Search your knowledge base to test retrieval.</p>
              ) : (
                searchResults.map((result, index) => (
                  <article className="result-card" key={`${result.source_name}-${result.chunk_index}-${index}`}>
                    <div className="result-meta-row">
                      <span className="result-badge">Result {index + 1}</span>
                      <span className="result-score">Similarity: {Number(result.similarity_score ?? 0).toFixed(4)}</span>
                    </div>
                    <dl>
                      <div><dt>Source name</dt><dd>{result.source_name || "Unnamed source"}</dd></div>
                      <div><dt>Source path</dt><dd>{result.source_path || "No path available"}</dd></div>
                      <div><dt>Chunk index</dt><dd>{result.chunk_index}</dd></div>
                      <div><dt>Similarity score</dt><dd>{Number(result.similarity_score ?? 0).toFixed(4)}</dd></div>
                    </dl>
                    <div className="result-content-block">
                      <h3>Chunk content</h3>
                      <p>{result.content}</p>
                    </div>
                  </article>
                ))
              )}
            </div>
          </section>

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

          <section className="upload-panel">
            <h2>GitHub Repository</h2>
            <form onSubmit={handleAddRepository}>
              <div style={{ marginBottom: 10 }}>
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(event) => setRepoUrl(event.target.value)}
                  placeholder="https://github.com/username/repository"
                  style={{ width: "100%", boxSizing: "border-box" }}
                />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label style={{ display: "block", marginBottom: 6 }}>Repository Type:</label>
                <label style={{ marginRight: 12 }}>
                  <input
                    type="radio"
                    name="repositoryType"
                    value="project"
                    checked={repositoryType === "project"}
                    onChange={(event) => setRepositoryType(event.target.value)}
                  />
                  Project
                </label>
                <label>
                  <input
                    type="radio"
                    name="repositoryType"
                    value="coding"
                    checked={repositoryType === "coding"}
                    onChange={(event) => setRepositoryType(event.target.value)}
                  />
                  Coding Solutions
                </label>
              </div>
              <button type="submit" disabled={isAddingRepository}>
                {isAddingRepository ? "Adding..." : "Add Repository"}
              </button>
            </form>
            {repositoryMessage && <p className="document-message">{repositoryMessage}</p>}
          </section>

          <section className="documents-section">
            <div className="section-heading">
              <h2>Your repositories</h2>
              <span>{repositories.length}</span>
            </div>
            {repositories.length === 0 ? (
              <p className="empty-state">No repositories added yet.</p>
            ) : (
              <ul className="document-list">
                {repositories.map((repository) => (
                  <li className="document-item" key={repository.id}>
                    <div>
                      <strong>{repository.repo_name}</strong>
                      <small>Type: {repository.repository_type === "coding" ? "Coding Solutions" : "Project"}</small>
                      <small>{repository.repo_url}</small>
                      <small>{new Date(repository.created_at).toLocaleString()}</small>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button onClick={() => navigate(`/repositories/${repository.id}`)}>View Files</button>
                      <button
                        onClick={() => handleProcessRepository(repository.id)}
                        disabled={processingRepositoryId === repository.id}
                      >
                        {processingRepositoryId === repository.id ? "Processing..." : "Process for AI"}
                      </button>
                      <button className="delete-button" onClick={() => handleDeleteRepository(repository.id)}>
                        Delete
                      </button>
                    </div>
                    {processingStatus[repository.id] && (
                      <small>{processingStatus[repository.id]}</small>
                    )}
                  </li>
                ))}
              </ul>
            )}
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
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button
                        onClick={() => handleProcessDocument(document.id)}
                        disabled={processingDocumentId === document.id}
                      >
                        {processingDocumentId === document.id ? "Processing..." : "Process for AI"}
                      </button>
                      <button
                        className="delete-button"
                        onClick={() => handleDelete(document.id)}
                      >
                        Delete
                      </button>
                    </div>
                    {processingStatus[document.id] && (
                      <small>{processingStatus[document.id]}</small>
                    )}
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
