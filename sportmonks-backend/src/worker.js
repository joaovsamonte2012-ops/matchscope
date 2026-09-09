const SPORTMONKS_BASE = "https://api.sportmonks.com/v3/football";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Content-Type": "application/json; charset=utf-8",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: corsHeaders });
}

function isoFromSportmonks(value) {
  if (!value) return null;
  const normalized = value.includes("T") ? value : value.replace(" ", "T") + "Z";
  const d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? value : d.toISOString();
}

function participantLocation(p, index) {
  return p?.meta?.location || p?.location || (index === 0 ? "home" : "away");
}

function getTeams(fixture) {
  const participants = Array.isArray(fixture?.participants) ? fixture.participants : [];
  let home = participants.find((p, i) => participantLocation(p, i) === "home");
  let away = participants.find((p, i) => participantLocation(p, i) === "away");
  if (!home) home = participants[0] || {};
  if (!away) away = participants[1] || {};
  return { home, away };
}

function scoreFor(fixture, participantId) {
  const scores = Array.isArray(fixture?.scores) ? fixture.scores : [];
  const mine = scores.filter(s => Number(s?.participant_id) === Number(participantId));
  if (!mine.length) return null;
  const values = mine
    .map(s => s?.score?.goals)
    .filter(v => v !== null && v !== undefined && !Number.isNaN(Number(v)))
    .map(Number);
  return values.length ? Math.max(...values) : null;
}

function mapStatus(fixture) {
  const short = fixture?.state?.short_name || fixture?.state?.code || "NS";
  const name = fixture?.state?.name || short;
  return { short, long: name, elapsed: fixture?.state?.elapsed || null };
}

function statValue(s) {
  const value = s?.data?.value ?? s?.value ?? null;
  if (value && typeof value === "object") {
    if ("value" in value) return value.value;
    return JSON.stringify(value);
  }
  return value;
}

function mapStatistics(fixture) {
  const stats = Array.isArray(fixture?.statistics) ? fixture.statistics : [];
  const { home, away } = getTeams(fixture);
  const grouped = new Map();
  for (const s of stats) {
    const pid = Number(s?.participant_id);
    const type = s?.type?.name || s?.type?.developer_name || `Stat ${s?.type_id ?? ""}`;
    if (!grouped.has(pid)) grouped.set(pid, []);
    grouped.get(pid).push({ type, value: statValue(s) });
  }
  return [
    { team: { id: home?.id, name: home?.name, logo: home?.image_path }, statistics: grouped.get(Number(home?.id)) || [] },
    { team: { id: away?.id, name: away?.name, logo: away?.image_path }, statistics: grouped.get(Number(away?.id)) || [] },
  ].filter(x => x.team.id);
}

function mapEvents(fixture) {
  const events = Array.isArray(fixture?.events) ? fixture.events : [];
  return events.map(e => ({
    time: { elapsed: e?.minute ?? e?.time?.minute ?? null, extra: e?.extra_minute ?? null },
    team: { id: e?.participant_id ?? e?.team_id ?? null, name: e?.participant?.name ?? null },
    player: { id: e?.player_id ?? null, name: e?.player?.display_name ?? e?.player?.name ?? null },
    assist: { id: e?.related_player_id ?? null, name: e?.related_player?.display_name ?? null },
    type: e?.type?.name ?? e?.type?.developer_name ?? "Evento",
    detail: e?.info ?? e?.addition ?? e?.result ?? null,
  }));
}

function formationFromStarters(starters) {
  const rows = new Map();
  for (const p of starters) {
    const grid = String(p?.grid || "");
    const m = grid.match(/^(\d+):(\d+)$/);
    if (!m) continue;
    const row = Number(m[1]);
    if (row <= 1) continue;
    rows.set(row, (rows.get(row) || 0) + 1);
  }
  const counts = [...rows.entries()].sort((a, b) => a[0] - b[0]).map(([, count]) => count);
  return counts.length ? counts.join("-") : null;
}

function mapLineups(fixture) {
  const lineups = Array.isArray(fixture?.lineups) ? fixture.lineups : [];
  const byTeam = new Map();

  for (const l of lineups) {
    const teamId = Number(l?.team_id ?? l?.participant_id);
    if (!teamId) continue;
    if (!byTeam.has(teamId)) byTeam.set(teamId, { starters: [], substitutes: [] });

    const player = {
      id: l?.player_id ?? l?.player?.id ?? null,
      name: l?.player?.display_name ?? l?.player?.name ?? l?.player_name ?? `Jogador ${l?.player_id ?? ""}`,
      number: l?.jersey_number ?? l?.shirt_number ?? null,
      pos: l?.position?.name ?? l?.position?.developer_name ?? l?.position ?? null,
      grid: l?.formation_field ?? (typeof l?.formation_position === "string" && l.formation_position.includes(":") ? l.formation_position : null),
    };

    // Sportmonks: type_id 11 = titular, 12 = reserva. formation_field é a posição oficial no desenho tático.
    const typeId = Number(l?.type_id);
    const isStarter = typeId === 11 || (!!player.grid && typeId !== 12);
    if (isStarter) byTeam.get(teamId).starters.push(player);
    else byTeam.get(teamId).substitutes.push(player);
  }

  const { home, away } = getTeams(fixture);
  return [home, away].filter(Boolean).map(t => {
    const group = byTeam.get(Number(t?.id)) || { starters: [], substitutes: [] };
    const starters = group.starters
      .sort((a, b) => {
        const ga = String(a.grid || "99:99").split(":").map(Number);
        const gb = String(b.grid || "99:99").split(":").map(Number);
        return (ga[0] - gb[0]) || (ga[1] - gb[1]);
      });
    return {
      team: { id: t?.id, name: t?.name, logo: t?.image_path },
      formation: formationFromStarters(starters),
      startXI: starters.map(player => ({ player })),
      substitutes: group.substitutes.map(player => ({ player })),
    };
  });
}

