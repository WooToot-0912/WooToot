import React, { useEffect, useRef, useState } from 'react';

interface WatermarkProps {
  text?: string;
  opacity?: number;
  fontSize?: number;
  gap?: number;
  showTimestamp?: boolean;
}

const Watermark: React.FC<WatermarkProps> = ({ 
  text = 'WooToot', 
  opacity = 0.08, 
  fontSize = 16,
  gap = 180,
  showTimestamp = true
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [timestamp] = useState(new Date().toLocaleString());

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const dpr = window.devicePixelRatio || 1;
      
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = `rgba(100, 100, 100, ${opacity})`;
      ctx.font = `${fontSize}px Inter, sans-serif`;
      
      const fullText = showTimestamp ? `${text} - ${timestamp}` : text;
      
      // 平铺绘制逻辑
      ctx.save();
      ctx.rotate((-25 * Math.PI) / 180);
      
      const stepX = gap;
      const stepY = gap / 1.5;
      
      // 扩大绘制范围以覆盖旋转后的空白
      for (let i = -width; i < width * 2; i += stepX) {
        for (let j = -height; j < height * 2; j += stepY) {
          ctx.fillText(fullText, i, j);
        }
      }
      ctx.restore();
    };

    draw();
    window.addEventListener('resize', draw);
    return () => window.removeEventListener('resize', draw);
  }, [text, opacity, fontSize, gap, showTimestamp, timestamp]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[99999]"
      style={{
        mixBlendMode: 'multiply'
      }}
    />
  );
};

export default Watermark;
