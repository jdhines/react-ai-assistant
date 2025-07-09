import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNodeHttpEndpoint,
} from '@copilotkit/runtime';

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
  remoteEndpoints: [
    { url: "http://localhost:8000/copilotkit" },
  ],
});

const handler = copilotRuntimeNodeHttpEndpoint({
  endpoint: '/copilotkit',
  runtime,
  serviceAdapter,
});

const server = createServer((req, res) => {
  if (req.url?.startsWith('/copilotkit')) {
    return handler(req, res);
  }

  // Serve static files from React
  const filePath = join(__dirname, 'client', 'dist', req.url === '/' ? 'index.html' : req.url);
  if (existsSync(filePath)) {
    const content = readFileSync(filePath);
    res.writeHead(200);
    res.end(content);
  } else {
    const fallback = readFileSync(join(__dirname, 'client', 'dist', 'index.html'));
    res.writeHead(200);
    res.end(fallback);
  }
});

server.listen(process.env.PORT || 4000, () => {
  console.log('Server running');
});

