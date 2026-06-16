/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        night: {
          900: '#0a0e1a',
          800: '#0f1628',
          700: '#151d36',
          600: '#1c2748',
        },
        fifa: {
          green: '#00d4aa',
          gold: '#ffd700',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
