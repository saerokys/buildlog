import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";

import { AppRoutes } from "./App.jsx";
import { AuthProvider } from "./auth/AuthContext.jsx";

const USER = { id: 1, email: "user1@example.com", nickname: "user_1", is_admin: false };

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: () => Promise.resolve(body) };
}

const NOT_LOGGED_IN = jsonResponse(401, { message: "로그인이 필요합니다.", errors: {} });

/** 주소와 방식별로 가짜 서버 응답을 정합니다. */
function mockServer(routes) {
  const fetchMock = vi.fn((path, options = {}) => {
    const key = `${options.method ?? "GET"} ${path}`;
    const handler = routes[key];
    if (!handler) throw new Error(`예상하지 못한 요청: ${key}`);
    return Promise.resolve(typeof handler === "function" ? handler(options) : handler);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderApp(path) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </AuthProvider>,
  );
}

function type(label, value) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("로그인이 필요한 화면", () => {
  it("로그인하지 않았으면 로그인 화면으로 보낸다", async () => {
    mockServer({ "GET /api/auth/me": NOT_LOGGED_IN });

    renderApp("/account");

    expect(await screen.findByRole("heading", { name: "로그인" })).toBeTruthy();
  });

  it("로그인했으면 내 기록 홈을 보여준다", async () => {
    mockServer({ "GET /api/auth/me": jsonResponse(200, USER) });

    renderApp("/");

    expect(await screen.findByRole("heading", { name: "내 기록 홈" })).toBeTruthy();
    expect(screen.getByText("안녕하세요, user_1님.")).toBeTruthy();
  });

  it("서버에 연결하지 못하면 실패 안내를 보여준다", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")));

    renderApp("/");

    expect((await screen.findByRole("alert")).textContent).toContain("서버에 연결하지 못했습니다");
  });
});

describe("회원가입", () => {
  it("성공하면 로그인 화면으로 이동해 완료 안내를 보여준다", async () => {
    const fetchMock = mockServer({
      "GET /api/auth/me": NOT_LOGGED_IN,
      "POST /api/auth/signup": jsonResponse(201, USER),
    });
    renderApp("/signup");
    await screen.findByRole("heading", { name: "회원가입" });

    type("이메일", "user1@example.com");
    type("비밀번호 (8~64자)", "password123");
    type("닉네임 (2~20자, 한글·영문·숫자·밑줄)", "user_1");
    fireEvent.click(screen.getByRole("button", { name: "회원가입" }));

    expect(await screen.findByRole("heading", { name: "로그인" })).toBeTruthy();
    expect(screen.getByText("회원가입이 완료되었습니다. 로그인해 주세요.")).toBeTruthy();
    const [, options] = fetchMock.mock.calls.find(([path]) => path === "/api/auth/signup");
    expect(JSON.parse(options.body)).toEqual({
      email: "user1@example.com",
      password: "password123",
      nickname: "user_1",
    });
  });

  it("실패하면 이메일과 닉네임은 남기고 비밀번호만 지운다", async () => {
    mockServer({
      "GET /api/auth/me": NOT_LOGGED_IN,
      "POST /api/auth/signup": jsonResponse(409, {
        message: "입력한 내용을 다시 확인해 주세요.",
        errors: { nickname: "이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요." },
      }),
    });
    renderApp("/signup");
    await screen.findByRole("heading", { name: "회원가입" });

    type("이메일", "user1@example.com");
    type("비밀번호 (8~64자)", "password123");
    type("닉네임 (2~20자, 한글·영문·숫자·밑줄)", "taken");
    fireEvent.click(screen.getByRole("button", { name: "회원가입" }));

    expect(await screen.findByText("이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요.")).toBeTruthy();
    expect(screen.getByLabelText("이메일").value).toBe("user1@example.com");
    expect(screen.getByLabelText("닉네임 (2~20자, 한글·영문·숫자·밑줄)").value).toBe("taken");
    expect(screen.getByLabelText("비밀번호 (8~64자)").value).toBe("");
  });
});

