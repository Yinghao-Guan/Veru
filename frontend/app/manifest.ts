import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Veru Audit',
    short_name: 'Veru',
    description: 'AI Hallucination Detector & Citation Auditor',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#4F46E5',
    icons: [
      {
        src: '/icon', // Next.js 会自动映射到我们刚才写的 icon.tsx
        sizes: 'any',
        type: 'image/png',
      },
    ],
  };
}