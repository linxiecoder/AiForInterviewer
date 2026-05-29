import type { AssetSummary } from "../../../entities/asset/model/types";
import type { JobSummary } from "../../../entities/job/model/types";
import type { PolishSessionSummary } from "../../../entities/polish/model/types";
import type { ResumeSummary } from "../../../entities/resume/model/types";
import type { WeaknessSummary } from "../../../entities/weakness/model/types";
import {
  buildDashboardData,
  DASHBOARD_ACTIVITY_SOURCE_KEYS,
  DASHBOARD_DATA_SOURCE_KEYS,
  DASHBOARD_METRIC_KEYS,
  type DashboardDataInput,
  type DashboardOverviewMetric,
  type DashboardTodoItem,
} from "./dashboardData";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type DashboardDataSourcesAreRealApis = Expect<
  Equal<
    typeof DASHBOARD_DATA_SOURCE_KEYS,
    readonly ["resumes", "jobs", "polish_sessions", "assets", "weaknesses"]
  >
>;
type DashboardMetricKeysAreStable = Expect<
  Equal<typeof DASHBOARD_METRIC_KEYS, readonly ["resume", "jobs", "progress", "mock"]>
>;
type DashboardActivitySourcesUseBusinessRecords = Expect<
  Equal<
    typeof DASHBOARD_ACTIVITY_SOURCE_KEYS,
    readonly ["resume", "job", "polish_session", "asset", "weakness"]
  >
>;
type DashboardMetricValuesAreNumeric = Expect<Equal<DashboardOverviewMetric["value"], number>>;
type DashboardTodosHaveRouteTargets = Expect<Equal<DashboardTodoItem["href"], "/resume" | "/job" | "/interview">>;

const versionRef = {
  resource_type: "resume",
  resource_id: "res_1",
  version_id: "res_ver_1",
} as const;

const sampleInput: DashboardDataInput = {
  now: new Date("2026-05-29T08:00:00.000Z"),
  resumes: [
    {
      resume_id: "res_1",
      title: "后端开发简历",
      updated_at: "2026-05-29T07:50:00.000Z",
      created_at: "2026-05-29T07:00:00.000Z",
      current_version_ref: versionRef,
      binding_eligible: false,
    } satisfies ResumeSummary,
  ],
  jobs: [
    {
      job_id: "job_1",
      title: "后端工程师",
      company: "示例公司",
      department: null,
      application_status: "draft",
      current_version_ref: { ...versionRef, resource_type: "job", resource_id: "job_1" },
      archived_at: null,
      binding_summary: {
        status: "bound",
        resume_job_binding_id: "bind_1",
        resume_id: "res_1",
        resume_title: "后端开发简历",
        bound_at: "2026-05-29T07:20:00.000Z",
      },
      latest_match_summary: { status: "match_not_generated" },
      status: "active",
      record_version: 1,
      created_at: "2026-05-29T07:10:00.000Z",
      updated_at: "2026-05-29T07:20:00.000Z",
    } satisfies JobSummary,
  ],
  polishSessions: [
    {
      id: "session_1",
      session_id: "session_1",
      title: "后端工程师模拟面试",
      mode: "polish",
      status: "ended",
      resume_job_binding_id: "bind_1",
      resume_id: "res_1",
      resume_version_id: "res_ver_1",
      job_id: "job_1",
      job_version_id: "job_ver_1",
      job_title: "后端工程师",
      job_company: "示例公司",
      resume_title: "后端开发简历",
      binding_label: "后端开发简历 / 后端工程师",
      report_id: null,
      report_status: "pending",
      report_generated_at: null,
      created_at: "2026-05-29T07:30:00.000Z",
      updated_at: "2026-05-29T07:40:00.000Z",
    } satisfies PolishSessionSummary,
  ],
  assets: [] satisfies AssetSummary[],
  weaknesses: [] satisfies WeaknessSummary[],
};

const sampleDashboardData = buildDashboardData(sampleInput);
const metricKeys: Array<DashboardOverviewMetric["key"]> = sampleDashboardData.overviewMetrics.map((item) => item.key);
const todoTargets: Array<DashboardTodoItem["href"]> = sampleDashboardData.todoItems.map((item) => item.href);

void metricKeys;
void todoTargets;
