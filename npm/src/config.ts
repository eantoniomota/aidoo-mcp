const DEFAULT_ENDPOINT = "https://mcp.aidoo.ai/mcp";
const DEFAULT_TIMEOUT = 60;
const DEFAULT_RETRIES = 3;

export type Transport = "http" | "sse";

export interface Config {
  apiKey: string;
  endpoint: string;
  transport: Transport;
  timeoutSeconds: number;
  retries: number;
  quiet: boolean;
  headers: Record<string, string>;
  healthUrl: string;
}

export class ConfigError extends Error {}

export function normalizeEndpoint(rawUrl: string | undefined): string {
  const url = (rawUrl ?? DEFAULT_ENDPOINT).trim();
  if (!url) {
    return DEFAULT_ENDPOINT;
  }
  if (!/^https?:\/\//i.test(url)) {
    throw new ConfigError(`The endpoint must start with http:// or https:// (got: ${url})`);
  }
  return url.replace(/\/+$/, "") || url;
}

export function inferTransport(endpoint: string, explicit: string | undefined): Transport {
  if (explicit === "http" || explicit === "sse") {
    return explicit;
  }
  return endpoint.endsWith("/sse") ? "sse" : "http";
}

export function maskKey(key: string): string {
  if (key.length <= 8) {
    return "***";
  }
  return `${key.slice(0, 8)}...${key.slice(-4)}`;
}

export function healthUrlFor(endpoint: string): string {
  try {
    const parsed = new URL(endpoint);
    parsed.pathname = "/health";
    parsed.search = "";
    return parsed.toString();
  } catch {
    return `${endpoint.replace(/\/(mcp|sse)\/?$/, "")}/health`;
  }
}

export interface CliArgs {
  apiKey?: string;
  url?: string;
  transport?: string;
  timeout?: string;
  retries?: string;
  check?: boolean;
  quiet?: boolean;
}

export function loadConfig(args: CliArgs, env: NodeJS.ProcessEnv): Config {
  const apiKey = args.apiKey ?? env.AIDOO_API_KEY;
  if (!apiKey) {
    throw new ConfigError(
      "No API key found. Pass --api-key or set the AIDOO_API_KEY environment variable. " +
        "Create one from the API keys page of your Aidoo workspace."
    );
  }
  if (!apiKey.startsWith("aid_live_")) {
    throw new ConfigError(
      `The key does not look like an Aidoo key (expected a prefix of aid_live_, got: ${maskKey(apiKey)})`
    );
  }

  const endpoint = normalizeEndpoint(args.url ?? env.AIDOO_MCP_URL);
  const transport = inferTransport(endpoint, args.transport ?? env.AIDOO_MCP_TRANSPORT);
  const timeoutSeconds = Number(args.timeout ?? env.AIDOO_MCP_TIMEOUT ?? DEFAULT_TIMEOUT);
  const retries = Number(args.retries ?? DEFAULT_RETRIES);

  if (!Number.isFinite(timeoutSeconds) || timeoutSeconds <= 0) {
    throw new ConfigError(`Invalid timeout: ${args.timeout ?? env.AIDOO_MCP_TIMEOUT}`);
  }

  return {
    apiKey,
    endpoint,
    transport,
    timeoutSeconds,
    retries: Number.isFinite(retries) && retries >= 0 ? retries : DEFAULT_RETRIES,
    quiet: Boolean(args.quiet),
    headers: { Authorization: `Bearer ${apiKey}` },
    healthUrl: healthUrlFor(endpoint),
  };
}