function normalizeFixture(fixture, includeDetails = false) {
  const { home, away } = getTeams(fixture);
  const normalized = {
    fixture: {
      id: fixture?.id,
      date: isoFromSportmonks(fixture?.starting_at),
      timestamp: fixture?.starting_at_timestamp ?? null,
      timezone: "UTC",
      status: mapStatus(fixture),
      venue: fixture?.venue ? { id: fixture.venue.id, name: fixture.venue.name, city: fixture.venue.city_name ?? null } : null,
    },
    league: {
      id: fixture?.league_id,
      name: fixture?.league?.name ?? `Liga ${fixture?.league_id ?? ""}`,
      country: fixture?.league?.country?.name ?? null,
      logo: fixture?.league?.image_path ?? null,
      season: fixture?.season_id ?? null,
      round: fixture?.round?.name ?? fixture?.stage?.name ?? null,
    },
    teams: {
      home: { id: home?.id, name: home?.name ?? "Casa", logo: home?.image_path ?? null, winner: null },
      away: { id: away?.id, name: away?.name ?? "Fora", logo: away?.image_path ?? null, winner: null },
    },
    goals: {
      home: home?.id ? scoreFor(fixture, home.id) : null,
      away: away?.id ? scoreFor(fixture, away.id) : null,
    },
    score: {},
  };
  if (includeDetails) {
    normalized.statistics = mapStatistics(fixture);
    normalized.events = mapEvents(fixture);
    normalized.lineups = mapLineups(fixture);
  }
  return normalized;
}

function getSportmonksToken(env) {
  return env.SPORTMONKS_TOKEN || env.SPORTMONKS_API_TOKEN || null;
}

async function sportmonks(env, path, params = {}) {
  const token = getSportmonksToken(env);
  if (!token) throw new Error("SPORTMONKS_TOKEN ou SPORTMONKS_API_TOKEN não configurado no backend");
  const url = new URL(SPORTMONKS_BASE + path);
  url.searchParams.set("api_token", token);
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== "") url.searchParams.set(k, v);
  }
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = body?.message || body?.error || `Sportmonks HTTP ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return body;
}

function dateDaysAgo(days) {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

async function handleFixtures(url, env) {
  const id = url.searchParams.get("id");
  const date = url.searchParams.get("date");
  const team = url.searchParams.get("team");
  const last = Math.min(Number(url.searchParams.get("last") || 5), 20);

  const listIncludes = "participants;scores;league;state";
  const detailIncludes = "participants;scores;league;state;venue;statistics.type;events.type;events.player;lineups.player";

  if (id) {
    const sm = await sportmonks(env, `/fixtures/${encodeURIComponent(id)}`, { include: detailIncludes });
    return { response: sm?.data ? [normalizeFixture(sm.data, true)] : [], results: sm?.data ? 1 : 0 };
  }

  if (date) {
    const sm = await sportmonks(env, `/fixtures/date/${encodeURIComponent(date)}`, { include: listIncludes, per_page: "100" });
    const data = Array.isArray(sm?.data) ? sm.data : [];
    return { response: data.map(f => normalizeFixture(f, false)), results: data.length, paging: sm?.pagination ?? null };
  }

  if (team) {
    const end = new Date().toISOString().slice(0, 10);
    const start = dateDaysAgo(100);
    const sm = await sportmonks(env, `/fixtures/between/${start}/${end}/${encodeURIComponent(team)}`, { include: listIncludes, per_page: "100" });
    const data = (Array.isArray(sm?.data) ? sm.data : [])
      .sort((a, b) => Number(b?.starting_at_timestamp || 0) - Number(a?.starting_at_timestamp_timestamp || a?.starting_at_timestamp || 0))
      .slice(0, last);
    return { response: data.map(f => normalizeFixture(f, false)), results: data.length };
  }

  return { response: [], results: 0, errors: { request: "Informe date, id ou team." } };
}

async function handleFixturePart(url, env, part) {
  const id = url.searchParams.get("fixture");
  if (!id) return { response: [], results: 0 };
  const includeMap = {
    statistics: "participants;statistics.type",
    events: "participants;events.type;events.player",
    lineups: "participants;lineups.player",
  };
  const sm = await sportmonks(env, `/fixtures/${encodeURIComponent(id)}`, { include: includeMap[part] });
  if (!sm?.data) return { response: [], results: 0 };
  let response = [];
  if (part === "statistics") response = mapStatistics(sm.data);
  if (part === "events") response = mapEvents(sm.data);
  if (part === "lineups") response = mapLineups(sm.data);
  return { response, results: response.length };
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });
    if (request.method !== "GET") return json({ error: "Método não permitido" }, 405);

    const url = new URL(request.url);
    try {
      if (url.pathname === "/health") return json({ ok: true, provider: "Sportmonks", tokenConfigured: Boolean(getSportmonksToken(env)) });
      if (url.pathname === "/fixtures") return json(await handleFixtures(url, env));
      if (url.pathname === "/fixtures/statistics") return json(await handleFixturePart(url, env, "statistics"));
      if (url.pathname === "/fixtures/events") return json(await handleFixturePart(url, env, "events"));
      if (url.pathname === "/fixtures/lineups") return json(await handleFixturePart(url, env, "lineups"));
      return json({ error: "Rota não encontrada" }, 404);
    } catch (error) {
      return json({ error: String(error?.message || error), response: [], results: 0 }, 502);
    }
  },
};
