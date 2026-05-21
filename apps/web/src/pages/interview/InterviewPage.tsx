import {
  DownOutlined,
  CheckCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  RightOutlined,
  SearchOutlined,
  SendOutlined,
} from "@ant-design/icons";
import { Alert, Button, Card, Drawer, Form, Input, Popover, Progress, Select, Space, Table, Tag, Tooltip, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { useRouteController } from "../../app/routes/router";
import { fetchJobs } from "../../entities/job/api/jobApi";
import type { JobSummary } from "../../entities/job/model/types";
import {
  createPolishAnswer,
  createPolishFeedbackTask,
  createPolishSession,
  createPolishQuestionTask,
  fetchPolishSession,
  fetchPolishSessions,
  fetchPolishTopics,
  refreshPolishProgressTreeState,
} from "../../entities/polish/api/polishApi";
import type {
  CreatePolishSessionRequest,
  PolishQuestionSource,
  PolishRecommendedAction,
  PolishProgressTreeNode,
  PolishSessionAnswer,
  PolishSessionDetail,
  PolishSessionSummary,
  PolishTopic,
} from "../../entities/polish/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";
import { AppShell } from "../../widgets/app-shell/AppShell";
import styles from "./InterviewWorkbench.module.css";

export const INTERVIEW_CREATE_BUTTON_STATE = "enabled";
export const INTERVIEW_CREATE_ENTRY_KIND = "drawer";
export const INTERVIEW_SUPPORTED_MODES = [
  { value: "polish", label: "打磨模式 / Polish" },
] as const;
export const INTERVIEW_CREATE_MODE_FIELD_KEY = "mode";
export const INTERVIEW_CREATE_FIELD_KEYS = [
  "mode",
  "resume_job_binding_id",
  "topic_id",
  "custom_topic_text",
] as const;
export const INTERVIEW_CREATE_SUCCESS_ACTIONS = ["navigate_to_workbench"] as const;
export const INTERVIEW_CREATE_PENDING_LOG_EVENTS = [
  "polish_session_create_started",
  "polish_session_create_completed",
  "polish_session_create_failed",
] as const;
export const INTERVIEW_CREATE_PENDING_STATUS = {
  message: "正在创建模拟面试",
  logHint: "后端日志可搜索 polish_session_create_started / polish_session_create_completed / polish_session_create_failed。",
} as const;
export const INTERVIEW_LIST_HEADER_CONTROL_ORDER = ["actions", "search"] as const;
export const INTERVIEW_LIST_HEADER_TEXT_STATE = "removed" as const;
export const INTERVIEW_SEARCH_PLACEHOLDER = "搜索模拟面试名称、岗位、简历、主题" as const;
export const INTERVIEW_LIST_TABLE_COLUMN_WIDTHS = {
  title: 220,
  mode: 118,
  status: 96,
  binding_label: 280,
  topic: 240,
  updated_at: 168,
  actions: 88,
} as const;
export const INTERVIEW_LIST_TABLE_SCROLL_X = 1210 as const;
export const INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY = {
  overflow: "single_line_ellipsis",
  hover: "tooltip",
} as const;
export const INTERVIEW_SESSION_WORKBENCH_FIELDS = [
  "title",
  "mode",
  "status",
  "topic",
  "binding",
  "created_at",
  "updated_at",
] as const;
export const INTERVIEW_WORKBENCH_LAYOUT_AREAS = [
  "top_summary",
  "progress_panel",
  "conversation_panel",
  "feedback_accordion",
  "bottom_composer",
] as const;
export const INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS = {
  root: "interview-workbench-viewport",
  progressPanel: "interview-workbench-progress-panel",
  progressNodeList: "interview-workbench-progress-node-list",
  conversationPanel: "interview-workbench-conversation-panel",
  chatScroll: "interview-workbench-chat-scroll",
  composer: "interview-workbench-composer",
} as const;
export const INTERVIEW_WORKBENCH_SCROLL_REGIONS = ["progress_node_list", "chat_scroll"] as const;
export const INTERVIEW_PROGRESS_TREE_SCROLL_CLASS = "progressTreeScroll" as const;
export const INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT = "title_row_end" as const;
export const INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY = "text_only" as const;
export const INTERVIEW_WORKBENCH_HERO_ACTION_COPY = [
  "返回模拟面试列表",
  "复制模拟面试内容",
] as const;
export const INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY = ["模拟面试进度"] as const;
export const INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS = [
  "岗位",
  "简历",
  "当前节点",
  "进度",
  "当前节点表现",
] as const;
export const INTERVIEW_WORKBENCH_FEEDBACK_ITEMS = [
  "点评",
  "打分",
  "失分点评价",
  "参考回答",
  "考点解析",
  "技术原理扩展",
] as const;
export type WorkbenchMachineState =
  | "creatingQuestion"
  | "waitingAnswer"
  | "feedbackGenerating"
  | "feedbackReady"
  | "feedbackFailedAnswerSaved"
  | "progressRefreshFailed";
export const INTERVIEW_WORKBENCH_STATE_MACHINE: readonly WorkbenchMachineState[] = [
  "creatingQuestion",
  "waitingAnswer",
  "feedbackGenerating",
  "feedbackReady",
  "feedbackFailedAnswerSaved",
  "progressRefreshFailed",
] as const;
const WORKBENCH_MACHINE_STATE_COPY: Record<WorkbenchMachineState, { label: string; description: string; color: string }> = {
  creatingQuestion: { label: "正在生成题目", description: "题目生成中，请稍候。", color: "processing" },
  waitingAnswer: { label: "等待回答", description: "可以提交当前题目的下一轮回答。", color: "default" },
  feedbackGenerating: { label: "正在生成反馈", description: "回答已保存，正在生成点评和下一步建议。", color: "processing" },
  feedbackReady: { label: "反馈已生成", description: "本轮反馈和下一步建议已同步。", color: "success" },
  feedbackFailedAnswerSaved: { label: "反馈生成失败", description: "回答已保存，可重试生成反馈或继续补充回答。", color: "warning" },
  progressRefreshFailed: { label: "进展刷新失败", description: "题目、回答和反馈已保留，仅进展树状态刷新失败。", color: "warning" },
};
const NEXT_RECOMMENDED_ACTION_LABELS: Record<string, string> = {
  answer_again: "再答一版",
  continue_same_question: "继续打磨本题",
  generate_reference_answer: "查看参考回答",
  explain_knowledge_point: "查看考点解析",
  expand_technical_principle: "展开技术原理",
  generate_next_round_suggestion: "生成下一轮建议",
  generate_next_question: "生成下一题",
  provide_more_answer_detail: "补充回答细节",
};
export const INTERVIEW_WORKBENCH_NORMAL_STATE_FORBIDDEN_COPY = [
  "fake task boundary",
  "题目引用",
  "反馈引用",
  "评分类型",
  "生成问题",
  "保存答案",
  "生成反馈",
  "下一题",
  "完成",
  "resume_version_id",
  "job_version_id",
] as const;
export const INTERVIEW_WORKBENCH_PRIMARY_ACTIONS = ["send_answer"] as const;
export const INTERVIEW_WORKBENCH_DISABLED_ACTIONS = [] as const;
export const INTERVIEW_WORKBENCH_STATE_REGIONS = ["loading", "error", "not_found"] as const;
export const INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT = {
  system_question: "left",
  user_answer: "right",
} as const;
export const INTERVIEW_WORKBENCH_KEYBOARD_SHORTCUTS = {
  send_answer: "Ctrl+Enter",
} as const;
const WORKBENCH_PROGRESS_NODE_STATUS_TEXT = {
  completed: "已完成",
  in_progress: "进行中",
  pending: "未开始",
} as const;
export const INTERVIEW_PROGRESS_TREE_NODE_STATUS_LIGHT_TONES = {
  completed: "green",
  in_progress: "blue",
  pending: "orange",
} as const;
export const INTERVIEW_PROGRESS_TREE_NODE_STATUS_PLACEMENT = "node_row_trailing_status_light" as const;
type WorkbenchProgressNodeStatus = keyof typeof WORKBENCH_PROGRESS_NODE_STATUS_TEXT;
type WorkbenchProgressNodeKind = "group" | "node" | "question";
export type WorkbenchProgressNode = {
  key: string;
  kind: WorkbenchProgressNodeKind;
  title: string;
  status: WorkbenchProgressNodeStatus;
  detail?: string;
  nodeCode?: string | null;
  questionTargetRef?: string;
  children?: WorkbenchProgressNode[];
};

type ProgressTreeDisplayNode = PolishProgressTreeNode & {
  basis_type?: string | null;
  category?: string | null;
  common_loss_risks?: string[] | string | null;
  confidence_level?: string | null;
  depth_goal?: string | null;
  display_category_title?: string | null;
  display_title?: string | null;
  expected_answer_signals?: string[] | string | null;
  first_question?: string | null;
  follow_up_directions?: string[] | string | null;
  follow_up_focus?: string[] | string | null;
  grounding_status?: string | null;
  jd_basis?: string[] | string | null;
  low_confidence_flags?: string[] | string | null;
  node_code?: string | null;
  preparation_goal?: string | null;
  recommended_first_question?: string | null;
  red_flags?: string[] | string | null;
  related_match_gaps?: string[] | string | null;
  resume_signal?: string[] | string | null;
};

export const INTERVIEW_PROGRESS_TREE_CATEGORY_TITLE_BY_CATEGORY = {
  resume_deep_dive: "深度打磨类",
  jd_gap_learning: "补齐学习类",
} as const;
export const INTERVIEW_PROGRESS_TREE_OTHER_CATEGORY_TITLE = "其他打磨项";
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE = "当前节点上下文";
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_HEADER_LAYOUT = "label_and_node_title_same_row" as const;
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY = "请选择一个进展节点查看本轮训练目标。";
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY = {
  expand: "展开",
  collapse: "收起",
} as const;
export const INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT = "conversation_context_banner" as const;
export const INTERVIEW_PROGRESS_TREE_LEFT_LIST_FIELDS = [
  "category_header",
  "node_title",
  "node_status",
  "current_priority",
  "question_entry",
] as const;
export const INTERVIEW_PROGRESS_TREE_DETAIL_EMPTY_COPY = "该节点暂无完整详情，可先生成题目继续打磨。";
export const INTERVIEW_PROGRESS_TREE_DETAIL_UNSELECTED_COPY = INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY;

export type ProgressTreeNodeDetailViewModel = {
  progressNodeRef: string;
  title: string;
  nodeCode: string | null;
  categoryTitle: string | null;
  confidenceLevel: string | null;
  groundingStatus: string | null;
  depthRequirement: string | null;
  firstQuestion: string | null;
  followUpDirections: string[];
  answerSignals: string[];
  lossRisks: string[];
  resumeEvidence: string[];
  jobEvidence: string[];
  hasAnyDetail: boolean;
  emptyDescription?: string;
};

export type ProgressTreeContextBannerContent = {
  title: string | null;
  depthRequirement: string | null;
  followUpDirections: string[];
  lossRisks: string[];
  emptyDescription?: string;
};

type ProgressTreeContextBannerSectionKey =
  | "depth_requirement"
  | "follow_up_directions"
  | "loss_risks";

export type ProgressTreeContextBannerSection = {
  key: ProgressTreeContextBannerSectionKey;
  title: string;
  items: string[];
};

type InterviewListError = {
  message: string;
  details: string;
  unauthorized: boolean;
};

type InterviewCreateFormValues = {
  mode?: "polish";
  resume_job_binding_id?: string;
  topic_id?: string;
  custom_topic_text?: string;
};

export type PolishBindingOption = {
  resume_job_binding_id: string;
  label: string;
  resume_id: string;
  resume_title: string;
  job_id: string;
  job_title: string;
};

type InterviewCreateAvailability =
  | {
      kind: "loading";
      canSubmit: false;
      message: string;
      details: string;
    }
  | {
      kind: "error";
      canSubmit: false;
      message: string;
      details: string;
    }
  | {
      kind: "no_prerequisites";
      canSubmit: false;
      message: string;
      details: string;
    }
  | {
      kind: "ready";
      canSubmit: true;
      message: string;
      details: string;
    };

export function buildPolishBindingOptions(jobs: JobSummary[]): PolishBindingOption[] {
  return jobs.flatMap((job) => {
    const summary = job.binding_summary;
    if (summary.status !== "bound" || typeof summary.resume_job_binding_id !== "string") {
      return [];
    }

    const resumeId = summary.resume_id ?? "";
    const resumeTitle = summary.resume_title ?? resumeId;
    const company = job.company ? ` / ${job.company}` : "";
    return [
      {
        resume_job_binding_id: summary.resume_job_binding_id,
        label: `${job.title}${company} -> ${resumeTitle}`,
        resume_id: resumeId,
        resume_title: resumeTitle,
        job_id: job.job_id,
        job_title: job.title,
      },
    ];
  });
}

export function getInterviewCreateAvailability(params: {
  loading: true;
  error: string | null;
  bindingOptions: readonly PolishBindingOption[];
}): Extract<InterviewCreateAvailability, { kind: "loading" }>;
export function getInterviewCreateAvailability(params: {
  loading: false;
  error: string;
  bindingOptions: readonly PolishBindingOption[];
}): Extract<InterviewCreateAvailability, { kind: "error" }>;
export function getInterviewCreateAvailability(params: {
  loading: false;
  error: null;
  bindingOptions: readonly [];
}): Extract<InterviewCreateAvailability, { kind: "no_prerequisites" }>;
export function getInterviewCreateAvailability(params: {
  loading: false;
  error: null;
  bindingOptions: readonly [PolishBindingOption, ...PolishBindingOption[]];
}): Extract<InterviewCreateAvailability, { kind: "ready" }>;
export function getInterviewCreateAvailability(params: {
  loading: boolean;
  error: string | null;
  bindingOptions: readonly PolishBindingOption[];
}): InterviewCreateAvailability;
export function getInterviewCreateAvailability(params: {
  loading: boolean;
  error: string | null;
  bindingOptions: readonly PolishBindingOption[];
}): InterviewCreateAvailability {
  if (params.loading) {
    return {
      kind: "loading",
      canSubmit: false,
      message: "正在读取可用绑定关系",
      details: "需要先确认当前账号下是否存在已绑定的简历与岗位。",
    };
  }
  if (params.error !== null) {
    return {
      kind: "error",
      canSubmit: false,
      message: "创建前置数据加载失败",
      details: params.error,
    };
  }
  if (params.bindingOptions.length === 0) {
    return {
      kind: "no_prerequisites",
      canSubmit: false,
      message: "暂时无法发起模拟面试",
      details: "模拟面试需要先完成一组简历与岗位绑定。请先到简历页关联岗位，或到岗位页创建岗位后再绑定简历。",
    };
  }
  return {
    kind: "ready",
    canSubmit: true,
    message: "可以发起模拟面试",
    details: "选择一组简历与岗位绑定后即可创建打磨模式会话。",
  };
}

export function buildPolishSessionCreateRequest(values: InterviewCreateFormValues): CreatePolishSessionRequest {
  const payload: CreatePolishSessionRequest = {
    resume_job_binding_id: values.resume_job_binding_id?.trim() ?? "",
  };
  const topicId = values.topic_id?.trim();
  const customTopicText = values.custom_topic_text?.trim();

  if (topicId) {
    payload.topic_id = topicId;
  }
  if (customTopicText) {
    payload.custom_topic_text = customTopicText;
  }

  return payload;
}

export function buildPolishSessionPath<const TSessionId extends string>(sessionId: TSessionId): `/interview/${TSessionId}` {
  return `/interview/${encodeURIComponent(sessionId)}` as `/interview/${TSessionId}`;
}

export function buildInterviewCreatePendingDescription(elapsedSeconds: number): string {
  const safeElapsedSeconds = Math.max(0, Math.floor(elapsedSeconds));
  return `已等待 ${safeElapsedSeconds} 秒，正在创建会话并生成进展树。耗时较长时请勿重复点击；${INTERVIEW_CREATE_PENDING_STATUS.logHint}`;
}

export function filterPolishSessionsBySearch(
  sessions: readonly PolishSessionSummary[],
  rawKeyword: string,
): PolishSessionSummary[] {
  const keyword = rawKeyword.trim().toLowerCase();
  if (keyword.length === 0) {
    return [...sessions];
  }

  return sessions.filter((session) =>
    [
      session.title,
      session.mode,
      session.status,
      session.binding_label,
      session.job_title,
      session.job_company,
      session.resume_title,
      session.topic_id,
      session.subtopic_id,
      session.custom_topic_text_summary,
      session.session_id,
    ].some((value) => (value ?? "").toLowerCase().includes(keyword)),
  );
}

function toDisplayDate(raw: string): string {
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }
  return date.toLocaleString();
}

