import { Navigate, Outlet } from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";

/** 로그인하지 않은 사용자는 로그인 화면으로 보냅니다. */
export default function RequireAuth() {
  const { user, status, refresh } = useAuth();

  if (status === "loading") {
    return <p className="page-message">불러오는 중입니다...</p>;
  }

  if (status === "error") {
    return (
      <div className="page-message">
        <p className="alert alert-error" role="alert">
          서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.
        </p>
        <button type="button" className="button" onClick={refresh}>
          다시 시도
        </button>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
