import type { ExplainResponse, KeyMoments, LiveResponse, Locale, MatchMeta, Persona, Recap, TacticalResponse, WhatIf } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100").replace(/\/$/, "");

async function get<T>(path: string, params: Record<string, string | number | undefined> = {}, signal?: AbortSignal): Promise<T> {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && q.set(k, String(v)));
  const r = await fetch(`${API_URL}${path}${q.toString() ? `?${q}` : ""}`, { signal, cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json() as Promise<T>;
}

export const api = {
  meta: (id: string) => get<MatchMeta>(`/api/matches/${id}`),
  keymoments: (id: string) => get<KeyMoments>(`/api/matches/${id}/keymoments`),
  live: (id: string, until: number, locale: Locale, signal?: AbortSignal, fail?: string) =>
    get<LiveResponse>(`/api/matches/${id}/live`, { until, locale, fail }, signal),
  explain: (id: string, until: number, persona: Persona, locale: Locale, momentId?: string, fail?: string) =>
    get<ExplainResponse>(`/api/matches/${id}/explain`, { until, persona, locale, moment_id: momentId, fail }),
  response: (id: string, until: number, locale: Locale, momentId?: string, playbook = "amplify_3_2_5") =>
    post<TacticalResponse>(`/api/matches/${id}/response`, { until, locale, moment_id: momentId, playbook }),
  whatif: (id: string, until: number, locale: Locale, option: string, momentId?: string) =>
    post<WhatIf>(`/api/matches/${id}/whatif`, { until, locale, option, moment_id: momentId }),
  recap: (id: string, until: number, locale: Locale) => get<Recap>(`/api/matches/${id}/recap`, { until, locale }),
};