function toModeLabel(mode: string): string {
  if (mode === "polish") {
    return "打磨模式 / Polish";
  }
  return mode;
}

function renderInterviewListEllipsisText(value: string, options: { strong?: boolean } = {}) {
  const displayValue = value.trim() || "-";
  return (
    <Tooltip title={displayValue} placement="topLeft">
      <Typography.Text strong={options.strong} className={styles.tableCellText}>
        {displayValue}
      </Typography.Text>
    </Tooltip>
  );
}

function parseListError(error: unknown): InterviewListError {
  if (isApiHttpError(error)) {
    if (error.status === 401) {
      return {
        message: "请先登录后查看模拟面试列表",
        details: "当前会话已过期或尚未登录。",
        unauthorized: true,
      };
    }
    return {
      message: "模拟面试列表加载失败",
      details: error.safeMessage || "服务端返回异常，请稍后重试。",
      unauthorized: false,
    };
  }
  if (error instanceof Error) {
    return {
      message: "模拟面试列表加载失败",
      details: error.message || "网络请求异常，请稍后重试。",
      unauthorized: false,
    };
  }
  return {
    message: "模拟面试列表加载失败",
    details: "未知错误，请稍后重试。",
    unauthorized: false,
  };
}

function parseWorkbenchError(error: unknown): InterviewListError {
  if (isApiHttpError(error)) {
    if (error.status === 401) {
      return {
        message: "请先登录后进入模拟面试工作台",
        details: "当前会话已过期或尚未登录。",
        unauthorized: true,
      };
    }
    if (error.status === 404) {
      return {
        message: "模拟面试不存在或不可访问",
        details: "这场模拟面试可能已删除，或不属于当前账号。",
        unauthorized: false,
      };
    }
    return {
      message: "模拟面试工作台加载失败",
      details: error.safeMessage || "服务端返回异常，请稍后重试。",
      unauthorized: false,
    };
  }
  if (error instanceof Error) {
    return {
      message: "模拟面试工作台加载失败",
      details: error.message || "网络请求异常，请稍后重试。",
      unauthorized: false,
    };
  }
  return {
    message: "模拟面试工作台加载失败",
    details: "未知错误，请稍后重试。",
    unauthorized: false,
  };
}

function toCreateErrorMessage(error: unknown): string {
  if (isApiHttpError(error)) {
    if (error.status === 401) {
      return "请先登录后再发起模拟面试。";
    }
    if (error.status === 404) {
      return "选择的简历与岗位绑定不存在或不可访问，请刷新后重新选择。";
    }
    if (error.status === 422) {
      return error.safeMessage || "创建信息未通过校验，请检查必填项。";
    }
    return error.safeMessage || "模拟面试创建失败，请稍后重试。";
  }
  if (error instanceof Error) {
    return error.message || "模拟面试创建失败，请稍后重试。";
  }
  return "模拟面试创建失败，请稍后重试。";
}

export function normalizeInterviewTopicTitle(title: string): string {
  return normalizeProgressTreeDetailCopy(title);
}

function toNeutralOptionalTitle(title: string | null | undefined): string | null {
  return title ? normalizeInterviewTopicTitle(title) : null;
}

export function normalizeProgressTreeDetailCopy(value: string): string {
  return value
    .replaceAll("经历真实性与贡献拷问", "经历真实性与贡献边界")
    .replaceAll("P7", "高阶")
    .replaceAll("攻击", "追问")
    .replaceAll("拷问", "深入追问")
    .replaceAll("碾压", "深挖")
    .replaceAll("吊打", "对比强化")
    .replaceAll("火力", "追问强度")
    .replaceAll("红队", "反向检验")
    .replaceAll("必挂", "风险较高")
    .replaceAll("必过", "准备较充分")
    .replaceAll("压迫", "连续追问")
    .replaceAll("击穿", "发现薄弱点")
    .replaceAll("杀招", "关键方法");
}

