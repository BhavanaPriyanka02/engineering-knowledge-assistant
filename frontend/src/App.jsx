import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import RepositoryDetail from "./pages/RepositoryDetail";

function App() {
  const isLoggedIn = Boolean(localStorage.getItem("token"));

  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/dashboard"
        element={isLoggedIn ? <Dashboard /> : <Navigate to="/" replace />}
      />
      <Route
        path="/repositories/:id"
        element={isLoggedIn ? <RepositoryDetail /> : <Navigate to="/" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;