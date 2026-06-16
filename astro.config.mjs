import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://talesmiguel.dev',
  base: '/worldcup2026',
  integrations: [tailwind()],
  output: 'static',
});