function toSafeProgressTreeText(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? normalizeProgressTreeDetailCopy(trimmed) : null;
}

function toSafeProgressTreeTextList(value: string[] | string | null | undefined, limit?: number): string[] {
  const rawItems = Array.isArray(value) ? value : value ? [value] : [];
  const safeItems = rawItems
    .map((item) => toSafeProgressTreeText(item))
    .filter((item): item is string => item !== null);
  return typeof limit === "number" ? safeItems.slice(0, limit) : safeItems;
}

function firstSafeProgressTreeTextList(
  ...values: Array<string[] | string | null | undefined>
): string[] {
  for (const value of values) {
    const safeItems = toSafeProgressTreeTextList(value);
    if (safeItems.length > 0) {
      return safeItems;
    }
  }
  return [];
}

function firstSafeProgressTreeText(
  ...values: Array<string | null | undefined>
): string | null {
  for (const value of values) {
    const safeValue = toSafeProgressTreeText(value);
    if (safeValue !== null) {
      return safeValue;
    }
  }
  return null;
}

function toSessionDisplayName(session: PolishSessionDetail): string {
  return (
    session.custom_topic_text_summary ||
    toNeutralOptionalTitle(session.subtopic_ref?.title) ||
    toNeutralOptionalTitle(session.topic_ref?.title) ||
    session.session_id
  );
}

function toTopicLabel(session: PolishSessionDetail): string {
  const topic = toNeutralOptionalTitle(session.topic_ref?.title) ?? session.topic_ref?.topic_id;
  const subtopic = toNeutralOptionalTitle(session.subtopic_ref?.title) ?? session.subtopic_ref?.subtopic_id;
  if (topic && subtopic) {
    return `${topic} / ${subtopic}`;
  }
  return topic ?? subtopic ?? session.custom_topic_text_summary ?? "未选择";
}

const WORKBENCH_NODE_SCORE_PLACEHOLDER = "--";
const FALLBACK_JOB_TITLE = "未命名岗位";
const FALLBACK_RESUME_TITLE = "未命名简历";
const FALLBACK_QUESTION_TEXT = "题干缺失";
const FALLBACK_ANSWER_TEXT = "暂无回答";
const FALLBACK_FEEDBACK_TEXT = "本轮反馈尚未生成";
const QUESTION_SOURCE_TYPE_LABELS: Record<PolishQuestionSource["source_type"], string> = {
  job_requirement: "岗位",
  resume_evidence: "简历",
  progress_node: "进展节点",
  missing_point: "缺口",
  history_feedback: "历史反馈",
};

function renderQuestionSourcePopover(source: PolishQuestionSource) {
  return (
    <div className={styles.questionSourcePopover}>
      <div className={styles.questionSourceHeader}>
        <Typography.Text strong>{source.title}</Typography.Text>
        <Tag className={styles.questionSourceTypeTag}>{QUESTION_SOURCE_TYPE_LABELS[source.source_type]}</Tag>
      </div>
      <Typography.Paragraph className={styles.questionSourceExcerpt}>
        {source.excerpt}
      </Typography.Paragraph>
    </div>
  );
}

function renderQuestionTextWithSources(
  questionText: string,
  questionSources: readonly PolishQuestionSource[],
) {
  if (questionSources.length === 0) {
    return questionText;
  }
  const sourceByIndex = new Map(questionSources.map((source) => [source.index, source]));
  return questionText.split(/(\[\d+\])/g).map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match === null) {
      return <span key={`${part}-${index}`}>{part}</span>;
    }
    const source = sourceByIndex.get(Number(match[1]));
    if (source === undefined) {
      return <span key={`${part}-${index}`}>{part}</span>;
    }
    return (
      <Popover
        key={`${part}-${index}`}
        content={renderQuestionSourcePopover(source)}
        placement="top"
        trigger={["hover", "click"]}
      >
        <button
          type="button"
          className={styles.questionSourceRef}
          aria-label={`查看题目来源 ${source.index}`}
        >
          [{source.index}]
        </button>
      </Popover>
    );
  });
}

export function buildPolishSessionClipboardMarkdown(session: PolishSessionDetail): string {
  const rows: string[] = [
    "# 模拟面试内容",
    "",
    `岗位：${session.job_title || FALLBACK_JOB_TITLE}`,
    `简历：${session.resume_title || FALLBACK_RESUME_TITLE}`,
    `主题：${toTopicLabel(session)}`,
    `创建时间：${toDisplayDate(session.created_at)}`,
    `更新时间：${toDisplayDate(session.updated_at)}`,
    "",
  ];

  if (session.turns.length === 0) {
    rows.push("## 题目与反馈");
    rows.push("- 尚未生成题目记录");
    return rows.join("\n");
  }

  rows.push("## 题目与反馈");
  session.turns.forEach((turn, turnIndex) => {
    const questionText = turn.question_text || FALLBACK_QUESTION_TEXT;
    rows.push(`### 第${turnIndex + 1}轮`);
    rows.push(`- 题干：${questionText}`);
    if (turn.answers.length === 0) {
      rows.push(`- 回答：${FALLBACK_ANSWER_TEXT}`);
      rows.push(`- 反馈：${FALLBACK_FEEDBACK_TEXT}`);
      return;
    }

    turn.answers.forEach((answer, answerIndex) => {
      const answerText = answer.answer_text || FALLBACK_ANSWER_TEXT;
      const feedbackText = answer.feedback_text || FALLBACK_FEEDBACK_TEXT;
      rows.push(`- 回答 ${answerIndex + 1}：${answerText}`);
      rows.push(`- 反馈 ${answerIndex + 1}：${feedbackText}`);
    });
  });

  return rows.join("\n");
}

type PolishSessionReadableHeader = PolishSessionDetail | PolishSessionSummary;

export function toDisplayJobTitle(session: PolishSessionReadableHeader): string {
  return session.job_title || FALLBACK_JOB_TITLE;
}

export function toDisplayResumeTitle(session: PolishSessionReadableHeader): string {
  return session.resume_title || FALLBACK_RESUME_TITLE;
}

export function resolveCurrentQuestionId(session: PolishSessionDetail): string | null {
  const lastTurn = getLatestTurn(session);
  return lastTurn?.question_id || null;
}

function getLatestTurn(session: PolishSessionDetail) {
  return session.turns.length > 0 ? session.turns[session.turns.length - 1] : null;
}

function getLatestAnswer(session: PolishSessionDetail): PolishSessionAnswer | null {
  const latestTurn = getLatestTurn(session);
  if (latestTurn === null || latestTurn.answers.length === 0) {
    return null;
  }
  return latestTurn.answers[latestTurn.answers.length - 1];
}

function answerHasGeneratedFeedback(answer: PolishSessionAnswer | null): boolean {
  return Boolean(answer?.feedback_id || answer?.feedback_created_at || answer?.feedback_payload?.status === "generated");
}

export function resolveSessionCurrentProgressNodeRef(session: PolishSessionDetail): string | null {
  return (
    session.active_question_progress_node_ref ??
    getLatestTurn(session)?.progress_node_ref ??
    session.current_node_progress_node_ref ??
    session.progress_tree_state.current_priority?.progress_node_ref ??
    null
  );
}

function toCurrentNodeLabel(session: PolishSessionDetail): string {
  const currentNodeRef = resolveSessionCurrentProgressNodeRef(session);
  const node = findProgressTreeNodeByRef(session.progress_tree_plan.nodes, currentNodeRef);
  return node !== null ? resolveProgressNodeTitle(node) : session.progress_tree_state.current_priority?.title ?? "待生成";
}

export function deriveWorkbenchMachineState(params: {
  session: PolishSessionDetail | null;
  creatingQuestion: boolean;
  feedbackGenerating: boolean;
  failureState: WorkbenchMachineState | null;
}): WorkbenchMachineState {
  if (params.creatingQuestion) {
    return "creatingQuestion";
  }
  if (params.feedbackGenerating) {
    return "feedbackGenerating";
  }
  if (params.failureState === "feedbackFailedAnswerSaved" || params.failureState === "progressRefreshFailed") {
    return params.failureState;
  }
  const latestAnswer = params.session === null ? null : getLatestAnswer(params.session);
  return answerHasGeneratedFeedback(latestAnswer) ? "feedbackReady" : "waitingAnswer";
}

export function buildWorkbenchProgressNodes(
  session: PolishSessionDetail,
): WorkbenchProgressNode[] {
  const questionNodes = buildQuestionProgressNodes(session);
  const activeNodeRef = resolveSessionCurrentProgressNodeRef(session);
  const stateByRef = new Map(
    session.progress_tree_state.node_states.map((nodeState) => [
      nodeState.progress_node_ref,
      normalizeProgressNodeStatus(nodeState.status),
    ]),
  );
  const groupedNodes = new Map<string, WorkbenchProgressNode[]>();
  for (const node of dedupeProgressTreeNodesByRef(session.progress_tree_plan.nodes)) {
    const groupTitle = resolveProgressNodeCategoryTitle(node);
    const workbenchNode = toWorkbenchProgressNode({
      node,
      stateByRef,
      activeNodeRef,
      questionNodes,
      level: 1,
    });
    groupedNodes.set(groupTitle, [...(groupedNodes.get(groupTitle) ?? []), workbenchNode]);
  }

  return Array.from(groupedNodes.entries()).map(([groupTitle, children]) => ({
    key: `progress-group:${groupTitle}`,
    kind: "group",
    title: groupTitle,
    status: summarizeProgressNodeStatus(children),
    detail: `${children.length}`,
    children,
  }));
}

function buildQuestionProgressNodes(session: PolishSessionDetail): WorkbenchProgressNode[] {
  const questionNodes: WorkbenchProgressNode[] = [];
  for (const [turnIndex, turn] of session.turns.entries()) {
    const shortQuestion = turn.question_text.length > 24 ? `${turn.question_text.slice(0, 21)}...` : turn.question_text;
    questionNodes.push({
      key: `question:${turn.question_id}`,
      kind: "question",
      title: `题目 ${turnIndex + 1}`,
      status: turn.answers.length > 0 ? "completed" : "in_progress",
      detail: shortQuestion,
    });
  }
  return questionNodes;
}

