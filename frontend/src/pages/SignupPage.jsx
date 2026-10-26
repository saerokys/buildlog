import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { signup } from "../api/auth.js";
import FormField from "../components/FormField.jsx";

export default function SignupPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setErrors({});
    setMessage("");

    try {
      await signup({ email, password, nickname });
      navigate("/login", { state: { notice: "회원가입이 완료되었습니다. 로그인해 주세요." } });
    } catch (error) {
      // 실패하면 이메일과 닉네임은 남기고 비밀번호만 지웁니다.
      setPassword("");
      setErrors(error.errors ?? {});
      setMessage(error.message);
      setSubmitting(false);
    }
  }

  return (
    <main className="page page-narrow">
      <section className="card">
        <h1>회원가입</h1>
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
            error={errors.email}
          />
          <FormField
            id="password"
            label="비밀번호 (8~64자)"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={errors.password}
          />
          <FormField
            id="nickname"
            label="닉네임 (2~20자, 한글·영문·숫자·밑줄)"
            type="text"
            autoComplete="nickname"
            value={nickname}
            onChange={(event) => setNickname(event.target.value)}
            error={errors.nickname}
          />
          <button type="submit" className="button button-primary" disabled={submitting}>
            {submitting ? "가입하는 중..." : "회원가입"}
          </button>
        </form>
        <p className="form-footer">
          이미 계정이 있나요? <Link to="/login">로그인</Link>
        </p>
      </section>
    </main>
  );
}
