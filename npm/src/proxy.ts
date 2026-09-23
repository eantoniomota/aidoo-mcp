import type { Transport as SdkTransport } from "@modelcontextprotocol/sdk/shared/transport.js";

export class ProxyError extends Error {}

export async function runProxy(local: SdkTransport, upstream: SdkTransport): Promise<void> {
  await Promise.all([local.start(), upstream.start()]);

  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      void local.close().catch(() => undefined);
      void upstream.close().catch(() => undefined);
      if (error) reject(error);
      else resolve();
    };

    local.onmessage = (message) => {
      upstream.send(message).catch((error) => finish(new ProxyError(String(error))));
    };
    upstream.onmessage = (message) => {
      local.send(message).catch((error) => finish(new ProxyError(String(error))));
    };

    local.onerror = (error) => finish(new ProxyError(`client transport error: ${error.message}`));
    upstream.onerror = (error) => finish(new ProxyError(`server transport error: ${error.message}`));

    local.onclose = () => finish();
    upstream.onclose = () => finish();
  });
}
