import type { AssetSummary } from "../../../entities/asset/model/types";
import type { JobSummary } from "../../../entities/job/model/types";
import type { PolishSessionSummary } from "../../../entities/polish/model/types";
import type { ResumeSummary } from "../../../entities/resume/model/types";
import type { WeaknessSummary } from "../../../entities/weakness/model/types";

export const DASHBOARD_DATA_SOURCE_KEYS = ["resumes", "jobs", "polish_sessions", "assets", "weaknesses"] as const;
export const DASHBOARD_METRIC_KEYS = ["resume", "jobs", "progress", "mock", "asset", "weakness"] as const;
export const DASHBOARD_ACTIVITY_SOURCE_KEYS = ["resume", "job", "polish_session", "asset", "weakness"] as const;

export type DashboardMetricKey = (typeof DASHBOARD_METRIC_KEYS)[number];
export type DashboardActivitySourceKey = (typeof DASHBOARD_ACTIVITY_SOURCE_KEYS)[number];
export type DashboardPriorityTone = "urgent" | "important" | "normal";
export type DashboardRouteTarget = "/resume" | "/job" | "/interview" | "/asset" | "/weakness";
export type DashboardSignalTone = "default" | "processing" | "success" | "warning" | "error";
export type DashboardLifecycleStepKey =
  | "resume"
  | "job"
  | "match"
  | "mock"
  | "review"
  | "weakness"
  | "training"
  | "asset";
export type DashboardReviewTrainingLoopStageKey =
  | "mock_interview"
  | "report_review"
  | "weakness"
  | "training"
  | "asset";

export type DashboardOverviewMetric = {
  key: DashboardMetricKey;
  title: string;
  value: number;
  hint: string;
  sourceLabel: string;
};

export type DashboardTodoItem = {
  key: string;
  title: string;
  count: number;
  priority: DashboardPriorityTone;
  description: string;
  actionLabel: string;
  href: DashboardRouteTarget;
};

export type DashboardPriorityItem = DashboardTodoItem & {
  sourceLabel: string;
};

export type DashboardLifecycleStep = {
  key: DashboardLifecycleStepKey;
  title: string;
  count: number;
  statusLabel: string;
  description: string;
  progressPercent: number;
  tone: DashboardSignalTone;
  href: DashboardRouteTarget;
};

export type DashboardReviewTrainingLoopStage = {
  key: DashboardReviewTrainingLoopStageKey;
  title: string;
  count: number;
  statusLabel: string;
  description: string;
  tone: DashboardSignalTone;
  href: DashboardRouteTarget;
};

export type DashboardRiskSignal = {
  key: string;
  title: string;
  severity: string;
  statusLabel: string;
  description: string;
  sourceLabel: string;
  actionLabel: string;
  href: DashboardRouteTarget;
};

export type DashboardQuickAction = {
  key: string;
  title: string;
  description: string;
  actionLabel: string;
  href: DashboardRouteTarget;
  primary?: boolean;
  disabledReason?: string;
};

export type DashboardActivityStatus = {
  label: string;
  tone: DashboardSignalTone;
};

export type DashboardActivityItem = {
  key: string;
  source: DashboardActivitySourceKey;
  title: string;
  status: DashboardActivityStatus;
  description: string;
  time: string;
  timestamp: string;
};

export type DashboardDataInput = {
  resumes: readonly ResumeSummary[];
  jobs: readonly JobSummary[];
  polishSessions: readonly PolishSessionSummary[];
  assets: readonly AssetSummary[];
  weaknesses: readonly WeaknessSummary[];
  now?: Date;
};

export type DashboardData = {
  overviewMetrics: DashboardOverviewMetric[];
  todoItems: DashboardTodoItem[];
  priorityItems: DashboardPriorityItem[];
  lifecycleSteps: DashboardLifecycleStep[];
  reviewTrainingLoop: DashboardReviewTrainingLoopStage[];
  riskSignals: DashboardRiskSignal[];
  quickActions: DashboardQuickAction[];
  activityItems: DashboardActivityItem[];
  sourceCounts: Record<(typeof DASHBOARD_DATA_SOURCE_KEYS)[number], number>;
  isSourceEmpty: boolean;
};

type ActivityCandidate = Omit<DashboardActivityItem, "time"> & {
  timeValue: number;
};