function dedupeProgressTreeNodesByRef(nodes: readonly PolishProgressTreeNode[]): PolishProgressTreeNode[] {
  const seenRefs = new Set<string>();
  const dedupedNodes: PolishProgressTreeNode[] = [];
  for (const node of nodes) {
    if (seenRefs.has(node.progress_node_ref)) {
      continue;
    }
    seenRefs.add(node.progress_node_ref);
    dedupedNodes.push(node);
  }
  return dedupedNodes;
}

function flattenProgressTreePlanNodes(nodes: readonly PolishProgressTreeNode[]): PolishProgressTreeNode[] {
  return nodes.flatMap((node) => [
    node,
    ...flattenProgressTreePlanNodes(node.children ?? []),
  ]);
}

function findProgressTreeNodeByRef(
  nodes: readonly PolishProgressTreeNode[],
  progressNodeRef: string | null | undefined,
): PolishProgressTreeNode | null {
  if (!progressNodeRef) {
    return null;
  }
  return flattenProgressTreePlanNodes(nodes).find((node) => node.progress_node_ref === progressNodeRef) ?? null;
}

function resolveProgressNodeCategoryTitle(node: PolishProgressTreeNode): string {
  const displayNode = node as ProgressTreeDisplayNode;
  const displayCategoryTitle = toSafeProgressTreeText(displayNode.display_category_title);
  if (displayCategoryTitle) {
    return displayCategoryTitle;
  }
  if (displayNode.category === "resume_deep_dive" || displayNode.category === "jd_gap_learning") {
    return INTERVIEW_PROGRESS_TREE_CATEGORY_TITLE_BY_CATEGORY[displayNode.category];
  }
  return INTERVIEW_PROGRESS_TREE_OTHER_CATEGORY_TITLE;
}

function resolveProgressNodeTitle(node: PolishProgressTreeNode): string {
  const displayTitle = toSafeProgressTreeText((node as ProgressTreeDisplayNode).display_title);
  return displayTitle || toSafeProgressTreeText(node.title) || node.progress_node_ref;
}

export function resolveProgressTreeDetailNodeRef(
  session: PolishSessionDetail,
  selectedProgressNodeRef: string | null,
): string | null {
  const planNodes = flattenProgressTreePlanNodes(session.progress_tree_plan.nodes);
  if (selectedProgressNodeRef && planNodes.some((node) => node.progress_node_ref === selectedProgressNodeRef)) {
    return selectedProgressNodeRef;
  }

  const currentPriorityRef = session.progress_tree_state.current_priority?.progress_node_ref ?? null;
  if (currentPriorityRef && planNodes.some((node) => node.progress_node_ref === currentPriorityRef)) {
    return currentPriorityRef;
  }

  return planNodes[0]?.progress_node_ref ?? null;
}

export function buildProgressTreeNodeDetailViewModel(
  session: PolishSessionDetail,
  progressNodeRef: string | null,
): ProgressTreeNodeDetailViewModel | null {
  const node = findProgressTreeNodeByRef(session.progress_tree_plan.nodes, progressNodeRef);
  if (node === null) {
    return null;
  }

  const detailNode = node as ProgressTreeDisplayNode;
  const depthRequirement = firstSafeProgressTreeText(
    detailNode.depth_goal,
    node.expected_capability,
    detailNode.preparation_goal,
  );
  const firstQuestion = firstSafeProgressTreeText(
    detailNode.first_question,
    detailNode.recommended_first_question,
  );
  const followUpDirections = firstSafeProgressTreeTextList(
    detailNode.follow_up_focus,
    detailNode.follow_up_directions,
  ).slice(0, 5);
  const answerSignals = toSafeProgressTreeTextList(detailNode.expected_answer_signals);
  const lossRisks = firstSafeProgressTreeTextList(detailNode.common_loss_risks, detailNode.red_flags);
  const resumeSignal = toSafeProgressTreeTextList(detailNode.resume_signal);
  const resumeEvidence = resumeSignal.length > 0 ? resumeSignal : toSafeProgressTreeTextList(node.related_resume_evidence, 2);
  const jdBasis = toSafeProgressTreeTextList(detailNode.jd_basis);
  const jobEvidence = jdBasis.length > 0 ? jdBasis : toSafeProgressTreeTextList(node.related_job_requirements, 2);
  const hasAnyDetail = Boolean(
    depthRequirement ||
      firstQuestion ||
      followUpDirections.length > 0 ||
      answerSignals.length > 0 ||
      lossRisks.length > 0 ||
      resumeEvidence.length > 0 ||
      jobEvidence.length > 0,
  );

  return {
    progressNodeRef: node.progress_node_ref,
    title: resolveProgressNodeTitle(node),
    nodeCode: toSafeProgressTreeText(detailNode.node_code),
    categoryTitle: resolveProgressNodeCategoryTitle(node),
    confidenceLevel: toSafeProgressTreeText(detailNode.confidence_level),
    groundingStatus: toSafeProgressTreeText(detailNode.grounding_status),
    depthRequirement,
    firstQuestion,
    followUpDirections,
    answerSignals,
    lossRisks,
    resumeEvidence,
    jobEvidence,
    hasAnyDetail,
    emptyDescription: hasAnyDetail ? undefined : INTERVIEW_PROGRESS_TREE_DETAIL_EMPTY_COPY,
  };
}

export function buildProgressTreeContextBannerContent(
  session: PolishSessionDetail,
  progressNodeRef: string | null,
): ProgressTreeContextBannerContent {
  const node = findProgressTreeNodeByRef(session.progress_tree_plan.nodes, progressNodeRef);
  if (node === null) {
    return {
      title: null,
      depthRequirement: null,
      followUpDirections: [],
      lossRisks: [],
      emptyDescription: INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY,
    };
  }

  const displayNode = node as ProgressTreeDisplayNode;
  const currentPriority =
    session.progress_tree_state.current_priority?.progress_node_ref === node.progress_node_ref
      ? session.progress_tree_state.current_priority
      : null;
  const title =
    firstSafeProgressTreeText(displayNode.display_title, node.title, currentPriority?.title) ?? node.progress_node_ref;
  const depthRequirement = firstSafeProgressTreeText(
    displayNode.depth_goal,
    node.expected_capability,
    displayNode.preparation_goal,
    currentPriority?.expected_capability,
  );
  const followUpDirections = firstSafeProgressTreeTextList(
    displayNode.follow_up_focus,
    displayNode.follow_up_directions,
  ).slice(0, 5);
  const lossRisks = firstSafeProgressTreeTextList(displayNode.common_loss_risks, displayNode.red_flags);

  return {
    title,
    depthRequirement,
    followUpDirections,
    lossRisks,
  };
}

export function shouldShowProgressTreeContextBannerToggle(content: ProgressTreeContextBannerContent): boolean {
  return buildProgressTreeContextBannerExpandedSections(content).length > 0;
}

function buildProgressTreeContextBannerListSection(
  key: ProgressTreeContextBannerSectionKey,
  title: string,
  items: readonly string[],
): ProgressTreeContextBannerSection[] {
  return items.length > 0 ? [{ key, title, items: [...items] }] : [];
}

export function buildProgressTreeContextBannerExpandedSections(
  content: ProgressTreeContextBannerContent,
): ProgressTreeContextBannerSection[] {
  return [
    ...buildProgressTreeContextBannerListSection(
      "depth_requirement",
      "深度要求",
      content.depthRequirement ? [content.depthRequirement] : [],
    ),
    ...buildProgressTreeContextBannerListSection("follow_up_directions", "连续追问方向", content.followUpDirections),
    ...buildProgressTreeContextBannerListSection("loss_risks", "常见失分风险", content.lossRisks),
  ];
}

function toWorkbenchProgressNode(params: {
  node: PolishProgressTreeNode;
  stateByRef: Map<string, WorkbenchProgressNodeStatus>;
  activeNodeRef: string | null;
  questionNodes: WorkbenchProgressNode[];
  level: number;
}): WorkbenchProgressNode {
  const children = params.node.children.map((childNode) =>
    toWorkbenchProgressNode({
      node: childNode,
      stateByRef: params.stateByRef,
      activeNodeRef: params.activeNodeRef,
      questionNodes: params.questionNodes,
      level: params.level + 1,
    }),
  );
  const shouldAttachQuestions = params.node.progress_node_ref === params.activeNodeRef && params.questionNodes.length > 0;
  const mergedChildren = shouldAttachQuestions ? [...children, ...params.questionNodes] : children;
  const displayNode = params.node as ProgressTreeDisplayNode;
  return {
    key: params.node.progress_node_ref,
    kind: "node",
    title: resolveProgressNodeTitle(params.node),
    status: params.stateByRef.get(params.node.progress_node_ref) ?? summarizeProgressNodeStatus(mergedChildren),
    nodeCode: toSafeProgressTreeText(displayNode.node_code),
    questionTargetRef: params.node.progress_node_ref,
    children: mergedChildren.length > 0 ? mergedChildren : undefined,
  };
}

export function getWorkbenchProgressNodeQuestionTargetRef(node: WorkbenchProgressNode | null | undefined): string | null {
  return node?.kind === "node" ? node.questionTargetRef ?? node.key : null;
}

export function resolveProgressTreeSelectedNodeRefAfterClick(
  node: WorkbenchProgressNode | null | undefined,
  currentSelectedProgressNodeRef: string | null,
): string | null {
  return node?.kind === "node" ? node.key : currentSelectedProgressNodeRef;
}

function normalizeProgressNodeStatus(status: string): WorkbenchProgressNodeStatus {
  if (status === "completed" || status === "in_progress" || status === "pending") {
    return status;
  }
  return "pending";
}

function summarizeProgressNodeStatus(children: readonly WorkbenchProgressNode[]): WorkbenchProgressNodeStatus {
  if (children.some((child) => child.status === "in_progress")) {
    return "in_progress";
  }
  if (children.length > 0 && children.every((child) => child.status === "completed")) {
    return "completed";
  }
  return "pending";
}

function flattenWorkbenchProgressNodes(
  nodes: readonly WorkbenchProgressNode[],
): WorkbenchProgressNode[] {
  return nodes.flatMap((node) => [
    node,
    ...(node.children ? flattenWorkbenchProgressNodes(node.children) : []),
  ]);
}

