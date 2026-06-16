import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://wc26.talesmiguel.dev',
  integrations: [tailwind()],
  output: 'static',
});
