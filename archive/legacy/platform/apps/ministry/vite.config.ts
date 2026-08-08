import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: [
        'icons/*.png',
        'icons/*.svg',
        'icons/*.ico',
      ],
      manifest: {
        name: 'GULA وزارة - منصة الرقابة الصحية الوطنية',
        short_name: 'GULA وزارة',
        description: 'منصة الرقابة الصحية الوطنية - GULA National Health Oversight Platform',
        theme_color: '#1e1b4b',
        background_color: '#0f172a',
        display: 'standalone',
        display_override: ['window-controls-overlay', 'minimal-ui'],
        orientation: 'any',
        start_url: '/',
        scope: '/',
        lang: 'ar',
        dir: 'rtl',
        categories: ['health', 'government', 'analytics', 'productivity'],
        launch_handler: { client_mode: 'focus-existing' },
        icons: [
          { src: 'icons/icon-48x48.png', sizes: '48x48', type: 'image/png' },
          { src: 'icons/icon-72x72.png', sizes: '72x72', type: 'image/png' },
          { src: 'icons/icon-96x96.png', sizes: '96x96', type: 'image/png' },
          { src: 'icons/icon-128x128.png', sizes: '128x128', type: 'image/png' },
          { src: 'icons/icon-144x144.png', sizes: '144x144', type: 'image/png' },
          { src: 'icons/icon-152x152.png', sizes: '152x152', type: 'image/png' },
          { src: 'icons/icon-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: 'icons/icon-384x384.png', sizes: '384x384', type: 'image/png' },
          { src: 'icons/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
        shortcuts: [
          { name: 'لوحة القيادة', short_name: 'الرئيسية', description: 'عرض لوحة القيادة الوطنية', url: '/dashboard', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'الإنذارات', short_name: 'الإنذارات', description: 'عرض الإنذارات الصحية الوطنية', url: '/alerts', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'التقارير', short_name: 'التقارير', description: 'إنشاء التقارير الوطنية', url: '/reports', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'الترصد الوبائي', short_name: 'الترصد', description: 'مراقبة الأمراض والأوبئة', url: '/surveillance', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.gula\.health\/api\/v1\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gula-ministry-api',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 7 },
              networkTimeoutSeconds: 5,
              backgroundSync: { name: 'gula-ministry-sync' },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gula-ministry-images',
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@gula/ui-platform': path.resolve(__dirname, '../../ui'),
    },
  },
  server: {
    port: 5000,
    host: true,
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
          pwa: ['workbox-precaching', 'workbox-routing', 'workbox-strategies'],
        },
      },
    },
  },
});
