import { ImageResponse } from 'next/og';

// 路由段配置
export const runtime = 'edge';

// 图片尺寸
export const size = {
  width: 32,
  height: 32,
};
export const contentType = 'image/png';

// 图片生成逻辑
export default function Icon() {
  return new ImageResponse(
    (
      // ImageResponse JSX 元素
      <div
        style={{
          fontSize: 24,
          background: 'linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          borderRadius: '20%', // 圆角矩形
          fontWeight: 800,
        }}
      >
        V
      </div>
    ),
    // ImageResponse 选项
    {
      ...size,
    }
  );
}