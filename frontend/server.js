const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const { createProxyMiddleware } = require('http-proxy-middleware');

const dev = process.env.NODE_ENV !== 'production';
const hostname = 'localhost';
const port = parseInt(process.env.PORT, 10) || 3000;
const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:5000';
const backendWsUrl = backendUrl.replace('http://', 'ws://').replace('https://', 'wss://');

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  // HTTP API proxy configuration
  const apiProxy = createProxyMiddleware({
    target: backendUrl,
    changeOrigin: true,
    // Don't rewrite the path - keep /api prefix for backend
    logLevel: dev ? 'debug' : 'warn',
    onError: (err, req, res) => {
      console.error('API Proxy Error:', err.message);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Proxy Error: ' + err.message);
    }
  });

  // WebSocket proxy configuration
  const wsProxy = createProxyMiddleware({
    target: backendUrl,
    changeOrigin: true,
    ws: true, // Enable WebSocket proxying
    logLevel: dev ? 'debug' : 'warn',
    onError: (err, req, res) => {
      console.error('WS Proxy Error:', err.message);
    }
  });

  const server = createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      
      // Handle API requests
      if (req.url.startsWith('/api/')) {
        return apiProxy(req, res);
      }
      
      // Handle Next.js requests
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error('Error occurred handling', req.url, err);
      res.statusCode = 500;
      res.end('internal server error');
    }
  });

  // Handle WebSocket upgrade requests
  server.on('upgrade', (request, socket, head) => {
    const url = parse(request.url, true);
    
    if (url.pathname.startsWith('/ws')) {
      return wsProxy.upgrade(request, socket, head);
    } else if (url.pathname.startsWith('/_next/webpack-hmr')) {
      // Handle Next.js HMR WebSocket - let it through to Next.js
      // Don't destroy the socket, let Next.js handle it
      return;
    } else {
      // For other WebSocket requests, destroy the connection
      socket.destroy();
    }
  });

  server.listen(port, (err) => {
    if (err) throw err;
    console.log(`> Ready on http://${hostname}:${port}`);
    console.log(`> API proxy: /api/* -> ${backendUrl}`);
    console.log(`> WebSocket proxy: /ws -> ${backendWsUrl}`);
    console.log(`> NODE_ENV: ${process.env.NODE_ENV}`);
    console.log(`> BACKEND_URL: ${backendUrl}`);
  });
});
