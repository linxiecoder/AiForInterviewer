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
  type DashboardLifecycleStep,
  type DashboardOverviewMetric,
  type DashboardQuickAction,
  type DashboardReviewTrainingLoopStage,
  type DashboardRiskSignal,
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
  Equal<typeof DASHBOARD_METRIC_KEYS, readonly ["resume", "jobs", "progress", "mock", "asset", "weakness"]>
>;
type DashboardActivitySourcesUseBusinessRecords = Expect<
  Equal<
    typeof DASHBOARD_ACTIVITY_SOURCE_KEYS,
    readonly ["resume", "job", "polish_session", "asset", "weakness"]
  >
>;
type DashboardMetricValuesAreNumeric = Expect<Equal<DashboardOverviewMetric["value"], number>>;
type DashboardTodosHaveRouteTargets = Expect<Equal<DashboardTodoItem["href"], "/resume" | "/job" | "/interview" | "/asset" | "/weakness">>;
type DashboardReviewTrainingLoopUsesFixedStages = Expect<
  Equal<
    DashboardReviewTrainingLoopStage["key"],
    "mock_interview" | "report_review" | "weakness" | "training" | "asset"
  >
>;
type DashboardLifecycleIncludesReviewLoop = Expect<
  Equal<
    DashboardLifecycleStep["key"],
    "resume" | "job" | "match" | "mock" | "review" | "weakness" | "training" | "asset"
  >
>;
type DashboardRiskSignalsUseExistingRoutes = Expect<
  Equal<DashboardRiskSignal["href"], "/resume" | "/job" | "/interview" | "/asset" | "/weakness">
>;
type DashboardQuickActionsCanBeDisabled = Expect<Equal<DashboardQuickAction["disabledReason"], string | undefined>>;

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
  assets: [
    {
      asset_id: "asset_1",
      owner_id: "owner_1",
      status: "asset_candidate_generated",
      asset_type: "answer_pattern",
      title: "限流降级回答框架",
      summary: "来自模拟面试报告的候选资产",
      current_version_id: null,
      source_refs: [],
      evidence_refs: [],
      trace_refs: [],
      created_at: "2026-05-29T07:45:00.000Z",
      updated_at: "2026-05-29T07:45:00.000Z",
    } satisfies AssetSummary,
  ],
  weaknesses: [
    {
      weakness_id: "weakness_1",
      owner_id: "owner_1",
      status: "weakness_detected",
      title: "分布式一致性边界",
      summary: "回答缺少故障边界和取舍说明",
      severity: "high",
      confidence_level: "medium",
      dimension: "technical",
      source_refs: [],
      evidence_refs: [],
      trace_refs: [],
      occurrence_count: 2,
      suggested_training_actions: ["专项追问训练"],
      created_at: "2026-05-29T07:42:00.000Z",
      updated_at: "2026-05-29T07:42:00.000Z",
    } satisfies WeaknessSummary,
  ],
};

const sampleDashboardData = buildDashboardData(sampleInput);
const metricKeys: Array<DashboardOverviewMetric["key"]> = sampleDashboardData.overviewMetrics.map((item) => item.key);
const todoTargets: Array<DashboardTodoItem["href"]> = sampleDashboardData.todoItems.map((item) => item.href);
const reviewLoopStages: DashboardReviewTrainingLoopStage[] = sampleDashboardData.reviewTrainingLoop;
const riskSignals: DashboardRiskSignal[] = sampleDashboardData.riskSignals;
const lifecycleSteps: DashboardLifecycleStep[] = sampleDashboardData.lifecycleSteps;
const quickActions: DashboardQuickAction[] = sampleDashboardData.quickActions;

void metricKeys;
void todoTargets;
void reviewLoopStages;
void riskSignals;
void lifecycleSteps;
void quickActions;
