import http from "node:http";
import worker from "./src/worker.js";

const port = Number(process.env.PORT || 3000);

const server = http.createServer(async (req, res) => {
  try {
    const host = req.headers.host || `localhost:${port}`;
    const protocol = req.headers["x-forwarded-proto"] || "http";
    const url = `${protocol}://${host}${req.url || "/"}`;

    const request = new Request(url, {
      method: req.method,
      headers: req.headers,
    });

    const response = await worker.fetch(request, process.env, {});

    res.statusCode = response.status;
    for (const [key, value] of response.headers.entries()) {
      res.setHeader(key, value);
    }

    const body = await response.arrayBuffer();
    res.end(Buffer.from(body));
  } catch (error) {
    res.statusCode = 500;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(JSON.stringify({ error: String(error?.message || error) }));
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(`MatchScope Sportmonks backend listening on port ${port}`);
});
