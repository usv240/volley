/**
 * The smallest MCP client the page needs: one JSON-RPC POST to the
 * deployed server, timed, with the session header when there is one.
 * McpProof and VoiceAsk both use it, so the two panels make exactly the
 * same calls Alexa+ would.
 */

export const MCP_URL = process.env.NEXT_PUBLIC_MCP_URL ?? "http://localhost:8791/mcp";
export const PROTOCOL = "2025-11-25";

export async function rpc(body: unknown, session?: string) {
  const headers: Record<string, string> = {
    "content-type": "application/json",
    "mcp-protocol-version": PROTOCOL,
  };
  if (session) headers["mcp-session-id"] = session;
  const t0 = performance.now();
  const res = await fetch(MCP_URL, { method: "POST", headers, body: JSON.stringify(body) });
  const ms = Math.round(performance.now() - t0);
  let json: unknown = null;
  try {
    json = await res.json();
  } catch {
    /* 202 and 204 carry no body */
  }
  return { status: res.status, ms, session: res.headers.get("mcp-session-id"), json };
}

/** A tool's result is JSON inside the first text block. */
export function toolJson<T>(json: unknown): T | null {
  const text = (json as { result?: { content?: { text: string }[] } })?.result?.content?.[0]?.text;
  if (!text) return null;
  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

/** Open a session, call one tool for the public simulated household, close it. */
export async function callOnce<T>(name: string, args: Record<string, unknown> = {}): Promise<{ data: T | null; ms: number; status: number }> {
  const t0 = performance.now();
  const init = await rpc({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: { protocolVersion: PROTOCOL, capabilities: {}, clientInfo: { name: "volley-site-voice", version: "1" } },
  });
  if (!init.session || init.status !== 200) throw new Error(`the server did not open a session (status ${init.status})`);
  await rpc({ jsonrpc: "2.0", method: "notifications/initialized" }, init.session);
  const call = await rpc({ jsonrpc: "2.0", id: 2, method: "tools/call", params: { name, arguments: args } }, init.session);
  void fetch(MCP_URL, { method: "DELETE", headers: { "mcp-session-id": init.session } }).catch(() => {});
  return { data: toolJson<T>(call.json), ms: Math.round(performance.now() - t0), status: call.status };
}
