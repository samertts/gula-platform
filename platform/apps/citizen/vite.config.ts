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
        name: 'السجل الصحي الوطني - GULA',
        short_name: 'GULA صحي',
        description: 'التطبيق الصحي الوطني للمواطنين العراقيين - GULA National Health Application',
        theme_color: '#1e3a5f',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait-primary',
        start_url: '/',
        scope: '/',
        lang: 'ar',
        dir: 'rtl',
        categories: ['health', 'medical', 'lifestyle'],
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
          { name: 'بطاقة الصحية', short_name: 'البطاقة', description: 'عرض بطاقة الهوية الصحية', url: '/health-id', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'المواعيد', short_name: 'مواعيدي', description: 'عرض المواعيد القادمة', url: '/appointments', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'النتائج', short_name: 'نتائجي', description: 'عرض نتائج المختبر', url: '/lab-results', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
          { name: 'الأدوية', short_name: 'أدويتي', description: 'عرض الأدوية النشطة', url: '/prescriptions', icons: [{ src: 'icons/icon-96x96.png', sizes: '96x96' }] },
        ],
        screenshots: [
          { src: 'screenshots/home.png', sizes: '1080x1920', type: 'image/png', form_factor: 'narrow', label: 'الصفحة الرئيسية' },
          { src: 'screenshots/wide-home.png', sizes: '1920x1080', type: 'image/png', form_factor: 'wide', label: 'لوحة المعلومات' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.gula\.health\/api\/v1\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'gula-api-cache',
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 7 },
              networkTimeoutSeconds: 5,
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gula-images',
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.(?:googleapis|gstatic)\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'gula-fonts',
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
    port: 3000,
    host: true,
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
    sourcemap: true,
  },
});
