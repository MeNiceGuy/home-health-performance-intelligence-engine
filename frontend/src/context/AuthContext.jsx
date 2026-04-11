import { createContext, useContext, useMemo, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(localStorage.getItem("bhpi_token"));
  const [user, setUser] = useState(null);

  const setToken = (value) => {
    setTokenState(value);
    if (value) localStorage.setItem("bhpi_token", value);
    else localStorage.removeItem("bhpi_token");
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = useMemo(() => ({
    token,
    setToken,
    user,
    setUser,
    logout,
    isAuthenticated: !!token
  }), [token, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
