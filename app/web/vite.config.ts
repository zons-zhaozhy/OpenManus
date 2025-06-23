import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000', // 使用IPv4地址而不是localhost
                changeOrigin: true,
                secure: false,
                // 保持/api前缀，因为后端路由就是/api/开头
            }
        }
    }
})
