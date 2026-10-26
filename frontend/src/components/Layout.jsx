import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router";

import { logout } from "../api/auth.js";
import { useAuth } from "../auth/AuthContext.jsx";

/** 로그인한 사용자 화면의 공통 머리글과 메뉴입니다. */
export default function Layout() {
  const { user, setUser } = useAuth();
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleLogout() {
    setSubmitting(true);
    setMessage("");
    try {
      await logout();
      // 사용자 정보를 비우면 로그인이 필요한 화면에서 로그인 화면으로 이동합니다.
      setUser(null);
    } catch (error) {
      setMessage(error.message);
      setSubmitting(false);
    }
  }

  return (
    <>
      <header className="site-header">
        <div className="site-header-inner">
          <Link to="/" className="brand">
            BuildLog
          </Link>
          <nav className="site-nav" aria-label="주요 메뉴">
            <NavLink to="/" end>
              홈
            </NavLink>
            <NavLink to="/account">계정 설정</NavLink>
          </nav>
          <span className="site-user">{user.nickname}님</span>
          <button type="button" className="button" onClick={handleLogout} disabled={submitting}>
            로그아웃
          </button>
        </div>
      </header>
      <main className="page">
        {message && (
          <p className="alert alert-error" role="alert">
            {message}
          </p>
        )}
        <Outlet />
      </main>
    </>
  );
}
