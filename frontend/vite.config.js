import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import http from "node:http";

/**
 * SSO proxy: intercept non-asset requests and proxy them to the backend,
 * so /{route_name} (e.g. /helpdesk) works during development through Vite.
 */
function ssoProxyPlugin() {
  const BACKEND = { host: "localhost", port: 8000 };
  return {
    name: "sso-proxy",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url || "";

        // Let Vite handle frontend resources
        if (
          url === "/" ||
          url.startsWith("/@") ||
          url.startsWith("/src/") ||
          url.startsWith("/node_modules/") ||
          url.startsWith("/assets/") ||
          url.startsWith("/favicon")
        ) {
          return next();
        }

        // Proxy everything else to the backend
        const proxyReq = http.request(
          {
            hostname: BACKEND.host,
            port: BACKEND.port,
            path: url,
            method: req.method,
            headers: { ...req.headers, host: `${BACKEND.host}:${BACKEND.port}` },
          },
          (proxyRes) => {
            // Forward status code and headers
            res.writeHead(proxyRes.statusCode, proxyRes.statusMessage, proxyRes.headers);
            proxyRes.pipe(res);
          },
        );

        proxyReq.on("error", (err) => {
          console.error(`[sso-proxy] Error proxying ${url}:`, err.message);
          res.statusCode = 502;
          res.end(`<h1>502 - Bad Gateway</h1><p>Proxy error: ${err.message}</p>`);
        });

        req.pipe(proxyReq);
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), ssoProxyPlugin()],
});
