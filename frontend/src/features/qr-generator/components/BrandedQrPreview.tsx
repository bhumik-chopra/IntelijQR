import React, { useMemo } from "react";
import QRCode from "qrcode";

import type { QrDesign } from "../types/qrGenerator";

interface BrandedQrPreviewProps {
  value: string;
  design: QrDesign;
  logo: string | null;
  className?: string;
}

function isFinder(row: number, column: number, size: number): boolean {
  return (row < 7 && column < 7) || (row < 7 && column >= size - 7) || (row >= size - 7 && column < 7);
}

export const BrandedQrPreview: React.FC<BrandedQrPreviewProps> = ({ value, design, logo, className }) => {
  const matrix = useMemo(() => {
    try {
      return QRCode.create(value, { errorCorrectionLevel: design.error_correction }).modules;
    } catch {
      return null;
    }
  }, [design.error_correction, value]);

  if (!matrix) return null;
  const frameInset = design.frame_style === "none" ? 0 : 3.5;
  const textHeight = design.frame_style !== "none" && design.frame_text ? 9 : 0;
  const availableWidth = 100 - frameInset * 2;
  const availableHeight = 100 - frameInset * 2 - textHeight;
  const moduleSize = Math.min(availableWidth, availableHeight) / (matrix.size + design.margin * 2);
  const qrSize = moduleSize * (matrix.size + design.margin * 2);
  const left = (100 - qrSize) / 2;
  const top = frameInset + Math.max(0, (availableHeight - qrSize) / 2);
  const gradientCoordinates = design.gradient_direction === "horizontal"
    ? { x1: "0%", y1: "0%", x2: "100%", y2: "0%" }
    : design.gradient_direction === "vertical"
      ? { x1: "0%", y1: "0%", x2: "0%", y2: "100%" }
      : { x1: "0%", y1: "0%", x2: "100%", y2: "100%" };
  const modules: React.ReactNode[] = [];

  for (let row = 0; row < matrix.size; row += 1) {
    for (let column = 0; column < matrix.size; column += 1) {
      if (!matrix.get(row, column)) continue;
      const x = left + (design.margin + column) * moduleSize;
      const y = top + (design.margin + row) * moduleSize;
      const finder = isFinder(row, column, matrix.size);
      if (design.module_style === "dots" && !finder) {
        modules.push(<circle key={`${row}-${column}`} cx={x + moduleSize / 2} cy={y + moduleSize / 2} r={moduleSize * 0.42} fill={design.gradient_enabled ? "url(#brand-gradient)" : design.foreground_color} />);
      } else {
        modules.push(<rect key={`${row}-${column}`} x={x} y={y} width={moduleSize} height={moduleSize} rx={design.module_style === "rounded" && !finder ? moduleSize * 0.3 : 0} fill={design.gradient_enabled ? "url(#brand-gradient)" : design.foreground_color} />);
      }
    }
  }

  const logoSize = qrSize * 0.18;
  const logoX = left + (qrSize - logoSize) / 2;
  const logoY = top + (qrSize - logoSize) / 2;

  return (
    <svg id="qr-live-preview" viewBox="0 0 100 100" role="img" aria-label="QR code live preview" className={className}>
      <defs>
        <linearGradient id="brand-gradient" gradientUnits="userSpaceOnUse" {...gradientCoordinates}>
          <stop offset="0%" stopColor={design.foreground_color} />
          <stop offset="100%" stopColor={design.gradient_color} />
        </linearGradient>
      </defs>
      <rect width="100" height="100" fill={design.background_color} />
      {design.frame_style !== "none" && (
        <rect x="1.2" y="1.2" width="97.6" height="97.6" rx={design.frame_style === "rounded" ? 4 : 0} fill="none" stroke={design.foreground_color} strokeWidth="1.2" />
      )}
      {modules}
      {logo && (
        <>
          <rect x={logoX - 1.5} y={logoY - 1.5} width={logoSize + 3} height={logoSize + 3} rx="2" fill={design.background_color} />
          <image href={logo} x={logoX} y={logoY} width={logoSize} height={logoSize} preserveAspectRatio="xMidYMid meet" />
        </>
      )}
      {design.frame_style !== "none" && design.frame_text && (
        <text x="50" y="96" textAnchor="middle" fontSize="3.6" fontWeight="600" fontFamily="Inter, sans-serif" fill={design.foreground_color}>
          {design.frame_text}
        </text>
      )}
    </svg>
  );
};
