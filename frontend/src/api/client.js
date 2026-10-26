const NETWORK_ERROR = "서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.";
const UNKNOWN_ERROR = "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";

/** 백엔드가 돌려준 안내 문구(message)와 칸별 오류(errors)를 담습니다. */
export class ApiError extends Error {
  constructor(status, message, errors = {}) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

export async function apiRequest(path, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "same-origin",
    });
  } catch {
    throw new ApiError(0, NETWORK_ERROR);
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, data?.message ?? UNKNOWN_ERROR, data?.errors ?? {});
  }
  return data;
}