const DRAFT_APPLICATION_STATUSES = new Set(["", "draft", "not_applied", "unsubmitted", "pending_application"]);
const SUBMITTED_APPLICATION_STATUSES = new Set(["applied", "submitted", "delivered", "interviewing", "interview", "offer", "accepted", "rejected"]);
const INTERVIEWING_APPLICATION_STATUSES = new Set(["interviewing", "interview", "phone_screen", "onsite", "technical_interview", "hr_interview"]);
const RUNNING_SESSION_STATUSES = new Set(["running", "active", "created", "in_progress"]);
const ENDED_SESSION_STATUSES = new Set(["ended", "completed", "finished"]);
const GENERATED_REPORT_STATUSES = new Set(["generated", "completed", "ready"]);
const GENERATED_MATCH_STATUSES = new Set(["completed", "generated", "ready", "success"]);
const INACTIVE_WEAKNESS_STATUSES = new Set(["ignored", "resolved", "archived"]);
const HIGH_WEAKNESS_SEVERITIES = new Set(["critical", "high"]);
const ASSET_CANDIDATE_STATUSES = new Set(["asset_candidate_generated", "candidate", "pending", "pending_confirmation", "needs_confirmation"]);
const ASSET_CONFIRMED_STATUSES = new Set(["asset_confirmed", "confirmed", "ready"]);

function normalizeStatus(value: string | null | undefined): string {
  return String(value ?? "").trim().toLowerCase();
}

function safeTitle(value: string | null | undefined, fallback: string): string {
  const trimmed = String(value ?? "").trim();
  return trimmed || fallback;
}

function parseTimestamp(value: string | null | undefined): number | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? null : parsed;
}

function hasMeaningfulUpdate(createdAt: string | null | undefined, updatedAt: string | null | undefined): boolean {
  const created = parseTimestamp(createdAt);
  const updated = parseTimestamp(updatedAt);
  if (created === null || updated === null) {
    return false;
  }
  return updated - created > 60_000;
}

