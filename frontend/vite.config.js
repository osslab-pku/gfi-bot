import { defineConfig, loadEnv } from 'vite';
import { splitVendorChunkPlugin } from 'vite';
import react from '@vitejs/plugin-react';
import { version } from './package.json';

process.env.REACT_APP_VERSION = version;

export default defineConfig(({command, mode}) => {
    const env = loadEnv(mode, process.cwd(), 'REACT_APP_');
    console.log(mode, env);
    return {
        plugins: [
            react(),
            splitVendorChunkPlugin(),
        ],
        envPrefix: 'REACT_APP_',
        build: {
            outDir: 'build',
        },
        define: {
            __APP_ENV__: env.APP_ENV
        }
    }
});