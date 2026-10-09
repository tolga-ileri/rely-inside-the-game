import { MatchBrainApp } from "@/components/MatchBrainApp";

const ALLOWED_FAIL = new Set(["event_analyst", "tactical_analyst", "evidence_verifier", "narrative"]);

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);
  const demo = one(sp.demo) === "1";
  const match = one(sp.match);
  const fail = demo ? undefined : one(sp.fail)?.split(",").filter((f) => ALLOWED_FAIL.has(f)).join(",");
  return <MatchBrainApp matchId={match && /^[a-z0-9-]+$/.test(match) ? match : undefined} demoMode={demo} fail={fail || undefined} />;
}
