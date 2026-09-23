#!/usr/bin/env node
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ConfigError, loadConfig, maskKey, type CliArgs } from "./config.js";
import { checkHealth, openUpstream } from "./transport.js";
import { runProxy } from "./proxy.js";

const PROBE_TOOL = "aidoo_context";
const VERSION = "0.1.0";

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    switch (arg) {
      case "--api-key":
        args.apiKey = argv[++i];
        break;
      case "--url":
        args.url = argv[++i];
        break;
      case "--transport":
        args.transport = argv[++i];
        break;
      case "--timeout":
        args.timeout = argv[++i];
        break;
      case "--retries":
        args.retries = argv[++i];
        break;
      case "--check":
        args.check = true;
        break;
      case "--quiet":
        args.quiet = true;
        break;
      case "--version":
        console.log(VERSION);
        process.exit(0);
        break;
      case "--help":
      case "-h":
        printHelp();
        process.exit(0);
        break;
      default:
        console.error(`[aidoo-mcp] Unknown argument: ${arg}`);
        process.exit(2);
    }
  }
  return args;
}

function printHelp(): void {
  console.log(
    [
      "aidoo-mcp [--api-key KEY] [--url URL] [--transport {http,sse}]",
      "          [--timeout SECONDS] [--retries N] [--check] [--quiet]",
      "",
      "Environment variables: AIDOO_API_KEY, AIDOO_MCP_URL, AIDOO_MCP_TRANSPORT, AIDOO_MCP_TIMEOUT",
    ].join("\n")
  );
}

function log(config: { quiet: boolean }, message: string): void {
  if (!config.quiet) {
    console.error(`[aidoo-mcp] ${message}`);
  }
}

async function runCheck(config: ReturnType<typeof loadConfig>): Promise<number> {
  const health = await checkHealth(config);
  console.error(`[aidoo-mcp] ${health.message}`);
  if (!health.ok) {
    return 1;
  }

  const client = new Client({ name: "aidoo-mcp-check", version: VERSION });
  try {
    await client.connect(openUpstream(config));
  } catch (error) {
    console.error(
      `[aidoo-mcp] handshake with ${config.endpoint} failed (${
        error instanceof Error ? error.message : String(error)
      })`
    );
    return 1;
  }

  console.error(
    `[aidoo-mcp] authenticated with ${config.endpoint} (transport=${config.transport}, key=${maskKey(
      config.apiKey
    )})`
  );

  try {
    const { tools } = await client.listTools();
    const names = tools.map((tool) => tool.name);
    console.error(`[aidoo-mcp] ${names.length} tools available: ${names.join(", ")}`);

    if (!names.includes(PROBE_TOOL)) {
      console.error(`[aidoo-mcp] ${PROBE_TOOL} is not exposed by this key, cannot verify the key is accepted`);
      return 1;
    }

    const result = await client.callTool({ name: PROBE_TOOL, arguments: {} });
    if (result.isError) {
      console.error(`[aidoo-mcp] ${PROBE_TOOL} was rejected, the key is likely invalid or revoked`);
      return 1;
    }
    console.error(`[aidoo-mcp] ${PROBE_TOOL} accepted, the key is valid`);
    return 0;
  } finally {
    await client.close();
  }
}

async function runBridge(config: ReturnType<typeof loadConfig>): Promise<number> {
  const local = new StdioServerTransport();
  const upstream = openUpstream(config);
  log(config, `bridging stdio to ${config.endpoint} (transport=${config.transport}, key=${maskKey(config.apiKey)})`);
  try {
    await runProxy(local, upstream);
    return 0;
  } catch (error) {
    console.error(`[aidoo-mcp] connection error: ${error instanceof Error ? error.message : String(error)}`);
    return 1;
  }
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  let config;
  try {
    config = loadConfig(args, process.env);
  } catch (error) {
    if (error instanceof ConfigError) {
      console.error(`[aidoo-mcp] ${error.message}`);
      process.exit(2);
    }
    throw error;
  }

  const exitCode = args.check ? await runCheck(config) : await runBridge(config);
  process.exit(exitCode);
}

main().catch((error) => {
  console.error(`[aidoo-mcp] unexpected error: ${error instanceof Error ? error.stack ?? error.message : error}`);
  process.exit(1);
});
