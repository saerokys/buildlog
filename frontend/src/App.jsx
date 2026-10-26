import { useEffect, useState } from "react";

const STATUS_TEXT = {
  loading: "서버 상태를 확인하는 중입니다...",
  ok: "서버가 정상적으로 동작하고 있습니다.",
  error: "서버에 연결하지 못했습니다. 백엔드 서버가 켜져 있는지 확인해 주세요.",
};

export default function App() {
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let ignore = false;

    fetch("/api/health")
      .then((response) => (response.ok ? response.json() : Promise.reject(response)))
      .then((data) => {
        if (!ignore) setStatus(data.status === "ok" ? "ok" : "error");
      })
      .catch(() => {
        if (!ignore) setStatus("error");
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <main className="page">
      <section className="card">
        <h1>BuildLog</h1>
        <p>학습한 내용과 해결한 오류를 기록하는 서비스입니다.</p>
        <p className={`status status-${status}`} role="status">
          {STATUS_TEXT[status]}
        </p>
      </section>
    </main>
  );
}
