import { createContext, useContext, useState } from "react";
import { decodeTokenPayload, login as apiLogin } from "../api";

const AuthContext = createContext(null);

const STORAGE_KEY = "mvrbac_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem(STORAGE_KEY));

  const user = token ? decodeTokenPayload(token) : null;

  async function login(username, password) {
    const { access_token } = await apiLogin(username, password);
    sessionStorage.setItem(STORAGE_KEY, access_token);
    setToken(access_token);
  }

  function logout() {
    sessionStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
