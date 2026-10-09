import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Controls } from "@/components/Controls";
import { EvidencePanel, TacticalPanel, WhyPanel } from "@/components/Panels";
import { DICTS } from "@/lib/i18n";
import { clock, initialPlayback, playbackReducer, shouldFetch } from "@/lib/playback";
import type { ExplainResponse, TacticalResponse } from "@/lib/types";
import explain from "./fixtures/explain.json";
import response from "./fixtures/response.json";

const ex = explain as unknown as ExplainResponse;
const resp = response as unknown as TacticalResponse;
const L = DICTS.en;

afterEach(() => cleanup());

const handlers = () => ({
  onPlayDemo: vi.fn(), onToggle: vi.fn(), onRestart: vi.fn(), onSpeed: vi.fn(), onHT: vi.fn(), onFT: vi.fn(), onJump: vi.fn(),
  onExplain: vi.fn(), onResponse: vi.fn(), onRecap: vi.fn(), onPersona: vi.fn(), onLanguage: vi.fn(),
});

describe("playback engine", () => {
  it("advances by speed and stops at full time", () => {
    let s = playbackReducer(initialPlayback(5400), { type: "seek", t: 3000, play: true });
    s = playbackReducer(s, { type: "tick", dtMs: 1000 });
    expect(s.t).toBe(3020);
    s = playbackReducer(s, { type: "speed", speed: 5 });
    s = playbackReducer(s, { type: "tick", dtMs: 2000 });
    expect(s.t).toBe(3030);
    s = playbackReducer(s, { type: "seek", t: 5399 });
    s = playbackReducer(playbackReducer(s, { type: "speed", speed: 20 }), { type: "tick", dtMs: 1000 });
    expect(s.t).toBe(5400);
    expect(s.playing).toBe(false);
  });
  it("does not move while paused, restart resets, seek clamps", () => {
    let s = playbackReducer(initialPlayback(), { type: "seek", t: 100 });
    expect(playbackReducer(s, { type: "tick", dtMs: 5000 }).t).toBe(100);
    s = playbackReducer(s, { type: "seek", t: 99999 });
    expect(s.t).toBe(5400);
    expect(playbackReducer(s, { type: "restart" }).t).toBe(0);
    expect(clock(3603)).toBe("60:03");
    expect(shouldFetch(null, 0)).toBe(true);
    expect(shouldFetch(100, 105, 10)).toBe(false);
    expect(shouldFetch(100, 110, 10)).toBe(true);
  });
  it("demo turning point arrives 25-35 s after Play Demo at the default speed", async () => {
    const km = (await import("./fixtures/keymoments.json")).default;
    const seconds = (km.headline!.detected_at - km.demo.start_second!) / km.demo.speed!;
    expect(seconds).toBeGreaterThanOrEqual(25);
    expect(seconds).toBeLessThanOrEqual(35);
  });
});

describe("controls", () => {
  it("fires demo handlers and marks the active speed", () => {
    const h = handlers();
    render(<Controls L={L} playing={false} speed={20} h={h} />);
    fireEvent.click(screen.getByRole("button", { name: /Play Demo/ }));
    fireEvent.click(screen.getByRole("button", { name: "Jump to Turning Point" }));
    fireEvent.click(screen.getByRole("button", { name: "Explain Moment" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Response" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Recap" }));
    fireEvent.click(screen.getByRole("button", { name: "5x" }));
    expect(h.onPlayDemo).toHaveBeenCalledOnce();
    expect(h.onJump).toHaveBeenCalledOnce();
    expect(h.onExplain).toHaveBeenCalledOnce();
    expect(h.onResponse).toHaveBeenCalledOnce();
    expect(h.onRecap).toHaveBeenCalledOnce();
    expect(h.onSpeed).toHaveBeenCalledWith(5);
    expect(screen.getByRole("button", { name: "20x" }).getAttribute("aria-pressed")).toBe("true");
  });
  it("renders in Turkish and Spanish", () => {
    const { rerender } = render(<Controls L={DICTS.tr} playing={false} speed={20} h={handlers()} />);
    expect(screen.getByRole("button", { name: /Demoyu Oynat/ })).toBeTruthy();
    rerender(<Controls L={DICTS.es} playing={false} speed={20} h={handlers()} />);
    expect(screen.getByRole("button", { name: /Reproducir demo/ })).toBeTruthy();
  });
});

