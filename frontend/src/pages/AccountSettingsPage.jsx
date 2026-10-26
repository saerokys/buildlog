import { useState } from "react";

import { changeNickname } from "../api/auth.js";
import { useAuth } from "../auth/AuthContext.jsx";
import FormField from "../components/FormField.jsx";

export default function AccountSettingsPage() {
  const { user, setUser } = useAuth();
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setMessage("");
    setSuccess("");

    try {
      setUser(await changeNickname(nickname));
      setNickname("");
      setSuccess("닉네임을 변경했습니다.");
    } catch (failure) {
      // 실패하면 입력한 새 닉네임을 그대로 둡니다.
      setError(failure.errors?.nickname ?? "");
      setMessage(failure.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="card">
      <h1>계정 설정</h1>
      <dl className="info-list">
        <dt>이메일</dt>
        <dd>{user.email}</dd>
        <dt>현재 닉네임</dt>
        <dd data-testid="current-nickname">{user.nickname}</dd>
      </dl>

      {success && (
        <p className="alert alert-success" role="status">
          {success}
        </p>
      )}
      {message && (
        <p className="alert alert-error" role="alert">
          {message}
        </p>
      )}
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="nickname"
          label="새 닉네임 (2~20자, 한글·영문·숫자·밑줄)"
          type="text"
          autoComplete="nickname"
          value={nickname}
          onChange={(event) => setNickname(event.target.value)}
          error={error}
        />
        <button type="submit" className="button button-primary" disabled={submitting}>
          {submitting ? "변경하는 중..." : "변경"}
        </button>
      </form>
    </section>
  );
}
