export type AnalyticsPeriod = "7d" | "30d" | "90d" | "12m";

export interface AnalyticsPoint {
  date: string;
  scans: number;
  unique_visitors: number;
}

export interface AnalyticsBreakdown {
  label: string;
  value: number;
  percentage: number;
}

export interface TopQrCode {
  id: string;
  label: string;
  scans: number;
  unique_visitors: number;
}

export interface RecentScanEvent {
  id: string;
  generation_id: string;
  qr_label: string;
  device_type: string;
  browser: string;
  operating_system: string;
  country: string;
  city: string;
  scanned_at: string;
}

export interface AnalyticsOverview {
  period: AnalyticsPeriod;
  starts_at: string;
  ends_at: string;
  total_scans: number;
  unique_visitors: number;
  previous_total_scans: number;
  scan_change_percentage: number | null;
  series: AnalyticsPoint[];
  devices: AnalyticsBreakdown[];
  browsers: AnalyticsBreakdown[];
  operating_systems: AnalyticsBreakdown[];
  countries: AnalyticsBreakdown[];
  cities: AnalyticsBreakdown[];
  top_qr_codes: TopQrCode[];
  recent_scans: RecentScanEvent[];
}