describe("why panel + persona lens", () => {
  it("shows before / trigger / after, the narrative and switches persona", () => {
    const onPersona = vi.fn();
    render(<WhyPanel L={L} ex={ex} persona="analyst" onPersona={onPersona} playerNames={{ "HCF-17": "Kai Okafor", "HCF-07": "Dario Mends" }} />);
    expect(screen.getByText("Before")).toBeTruthy();
    expect(screen.getByText("Trigger")).toBeTruthy();
    expect(screen.getByText("After")).toBeTruthy();
    expect(screen.getByTestId("narrative").textContent).toContain(ex.narrative!.headline);
    fireEvent.click(screen.getByRole("button", { name: "Coach" }));
    expect(onPersona).toHaveBeenCalledWith("coach");
  });
  it("shows the unavailable state when the narrative agent failed", () => {
    render(<WhyPanel L={L} ex={{ ...ex, narrative: null, explanation_unavailable: "AI explanation unavailable" }} persona="fan" onPersona={vi.fn()} playerNames={{}} />);
    expect(screen.getByTestId("unavailable").textContent).toContain("AI explanation unavailable");
  });
});

describe("evidence panel", () => {
  it("lists event ids, windows and metrics with honest coverage", () => {
    render(<EvidencePanel L={L} ex={ex} demo={false} />);
    const items = screen.getAllByTestId("evidence-item");
    expect(items.length).toBe(ex.moment.evidence.filter((e) => e.kind !== "rule").length + ex.moment.evidence.filter((e) => e.kind === "rule").length);
    const firstEventId = ex.moment.evidence.find((e) => e.kind === "event")!.event_ids[0];
    expect(screen.getAllByText(firstEventId).length).toBeGreaterThan(0);
    expect(screen.getByText(`${Math.round(ex.verification!.coverage * 100)}%`)).toBeTruthy();
  });
  it("shortens internal ids in demo mode", () => {
    render(<EvidencePanel L={L} ex={ex} demo />);
    const firstEventId = ex.moment.evidence.find((e) => e.kind === "event")!.event_ids[0];
    expect(screen.queryByText(firstEventId)).toBeNull();
    expect(screen.getAllByText(`#${firstEventId.slice(-5)}`).length).toBeGreaterThan(0);
  });
});

describe("tactical response", () => {
  beforeEach(() => localStorage.clear());
  it("renders the 4-3-3 to 3-2-5 shape, movements, risk and saves locally", async () => {
    vi.useFakeTimers();
    const onWhatIf = vi.fn();
    render(<TacticalPanel L={L} resp={resp} colors={{ HCF: "#1F4E8C" }} whatIf={null} onWhatIf={onWhatIf} onPlaybook={vi.fn()} locale="en" />);
    expect(screen.getByTestId("studio-preview").getAttribute("aria-label")).toBe("4-3-3 to 3-2-5");
    expect(screen.getByText(/inverts into midfield/)).toBeTruthy();
    expect(screen.getByText(/Rest defence/)).toBeTruthy();
    act(() => { vi.advanceTimersByTime(600); });
    fireEvent.click(screen.getByRole("button", { name: "Save demo tactic" }));
    const saved = JSON.parse(localStorage.getItem("rely.demoTactics") || "[]");
    expect(saved).toHaveLength(1);
    expect(saved[0].to).toBe("3-2-5");
    fireEvent.click(screen.getByRole("button", { name: "Counter: 5-4-1" }));
    expect(onWhatIf).toHaveBeenCalledWith("counter_5_4_1");
    vi.useRealTimers();
  });
});

describe("app language switch", () => {
  it("switches UI language without refetching facts", async () => {
    const fixtures = {
      meta: (await import("./fixtures/meta.json")).default, km: (await import("./fixtures/keymoments.json")).default,
      live: (await import("./fixtures/live.json")).default,
    };
    const live = vi.fn(async () => fixtures.live);
    vi.doMock("@/lib/api", () => ({ api: { meta: async () => fixtures.meta, keymoments: async () => fixtures.km, live } }));
    const { MatchBrainApp } = await import("@/components/MatchBrainApp");
    render(<MatchBrainApp />);
    await waitFor(() => expect(screen.getByTestId("synthetic-label").textContent).toBe("SYNTHETIC FOOTBALL-REALISTIC DATA"));
    fireEvent.click(screen.getByRole("button", { name: "Switch Language" }));
    await waitFor(() => expect(screen.getByTestId("synthetic-label").textContent).toBe("SENTETİK FUTBOL-GERÇEKÇİ VERİ"));
    expect(screen.getByRole("button", { name: /Demoyu Oynat/ })).toBeTruthy();
    vi.doUnmock("@/lib/api");
  });
});
