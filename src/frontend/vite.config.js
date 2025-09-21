import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
    // 加载环境变量
    const env = loadEnv(mode, process.cwd())
    return {
        plugins: [vue()],
        server: {
            proxy: {
                // 匹配以 /api 开头的请求路径
                '/api': {
                    // 目标服务器地址
                    target: env.VITE_API_BASE_URL,
                    // 允许跨域
                    changeOrigin: true,
                    // 重写路径，去除 /api 前缀
                    rewrite: (path) => path.replace(/^\/api/, ''),
                },
            },
            port: 5173
        },
        define: {
            // 将配置暴露给客户端
            '__API_PROXY__': JSON.stringify({
                baseUrl: env.VITE_API_BASE_URL,
            })
        }
    }
})