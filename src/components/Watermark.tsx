import React, { useEffect, useRef } from 'react';

interface WatermarkProps {
  text?: string;
  opacity?: number;
  fontSize?: number;
  gap?: number;
}

const Watermark: React.FC<WatermarkProps> = ({ 
  text = 'WooToot', 
  opacity = 0.05, 
  fontSize = 20,
  gap = 150 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = `rgba(150, 150, 150, ${opacity})`;
      ctx.font = `${fontSize}px Arial`;
      ctx.rotate((-20 * Math.PI) / 180);

      for (let i = -width; i < width * 2; i += gap) {
        for (let j = -height; j < height * 2; j += gap) {
          ctx.fillText(text, i, j);
        }
      }
    };

    draw();
    window.addEventListener('resize', draw);
    return () => window.removeEventListener('resize', draw);
  }, [text, opacity, fontSize, gap]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 9999,
        mixBlendMode: 'multiply'
      }}
    />
  );
};

export default Watermark;
