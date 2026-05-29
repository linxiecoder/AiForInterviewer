import { useCallback, useEffect, useState } from "react";
import { fetchAssets } from "../../../entities/asset/api/assetApi";
import { fetchJobs } from "../../../entities/job/api/jobApi";
import { fetchPolishSessions } from "../../../entities/polish/api/polishApi";
import { fetchResumeSummaries } from "../../../entities/resume/api/resumeApi";
import { fetchWeaknesses } from "../../../entities/weakness/api/weaknessApi";
import { isApiHttpError } from "../../../shared/api/errors";
import { buildDashboardData, type DashboardData } from "./dashboardData";

export type DashboardDataLoadState =
  | {
      status: "loading";
      data: null;
      error: null;
    }
  | {
      status: "error";
      data: null;
      error: string;
    }
  | {
      status: "ready";
      data: DashboardData;
      error: null;
    };

function toErrorMessage(error: unknown): string {
  if (isApiHttpError(error)) {
    return error.safeMessage;
  }
  if (error instanceof Error) {
    return error.message || "工作台数据加载失败";
  }
  return "工作台数据加载失败";
}

export function useDashboardData(): DashboardDataLoadState & { reload: () => Promise<void> } {
  const [state, setState] = useState<DashboardDataLoadState>({
    status: "loading",
    data: null,
    error: null,
  });

  const reload = useCallback(async () => {
    setState({ status: "loading", data: null, error: null });
    try {
      const [resumeState, jobs, polishSessions, assets, weaknesses] = await Promise.all([
        fetchResumeSummaries(),
        fetchJobs(),
        fetchPolishSessions(),
        fetchAssets(),
        fetchWeaknesses(),
      ]);

      if (resumeState.kind === "error") {
        throw new Error(resumeState.message);
      }

      setState({
        status: "ready",
        data: buildDashboardData({
          resumes: resumeState.resumes,
          jobs,
          polishSessions,
          assets,
          weaknesses,
        }),
        error: null,
      });
    } catch (error) {
      setState({ status: "error", data: null, error: toErrorMessage(error) });
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    ...state,
    reload,
  };
}
