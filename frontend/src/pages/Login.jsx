import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../services/api";

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });
      localStorage.setItem("token", response.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError("Invalid email or password.");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "auto", padding: 24 }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={6}
            required
          />
        </label>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit">Login</button>
      </form>
      <p>
        Don't have an account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}

export default Login;
