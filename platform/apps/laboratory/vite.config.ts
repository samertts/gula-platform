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
        name: 'GULA مختبر - نظام معلومات المختبرات',
        short_name: 'GULA مختبر',
        description: 'نظام إدارة معلومات المختبرات - GULA National Laboratory Information System',
        theme_color: '#6366f1',
        background_color: '#f8fafc',
        display: 'standalone',
        display_override: ['window-controls-overlay', 'minimal-ui'],
        orientation: 'any',
        start_url: '/',
        scope: '/',
        lang: 'ar',
        dir: 'rtl',
        categories: ['health', 'medical', 'laboratory', 'productivity'],
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
          { name: 'لوحة المعلومات', short_name: 'الرئيسية', description: 'عرض لوحة المعلومات', url: '/dashboard', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'قائمة العمل', short_name: 'العمل', description: 'عرض قائمة العمل اليومية', url: '/worklist', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'مراقبة الجودة', short_name: 'الجودة', description: 'إدارة مراقبة الجودة', url: '/quality-control', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'المخزون', short_name: 'المخزون', description: 'إدارة المخزون والمواد', url: '/inventory', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
        ],
        screenshots: [
          { src: 'screenshots/dashboard.png', sizes: '1920x1080', type: 'image/png', form_factor: 'wide', label: 'لوحة معلومات المختبر' },
          { src: 'screenshots/mobile-dashboard.png', sizes: '1080x1920', type: 'image/png', form_factor: 'narrow', label: 'لوحة المعلومات' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.gula\.health\/api\/v1\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gula-lab-api',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 7 },
              networkTimeoutSeconds: 5,
              backgroundSync: { name: 'gula-lab-sync' },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gula-lab-images',
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.(?:googleapis|gstatic)\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'gula-lab-fonts',
              expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 365 },
            },
          },
          {
            urlPattern: /\/api\/v1\/(?:samples|results|orders)\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gula-lab-transactional',
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 },
              backgroundSync: { name: 'gula-lab-transaction-sync' },
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
    port: 4000,
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
          pwa: ['workbox-precaching', 'workbox-routing', 'workbox-strategies', 'workbox-background-sync'],
        },
      },
    },
  },
});
