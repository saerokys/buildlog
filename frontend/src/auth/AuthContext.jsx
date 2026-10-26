import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { getMe } from "../api/auth.js";

const AuthContext = createContext(null);

/** 로그인한 사용자 정보를 앱 전체에서 함께 씁니다. */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // loading: 확인 중, ready: 확인 끝, error: 서버에 연결하지 못함
  const [status, setStatus] = useState("loading");

  const refresh = useCallback(async () => {
    setStatus("loading");
    try {
      setUser(await getMe());
      setStatus("ready");
    } catch (error) {
      setUser(null);
      setStatus(error.status === 401 ? "ready" : "error");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <AuthContext.Provider value={{ user, setUser, status, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