function progressNodeStatusLabel(status: WorkbenchProgressNodeStatus): string {
  return WORKBENCH_PROGRESS_NODE_STATUS_TEXT[status];
}

export function getWorkbenchProgressNodeStatusLightTone(
  status: WorkbenchProgressNodeStatus,
): typeof INTERVIEW_PROGRESS_TREE_NODE_STATUS_LIGHT_TONES[WorkbenchProgressNodeStatus] {
  return INTERVIEW_PROGRESS_TREE_NODE_STATUS_LIGHT_TONES[status];
}

export function buildWorkbenchProgressNodeTitleMeta(node: WorkbenchProgressNode) {
  return {
    title: node.title,
    statusLabel: progressNodeStatusLabel(node.status),
    statusLightTone: getWorkbenchProgressNodeStatusLightTone(node.status),
  };
}

export function shouldSubmitAnswerFromKeyboard(event: {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  isComposing?: boolean;
}): boolean {
  return event.key === "Enter" && Boolean(event.ctrlKey) && !event.shiftKey && !event.altKey && !event.isComposing;
}

export function resolveCurrentWorkbenchProgressNodeKey(
  nodes: readonly WorkbenchProgressNode[],
  preferredProgressNodeRef: string | null = null,
): string | null {
  const flattenedNodes = flattenWorkbenchProgressNodes(nodes).filter((node) => node.kind === "node");
  if (preferredProgressNodeRef && flattenedNodes.some((node) => node.key === preferredProgressNodeRef)) {
    return preferredProgressNodeRef;
  }
  for (const node of flattenedNodes) {
    if (node.status === "in_progress") {
      return node.key;
    }
  }
  for (const node of flattenedNodes) {
    if (node.status === "pending") {
      return node.key;
    }
  }
  return flattenedNodes.length > 0 ? flattenedNodes[flattenedNodes.length - 1].key : null;
}

export function collectDefaultExpandedProgressNodeKeys(nodes: readonly WorkbenchProgressNode[]): string[] {
  const expandedKeys: string[] = [];
  for (const node of nodes) {
    if (node.kind === "group" && node.children && node.children.length > 0) {
      expandedKeys.push(node.key);
    } else if (node.children && node.children.length > 0 && node.status !== "pending") {
      expandedKeys.push(node.key);
    }
    if (node.children) {
      expandedKeys.push(...collectDefaultExpandedProgressNodeKeys(node.children));
    }
  }
  return Array.from(new Set(expandedKeys));
}

function buildWorkbenchHeaderChips(session: PolishSessionDetail, progressPercent: number) {
  return [
    { key: "job", label: "岗位", value: toDisplayJobTitle(session) },
    { key: "resume", label: "简历", value: toDisplayResumeTitle(session) },
    { key: "node", label: "当前节点", value: toCurrentNodeLabel(session) },
    { key: "progress", label: "进度", value: `${progressPercent}%` },
    { key: "score", label: "当前节点表现", value: WORKBENCH_NODE_SCORE_PLACEHOLDER },
  ] as const;
}

function logInterviewCreateEvent(event: string, payload: Record<string, unknown>): void {
  if (!["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    return;
  }
  console.info(`[interview:create] ${event}`, payload);
}

function getAnswerNextRecommendedActions(answer: PolishSessionAnswer): PolishRecommendedAction[] {
  const actions = answer.next_recommended_actions ?? answer.feedback_payload?.next_recommended_actions ?? [];
  return actions.filter((action, index) => actions.indexOf(action) === index);
}

function toNextRecommendedActionLabel(action: PolishRecommendedAction): string {
  return NEXT_RECOMMENDED_ACTION_LABELS[action] ?? action;
}

export function InterviewPage() {
  const { navigate } = useRouteController();
  const [sessions, setSessions] = useState<PolishSessionSummary[]>([]);
  const [sessionSearchKeyword, setSessionSearchKeyword] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<InterviewListError | null>(null);
  const [createOpen, setCreateOpen] = useState<boolean>(false);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [topics, setTopics] = useState<PolishTopic[]>([]);
  const [createPrerequisiteLoading, setCreatePrerequisiteLoading] = useState<boolean>(false);
  const [createPrerequisiteError, setCreatePrerequisiteError] = useState<string | null>(null);
  const [topicLoadError, setTopicLoadError] = useState<string | null>(null);
  const [createSubmitLoading, setCreateSubmitLoading] = useState<boolean>(false);
  const [createStartedAt, setCreateStartedAt] = useState<number | null>(null);
  const [createElapsedSeconds, setCreateElapsedSeconds] = useState<number>(0);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createForm] = Form.useForm<InterviewCreateFormValues>();

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await fetchPolishSessions();
      setSessions(list);
    } catch (loadError) {
      setError(parseListError(loadError));
    } finally {
      setLoading(false);
    }
  };

  const loadCreatePrerequisites = async () => {
    setCreatePrerequisiteLoading(true);
    setCreatePrerequisiteError(null);
    setTopicLoadError(null);
    try {
      const [jobResult, topicResult] = await Promise.allSettled([
        fetchJobs(),
        fetchPolishTopics(),
      ]);
      if (jobResult.status === "fulfilled") {
        setJobs(jobResult.value);
      } else {
        setJobs([]);
        setCreatePrerequisiteError(toCreateErrorMessage(jobResult.reason));
      }
      if (topicResult.status === "fulfilled") {
        setTopics(topicResult.value);
      } else {
        setTopics([]);
        setTopicLoadError("固定主题列表加载失败，请稍后重试。");
      }
    } finally {
      setCreatePrerequisiteLoading(false);
    }
  };

  useEffect(() => {
    void loadSessions();
  }, []);

  useEffect(() => {
    if (!createSubmitLoading || createStartedAt === null) {
      setCreateElapsedSeconds(0);
      return undefined;
    }

    const updateElapsedSeconds = () => {
      setCreateElapsedSeconds(Math.floor((Date.now() - createStartedAt) / 1000));
    };
    updateElapsedSeconds();
    const timer = window.setInterval(updateElapsedSeconds, 1000);
    return () => window.clearInterval(timer);
  }, [createStartedAt, createSubmitLoading]);

  const bindingOptions = useMemo(() => buildPolishBindingOptions(jobs), [jobs]);
  const filteredSessions = useMemo(
    () => filterPolishSessionsBySearch(sessions, sessionSearchKeyword),
    [sessions, sessionSearchKeyword],
  );
  const createAvailability = useMemo(
    () =>
      getInterviewCreateAvailability({
        loading: createPrerequisiteLoading,
        error: createPrerequisiteError,
        bindingOptions,
      }),
    [bindingOptions, createPrerequisiteError, createPrerequisiteLoading],
  );
  const openCreateEntry = () => {
    setCreateOpen(true);
    setCreateError(null);
    createForm.resetFields();
    void loadCreatePrerequisites();
  };

  const closeCreateEntry = () => {
    if (createSubmitLoading) {
      return;
    }
    setCreateOpen(false);
    setCreateError(null);
    createForm.resetFields();
  };

  const submitCreate = async () => {
    if (!createAvailability.canSubmit) {
      setCreateError(createAvailability.details);
      return;
    }

    let values: InterviewCreateFormValues;
    try {
      values = await createForm.validateFields();
    } catch {
      return;
    }

    const requestPayload = buildPolishSessionCreateRequest(values);
    const startedAt = Date.now();
    setCreateSubmitLoading(true);
    setCreateStartedAt(startedAt);
    setCreateError(null);
    logInterviewCreateEvent("polish_session_create_submit_started", {
      resume_job_binding_id: requestPayload.resume_job_binding_id,
      topic_id: requestPayload.topic_id ?? null,
      has_custom_topic_text: Boolean(requestPayload.custom_topic_text),
    });
    try {
      const created = await createPolishSession(requestPayload);
      logInterviewCreateEvent("polish_session_create_submit_succeeded", {
        session_id: created.session_id,
        elapsed_ms: Date.now() - startedAt,
      });
      message.success(`模拟面试「${toSessionDisplayName(created)}」已创建。`);
      setCreateOpen(false);
      createForm.resetFields();
      navigate(buildPolishSessionPath(created.session_id));
    } catch (submitError) {
      logInterviewCreateEvent("polish_session_create_submit_failed", {
        elapsed_ms: Date.now() - startedAt,
        error: submitError instanceof Error ? submitError.message : "unknown",
      });
      setCreateError(toCreateErrorMessage(submitError));
    } finally {
      setCreateSubmitLoading(false);
      setCreateStartedAt(null);
    }
  };

  const columns: ColumnsType<PolishSessionSummary> = useMemo(
    () => [
      {
        title: "名称",
        dataIndex: "title",
        key: "title",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.title,
        ellipsis: true,
        render: (value: string) => renderInterviewListEllipsisText(value, { strong: true }),
      },
      {
        title: "模式",
        dataIndex: "mode",
        key: "mode",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.mode,
        ellipsis: true,
        render: (value: string) => <Tag color="blue">{toModeLabel(value)}</Tag>,
      },
      {
        title: "状态",
        dataIndex: "status",
        key: "status",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.status,
        ellipsis: true,
        render: (value: string) => <Tag color={value === "running" ? "green" : "default"}>{value}</Tag>,
      },
      {
        title: "绑定关系",
        dataIndex: "binding_label",
        key: "binding_label",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.binding_label,
        ellipsis: true,
        render: (_: unknown, record) => {
          const value = record.binding_label || `${toDisplayJobTitle(record)} / ${toDisplayResumeTitle(record)}`;
          return renderInterviewListEllipsisText(value);
        },
      },
      {
        title: "主题",
        key: "topic",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.topic,
        ellipsis: true,
        render: (_, record) => renderInterviewListEllipsisText(record.title || "未选择"),
      },
      {
        title: "更新时间",
        dataIndex: "updated_at",
        key: "updated_at",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.updated_at,
        ellipsis: true,
        render: (value: string) => renderInterviewListEllipsisText(toDisplayDate(value)),
      },
      {
        title: "操作",
        key: "actions",
        width: INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.actions,
        fixed: "right",
        render: (_, record) => (
          <Button
            type="link"
            size="small"
            icon={<RightOutlined />}
            onClick={() => navigate(buildPolishSessionPath(record.session_id))}
          >
            进入
          </Button>
        ),
      },
    ],
    [navigate],
  );

  return (
    <AppShell>
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Card>
          <div
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              flexWrap: "wrap",
            }}
          >
            <Space wrap>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateEntry}>
                发起模拟面试
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  void loadSessions();
                }}
              >
                刷新
              </Button>
            </Space>
            <Input.Search
              allowClear
              enterButton={<SearchOutlined aria-label="搜索" />}
              value={sessionSearchKeyword}
              onChange={(event) => {
                setSessionSearchKeyword(event.target.value);
              }}
              onSearch={(value) => {
                setSessionSearchKeyword(value);
              }}
              placeholder={INTERVIEW_SEARCH_PLACEHOLDER}
              style={{ width: 360, maxWidth: "100%", marginLeft: "auto" }}
            />
          </div>
        </Card>

        <Card>
          {loading ? (
            <LoadingState compact message="模拟面试列表加载中..." />
          ) : error !== null ? (
            <ErrorState
              compact
              message={error.message}
              details={error.details}
              actionLabel={error.unauthorized ? "前往登录" : "重试"}
              onAction={() => {
                if (error.unauthorized) {
                  navigate("/login", { replace: true });
                } else {
                  void loadSessions();
                }
              }}
            />
          ) : sessions.length === 0 ? (
            <EmptyState
              compact
              title="暂无模拟面试记录"
              description="当前账号下还没有打磨模式会话。"
              reason="点击右上角「发起模拟面试」，选择已绑定的简历与岗位后创建第一场模拟面试。"
            />
          ) : (
            <Table<PolishSessionSummary>
              rowKey="id"
              columns={columns}
              dataSource={filteredSessions}
              pagination={{
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
              }}
              size="small"
              tableLayout="fixed"
              scroll={{ x: INTERVIEW_LIST_TABLE_SCROLL_X }}
            />
          )}
        </Card>

        <Drawer
          title="发起模拟面试"
          width={560}
          open={createOpen}
          onClose={closeCreateEntry}
          closable={!createSubmitLoading}
          keyboard={!createSubmitLoading}
          maskClosable={!createSubmitLoading}
          destroyOnClose
          extra={
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              loading={createSubmitLoading}
              disabled={!createAvailability.canSubmit || createSubmitLoading}
              onClick={() => {
                void submitCreate();
              }}
            >
              创建
            </Button>
          }
        >
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            {createAvailability.kind === "error" ? (
              <Alert
                type="error"
                showIcon
                message={createAvailability.message}
                description={createAvailability.details}
                action={
                  <Button size="small" onClick={() => void loadCreatePrerequisites()}>
                    重试
                  </Button>
                }
              />
            ) : null}
            {createAvailability.kind === "no_prerequisites" ? (
              <Alert
                type="warning"
                showIcon
                message={createAvailability.message}
                description={createAvailability.details}
                action={
                  <Space>
                    <Button size="small" onClick={() => navigate("/resume")}>
                      去简历页
                    </Button>
                    <Button size="small" onClick={() => navigate("/job")}>
                      去岗位页
                    </Button>
                  </Space>
                }
              />
            ) : null}
            {topicLoadError !== null ? (
              <Alert type="warning" showIcon message="主题暂不可用" description={topicLoadError} />
            ) : null}
            {createSubmitLoading ? (
              <Alert
                type="info"
                showIcon
                message={INTERVIEW_CREATE_PENDING_STATUS.message}
                description={buildInterviewCreatePendingDescription(createElapsedSeconds)}
              />
            ) : null}
            {createError !== null ? <Alert type="error" showIcon message={createError} /> : null}

            <Form<InterviewCreateFormValues>
              form={createForm}
              layout="vertical"
              initialValues={{ mode: "polish" }}
            >
              <Form.Item
                label="模拟模式"
                name={INTERVIEW_CREATE_MODE_FIELD_KEY}
                extra="当前 F5-M4 后端 Core 只开放打磨模式；完整多模式选择会在后续阶段接入真实 contract 后开放。"
              >
                <Select
                  disabled
                  options={INTERVIEW_SUPPORTED_MODES.map((mode) => ({
                    value: mode.value,
                    label: mode.label,
                  }))}
                />
              </Form.Item>

              <Form.Item
                label="简历与岗位绑定"
                name="resume_job_binding_id"
                rules={[{ required: true, message: "请选择一组已绑定的简历与岗位" }]}
              >
                <Select
                  loading={createPrerequisiteLoading}
                  disabled={!createAvailability.canSubmit || createSubmitLoading}
                  placeholder="选择一组简历与岗位绑定"
                  options={bindingOptions.map((option) => ({
                    value: option.resume_job_binding_id,
                    label: option.label,
                  }))}
                />
              </Form.Item>

              <Form.Item
                label="打磨主题"
                name="topic_id"
                rules={[{ required: true, message: "请选择 1 个模拟面试主题" }]}
              >
                <Select
                  disabled={topics.length === 0 || createSubmitLoading}
                  placeholder="选择 1 个模拟面试主题"
                  options={topics.map((topic) => ({
                    value: topic.topic_id,
                    label: normalizeInterviewTopicTitle(topic.title),
                    disabled: Boolean(topic.disabled_reason),
                  }))}
                />
              </Form.Item>

              <Form.Item
                label="自定义打磨目标"
                name="custom_topic_text"
                rules={[{ max: 240, message: "自定义打磨目标不能超过 240 个字符" }]}
              >
                <Input.TextArea
                  disabled={createSubmitLoading}
                  rows={4}
                  maxLength={240}
                  showCount
                  placeholder="例如：请重点打磨支付系统项目中的技术取舍表达"
                />
              </Form.Item>
            </Form>
          </Space>
        </Drawer>
      </Space>
    </AppShell>
  );
}

