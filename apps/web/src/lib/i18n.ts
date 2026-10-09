import type { Locale, Persona } from "./types";

const en = {
  synthetic: "SYNTHETIC FOOTBALL-REALISTIC DATA",
  playDemo: "Play Demo", play: "Play", pause: "Pause", restart: "Restart", jump: "Jump to Turning Point", explain: "Explain Moment",
  response: "Generate Response", recap: "Generate Recap", switchPersona: "Switch Persona", switchLanguage: "Switch Language",
  ht: "HT", ft: "FT", feed: "Intelligence feed", noFeed: "Waiting for the first signals…", why: "Why did the match change?",
  evidence: "Evidence", trace: "Agent Trace", tactics: "Tactical Response", recapTab: "Recap", before: "Before", trigger: "Trigger",
  after: "After", explanation: "Explanation", confidence: "Confidence", turningPoint: "Turning point detected", close: "Close",
  persona: { coach: "Coach", analyst: "Analyst", broadcaster: "Broadcaster", fan: "Fan" } as Record<Persona, string>,
  momentum: "Momentum", shots: "Shots", onTarget: "On target", passShare: "Pass share", entries: "Final-third entries",
  progressive: "Progressive actions", box: "Box entries", highPress: "High pressures", recoveries: "Recoveries",
  window: "Window", events: "Events", sequence: "Sequence", metrics: "Derived metrics", rule: "Rule", coverage: "Evidence coverage",
  agent: "Agent", status: "Status", provider: "Provider", model: "Model", fallback: "Fallback", outputs: "Outputs",
  instruction: "Instruction", risk: "Risk", movements: "Player movements", impact: "Formation impact", whatIf: "What-if",
  effect: "Effect", advantage: "Advantage", players: "Players", limitations: "Limitations", saveTactic: "Save demo tactic",
  saved: "Saved locally", story: "Match Story", formats: { thirty_seconds: "30 s", analyst_two_minutes: "2-min analyst", coach: "Coach", broadcast: "Broadcast", fan: "Fan", social: "Social" },
  storyCards: "Broadcast story cards", prep: "Commentator prep", unavailable: "AI explanation unavailable", sequenceViewer: "Sequence viewer",
  liveSeq: "Live sequence", keyEvents: "Key events behind the moment", openWindow: "after window still open", backLine: "Back line",
  frontLine: "Front line", noMoment: "No turning point yet. Keep playing.", channels: { L: "Left", C: "Centre", R: "Right" },
  supported: "supported", unverifiable: "unverifiable (causal)", rejected: "rejected", lens: "Persona lens", language: "Language",
  sameEvidence: "Same evidence, different presentation.",
};
type Dict = typeof en;

const tr: Dict = {
  ...en,
  synthetic: "SENTETİK FUTBOL-GERÇEKÇİ VERİ",
  playDemo: "Demoyu Oynat", play: "Oynat", pause: "Duraklat", restart: "Baştan", jump: "Kırılma Anına Git", explain: "Anı Açıkla",
  response: "Taktik Yanıt Üret", recap: "Özet Üret", switchPersona: "Persona Değiştir", switchLanguage: "Dil Değiştir",
  ht: "İY", ft: "MS", feed: "Analiz akışı", noFeed: "İlk sinyaller bekleniyor…", why: "Maç neden değişti?", evidence: "Kanıt",
  trace: "Ajan İzi", tactics: "Taktik Yanıt", recapTab: "Özet", before: "Önce", trigger: "Tetikleyici", after: "Sonra",
  explanation: "Açıklama", confidence: "Güven", turningPoint: "Kırılma anı tespit edildi", close: "Kapat",
  persona: { coach: "Teknik Direktör", analyst: "Analist", broadcaster: "Yayıncı", fan: "Taraftar" },
  momentum: "Momentum", shots: "Şut", onTarget: "İsabetli", passShare: "Pas payı", entries: "Son üçte bir girişi",
  progressive: "İleri aksiyon", box: "Ceza sahası girişi", highPress: "Önde baskı", recoveries: "Top kazanımı",
  window: "Pencere", events: "Olaylar", sequence: "Atak dizisi", metrics: "Türetilmiş metrikler", rule: "Kural", coverage: "Kanıt kapsamı",
  agent: "Ajan", status: "Durum", provider: "Sağlayıcı", model: "Model", fallback: "Yedek", outputs: "Çıktı",
  instruction: "Talimat", risk: "Risk", movements: "Oyuncu hareketleri", impact: "Diziliş etkisi", whatIf: "Ya şöyle olursa",
  effect: "Etki", advantage: "Avantaj", players: "Oyuncular", limitations: "Sınırlamalar", saveTactic: "Demo taktiğini kaydet",
  saved: "Yerel olarak kaydedildi", story: "Maç Hikâyesi", formats: { thirty_seconds: "30 sn", analyst_two_minutes: "2 dk analist", coach: "Teknik", broadcast: "Yayın", fan: "Taraftar", social: "Sosyal" },
  storyCards: "Yayın hikâye kartları", prep: "Spiker hazırlığı", unavailable: "Yapay zekâ açıklaması yok", sequenceViewer: "Atak görüntüleyici",
  liveSeq: "Canlı atak", keyEvents: "Anın arkasındaki olaylar", openWindow: "sonrası penceresi açık", backLine: "Savunma hattı",
  frontLine: "Hücum hattı", noMoment: "Henüz kırılma anı yok. Oynatmaya devam edin.", channels: { L: "Sol", C: "Merkez", R: "Sağ" },
  supported: "destekli", unverifiable: "doğrulanamaz (nedensel)", rejected: "reddedildi", lens: "Persona merceği", language: "Dil",
  sameEvidence: "Aynı kanıt, farklı sunum.",
};

