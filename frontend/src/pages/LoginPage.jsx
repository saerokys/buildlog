import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { login } from "../api/auth.js";
import { useAuth } from "../auth/AuthContext.jsx";
import FormField from "../components/FormField.jsx";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const notice = location.state?.notice;

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");

    try {
      setUser(await login({ email, password }));
      navigate("/", { replace: true });
    } catch (error) {
      // 실패하면 이메일은 남기고 비밀번호만 지웁니다.
      setPassword("");
      setMessage(error.message);
      setSubmitting(false);
    }
  }

  return (
    <main className="page page-narrow">
      <section className="card">
        <h1>로그인</h1>
        {notice && !message && (
          <p className="alert alert-success" role="status">
            {notice}
          </p>
        )}
        {message && (
          <p className="alert alert-error" role="alert">
            {message}
          </p>
        )}
        <form onSubmit={handleSubmit} noValidate>
          <FormField
            id="email"
            label="이메일"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <FormField
            id="password"
            label="비밀번호"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <button type="submit" className="button button-primary" disabled={submitting}>
            {submitting ? "로그인하는 중..." : "로그인"}
          </button>
        </form>
        <p className="form-footer">
          아직 계정이 없나요? <Link to="/signup">회원가입</Link>
        </p>
      </section>
    </main>
  );
}
