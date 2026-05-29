import type { AssetSummary } from "../../../entities/asset/model/types";
import type { JobSummary } from "../../../entities/job/model/types";
import type { PolishSessionSummary } from "../../../entities/polish/model/types";
import type { ResumeSummary } from "../../../entities/resume/model/types";
import type { WeaknessSummary } from "../../../entities/weakness/model/types";

export const DASHBOARD_DATA_SOURCE_KEYS = ["resumes", "jobs", "polish_sessions", "assets", "weaknesses"] as const;
export const DASHBOARD_METRIC_KEYS = ["resume", "jobs", "progress", "mock"] as const;
export const DASHBOARD_ACTIVITY_SOURCE_KEYS = ["resume", "job", "polish_session", "asset", "weakness"] as const;

export type DashboardMetricKey = (typeof DASHBOARD_METRIC_KEYS)[number];
export type DashboardActivitySourceKey = (typeof DASHBOARD_ACTIVITY_SOURCE_KEYS)[number];
export type DashboardPriorityTone = "urgent" | "important" | "normal";
export type DashboardRouteTarget = "/resume" | "/job" | "/interview";

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

export type DashboardActivityStatus = {
  label: string;
  tone: "default" | "processing" | "success" | "warning" | "error";
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

function buildOverviewMetrics(input: DashboardDataInput): DashboardOverviewMetric[] {
  const incompleteResumeCount = input.resumes.filter(isResumeIncomplete).length;
  const boundJobCount = input.jobs.filter((job) => job.binding_summary.status === "bound").length;
  const submittedJobCount = input.jobs.filter(isSubmittedJob).length;
  const interviewingJobCount = input.jobs.filter(isInterviewingJob).length;
  const runningSessionCount = input.polishSessions.filter(isRunningSession).length;
  const endedSessionCount = input.polishSessions.filter(isEndedSession).length;

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
  const sourceCounts = {
    resumes: input.resumes.length,
    jobs: input.jobs.length,
    polish_sessions: input.polishSessions.length,
    assets: input.assets.length,
    weaknesses: input.weaknesses.length,
  };

  return {
    overviewMetrics: buildOverviewMetrics(input),
    todoItems: buildTodoItems(input),
    activityItems: buildActivityItems(input),
    sourceCounts,
    isSourceEmpty: Object.values(sourceCounts).every((count) => count === 0),
  };
}
