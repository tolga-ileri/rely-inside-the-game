export type Persona = "coach" | "analyst" | "broadcaster" | "fan";
export type Locale = "en" | "tr" | "es";
export const PERSONAS: Persona[] = ["coach", "analyst", "broadcaster", "fan"];
export const LOCALES: Locale[] = ["en", "tr", "es"];

export interface MatchEvent {
  event_id: string;
  match_second: number;
  minute: number;
  second: number;
  period: number;
  team_id: string;
  player_id: string | null;
  event_type: string;
  outcome: string | null;
  start_x: number;
  start_y: number;
  end_x: number | null;
  end_y: number | null;
  possession_id: number;
  sequence_id: number;
  qualifiers: Record<string, unknown>;
}

export interface Player { player_id: string; name: string; number: number; position: string; starter: boolean }
export interface Team {
  side: "home" | "away"; team_id: string; name: string; short: string; color: string;
  crest: { shape: string; initials: string }; players: Player[];
}
export interface MatchMeta {
  match_id: string; scenario: string; title: string; data_statement: string; data_label: string; duration_seconds: number;
  demo: { start_second?: number; speed?: number }; home_team_id: string; away_team_id: string; teams: Team[]; event_count: number;
}

export interface WindowMetrics {
  team_id: string; start: number; end: number; passes: number; pass_share: number; progressive_actions: number;
  prog_L: number; prog_C: number; prog_R: number; final_third_entries: number; entries_L: number; entries_C: number; entries_R: number;
  box_entries: number; shots: number; shots_on_target: number; xg: number; recoveries: number; turnovers: number; pressures: number;
  high_pressures: number; dangerous_sequences: number; final_third_share: number;
}
export interface TeamStats {
  team_id: string; goals: number; shots: number; shots_on_target: number; xg: number; possession: number; pass_accuracy: number;
  final_third_entries: number; entries_by_channel: Record<string, number>; box_entries: number; recoveries: number; turnovers: number;
  pressures: number; high_pressures: number; yellow_cards: number; red_cards: number; substitutions: number; players_on_pitch: number;
}
export interface MatchState {
  until: number; period: number; clock: string; minute: number; score: Record<string, number>; possession_team_id: string | null;
  teams: Record<string, TeamStats>; momentum: number; momentum_series: number[]; last5: Record<string, WindowMetrics>;
  last10: Record<string, WindowMetrics>; recent_events: MatchEvent[]; current_sequence: MatchEvent[];
  player_involvement: { player_id: string; name: string; team_id: string; touches: number }[]; events_processed: number;
  is_full_time: boolean;
}
export interface Evidence {
  id: string; kind: "metric" | "event" | "sequence" | "window" | "rule"; label: string; value: number | string | null;
  unit: string | null; metric_path: string | null; event_ids: string[]; timestamp: number | null; window: [number, number] | null;
}
export interface Moment {
  id: string; timestamp: number; minute: number; detected_at: number; type: string; team_id: string;
  severity: "low" | "medium" | "high"; title: string; title_localized: string; params: Record<string, unknown>;
  trigger: Record<string, unknown>; before_state: WindowMetrics | null; after_state: WindowMetrics | null;
  after_window_complete: boolean; evidence: Evidence[]; confidence: number; linked_event_ids: string[];
  explanation_status: "pending" | "generated" | "fallback" | "unavailable"; rule: string; clock: string; detected_clock: string;
}
export interface FeedItem {
  id: string; second: number; clock: string; kind: "moment" | "goal" | "card" | "sub"; severity: string; team_id: string;
  moment_id: string | null; text: string; confidence?: number;
}
export interface AgentTrace {
  agent: string; status: "ok" | "fallback" | "failed" | "skipped"; ms: number; provider: string; model: string | null;
  fallback_used: boolean; evidence_coverage: number | null; outputs: number; note: string | null;
}
export interface Verification { total_claims: number; supported: number; rejected: number; unverifiable: number; coverage: number; issues: string[] }
export interface Claim {
  id: string; kind: string; agent: string; text: string; team_id: string | null; metrics: { path: string; value: unknown }[];
  event_ids: string[]; moment_id: string | null; confidence: number | null; caveat: string | null; verified: boolean | null;
}
export interface LiveResponse {
  state: MatchState; moments: Moment[]; headline_id: string | null; feed: FeedItem[]; observations: Claim[]; tactical: Claim[];
  verification: Verification | null; trace: AgentTrace[]; chapters: { moment_id: string; clock: string; title: string; summary: string; evidence_ids: string[] }[];
}
export interface Narrative { headline: string; explanation: string; bullets: string[]; persona: Persona; locale: Locale; source: "llm" | "template"; verified: boolean }
export interface ExplainResponse {
  moment: Moment; narrative: Narrative | null; explanation_unavailable: string | null; claims: Claim[]; verification: Verification | null;
  trace: AgentTrace[]; events: MatchEvent[]; story_cards: { moment_id: string; clock: string; title: string; stat: string; context: string }[];
  commentator_prep: string[];
}
export interface ResponsePlayer { role: string; player_id: string; name: string; number: number; from: [number, number]; to: [number, number]; moves: boolean; text: string | null }
export interface TacticalResponse {
  moment_id: string; team_id: string; team: string; playbook: string; name: string; from_shape: string; to_shape: string;
  formation_impact: { back_line: [number, number]; front_line: [number, number]; phase: string };
  instruction: string; risk: string; players: ResponsePlayer[]; movements: Claim[]; evidence_ids: string[];
  grounding: Record<string, unknown>; options: string[];
}
export interface WhatIf {
  option: string; name: string; team: string; effect: string; advantage: string; risk: string;
  players: { role: string; name: string; number: number }[]; limitations: string; score_prediction: null;
}
export interface Recap {
  status: string; thirty_seconds: string; analyst_two_minutes: string; coach: string; broadcast: string; fan: string; social: string;
}
export interface KeyMoments {
  headline: { id: string; detected_at: number; timestamp: number } | null;
  markers: { id: string; type: string; second: number; team_id: string; severity: string }[];
  half_time: number; full_time: number; demo: { start_second?: number; speed?: number };
}
