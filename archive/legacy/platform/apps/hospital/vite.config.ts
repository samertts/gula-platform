import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/*.png', 'icons/*.svg', 'icons/*.ico'],
      manifest: {
        name: 'GULA - نظام إدارة المستشفيات الوطني',
        short_name: 'GULA مستشفى',
        description: 'نظام إدارة المستشفيات الوطني العراقي - GULA National Hospital Administration',
        theme_color: '#1e3a5f',
        background_color: '#0f172a',
        display: 'standalone',
        orientation: 'any',
        start_url: '/',
        scope: '/',
        lang: 'ar',
        dir: 'rtl',
        categories: ['medical', 'hospital', 'healthcare', 'administration'],
        display_override: ['window-controls-overlay', 'minimal-ui'],
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
          { src: 'icons/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
        shortcuts: [
          { name: 'لوحة المعلومات', short_name: 'الرئيسية', description: 'لوحة معلومات المستشفى', url: '/dashboard', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'الأسرة', short_name: 'الأسرة', description: 'إدارة الأسرة والإشغال', url: '/beds', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'التقارير', short_name: 'تقارير', description: 'تقارير التحليلات', url: '/reporting', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
        ],
        screenshots: [
          { src: 'screenshots/dashboard.png', sizes: '1920x1080', type: 'image/png', form_factor: 'wide', label: 'لوحة معلومات المستشفى' },
          { src: 'screenshots/mobile-dashboard.png', sizes: '1080x1920', type: 'image/png', form_factor: 'narrow', label: 'لوحة المعلومات' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2,webp}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.gula\.health\/api\/v1\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gula-hospital-api',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 7 },
              networkTimeoutSeconds: 5,
              backgroundSync: { name: 'gula-hospital-sync' },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gula-hospital-images',
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.(?:googleapis|gstatic)\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'gula-hospital-fonts',
              expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 365 },
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
    port: 3002,
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
          ui: ['@gula/ui-platform'],
          charts: ['recharts'],
        },
      },
    },
  },
});
