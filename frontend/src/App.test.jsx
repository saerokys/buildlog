import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import App from "./App.jsx";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("서버가 정상이면 정상 안내를 보여준다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ status: "ok" }) }),
    );

    render(<App />);

    expect(await screen.findByText("서버가 정상적으로 동작하고 있습니다.")).toBeTruthy();
    expect(fetch).toHaveBeenCalledWith("/api/health");
  });

  it("서버에 연결하지 못하면 실패 안내를 보여준다", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")));

    render(<App />);

    expect(await screen.findByText(/서버에 연결하지 못했습니다/)).toBeTruthy();
  });
});
