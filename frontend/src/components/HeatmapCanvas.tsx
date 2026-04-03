import { useEffect, useRef } from 'react';

type HeatmapCanvasProps = {
  grid: number[][];
  backgroundUrl: string;
};

function interpolateColor(value: number): [number, number, number] {
  const anchors = [
    { at: 0.0, rgb: [245, 252, 247] as [number, number, number] },
    { at: 0.2, rgb: [186, 228, 188] as [number, number, number] },
    { at: 0.4, rgb: [116, 196, 118] as [number, number, number] },
    { at: 0.65, rgb: [49, 163, 84] as [number, number, number] },
    { at: 0.85, rgb: [0, 109, 44] as [number, number, number] },
    { at: 1.0, rgb: [0, 68, 27] as [number, number, number] },
  ];

  for (let i = 0; i < anchors.length - 1; i += 1) {
    const left = anchors[i];
    const right = anchors[i + 1];
    if (value >= left.at && value <= right.at) {
      const range = right.at - left.at || 1;
      const t = (value - left.at) / range;
      return [
        Math.round(left.rgb[0] + (right.rgb[0] - left.rgb[0]) * t),
        Math.round(left.rgb[1] + (right.rgb[1] - left.rgb[1]) * t),
        Math.round(left.rgb[2] + (right.rgb[2] - left.rgb[2]) * t),
      ];
    }
  }

  return anchors[anchors.length - 1].rgb;
}

export default function HeatmapCanvas({ grid, backgroundUrl }: HeatmapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !grid || grid.length === 0) {
      return;
    }

    const rows = grid.length;
    const cols = grid[0].length;
    const values = grid.flat();
    const maxValue = Math.max(...values, 1);
    const minValue = Math.min(...values);

    const drawWidth = 960;
    const drawHeight = 480;
    canvas.width = drawWidth;
    canvas.height = drawHeight;

    const context = canvas.getContext('2d');
    if (!context) {
      return;
    }

    const offscreen = document.createElement('canvas');
    offscreen.width = cols;
    offscreen.height = rows;
    const offscreenContext = offscreen.getContext('2d');
    if (!offscreenContext) {
      return;
    }

    const imageData = offscreenContext.createImageData(cols, rows);

    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const index = (row * cols + col) * 4;
        const raw = grid[row][col];
        const value = (raw - minValue) / (maxValue - minValue || 1);
        const [r, g, b] = interpolateColor(value);
        imageData.data[index] = r;
        imageData.data[index + 1] = g;
        imageData.data[index + 2] = b;
        imageData.data[index + 3] = raw > 0 ? Math.floor(70 + 160 * value) : 0;
      }
    }

    offscreenContext.putImageData(imageData, 0, 0);

    context.clearRect(0, 0, drawWidth, drawHeight);
    context.imageSmoothingEnabled = true;
    context.drawImage(offscreen, 0, 0, drawWidth, drawHeight);

    context.strokeStyle = 'rgba(255, 255, 255, 0.22)';
    context.lineWidth = 1;
    for (let x = 0; x <= 12; x += 1) {
      const px = (x / 12) * drawWidth;
      context.beginPath();
      context.moveTo(px, 0);
      context.lineTo(px, drawHeight);
      context.stroke();
    }
    for (let y = 0; y <= 6; y += 1) {
      const py = (y / 6) * drawHeight;
      context.beginPath();
      context.moveTo(0, py);
      context.lineTo(drawWidth, py);
      context.stroke();
    }
  }, [grid]);

  const values = grid.flat();
  const maxValue = Math.max(...values, 0);
  const minValue = Math.min(...values, 0);

  return (
    <div className="heatmap-figure">
      <div className="heatmap-stage">
        <img src={backgroundUrl} alt="Tło mapy obszaru symulacji" className="heatmap-background" />
        <canvas ref={canvasRef} className="heatmap-canvas" aria-label="Mapa cieplna masy ropy" />
      </div>
      <div className="heatmap-legend">
        <span>masa niska</span>
        <div className="legend-gradient" aria-hidden="true" />
        <span>masa wysoka</span>
      </div>
      <div className="heatmap-scale">
        <span>min: {minValue.toFixed(2)}</span>
        <span>max: {maxValue.toFixed(2)}</span>
      </div>
      <div className="heatmap-coords">
        <span>lat: 25.5</span>
        <span>lat: 31.0</span>
        <span>lon: -98.5</span>
        <span>lon: -87.5</span>
      </div>
    </div>
  );
}