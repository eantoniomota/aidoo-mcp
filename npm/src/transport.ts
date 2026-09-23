import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import type { Transport as SdkTransport } from "@modelcontextprotocol/sdk/shared/transport.js";
import type { Config } from "./config.js";

export function openUpstream(config: Config): SdkTransport {
  const url = new URL(config.endpoint);
  const requestInit: RequestInit = { headers: config.headers };

  if (config.transport === "sse") {
    return new SSEClientTransport(url, {
      requestInit,
      eventSourceInit: {
        fetch: (input, init) => fetch(input, { ...init, headers: config.headers }),
      },
    });
  }

  return new StreamableHTTPClientTransport(url, { requestInit });
}

export async function checkHealth(config: Config): Promise<{ ok: boolean; message: string }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15_000);
  try {
    const response = await fetch(config.healthUrl, { signal: controller.signal });
    if (!response.ok) {
      return { ok: false, message: `${config.healthUrl} returned HTTP ${response.status}` };
    }
    return { ok: true, message: `${config.healthUrl} is reachable` };
  } catch (error) {
    const name = error instanceof Error ? error.name : "Error";
    return { ok: false, message: `${config.healthUrl} is unreachable (${name})` };
  } finally {
    clearTimeout(timer);
  }
}