const es: Dict = {
  ...en,
  synthetic: "DATOS SINTÉTICOS REALISTAS DE FÚTBOL",
  playDemo: "Reproducir demo", play: "Reproducir", pause: "Pausa", restart: "Reiniciar", jump: "Ir al punto de inflexión", explain: "Explicar momento",
  response: "Generar respuesta", recap: "Generar resumen", switchPersona: "Cambiar perfil", switchLanguage: "Cambiar idioma",
  ht: "DES", ft: "FIN", feed: "Feed de inteligencia", noFeed: "Esperando las primeras señales…", why: "¿Por qué cambió el partido?",
  evidence: "Evidencia", trace: "Traza de agentes", tactics: "Respuesta táctica", recapTab: "Resumen", before: "Antes", trigger: "Detonante",
  after: "Después", explanation: "Explicación", confidence: "Confianza", turningPoint: "Punto de inflexión detectado", close: "Cerrar",
  persona: { coach: "Entrenador", analyst: "Analista", broadcaster: "Narrador", fan: "Aficionado" },
  momentum: "Inercia", shots: "Tiros", onTarget: "A puerta", passShare: "Cuota de pases", entries: "Entradas al último tercio",
  progressive: "Acciones progresivas", box: "Llegadas al área", highPress: "Presión alta", recoveries: "Recuperaciones",
  window: "Ventana", events: "Eventos", sequence: "Secuencia", metrics: "Métricas derivadas", rule: "Regla", coverage: "Cobertura de evidencia",
  agent: "Agente", status: "Estado", provider: "Proveedor", model: "Modelo", fallback: "Respaldo", outputs: "Salidas",
  instruction: "Instrucción", risk: "Riesgo", movements: "Movimientos", impact: "Impacto en el sistema", whatIf: "Qué pasaría si",
  effect: "Efecto", advantage: "Ventaja", players: "Jugadores", limitations: "Limitaciones", saveTactic: "Guardar táctica demo",
  saved: "Guardado en local", story: "Historia del partido", formats: { thirty_seconds: "30 s", analyst_two_minutes: "Analista 2 min", coach: "Entrenador", broadcast: "Retransmisión", fan: "Aficionado", social: "Social" },
  storyCards: "Tarjetas para la retransmisión", prep: "Preparación del comentarista", unavailable: "Explicación IA no disponible", sequenceViewer: "Visor de secuencias",
  liveSeq: "Secuencia en vivo", keyEvents: "Eventos clave del momento", openWindow: "ventana posterior abierta", backLine: "Línea defensiva",
  frontLine: "Línea de ataque", noMoment: "Aún no hay punto de inflexión. Sigue reproduciendo.", channels: { L: "Izquierda", C: "Centro", R: "Derecha" },
  supported: "respaldada", unverifiable: "no verificable (causal)", rejected: "rechazada", lens: "Lente de perfil", language: "Idioma",
  sameEvidence: "Misma evidencia, distinta presentación.",
};

export const DICTS: Record<Locale, Dict> = { en, tr, es };
export const t = (l: Locale) => DICTS[l];
export type { Dict };
