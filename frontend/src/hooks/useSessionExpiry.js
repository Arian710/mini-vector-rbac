import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Faengt abgelaufene/ungueltige Tokens (401 vom Backend) zentral ab, statt in
 * jeder Seite dieselbe Fehlermeldung anzuzeigen - loggt aus und schickt zurueck
 * zum Login, wo ein frisches Token geholt werden kann.
 *
 * Nutzung in einem catch-Block: if (!handleSessionExpiry(err)) setError(err.message);
 */
export function useSessionExpiry() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return function handleSessionExpiry(err) {
    if (err.status === 401) {
      logout();
      navigate("/login");
      return true;
    }
    return false;
  };
}
