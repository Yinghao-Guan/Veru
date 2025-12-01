import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 24,
          // ✅ 更新：起始色改为 #2563EB (Blue-600)
          background: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          borderRadius: '20%',
          fontWeight: 800,
        }}
      >
        V
      </div>
    ),
    { ...size }
  );
}