function formatRelativeTime(timestamp: number, now: Date): string {
  const diffMs = Math.max(0, now.getTime() - timestamp);
  const diffMinutes = Math.floor(diffMs / 60_000);
  if (diffMinutes < 1) {
    return "刚刚";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}小时前`;
  }
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) {
    return `${diffDays}天前`;
  }
  return new Date(timestamp).toLocaleDateString();
}

function priorityFromCount(count: number, urgentAt = 5, importantAt = 2): DashboardPriorityTone {
  if (count >= urgentAt) {
    return "urgent";
  }
  if (count >= importantAt) {
    return "important";
  }
  return "normal";
}

function progressPercent(done: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Math.min(100, Math.round((done / total) * 100));
}

function listNames(names: readonly string[]): string {
  const visibleNames = names.slice(0, 2);
  const suffix = names.length > visibleNames.length ? ` 等 ${names.length} 项` : "";
  return `${visibleNames.join("、")}${suffix}`;
}

function isResumeIncomplete(resume: ResumeSummary): boolean {
  return resume.binding_eligible === false || !safeTitle(resume.title, "").trim();
}

function isActiveJob(job: JobSummary): boolean {
  return job.archived_at === null && normalizeStatus(job.status) !== "archived";
}

function isDraftJob(job: JobSummary): boolean {
  return isActiveJob(job) && DRAFT_APPLICATION_STATUSES.has(normalizeStatus(job.application_status));
}

function isSubmittedJob(job: JobSummary): boolean {
  const status = normalizeStatus(job.application_status);
  return isActiveJob(job) && (SUBMITTED_APPLICATION_STATUSES.has(status) || !DRAFT_APPLICATION_STATUSES.has(status));
}

function isInterviewingJob(job: JobSummary): boolean {
  return isActiveJob(job) && INTERVIEWING_APPLICATION_STATUSES.has(normalizeStatus(job.application_status));
}

function isRunningSession(session: PolishSessionSummary): boolean {
  return RUNNING_SESSION_STATUSES.has(normalizeStatus(session.status));
}

function isEndedSession(session: PolishSessionSummary): boolean {
  return ENDED_SESSION_STATUSES.has(normalizeStatus(session.status));
}

function hasGeneratedReport(session: PolishSessionSummary): boolean {
  return Boolean(session.report_generated_at) || GENERATED_REPORT_STATUSES.has(normalizeStatus(session.report_status));
}

function hasGeneratedMatch(job: JobSummary): boolean {
  const match = job.latest_match_summary;
  return Boolean(match.analysis_id || match.generated_at) || GENERATED_MATCH_STATUSES.has(normalizeStatus(match.status));
}

function isActiveWeakness(weakness: WeaknessSummary): boolean {
  return weakness.archived_at == null && !INACTIVE_WEAKNESS_STATUSES.has(normalizeStatus(weakness.status));
}

function isHighSeverityWeakness(weakness: WeaknessSummary): boolean {
  return HIGH_WEAKNESS_SEVERITIES.has(normalizeStatus(weakness.severity));
}

function hasTrainingSuggestion(weakness: WeaknessSummary): boolean {
  return isActiveWeakness(weakness) && weakness.suggested_training_actions.length > 0;
}

function isCandidateAsset(asset: AssetSummary): boolean {
  return ASSET_CANDIDATE_STATUSES.has(normalizeStatus(asset.status));
}

function isConfirmedAsset(asset: AssetSummary): boolean {
  return ASSET_CONFIRMED_STATUSES.has(normalizeStatus(asset.status));
}

function severityRank(weakness: WeaknessSummary): number {
  const severity = normalizeStatus(weakness.severity);
  if (severity === "critical") {
    return 4;
  }
  if (severity === "high") {
    return 3;
  }
  if (severity === "medium") {
    return 2;
  }
  if (severity === "low") {
    return 1;
  }
  return 0;
}

function buildOverviewMetrics(input: DashboardDataInput): DashboardOverviewMetric[] {
  const incompleteResumeCount = input.resumes.filter(isResumeIncomplete).length;
  const boundJobCount = input.jobs.filter((job) => job.binding_summary.status === "bound").length;
  const submittedJobCount = input.jobs.filter(isSubmittedJob).length;
  const interviewingJobCount = input.jobs.filter(isInterviewingJob).length;
  const runningSessionCount = input.polishSessions.filter(isRunningSession).length;
  const endedSessionCount = input.polishSessions.filter(isEndedSession).length;
  const assetCandidateCount = input.assets.filter(isCandidateAsset).length;
  const confirmedAssetCount = input.assets.filter(isConfirmedAsset).length;
  const activeWeaknesses = input.weaknesses.filter(isActiveWeakness);
  const highWeaknessCount = activeWeaknesses.filter(isHighSeverityWeakness).length;

  return [
    {
      key: "resume",
      title: "简历管理",
      value: input.resumes.length,
      hint: incompleteResumeCount > 0 ? `待完善 ${incompleteResumeCount} 份` : `已创建 ${input.resumes.length} 份`,
      sourceLabel: "简历",
    },
    {
      key: "jobs",
      title: "目标岗位",
      value: input.jobs.length,
      hint: `已绑定 ${boundJobCount} 个岗位`,
      sourceLabel: "岗位",
    },
    {
      key: "progress",
      title: "投递进度",
      value: submittedJobCount,
      hint: interviewingJobCount > 0 ? `面试中 ${interviewingJobCount} 个` : `已投递 ${submittedJobCount} 个`,
      sourceLabel: "进展",
    },
    {
      key: "mock",
      title: "模拟面试",
      value: input.polishSessions.length,
      hint: runningSessionCount > 0 ? `运行中 ${runningSessionCount} 场` : `已完成 ${endedSessionCount} 场`,
      sourceLabel: "会话",
    },
    {
      key: "asset",
      title: "资产沉淀",
      value: input.assets.length,
      hint: assetCandidateCount > 0 ? `待确认 ${assetCandidateCount} 条` : `已确认 ${confirmedAssetCount} 条`,
      sourceLabel: "资产",
    },
    {
      key: "weakness",
      title: "薄弱项",
      value: activeWeaknesses.length,
      hint: highWeaknessCount > 0 ? `高严重度 ${highWeaknessCount} 项` : "暂无高严重度项",
      sourceLabel: "薄弱项",
    },
  ];
}

function buildTodoItems(input: DashboardDataInput): DashboardTodoItem[] {
  const incompleteResumes = input.resumes.filter(isResumeIncomplete);
  const draftJobs = input.jobs.filter(isDraftJob);
  const sessionBindingIds = new Set(input.polishSessions.map((session) => session.resume_job_binding_id).filter((bindingId) => bindingId.length > 0));
  const boundJobsWithoutSession = input.jobs.filter((job) => {
    const bindingId = job.binding_summary.resume_job_binding_id;
    return isActiveJob(job) && job.binding_summary.status === "bound" && typeof bindingId === "string" && bindingId.length > 0 && !sessionBindingIds.has(bindingId);
  });
  const reviewPendingSessions = input.polishSessions.filter((session) => isEndedSession(session) && !hasGeneratedReport(session));

  const items: DashboardTodoItem[] = [];

  if (incompleteResumes.length > 0) {
    items.push({
      key: "todo-resume",
      title: "待完善简历",
      count: incompleteResumes.length,
      priority: priorityFromCount(incompleteResumes.length, 3, 1),
      description: `${listNames(incompleteResumes.map((resume) => safeTitle(resume.title, resume.resume_id)))} 需要补全后再绑定岗位或进入模拟面试。`,
      actionLabel: "去完善",
      href: "/resume",
    });
  }

  if (draftJobs.length > 0) {
    items.push({
      key: "todo-apply",
      title: "待投递岗位",
      count: draftJobs.length,
      priority: priorityFromCount(draftJobs.length, 5, 2),
      description: `${listNames(draftJobs.map((job) => safeTitle(job.title, job.job_id)))} 仍处于未投递状态。`,
      actionLabel: "去投递",
      href: "/job",
    });
  }

  if (boundJobsWithoutSession.length > 0) {
    items.push({
      key: "todo-interview",
      title: "待模拟面试",
      count: boundJobsWithoutSession.length,
      priority: priorityFromCount(boundJobsWithoutSession.length, 3, 1),
      description: `${listNames(boundJobsWithoutSession.map((job) => safeTitle(job.title, job.job_id)))} 已绑定简历但尚未创建模拟面试。`,
      actionLabel: "开始练习",
      href: "/interview",
    });
  }

  if (reviewPendingSessions.length > 0) {
    items.push({
      key: "todo-review",
      title: "待复盘面试",
      count: reviewPendingSessions.length,
      priority: priorityFromCount(reviewPendingSessions.length, 3, 1),
      description: `${listNames(reviewPendingSessions.map((session) => safeTitle(session.title, session.session_id)))} 已结束但尚未生成复盘报告。`,
      actionLabel: "查看复盘",
      href: "/interview",
    });
  }

  return items;
}

function buildPriorityItems(input: DashboardDataInput, todoItems: DashboardTodoItem[]): DashboardPriorityItem[] {
  const activeWeaknesses = input.weaknesses.filter(isActiveWeakness);
  const highSeverityWeaknesses = activeWeaknesses.filter(isHighSeverityWeakness);
  const trainingWeaknesses = activeWeaknesses.filter(hasTrainingSuggestion);
  const candidateAssets = input.assets.filter(isCandidateAsset);
  const sourceLabelByTodoKey: Record<string, string> = {
    "todo-resume": "简历",
    "todo-apply": "岗位",
    "todo-interview": "模拟",
    "todo-review": "复盘",
  };

  const items: DashboardPriorityItem[] = todoItems.map((item) => ({
    ...item,
    sourceLabel: sourceLabelByTodoKey[item.key] ?? "任务",
  }));

  if (highSeverityWeaknesses.length > 0) {
    items.push({
      key: "priority-high-weakness",
      title: "高严重度薄弱项",
      count: highSeverityWeaknesses.length,
      priority: priorityFromCount(highSeverityWeaknesses.length, 3, 1),
      description: `${listNames(highSeverityWeaknesses.map((weakness) => safeTitle(weakness.title, weakness.weakness_id)))} 需要安排训练或复盘。`,
      actionLabel: "查看薄弱项",
      href: "/weakness",
      sourceLabel: "薄弱项",
    });
  } else if (trainingWeaknesses.length > 0) {
    items.push({
      key: "priority-training",
      title: "待训练薄弱项",
      count: trainingWeaknesses.length,
      priority: priorityFromCount(trainingWeaknesses.length, 4, 2),
      description: `${listNames(trainingWeaknesses.map((weakness) => safeTitle(weakness.title, weakness.weakness_id)))} 已有训练建议。`,
      actionLabel: "进入训练",
      href: "/weakness",
      sourceLabel: "训练",
    });
  }

  if (candidateAssets.length > 0) {
    items.push({
      key: "priority-assets",
      title: "待确认资产沉淀",
      count: candidateAssets.length,
      priority: priorityFromCount(candidateAssets.length, 4, 1),
      description: `${listNames(candidateAssets.map((asset) => safeTitle(asset.title, asset.asset_id)))} 来自报告、复盘或薄弱项，需要人工确认。`,
      actionLabel: "确认资产",
      href: "/asset",
      sourceLabel: "资产",
    });
  }

  const priorityOrder: Record<DashboardPriorityTone, number> = {
    urgent: 0,
    important: 1,
    normal: 2,
  };

  return items.sort((left, right) => {
    const priorityDiff = priorityOrder[left.priority] - priorityOrder[right.priority];
    if (priorityDiff !== 0) {
      return priorityDiff;
    }
    return right.count - left.count;
  });
}

function buildLifecycleSteps(input: DashboardDataInput): DashboardLifecycleStep[] {
  const incompleteResumeCount = input.resumes.filter(isResumeIncomplete).length;
  const activeJobs = input.jobs.filter(isActiveJob);
  const boundJobs = activeJobs.filter((job) => job.binding_summary.status === "bound");
  const matchedJobs = activeJobs.filter(hasGeneratedMatch);
  const runningSessions = input.polishSessions.filter(isRunningSession);
  const endedSessions = input.polishSessions.filter(isEndedSession);
  const pendingReviewSessions = input.polishSessions.filter((session) => isEndedSession(session) && !hasGeneratedReport(session));
  const reportReadySessions = input.polishSessions.filter(hasGeneratedReport);
  const activeWeaknesses = input.weaknesses.filter(isActiveWeakness);
  const trainingWeaknesses = activeWeaknesses.filter(hasTrainingSuggestion);
  const candidateAssets = input.assets.filter(isCandidateAsset);
  const confirmedAssets = input.assets.filter(isConfirmedAsset);
  const matchTotal = boundJobs.length > 0 ? boundJobs.length : activeJobs.length;

  return [
    {
      key: "resume",
      title: "简历",
      count: input.resumes.length,
      statusLabel: incompleteResumeCount > 0 ? `${incompleteResumeCount} 待补` : `${input.resumes.length} 份`,
      description: input.resumes.length > 0 ? "用于岗位绑定和模拟面试输入。" : "暂无简历，后续链路会显示 0。",
      progressPercent: progressPercent(input.resumes.length - incompleteResumeCount, input.resumes.length),
      tone: incompleteResumeCount > 0 ? "warning" : input.resumes.length > 0 ? "success" : "default",
      href: "/resume",
    },
    {
      key: "job",
      title: "岗位 / JD",
      count: activeJobs.length,
      statusLabel: boundJobs.length > 0 ? `已绑定 ${boundJobs.length}` : `${activeJobs.length} 个`,
      description: activeJobs.length > 0 ? "岗位与 JD 由现有岗位接口提供。" : "暂无岗位，无法进入匹配与面试准备。",
      progressPercent: progressPercent(boundJobs.length, activeJobs.length),
      tone: boundJobs.length > 0 ? "success" : activeJobs.length > 0 ? "warning" : "default",
      href: "/job",
    },
    {
      key: "match",
      title: "匹配分析",
      count: matchedJobs.length,
      statusLabel: matchTotal > 0 ? `${matchedJobs.length}/${matchTotal}` : "0",
      description: matchTotal > 0 ? "统计已生成匹配分析的岗位。" : "缺少已绑定岗位时显示 0。",
      progressPercent: progressPercent(matchedJobs.length, matchTotal),
      tone: matchedJobs.length > 0 ? "processing" : matchTotal > 0 ? "warning" : "default",
      href: "/job",
    },
    {
      key: "mock",
      title: "模拟面试",
      count: input.polishSessions.length,
      statusLabel: runningSessions.length > 0 ? `运行中 ${runningSessions.length}` : `${endedSessions.length} 已完成`,
      description: "来自模拟面试会话列表。",
      progressPercent: progressPercent(endedSessions.length, input.polishSessions.length),
      tone: runningSessions.length > 0 ? "processing" : input.polishSessions.length > 0 ? "success" : "default",
      href: "/interview",
    },
    {
      key: "review",
      title: "报告 / 复盘",
      count: pendingReviewSessions.length + reportReadySessions.length,
      statusLabel: pendingReviewSessions.length > 0 ? `待复盘 ${pendingReviewSessions.length}` : `报告 ${reportReadySessions.length}`,
      description: "已结束未生成报告的会话进入待复盘，已生成报告可从模拟面试入口查看。",
      progressPercent: progressPercent(reportReadySessions.length, endedSessions.length),
      tone: pendingReviewSessions.length > 0 ? "warning" : reportReadySessions.length > 0 ? "success" : "default",
      href: "/interview",
    },
    {
      key: "weakness",
      title: "薄弱项",
      count: activeWeaknesses.length,
      statusLabel: `${activeWeaknesses.length} 项`,
      description: "来自薄弱项接口，忽略已解决、已忽略和已归档项。",
      progressPercent: activeWeaknesses.length > 0 ? 100 : 0,
      tone: activeWeaknesses.some(isHighSeverityWeakness) ? "error" : activeWeaknesses.length > 0 ? "warning" : "default",
      href: "/weakness",
    },
    {
      key: "training",
      title: "训练",
      count: trainingWeaknesses.length,
      statusLabel: trainingWeaknesses.length > 0 ? `${trainingWeaknesses.length} 条建议` : "0",
      description: "基于薄弱项中的 suggested_training_actions 展示。",
      progressPercent: progressPercent(trainingWeaknesses.length, activeWeaknesses.length),
      tone: trainingWeaknesses.length > 0 ? "processing" : "default",
      href: "/weakness",
    },
    {
      key: "asset",
      title: "资产沉淀",
      count: input.assets.length,
      statusLabel: candidateAssets.length > 0 ? `待确认 ${candidateAssets.length}` : `已确认 ${confirmedAssets.length}`,
      description: "来自资产接口；候选资产仍需人工确认，不自动写入。",
      progressPercent: progressPercent(confirmedAssets.length, input.assets.length),
      tone: candidateAssets.length > 0 ? "warning" : input.assets.length > 0 ? "success" : "default",
      href: "/asset",
    },
  ];
}

function buildReviewTrainingLoop(input: DashboardDataInput): DashboardReviewTrainingLoopStage[] {
  const runningSessions = input.polishSessions.filter(isRunningSession);
  const endedSessions = input.polishSessions.filter(isEndedSession);
  const pendingReviewSessions = input.polishSessions.filter((session) => isEndedSession(session) && !hasGeneratedReport(session));
  const reportReadySessions = input.polishSessions.filter(hasGeneratedReport);
  const activeWeaknesses = input.weaknesses.filter(isActiveWeakness);
  const highWeaknesses = activeWeaknesses.filter(isHighSeverityWeakness);
  const trainingWeaknesses = activeWeaknesses.filter(hasTrainingSuggestion);
  const candidateAssets = input.assets.filter(isCandidateAsset);

  return [
    {
      key: "mock_interview",
      title: "模拟面试",
      count: input.polishSessions.length,
      statusLabel: runningSessions.length > 0 ? `运行中 ${runningSessions.length}` : `已完成 ${endedSessions.length}`,
      description: "练习记录来自 polishSessions。",
      tone: runningSessions.length > 0 ? "processing" : input.polishSessions.length > 0 ? "success" : "default",
      href: "/interview",
    },
    {
      key: "report_review",
      title: "报告 / 复盘",
      count: pendingReviewSessions.length + reportReadySessions.length,
      statusLabel: pendingReviewSessions.length > 0 ? `待复盘 ${pendingReviewSessions.length}` : `报告 ${reportReadySessions.length}`,
      description: `${reportReadySessions.length} 份报告可查看，${pendingReviewSessions.length} 场结束会话待复盘。`,
      tone: pendingReviewSessions.length > 0 ? "warning" : reportReadySessions.length > 0 ? "success" : "default",
      href: "/interview",
    },
    {
      key: "weakness",
      title: "薄弱项",
      count: activeWeaknesses.length,
      statusLabel: highWeaknesses.length > 0 ? `高严重度 ${highWeaknesses.length}` : `${activeWeaknesses.length} 项`,
      description: "从弱项列表沉淀可训练问题。",
      tone: highWeaknesses.length > 0 ? "error" : activeWeaknesses.length > 0 ? "warning" : "default",
      href: "/weakness",
    },
    {
      key: "training",
      title: "训练建议",
      count: trainingWeaknesses.length,
      statusLabel: trainingWeaknesses.length > 0 ? `${trainingWeaknesses.length} 条` : "0",
      description: "仅展示已有 suggested_training_actions 的薄弱项。",
      tone: trainingWeaknesses.length > 0 ? "processing" : "default",
      href: "/weakness",
    },
    {
      key: "asset",
      title: "资产沉淀",
      count: input.assets.length,
      statusLabel: candidateAssets.length > 0 ? `待确认 ${candidateAssets.length}` : `${input.assets.length} 条`,
      description: "资产来自 assets；候选内容必须人工确认。",
      tone: candidateAssets.length > 0 ? "warning" : input.assets.length > 0 ? "success" : "default",
      href: "/asset",
    },
  ];
}

function buildRiskSignals(input: DashboardDataInput): DashboardRiskSignal[] {
  return input.weaknesses
    .filter(isActiveWeakness)
    .sort((left, right) => {
      const rankDiff = severityRank(right) - severityRank(left);
      if (rankDiff !== 0) {
        return rankDiff;
      }
      const countDiff = right.occurrence_count - left.occurrence_count;
      if (countDiff !== 0) {
        return countDiff;
      }
      return (parseTimestamp(right.updated_at) ?? 0) - (parseTimestamp(left.updated_at) ?? 0);
    })
    .slice(0, 4)
    .map((weakness) => {
      const severity = normalizeStatus(weakness.severity) || "unknown";
      const evidenceCount = weakness.evidence_refs.length + weakness.source_refs.length;
      return {
        key: weakness.weakness_id,
        title: safeTitle(weakness.title, weakness.weakness_id),
        severity,
        statusLabel: severity === "critical" || severity === "high" ? "高严重度" : weakness.status,
        description: weakness.summary || `出现 ${weakness.occurrence_count} 次，需结合复盘或训练继续处理。`,
        sourceLabel: evidenceCount > 0 ? `${evidenceCount} 条证据` : `出现 ${weakness.occurrence_count} 次`,
        actionLabel: weakness.suggested_training_actions.length > 0 ? "训练该薄弱项" : "查看薄弱项",
        href: "/weakness",
      };
    });
}

function buildQuickActions(input: DashboardDataInput): DashboardQuickAction[] {
  const boundJobCount = input.jobs.filter((job) => isActiveJob(job) && job.binding_summary.status === "bound").length;
  const activeWeaknessCount = input.weaknesses.filter(isActiveWeakness).length;
  const reportReadyCount = input.polishSessions.filter(hasGeneratedReport).length;

  return [
    {
      key: "start-interview",
      title: "发起模拟面试",
      description: "进入现有模拟面试入口，不创建新路由。",
      actionLabel: "开始",
      href: "/interview",
      primary: true,
      disabledReason: boundJobCount === 0 ? "需要先完成简历与岗位绑定。" : undefined,
    },
    {
      key: "new-resume",
      title: "新增简历",
      description: "补充简历资料后可继续绑定岗位。",
      actionLabel: "进入简历",
      href: "/resume",
    },
    {
      key: "new-job",
      title: "新增岗位",
      description: "录入岗位 / JD 后可进行绑定和匹配分析。",
      actionLabel: "进入岗位",
      href: "/job",
    },
    {
      key: "review-report",
      title: "查看报告 / 复盘",
      description: "报告和复盘仍从模拟面试入口进入。",
      actionLabel: "查看",
      href: "/interview",
      disabledReason: input.polishSessions.length === 0 ? "暂无模拟面试记录。" : undefined,
    },
    {
      key: "weakness-training",
      title: "薄弱项训练",
      description: "基于已有薄弱项和训练建议处理。",
      actionLabel: "查看薄弱项",
      href: "/weakness",
      disabledReason: activeWeaknessCount === 0 ? "暂无薄弱项，可先完成模拟面试或匹配分析。" : undefined,
    },
    {
      key: "asset-library",
      title: "资产库",
      description: "查看已确认或待确认的沉淀资产。",
      actionLabel: "查看资产",
      href: "/asset",
      disabledReason: input.assets.length === 0 && reportReadyCount === 0 ? "暂无资产或可沉淀报告。" : undefined,
    },
  ];
}

function pushActivity(
  items: ActivityCandidate[],
  candidate: Omit<ActivityCandidate, "timeValue">,
): void {
  const timestamp = parseTimestamp(candidate.timestamp);
  if (timestamp === null) {
    return;
  }
  items.push({ ...candidate, timeValue: timestamp });
}

function buildActivityItems(input: DashboardDataInput): DashboardActivityItem[] {
  const now = input.now ?? new Date();
  const candidates: ActivityCandidate[] = [];

  for (const resume of input.resumes) {
    const updated = hasMeaningfulUpdate(resume.created_at, resume.updated_at);
    pushActivity(candidates, {
      key: `resume-${resume.resume_id}`,
      source: "resume",
      title: updated ? "简历更新" : "新增简历",
      status: { label: updated ? "已更新" : "新建", tone: updated ? "warning" : "success" },
      description: safeTitle(resume.title, resume.resume_id),
      timestamp: updated ? resume.updated_at : resume.created_at,
    });
  }

  for (const job of input.jobs) {
    const submitted = isSubmittedJob(job);
    const updated = hasMeaningfulUpdate(job.created_at, job.updated_at);
    pushActivity(candidates, {
      key: `job-${job.job_id}`,
      source: "job",
      title: submitted ? "投递进度更新" : updated ? "岗位更新" : "新增岗位",
      status: { label: submitted ? job.application_status : updated ? "已更新" : "新建", tone: submitted ? "processing" : updated ? "warning" : "success" },
      description: [safeTitle(job.title, job.job_id), job.company].filter(Boolean).join(" · "),
      timestamp: updated ? job.updated_at : job.created_at,
    });
  }

  for (const session of input.polishSessions) {
    const generatedAt = parseTimestamp(session.report_generated_at);
    if (generatedAt !== null) {
      pushActivity(candidates, {
        key: `polish-report-${session.session_id}`,
        source: "polish_session",
        title: "模拟面试报告生成",
        status: { label: "已生成", tone: "success" },
        description: session.binding_label || safeTitle(session.title, session.session_id),
        timestamp: session.report_generated_at ?? session.updated_at,
      });
      continue;
    }

    pushActivity(candidates, {
      key: `polish-${session.session_id}`,
      source: "polish_session",
      title: isEndedSession(session) ? "模拟面试完成" : "模拟面试更新",
      status: { label: isEndedSession(session) ? "待复盘" : session.status, tone: isEndedSession(session) ? "processing" : "default" },
      description: session.binding_label || safeTitle(session.title, session.session_id),
      timestamp: session.updated_at || session.created_at,
    });
  }

  for (const asset of input.assets) {
    const updated = hasMeaningfulUpdate(asset.created_at, asset.updated_at);
    pushActivity(candidates, {
      key: `asset-${asset.asset_id}`,
      source: "asset",
      title: updated ? "资产更新" : "新增资产",
      status: { label: updated ? "已更新" : "新建", tone: updated ? "warning" : "success" },
      description: safeTitle(asset.title, asset.asset_id),
      timestamp: updated ? asset.updated_at : asset.created_at,
    });
  }

  for (const weakness of input.weaknesses) {
    const updated = hasMeaningfulUpdate(weakness.created_at, weakness.updated_at);
    pushActivity(candidates, {
      key: `weakness-${weakness.weakness_id}`,
      source: "weakness",
      title: updated ? "薄弱项更新" : "新增薄弱项",
      status: { label: weakness.severity ?? weakness.status, tone: weakness.severity === "critical" || weakness.severity === "high" ? "error" : "warning" },
      description: safeTitle(weakness.title, weakness.weakness_id),
      timestamp: updated ? weakness.updated_at : weakness.created_at,
    });
  }

  return candidates
    .sort((left, right) => right.timeValue - left.timeValue)
    .slice(0, 8)
    .map(({ timeValue, ...item }) => ({
      ...item,
      time: formatRelativeTime(timeValue, now),
    }));
}

export function buildDashboardData(input: DashboardDataInput): DashboardData {
  const todoItems = buildTodoItems(input);
  const sourceCounts = {
    resumes: input.resumes.length,
    jobs: input.jobs.length,
    polish_sessions: input.polishSessions.length,
    assets: input.assets.length,
    weaknesses: input.weaknesses.length,
  };

  return {
    overviewMetrics: buildOverviewMetrics(input),
    todoItems,
    priorityItems: buildPriorityItems(input, todoItems),
    lifecycleSteps: buildLifecycleSteps(input),
    reviewTrainingLoop: buildReviewTrainingLoop(input),
    riskSignals: buildRiskSignals(input),
    quickActions: buildQuickActions(input),
    activityItems: buildActivityItems(input),
    sourceCounts,
    isSourceEmpty: Object.values(sourceCounts).every((count) => count === 0),
  };
}
