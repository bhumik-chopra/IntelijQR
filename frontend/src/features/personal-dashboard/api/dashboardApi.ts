import { apiClient } from "../../../lib/api/client";
import type { DashboardSummary } from "../types/dashboard";
export const dashboardApi = { summary: (): Promise<DashboardSummary> => apiClient.get<DashboardSummary>("/dashboard/summary") };
