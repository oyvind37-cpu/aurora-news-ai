// Aurora News AI - Cloudflare Worker
// Configure GITHUB_TOKEN and REFRESH_SECRET as Cloudflare secrets.
// Never put REFRESH_SECRET in publicly served frontend code.
const owner = "oyvind37-cpu";
const repo = "aurora-news-ai";
const workflow = "news.yml";

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    }
  });
}

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path === "/health" && request.method === "GET") {
      return reply({ service: "aurora-news-refresh", configured: Boolean(env.GITHUB_TOKEN && env.REFRESH_SECRET) });
    }
    if (path !== "/refresh") return reply({ error: "Not found" }, 404);
    if (request.method !== "POST") return reply({ error: "POST required" }, 405);
    if (!env.GITHUB_TOKEN || !env.REFRESH_SECRET) return reply({ error: "Not configured" }, 503);
    if (request.headers.get("Authorization") !== `Bearer ${env.REFRESH_SECRET}`) {
      return reply({ error: "Unauthorized" }, 401);
    }
    try {
      const response = await fetch(
        `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${env.GITHUB_TOKEN}`,
            Accept: "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Aurora-News-AI"
          },
          body: JSON.stringify({ ref: "main" })
        }
      );
      if (response.status === 204) return reply({ success: true, status: "queued" }, 202);
      console.error("GitHub dispatch status", response.status);
      return reply({ error: "Unable to dispatch workflow" }, 502);
    } catch (error) {
      console.error("GitHub dispatch network error", error);
      return reply({ error: "GitHub request failed" }, 502);
    }
  }
};
