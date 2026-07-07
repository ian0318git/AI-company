import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const apiHost = env.VITE_API_HOST || '127.0.0.1'
  const apiPort = env.VITE_API_PORT || '8765'
  const apiTarget = `http://${apiHost}:${apiPort}`

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/health': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/status': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/autonomous': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