describe("로그인", () => {
  it("성공하면 내 기록 홈으로 이동한다", async () => {
    mockServer({
      "GET /api/auth/me": NOT_LOGGED_IN,
      "POST /api/auth/login": jsonResponse(200, USER),
    });
    renderApp("/login");
    await screen.findByRole("heading", { name: "로그인" });

    type("이메일", "user1@example.com");
    type("비밀번호", "password123");
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    expect(await screen.findByRole("heading", { name: "내 기록 홈" })).toBeTruthy();
  });

  it("실패하면 이메일은 남기고 비밀번호만 지운다", async () => {
    mockServer({
      "GET /api/auth/me": NOT_LOGGED_IN,
      "POST /api/auth/login": jsonResponse(401, { message: "이메일 또는 비밀번호가 맞지 않습니다.", errors: {} }),
    });
    renderApp("/login");
    await screen.findByRole("heading", { name: "로그인" });

    type("이메일", "user1@example.com");
    type("비밀번호", "wrong-password");
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    expect(await screen.findByText("이메일 또는 비밀번호가 맞지 않습니다.")).toBeTruthy();
    expect(screen.getByLabelText("이메일").value).toBe("user1@example.com");
    expect(screen.getByLabelText("비밀번호").value).toBe("");
  });
});

describe("로그아웃", () => {
  it("로그아웃하면 로그인 화면으로 이동한다", async () => {
    const fetchMock = mockServer({
      "GET /api/auth/me": jsonResponse(200, USER),
      "POST /api/auth/logout": { ok: true, status: 204, json: () => Promise.reject(new Error("no body")) },
    });
    renderApp("/");
    await screen.findByRole("heading", { name: "내 기록 홈" });

    fireEvent.click(screen.getByRole("button", { name: "로그아웃" }));

    expect(await screen.findByRole("heading", { name: "로그인" })).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/logout", expect.objectContaining({ method: "POST" }));
  });

  it("실패하면 이유를 알려주고 로그인 상태를 유지한다", async () => {
    mockServer({
      "GET /api/auth/me": jsonResponse(200, USER),
      "POST /api/auth/logout": () => {
        throw new Error("network");
      },
    });
    renderApp("/");
    await screen.findByRole("heading", { name: "내 기록 홈" });

    fireEvent.click(screen.getByRole("button", { name: "로그아웃" }));

    expect((await screen.findByRole("alert")).textContent).toContain("서버에 연결하지 못했습니다");
    expect(screen.getByRole("heading", { name: "내 기록 홈" })).toBeTruthy();
  });
});

describe("닉네임 변경", () => {
  const LABEL = "새 닉네임 (2~20자, 한글·영문·숫자·밑줄)";

  it("성공하면 바뀐 닉네임을 보여준다", async () => {
    mockServer({
      "GET /api/auth/me": jsonResponse(200, USER),
      "PATCH /api/account/nickname": jsonResponse(200, { ...USER, nickname: "새닉네임" }),
    });
    renderApp("/account");
    await screen.findByRole("heading", { name: "계정 설정" });

    type(LABEL, "새닉네임");
    fireEvent.click(screen.getByRole("button", { name: "변경" }));

    expect(await screen.findByText("닉네임을 변경했습니다.")).toBeTruthy();
    expect(screen.getByTestId("current-nickname").textContent).toBe("새닉네임");
  });

  it("실패하면 이유를 알려주고 입력한 닉네임을 유지한다", async () => {
    mockServer({
      "GET /api/auth/me": jsonResponse(200, USER),
      "PATCH /api/account/nickname": jsonResponse(409, {
        message: "닉네임을 변경하지 못했습니다. 입력한 내용을 확인해 주세요.",
        errors: { nickname: "이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요." },
      }),
    });
    renderApp("/account");
    await screen.findByRole("heading", { name: "계정 설정" });

    type(LABEL, "taken");
    fireEvent.click(screen.getByRole("button", { name: "변경" }));

    expect(await screen.findByText("이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해 주세요.")).toBeTruthy();
    expect(screen.getByLabelText(LABEL).value).toBe("taken");
    expect(screen.getByTestId("current-nickname").textContent).toBe("user_1");
  });
});
