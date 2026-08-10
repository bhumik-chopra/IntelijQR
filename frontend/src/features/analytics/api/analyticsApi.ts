import { apiClient } from "../../../lib/api/client";
import type { AnalyticsOverview, AnalyticsPeriod } from "../types/analytics";


export const analyticsApi = {
  overview(period: AnalyticsPeriod, qrId?: string): Promise<AnalyticsOverview> {
    const query = new URLSearchParams({ period });
    if (qrId) query.set("qr_id", qrId);
    return apiClient.get<AnalyticsOverview>(`/analytics/overview?${query}`);
  },
};
