/** Pure playback model. `t` is the match clock in seconds; speed is match-seconds per real second. */
export const SPEEDS = [1, 5, 20] as const;
export type Speed = (typeof SPEEDS)[number];

export interface Playback {
  t: number;
  playing: boolean;
  speed: Speed;
  duration: number;
}

export type PlaybackAction =
  | { type: "play" }
  | { type: "pause" }
  | { type: "toggle" }
  | { type: "restart" }
  | { type: "speed"; speed: Speed }
  | { type: "seek"; t: number; play?: boolean }
  | { type: "tick"; dtMs: number };

export const initialPlayback = (duration = 5400): Playback => ({ t: 0, playing: false, speed: 20, duration });

export function playbackReducer(s: Playback, a: PlaybackAction): Playback {
  switch (a.type) {
    case "play":
      return s.t >= s.duration ? { ...s, t: 0, playing: true } : { ...s, playing: true };
    case "pause":
      return { ...s, playing: false };
    case "toggle":
      return playbackReducer(s, { type: s.playing ? "pause" : "play" });
    case "restart":
      return { ...s, t: 0, playing: false };
    case "speed":
      return { ...s, speed: a.speed };
    case "seek":
      return { ...s, t: Math.max(0, Math.min(s.duration, Math.round(a.t))), playing: a.play ?? s.playing };
    case "tick": {
      if (!s.playing) return s;
      const t = Math.min(s.duration, s.t + (s.speed * a.dtMs) / 1000);
      return { ...s, t, playing: t < s.duration };
    }
  }
}

export function clock(t: number): string {
  const s = Math.floor(t);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

/** Fetch cadence: one /live request per `everyMatchSeconds` of match time (bounded so 20x stays light). */
export function shouldFetch(lastFetchedT: number | null, t: number, everyMatchSeconds = 10): boolean {
  if (lastFetchedT === null) return true;
  return Math.abs(t - lastFetchedT) >= everyMatchSeconds;
}