export function InterviewWorkbenchPage({ sessionId }: { sessionId: string }) {
  const { navigate } = useRouteController();
  const [session, setSession] = useState<PolishSessionDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<InterviewListError | null>(null);
  const [answerText, setAnswerText] = useState<string>("");
  const [answerError, setAnswerError] = useState<string | null>(null);
  const [creatingQuestion, setCreatingQuestion] = useState<boolean>(false);
  const [submittingAnswer, setSubmittingAnswer] = useState<boolean>(false);
  const [feedbackGenerating, setFeedbackGenerating] = useState<boolean>(false);
  const [workbenchFailureState, setWorkbenchFailureState] = useState<WorkbenchMachineState | null>(null);
  const [copyingSession, setCopyingSession] = useState<boolean>(false);
  const [expandedProgressNodeKeys, setExpandedProgressNodeKeys] = useState<Set<string>>(() => new Set());
  const [selectedProgressNodeRef, setSelectedProgressNodeRef] = useState<string | null>(null);
  const [isProgressNodeContextExpanded, setProgressNodeContextExpanded] = useState(false);

  const loadSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const detail = await fetchPolishSession(sessionId);
      setSession(detail);
    } catch (loadError) {
      setSession(null);
      setError(parseWorkbenchError(loadError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setAnswerText("");
    setAnswerError(null);
    setWorkbenchFailureState(null);
    setSelectedProgressNodeRef(null);
    void loadSession();
  }, [sessionId]);

  const createQuestion = async (progressNodeRef?: string | null) => {
    if (session === null) {
      return;
    }
    setCreatingQuestion(true);
    setAnswerError(null);
    setWorkbenchFailureState(null);
    try {
      await createPolishQuestionTask(sessionId, {
        progress_node_ref: progressNodeRef ?? session.progress_tree_state.current_priority?.progress_node_ref ?? null,
      });
      await loadSession();
    } catch (createError) {
      setAnswerError(
        createError instanceof Error
          ? createError.message
          : "生成题目失败，请稍后重试。",
      );
    } finally {
      setCreatingQuestion(false);
    }
  };

  const sendAnswer = async () => {
    const trimmedAnswer = answerText.trim();
    if (!trimmedAnswer) {
      setAnswerError("请先输入回答内容。");
      return;
    }
    if (session === null) {
      setAnswerError("会话尚未加载完成，请稍后重试。");
      return;
    }
    const questionId = resolveCurrentQuestionId(session);
    if (!questionId) {
      setAnswerError("请先生成题目后再提交回答。");
      return;
    }

    setAnswerError(null);
    setWorkbenchFailureState(null);
    setSubmittingAnswer(true);
    try {
      const answer = await createPolishAnswer(sessionId, {
        question_id: questionId,
        answer_text: trimmedAnswer,
      });
      setFeedbackGenerating(true);
      try {
        await createPolishFeedbackTask(sessionId, {
          answer_id: answer.answer_id,
        });
      } catch (feedbackError) {
        setWorkbenchFailureState("feedbackFailedAnswerSaved");
        setAnswerError(
          feedbackError instanceof Error
            ? `回答已保存，但反馈生成失败：${feedbackError.message}`
            : "回答已保存，但反馈生成失败，请稍后重试。",
        );
        setAnswerText("");
        await loadSession();
        return;
      } finally {
        setFeedbackGenerating(false);
      }

      try {
        const refreshed = await refreshPolishProgressTreeState(sessionId);
        setSession(refreshed);
        setAnswerText("");
        if (refreshed.progress_tree_status === "refresh_failed") {
          setWorkbenchFailureState("progressRefreshFailed");
          setAnswerError("反馈已生成，但进展树刷新失败；当前题目、回答和反馈不会丢失。");
        } else {
          setWorkbenchFailureState(null);
        }
      } catch (refreshError) {
        setWorkbenchFailureState("progressRefreshFailed");
        setAnswerError(
          refreshError instanceof Error
            ? `反馈已生成，但进展树刷新失败：${refreshError.message}`
            : "反馈已生成，但进展树刷新失败；当前题目、回答和反馈不会丢失。",
        );
        setAnswerText("");
        await loadSession();
      }
    } catch (submitError) {
      setAnswerError(
        submitError instanceof Error
          ? submitError.message
          : "提交回答失败，请稍后重试。",
      );
    } finally {
      setFeedbackGenerating(false);
      setSubmittingAnswer(false);
    }
  };

  const copySessionContent = async () => {
    if (session === null) {
      return;
    }
    if (!window.navigator.clipboard?.writeText) {
      message.error("当前环境不支持剪贴板复制。");
      return;
    }
    setCopyingSession(true);
    try {
      await window.navigator.clipboard.writeText(buildPolishSessionClipboardMarkdown(session));
      message.success("模拟面试内容已复制到剪贴板。");
    } catch (copyError) {
      if (copyError instanceof Error) {
        message.error(copyError.message);
      } else {
        message.error("复制失败，请稍后重试。");
      }
    } finally {
      setCopyingSession(false);
    }
  };

  const hasQuestion = session !== null && session.turns.length > 0;
  const progressNodes = session === null ? [] : buildWorkbenchProgressNodes(session);
  const progressPercent =
    session === null ? 0 : Math.max(0, Math.min(100, session.progress_tree_state?.progress?.progress_percent ?? 0));
  const currentProgressNodeKey =
    resolveCurrentWorkbenchProgressNodeKey(
      progressNodes,
      session === null ? null : resolveSessionCurrentProgressNodeRef(session),
    );
  const selectedProgressNodeDetailRef =
    session === null ? null : resolveProgressTreeDetailNodeRef(session, selectedProgressNodeRef);
  const selectedProgressNodeBanner =
    session === null ? null : buildProgressTreeContextBannerContent(session, selectedProgressNodeDetailRef);
  const headerChips = session === null ? [] : buildWorkbenchHeaderChips(session, progressPercent);
  const isProgressTreeInsufficient = session?.progress_tree_status === "insufficient_context";
  const isProgressTreeReady = session?.progress_tree_status === "ready";
  const isProgressTreeRefreshFailed = session?.progress_tree_status === "refresh_failed";
  const hasProgressTreeNodes = progressNodes.length > 0;
  const canShowProgressTree = hasProgressTreeNodes && (isProgressTreeReady || isProgressTreeRefreshFailed);
  const workbenchMachineState = deriveWorkbenchMachineState({
    session,
    creatingQuestion,
    feedbackGenerating,
    failureState: isProgressTreeRefreshFailed ? "progressRefreshFailed" : workbenchFailureState,
  });
  const workbenchMachineCopy = WORKBENCH_MACHINE_STATE_COPY[workbenchMachineState];
  const [refreshingProgressTree, setRefreshingProgressTree] = useState<boolean>(false);
  const refreshProgressTree = async () => {
    if (session === null || refreshingProgressTree) {
      return;
    }
    setRefreshingProgressTree(true);
    setWorkbenchFailureState(null);
    try {
      const refreshed = await refreshPolishProgressTreeState(sessionId);
      setSession(refreshed);
      if (refreshed.progress_tree_status === "refresh_failed") {
        setWorkbenchFailureState("progressRefreshFailed");
        message.warning("进展树刷新失败，已保留当前题目、回答和反馈。");
      } else {
        message.success("进展树已刷新。");
      }
    } catch (error) {
      setWorkbenchFailureState("progressRefreshFailed");
      message.error(error instanceof Error ? error.message : "刷新进展树失败，请稍后重试。");
    } finally {
      setRefreshingProgressTree(false);
    }
  };

  useEffect(() => {
    setExpandedProgressNodeKeys(new Set(collectDefaultExpandedProgressNodeKeys(progressNodes)));
  }, [session]);

  useEffect(() => {
    setProgressNodeContextExpanded(false);
  }, [selectedProgressNodeDetailRef]);

  const toggleProgressNode = (nodeKey: string) => {
    setExpandedProgressNodeKeys((currentKeys) => {
      const nextKeys = new Set(currentKeys);
      if (nextKeys.has(nodeKey)) {
        nextKeys.delete(nodeKey);
      } else {
        nextKeys.add(nodeKey);
      }
      return nextKeys;
    });
  };

  const handleNextRecommendedAction = (action: PolishRecommendedAction, progressNodeRef?: string | null) => {
    if (action === "generate_next_question") {
      void createQuestion(progressNodeRef ?? resolveSessionCurrentProgressNodeRef(session!));
      return;
    }
    if (action === "answer_again" || action === "continue_same_question" || action === "provide_more_answer_detail") {
      setSelectedProgressNodeRef(progressNodeRef ?? selectedProgressNodeDetailRef);
      setAnswerError(null);
      message.info("可以在下方输入区继续补充本题回答。");
      return;
    }
    message.info(`${toNextRecommendedActionLabel(action)}已在反馈区呈现，可结合本轮内容继续打磨。`);
  };

  const renderProgressTreeContextBanner = () => {
    if (selectedProgressNodeBanner === null || selectedProgressNodeBanner.title === null) {
      return (
        <section
          className={`${styles.progressNodeContextBanner} ${styles.progressNodeContextEmpty}`}
          aria-label={INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE}
        >
          <div className={styles.progressNodeContextHeader}>
            <Typography.Text strong className={styles.progressNodeContextLabel}>
              {INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE}
            </Typography.Text>
            <Typography.Text type="secondary" className={styles.progressNodeContextDepth}>
              {selectedProgressNodeBanner?.emptyDescription ?? INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY}
            </Typography.Text>
          </div>
        </section>
      );
    }

    const canExpandContext = shouldShowProgressTreeContextBannerToggle(selectedProgressNodeBanner);
    const expandedSections = buildProgressTreeContextBannerExpandedSections(selectedProgressNodeBanner);

    return (
      <section className={styles.progressNodeContextBanner} aria-label={INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE}>
        <div className={styles.progressNodeContextHeader}>
          <Typography.Text strong className={styles.progressNodeContextLabel}>
            {INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE}
          </Typography.Text>
          <Typography.Text strong className={styles.progressNodeContextTitle}>
            {selectedProgressNodeBanner.title}
          </Typography.Text>
        </div>
        {canExpandContext ? (
          <button
            className={styles.progressNodeContextToggle}
            type="button"
            aria-expanded={isProgressNodeContextExpanded}
            onClick={() => setProgressNodeContextExpanded((isExpanded) => !isExpanded)}
          >
            {isProgressNodeContextExpanded
              ? INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY.collapse
              : INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY.expand}
          </button>
        ) : null}
        {selectedProgressNodeBanner.depthRequirement && !isProgressNodeContextExpanded ? (
          <Typography.Text type="secondary" className={styles.progressNodeContextDepth}>
            {selectedProgressNodeBanner.depthRequirement}
          </Typography.Text>
        ) : null}
        {isProgressNodeContextExpanded ? (
          <div className={styles.progressNodeContextExpandedBody}>
            {expandedSections.map((section) => (
              <section className={styles.progressNodeContextSection} key={section.key}>
                <Typography.Text strong className={styles.progressNodeContextSectionTitle}>
                  {section.title}
                </Typography.Text>
                {section.items.length === 1 ? (
                  <Typography.Text type="secondary" className={styles.progressNodeContextSectionText}>
                    {section.items[0]}
                  </Typography.Text>
                ) : (
                  <ul className={styles.progressNodeContextList}>
                    {section.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </section>
            ))}
          </div>
        ) : null}
      </section>
    );
  };

  const renderProgressNode = (node: WorkbenchProgressNode, level = 0) => {
    if (node.kind === "group") {
      const isExpanded = expandedProgressNodeKeys.has(node.key);
      return (
        <div className={styles.nodeGroupBranch} key={node.key}>
          <button
            className={styles.nodeGroupHeader}
            type="button"
            aria-expanded={isExpanded}
            onClick={() => toggleProgressNode(node.key)}
          >
            <span className={styles.nodeGroupTitleRow}>
              <span className={styles.nodeChevron}>{isExpanded ? <DownOutlined /> : <RightOutlined />}</span>
              <Typography.Text strong className={styles.nodeGroupTitle}>
                {node.title}
              </Typography.Text>
              <Typography.Text type="secondary" className={styles.nodeCount}>
                · {node.detail}
              </Typography.Text>
            </span>
          </button>
          {isExpanded ? (
            <div className={styles.childNodeList}>
              {node.children?.map((childNode) => renderProgressNode(childNode, level + 1))}
            </div>
          ) : null}
        </div>
      );
    }

    const questionTargetRef = getWorkbenchProgressNodeQuestionTargetRef(node);
    const canCreateQuestionFromNode =
      questionTargetRef !== null && isProgressTreeReady && !creatingQuestion && !submittingAnswer && !feedbackGenerating;
    const canSelectNode = node.kind === "node";
    const isActive = canSelectNode && node.key === selectedProgressNodeDetailRef;
    const isCurrentPriority = canSelectNode && node.key === currentProgressNodeKey;
    const isExpandable = !canCreateQuestionFromNode && Boolean(node.children && node.children.length > 0);
    const isExpanded = expandedProgressNodeKeys.has(node.key);
    const titleMeta = buildWorkbenchProgressNodeTitleMeta(node);
    const cardClassName = [
      isActive ? styles.nodeCardActive : styles.nodeCard,
      isCurrentPriority ? styles.nodeCardCurrentPriority : "",
      level > 0 ? styles.nodeCardChild : "",
    ].filter(Boolean).join(" ");
    const statusDotClassName = [
      styles.nodeStatusDot,
      node.status === "completed" ? styles.nodeStatusDotCompleted : "",
      node.status === "in_progress" ? styles.nodeStatusDotInProgress : "",
      node.status === "pending" ? styles.nodeStatusDotPending : "",
    ].filter(Boolean).join(" ");

    return (
      <div className={styles.nodeBranch} key={node.key}>
        <button
          className={cardClassName}
          type="button"
          disabled={!canSelectNode && !isExpandable}
          aria-expanded={isExpandable ? isExpanded : undefined}
          onClick={
            canSelectNode
              ? () => {
                  setSelectedProgressNodeRef(resolveProgressTreeSelectedNodeRefAfterClick(node, selectedProgressNodeDetailRef));
                  if (canCreateQuestionFromNode) {
                    void createQuestion(questionTargetRef);
                    return;
                  }
                  if (isExpandable) {
                    toggleProgressNode(node.key);
                  }
                }
              : isExpandable
                ? () => toggleProgressNode(node.key)
                : undefined
          }
        >
          <span className={styles.nodeContent}>
            {node.kind === "question" && node.detail ? (
              <>
                <Typography.Text strong>{node.title}</Typography.Text>
                <Typography.Text type="secondary">{node.detail}</Typography.Text>
              </>
            ) : (
              <span className={styles.nodeTitleRow}>
                <Typography.Text strong className={styles.nodeTitleText}>
                  {titleMeta.title}
                </Typography.Text>
              </span>
            )}
            {isCurrentPriority ? (
              <Tag
                color={node.status === "completed" ? "success" : "processing"}
                style={{ width: "fit-content", margin: 0 }}
              >
                当前优先
              </Tag>
            ) : null}
          </span>
          {node.kind === "question" ? null : (
            <span className={styles.nodeStatusCluster}>
              <span className={statusDotClassName} />
              <Typography.Text type="secondary" className={styles.nodeStatusLabel}>
                {titleMeta.statusLabel}
              </Typography.Text>
            </span>
          )}
          {isExpandable ? (
            <span className={styles.nodeChevron}>
              {isExpanded ? <DownOutlined /> : <RightOutlined />}
            </span>
          ) : (
            <span className={styles.nodeChevron} />
          )}
        </button>
        {isExpandable && isExpanded ? (
          <div className={styles.childNodeList}>
            {node.children?.map((childNode) => renderProgressNode(childNode, level + 1))}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <AppShell>
      {loading ? (
        <div className={styles.workbenchState}>
          <LoadingState compact message="模拟面试工作台加载中..." />
        </div>
      ) : error !== null ? (
        <div className={styles.workbenchState}>
          <ErrorState
            compact
            message={error.message}
            details={error.details}
            actionLabel={error.unauthorized ? "前往登录" : "返回列表"}
            onAction={() => {
              navigate(error.unauthorized ? "/login" : "/interview", { replace: error.unauthorized });
            }}
          />
        </div>
      ) : session === null ? (
        <div className={styles.workbenchState}>
          <EmptyState
            compact
            title="未找到模拟面试"
            description="当前会话详情为空。"
            reason="请返回列表重新选择一场模拟面试。"
          />
        </div>
      ) : (
        <div className={styles.workbenchRoot} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.root}>
          <section className={styles.heroPanel}>
            <div className={styles.heroHeader}>
              <div className={styles.heroSummary}>
                <Typography.Title level={3} className={styles.heroTitle}>
                  打磨模式工作台
                </Typography.Title>
                <div className={styles.metaPills}>
                  {headerChips.map((chip) => (
                    <span key={chip.key}>
                      <strong>{chip.label}：</strong>
                      {chip.value}
                    </span>
                  ))}
                </div>
              </div>

              <div className={styles.heroActions}>
                <Button
                  type="primary"
                  onClick={() => navigate("/interview")}
                >
                  {INTERVIEW_WORKBENCH_HERO_ACTION_COPY[0]}
                </Button>
                <Button
                  loading={copyingSession}
                  onClick={() => void copySessionContent()}
                >
                  {INTERVIEW_WORKBENCH_HERO_ACTION_COPY[1]}
                </Button>
              </div>
            </div>
          </section>

          <section className={styles.workspaceGrid}>
            <aside className={styles.progressPanel} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.progressPanel}>
              <div className={styles.progressPanelHeader}>
                <div className={styles.panelHeader}>
                  <Typography.Title level={4} className={styles.panelTitle}>
                    模拟面试进度
                  </Typography.Title>
                </div>
                <Progress percent={progressPercent} showInfo={false} strokeColor="#2563eb" trailColor="#e4ecf7" />
              </div>

              <div className={styles.progressTreeBody}>
                <div
                  className={`${styles.nodeList} ${styles[INTERVIEW_PROGRESS_TREE_SCROLL_CLASS]}`}
                  data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.progressNodeList}
                >
                  {isProgressTreeInsufficient ? (
                    <Alert
                      type="warning"
                      showIcon
                      message="岗位或简历内容不足，暂不能生成进展树。"
                      description="请补充当前绑定的岗位职责、岗位要求和简历正文后重新发起模拟面试。"
                    />
                  ) : !canShowProgressTree ? (
                    <Alert
                      type="warning"
                      showIcon
                      message={hasProgressTreeNodes ? "进展树状态异常" : "进展树暂未生成"}
                      description={
                        isProgressTreeReady
                          ? "当前会话尚无可展示进展节点，建议刷新后重试，或稍后再次访问。"
                          : "进展树暂未就绪，建议点击刷新重新生成。"
                      }
                      action={
                        <Button
                          size="small"
                          loading={refreshingProgressTree}
                          onClick={refreshProgressTree}
                        >
                          刷新进展树
                        </Button>
                      }
                    />
                  ) : (
                    <>
                      {isProgressTreeRefreshFailed ? (
                        <Alert
                          type="warning"
                          showIcon
                          message="进度刷新失败，可重试。"
                          description="已保留当前进展树结构，本次只影响节点状态刷新。"
                          action={
                            <Button size="small" loading={refreshingProgressTree} onClick={refreshProgressTree}>
                              重试刷新
                            </Button>
                          }
                        />
                      ) : null}
                      {progressNodes.map((node) => renderProgressNode(node))}
                    </>
                  )}
                </div>
              </div>
            </aside>

            <main className={styles.conversationPanel} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.conversationPanel}>
              <div className={styles.conversationHeader}>
                <div className={styles.conversationHeaderTitle}>
                  <Typography.Title level={4} className={styles.panelTitle}>
                    对话与反馈
                  </Typography.Title>
                  <Tag color={workbenchMachineCopy.color} className={styles.workbenchStateTag}>
                    {workbenchMachineCopy.label}
                  </Tag>
                </div>
                {hasQuestion ? null : (
                  <Button
                    type="primary"
                    onClick={() => {
                      void createQuestion();
                    }}
                    loading={creatingQuestion}
                    disabled={isProgressTreeInsufficient || !isProgressTreeReady || !hasProgressTreeNodes}
                  >
                    生成题目
                  </Button>
                )}
              </div>

              <div className={styles.chatScroll} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.chatScroll}>
                {renderProgressTreeContextBanner()}
                {hasQuestion ? null : (
                  <EmptyState
                    compact
                    title="暂无题目"
                    description="请先生成题目后再开始作答。"
                    reason="点击上方“生成题目”按钮，系统将基于当前主题生成题干。"
                  />
                )}
                {session.turns.map((turn, turnIndex) => (
                  <section key={turn.question_id} style={{ display: "grid", gap: 12 }}>
                    <div className={styles.questionBubble}>
                      <Typography.Text strong>{`题目 ${turnIndex + 1}：`}</Typography.Text>
                      <Typography.Text className={styles.questionText}>
                        {renderQuestionTextWithSources(
                          turn.question_text || FALLBACK_QUESTION_TEXT,
                          turn.question_sources ?? [],
                        )}
                      </Typography.Text>
                    </div>
                    {turn.answers.length === 0 ? (
                      <div style={{ display: "grid", gap: 12 }}>
                        <div className={styles.answerBubble}>
                          <Typography.Text>{FALLBACK_ANSWER_TEXT}</Typography.Text>
                        </div>
                        <section className={styles.feedbackAccordion} aria-label="反馈占位区域">
                          <div className={styles.feedbackItem}>
                            <Typography.Text type="secondary">{FALLBACK_FEEDBACK_TEXT}</Typography.Text>
                          </div>
                        </section>
                      </div>
                    ) : (
                      turn.answers.map((answer) => {
                        const nextActions = getAnswerNextRecommendedActions(answer);
                        return (
                          <section key={answer.answer_id} style={{ display: "grid", gap: 10 }}>
                            <div className={styles.answerBubble}>
                              <Typography.Text strong>{`第 ${answer.answer_round} 轮回答`}</Typography.Text>
                              <Typography.Text>{answer.answer_text || FALLBACK_ANSWER_TEXT}</Typography.Text>
                            </div>
                            <section className={styles.feedbackAccordion} aria-label="反馈区域">
                              <div className={styles.feedbackItem}>
                                <div className={styles.feedbackTextBlock}>
                                  <Typography.Text strong>{`第 ${answer.answer_round} 轮反馈`}</Typography.Text>
                                  <Typography.Text>{answer.feedback_text || FALLBACK_FEEDBACK_TEXT}</Typography.Text>
                                </div>
                              </div>
                              {nextActions.length > 0 ? (
                                <div className={styles.nextActionBar} aria-label="下一步建议">
                                  {nextActions.map((action) => (
                                    <Button
                                      key={`${answer.answer_id}:${action}`}
                                      size="small"
                                      disabled={creatingQuestion || submittingAnswer || feedbackGenerating}
                                      loading={action === "generate_next_question" && creatingQuestion}
                                      onClick={() => handleNextRecommendedAction(action, turn.progress_node_ref)}
                                    >
                                      {toNextRecommendedActionLabel(action)}
                                    </Button>
                                  ))}
                                </div>
                              ) : null}
                            </section>
                          </section>
                        );
                      })
                    )}
                  </section>
                ))}
              </div>

              <div className={styles.composer} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.composer}>
                <Alert type={workbenchMachineState === "feedbackReady" ? "success" : "info"} showIcon message={workbenchMachineCopy.label} description={workbenchMachineCopy.description} />
                {answerError !== null ? <Alert type="error" showIcon message={answerError} /> : null}
                {!hasQuestion && (
                  <Alert
                    type="info"
                    showIcon
                    message="当前未生成题目"
                    description="请先点击“生成题目”后提交回答。"
                  />
                )}
                <Input.TextArea
                  className={styles.composerInput}
                  rows={4}
                  value={answerText}
                  onChange={(event) => setAnswerText(event.target.value)}
                  onKeyDown={(event) => {
                    if (shouldSubmitAnswerFromKeyboard({
                      key: event.key,
                      ctrlKey: event.ctrlKey,
                      shiftKey: event.shiftKey,
                      altKey: event.altKey,
                      isComposing: event.nativeEvent.isComposing,
                    })) {
                      event.preventDefault();
                      sendAnswer();
                    }
                  }}
                  placeholder="请输入你的回答"
                  maxLength={2000}
                  disabled={submittingAnswer || feedbackGenerating || creatingQuestion || !hasQuestion}
                />
                <div className={styles.composerActions}>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    loading={submittingAnswer || feedbackGenerating}
                    disabled={submittingAnswer || feedbackGenerating || creatingQuestion || !hasQuestion}
                    onClick={() => {
                      sendAnswer();
                    }}
                  >
                    发送
                  </Button>
                </div>
              </div>
            </main>
          </section>
        </div>
      )}
    </AppShell>
  );
}
