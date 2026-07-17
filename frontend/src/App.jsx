import { useEffect, useState } from "react";
import api from "./services/api";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.get("/")
      .then((res) => {
        setMessage(res.data.message);
      })
      .catch(() => {
        setMessage("Backend Connection Failed");
      });
  }, []);

  return (
    <div>
      <h1>Personal Engineering Knowledge Assistant</h1>
      <p>{message}</p>
    </div>
  );
}

export default App;