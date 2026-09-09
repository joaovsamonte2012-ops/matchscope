import http from "node:http";
import worker from "./src/worker.js";

const port = Number(process.env.PORT || 3000);
const rooms = new Map();
const users = new Map();
const streams = new Map();
const recent = new Map();

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
};

function json(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", ...cors });
  res.end(JSON.stringify(body));
}

function levelFromXp(xp) {
  return Math.max(1, Math.floor(Math.sqrt(Math.max(0, xp) / 40)) + 1);
}

function levelFloor(level) {
  return Math.pow(Math.max(0, level - 1), 2) * 40;
}

function levelCeil(level) {
  return Math.pow(level, 2) * 40;
}

function publicUser(userId) {
  const u = users.get(userId) || { xp: 0, messages: 0 };
  const level = levelFromXp(u.xp);
  const floor = levelFloor(level);
  const ceil = levelCeil(level);
  return {
    xp: u.xp,
    level,
    currentLevelXp: u.xp - floor,
    nextLevelXp: ceil - floor,
    progress: Math.max(0, Math.min(1, (u.xp - floor) / Math.max(1, ceil - floor))),
    messages: u.messages,
  };
}

function safeText(value, max = 280) {
  return String(value ?? "").replace(/[\u0000-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

function pushRoom(fixtureId, message) {
  const list = rooms.get(fixtureId) || [];
  list.push(message);
  if (list.length > 150) list.splice(0, list.length - 150);
  rooms.set(fixtureId, list);

  const clients = streams.get(fixtureId);
  if (clients) {
    const payload = `event: message\ndata: ${JSON.stringify(message)}\n\n`;
    for (const res of clients) {
      try { res.write(payload); } catch { clients.delete(res); }
    }
  }
}

function parseFixture(pathname, prefix) {
  return decodeURIComponent(pathname.slice(prefix.length)).replace(/[^a-zA-Z0-9_.:-]/g, "").slice(0, 80);
}

async function readJson(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 16_384) throw new Error("payload_too_large");
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

const server = http.createServer(async (req, res) => {
  try {
    const host = req.headers.host || `localhost:${port}`;
    const protocol = req.headers["x-forwarded-proto"] || "http";
    const url = new URL(`${protocol}://${host}${req.url || "/"}`);

    if (req.method === "OPTIONS") {
      res.writeHead(204, cors);
      return res.end();
    }

    if (url.pathname.startsWith("/chat/messages/")) {
      const fixtureId = parseFixture(url.pathname, "/chat/messages/");
      if (!fixtureId) return json(res, 400, { error: "fixture_required" });

      if (req.method === "GET") {
        return json(res, 200, { fixtureId, messages: rooms.get(fixtureId) || [] });
      }

      if (req.method === "POST") {
        const body = await readJson(req);
        const userId = safeText(body.userId, 80);
        const nickname = safeText(body.nickname, 24) || "Torcedor";
        const text = safeText(body.text, 280);
        if (!userId || text.length < 2) return json(res, 400, { error: "invalid_message" });

        const now = Date.now();
        const key = `${fixtureId}:${userId}`;
        const last = recent.get(key) || { at: 0, text: "" };
        if (now - last.at < 2500) return json(res, 429, { error: "cooldown" });

        const normalized = text.toLocaleLowerCase("pt-BR");
        const duplicate = normalized === last.text;
        recent.set(key, { at: now, text: normalized });

        const u = users.get(userId) || { xp: 0, messages: 0 };
        u.messages += 1;
        let earnedXp = 0;
        if (!duplicate) {
          earnedXp = 8;
          if (u.messages % 5 === 0) earnedXp += 5;
          u.xp += earnedXp;
        }
        users.set(userId, u);

        const profile = publicUser(userId);
        const message = {
          id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
          fixtureId,
          userId,
          nickname,
          text,
          createdAt: new Date(now).toISOString(),
          level: profile.level,
          xp: profile.xp,
        };
        pushRoom(fixtureId, message);
        return json(res, 201, { message, earnedXp, profile });
      }
    }

    if (url.pathname.startsWith("/chat/stream/")) {
      const fixtureId = parseFixture(url.pathname, "/chat/stream/");
      if (!fixtureId) return json(res, 400, { error: "fixture_required" });
      res.writeHead(200, {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        ...cors,
      });
      res.write(`event: ready\ndata: ${JSON.stringify({ fixtureId })}\n\n`);
      const set = streams.get(fixtureId) || new Set();
      set.add(res);
      streams.set(fixtureId, set);
      const ping = setInterval(() => {
        try { res.write(": ping\n\n"); } catch { clearInterval(ping); }
      }, 20000);
      req.on("close", () => {
        clearInterval(ping);
        set.delete(res);
        if (!set.size) streams.delete(fixtureId);
      });
      return;
    }

    if (url.pathname.startsWith("/chat/profile/")) {
      const userId = parseFixture(url.pathname, "/chat/profile/");
      if (!userId) return json(res, 400, { error: "user_required" });
      return json(res, 200, { userId, profile: publicUser(userId) });
    }

    if (url.pathname.startsWith("/chat/leaderboard/")) {
      const fixtureId = parseFixture(url.pathname, "/chat/leaderboard/");
      const ids = new Set((rooms.get(fixtureId) || []).map(m => m.userId));
      const ranking = [...ids].map(userId => ({ userId, ...publicUser(userId) }))
        .sort((a, b) => b.xp - a.xp).slice(0, 30);
      return json(res, 200, { fixtureId, ranking });
    }

    const request = new Request(url.toString(), {
      method: req.method,
      headers: req.headers,
    });
    const response = await worker.fetch(request, process.env, {});
    res.statusCode = response.status;
    for (const [key, value] of response.headers.entries()) res.setHeader(key, value);
    const body = await response.arrayBuffer();
    res.end(Buffer.from(body));
  } catch (error) {
    json(res, 500, { error: String(error?.message || error) });
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(`MatchScope backend listening on port ${port}`);
});
