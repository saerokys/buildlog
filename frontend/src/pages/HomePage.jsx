import { Link } from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";

export default function HomePage() {
  const { user } = useAuth();

  return (
    <section className="card">
      <h1>내 기록 홈</h1>
      <p>안녕하세요, {user.nickname}님.</p>
      <p>
        닉네임은 <Link to="/account">계정 설정</Link>에서 바꿀 수 있습니다.
      </p>
    </section>
  );
}
