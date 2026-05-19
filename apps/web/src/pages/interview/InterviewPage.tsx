import {
  ArrowLeftOutlined,
  CopyOutlined,
  DownOutlined,
  CheckCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  RightOutlined,
  SendOutlined,
} from "@ant-design/icons";
import { Alert, Button, Card, Drawer, Form, Input, Progress, Select, Space, Table, Tag, Typography, message } from "antd";
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
  PolishProgressTreeNode,
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
const WORKBENCH_PROGRESS_NODE_STATUS_TEXT = {
  completed: "已完成",
  in_progress: "进行中",
  pending: "未开始",
} as const;
type WorkbenchProgressNodeStatus = keyof typeof WORKBENCH_PROGRESS_NODE_STATUS_TEXT;
type WorkbenchProgressNode = {
  key: string;
  title: string;
  status: WorkbenchProgressNodeStatus;
  detail?: string;
  children?: WorkbenchProgressNode[];
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

function toSessionDisplayName(session: PolishSessionDetail): string {
  return (
    session.custom_topic_text_summary ||
    session.subtopic_ref?.title ||
    session.topic_ref?.title ||
    session.session_id
  );
}

function toTopicLabel(session: PolishSessionDetail): string {
  const topic = session.topic_ref?.title ?? session.topic_ref?.topic_id;
  const subtopic = session.subtopic_ref?.title ?? session.subtopic_ref?.subtopic_id;
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

export function buildPolishSessionClipboardMarkdown(session: PolishSessionDetail): string {
  const rows: string[] = [
    "# 模拟面试复盘",
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
  if (session.turns.length === 0) {
    return null;
  }
  const lastTurn = session.turns[session.turns.length - 1];
  return lastTurn.question_id || null;
}

function toCurrentNodeLabel(session: PolishSessionDetail): string {
  return session.progress_tree_state.current_priority?.title ?? "待生成";
}

function buildWorkbenchProgressNodes(
  session: PolishSessionDetail,
): WorkbenchProgressNode[] {
  const questionNodes = buildQuestionProgressNodes(session);
  const activeNodeRef = session.progress_tree_state.current_priority?.progress_node_ref ?? null;
  const stateByRef = new Map(
    session.progress_tree_state.node_states.map((nodeState) => [
      nodeState.progress_node_ref,
      normalizeProgressNodeStatus(nodeState.status),
    ]),
  );
  return session.progress_tree_plan.nodes.map((node) =>
    toWorkbenchProgressNode({
      node,
      stateByRef,
      activeNodeRef,
      questionNodes,
      level: 0,
    }),
  );
}

function buildQuestionProgressNodes(session: PolishSessionDetail): WorkbenchProgressNode[] {
  const questionNodes: WorkbenchProgressNode[] = [];
  for (const [turnIndex, turn] of session.turns.entries()) {
    const shortQuestion = turn.question_text.length > 24 ? `${turn.question_text.slice(0, 21)}...` : turn.question_text;
    questionNodes.push({
      key: `question:${turn.question_id}`,
      title: `题目 ${turnIndex + 1}`,
      status: turn.answers.length > 0 ? "completed" : "in_progress",
      detail: shortQuestion,
    });
  }
  return questionNodes;
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
  return {
    key: params.node.progress_node_ref,
    title: params.node.title,
    status: params.stateByRef.get(params.node.progress_node_ref) ?? summarizeProgressNodeStatus(mergedChildren),
    detail: params.level === 0 ? "一级方向" : params.node.expected_capability,
    children: mergedChildren.length > 0 ? mergedChildren : undefined,
  };
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

function resolveCurrentWorkbenchProgressNodeKey(nodes: readonly WorkbenchProgressNode[]): string | null {
  const flattenedNodes = flattenWorkbenchProgressNodes(nodes);
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

function collectDefaultExpandedProgressNodeKeys(nodes: readonly WorkbenchProgressNode[]): string[] {
  const expandedKeys: string[] = [];
  for (const node of nodes) {
    if (node.children && node.children.length > 0 && node.status !== "pending") {
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

export function InterviewPage() {
  const { navigate } = useRouteController();
  const [sessions, setSessions] = useState<PolishSessionSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<InterviewListError | null>(null);
  const [createOpen, setCreateOpen] = useState<boolean>(false);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [topics, setTopics] = useState<PolishTopic[]>([]);
  const [createPrerequisiteLoading, setCreatePrerequisiteLoading] = useState<boolean>(false);
  const [createPrerequisiteError, setCreatePrerequisiteError] = useState<string | null>(null);
  const [topicLoadError, setTopicLoadError] = useState<string | null>(null);
  const [createSubmitLoading, setCreateSubmitLoading] = useState<boolean>(false);
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

  const bindingOptions = useMemo(() => buildPolishBindingOptions(jobs), [jobs]);
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

    setCreateSubmitLoading(true);
    setCreateError(null);
    try {
      const created = await createPolishSession(buildPolishSessionCreateRequest(values));
      message.success(`模拟面试「${toSessionDisplayName(created)}」已创建。`);
      setCreateOpen(false);
      createForm.resetFields();
      navigate(buildPolishSessionPath(created.session_id));
    } catch (submitError) {
      setCreateError(toCreateErrorMessage(submitError));
    } finally {
      setCreateSubmitLoading(false);
    }
  };

  const columns: ColumnsType<PolishSessionSummary> = useMemo(
    () => [
      {
        title: "名称",
        dataIndex: "title",
        key: "title",
        width: 220,
        render: (value: string) => <Typography.Text strong>{value}</Typography.Text>,
      },
      {
        title: "模式",
        dataIndex: "mode",
        key: "mode",
        width: 110,
        render: (value: string) => <Tag color="blue">{toModeLabel(value)}</Tag>,
      },
      {
        title: "状态",
        dataIndex: "status",
        key: "status",
        width: 110,
        render: (value: string) => <Tag color={value === "running" ? "green" : "default"}>{value}</Tag>,
      },
      {
        title: "绑定关系",
        dataIndex: "binding_label",
        key: "binding_label",
        width: 180,
        render: (_: unknown, record) => {
          const value = record.binding_label || `${toDisplayJobTitle(record)} / ${toDisplayResumeTitle(record)}`;
          return <Typography.Text>{value}</Typography.Text>;
        },
      },
      {
        title: "主题",
        key: "topic",
        width: 180,
        render: (_, record) => <Typography.Text>{record.title || "未选择"}</Typography.Text>,
      },
      {
        title: "更新时间",
        dataIndex: "updated_at",
        key: "updated_at",
        width: 180,
        render: (value: string) => toDisplayDate(value),
      },
      {
        title: "操作",
        key: "actions",
        width: 96,
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
          <Space wrap style={{ width: "100%", justifyContent: "space-between" }}>
            <div>
              <Typography.Title level={4} style={{ marginBottom: 4 }}>
                模拟面试
              </Typography.Title>
              <Typography.Text type="secondary">
                查看当前账号下的打磨模式会话记录。
              </Typography.Text>
            </div>
            <Space wrap>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  void loadSessions();
                }}
              >
                刷新
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateEntry}>
                发起模拟面试
              </Button>
            </Space>
          </Space>
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
              dataSource={sessions}
              pagination={{
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
              }}
              size="small"
              scroll={{ x: 1080 }}
            />
          )}
        </Card>

        <Drawer
          title="发起模拟面试"
          width={560}
          open={createOpen}
          onClose={closeCreateEntry}
          destroyOnClose
          extra={
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              loading={createSubmitLoading}
              disabled={!createAvailability.canSubmit}
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
                  disabled={!createAvailability.canSubmit}
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
                  disabled={topics.length === 0}
                  placeholder="选择 1 个模拟面试主题"
                  options={topics.map((topic) => ({
                    value: topic.topic_id,
                    label: topic.title,
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
  const [copyingSession, setCopyingSession] = useState<boolean>(false);
  const [expandedProgressNodeKeys, setExpandedProgressNodeKeys] = useState<Set<string>>(() => new Set());

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
    void loadSession();
  }, [sessionId]);

  const createQuestion = async () => {
    if (session === null) {
      return;
    }
    setCreatingQuestion(true);
    setAnswerError(null);
    try {
      await createPolishQuestionTask(sessionId, {
        progress_node_ref: session.progress_tree_state.current_priority?.progress_node_ref ?? null,
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
    setSubmittingAnswer(true);
    try {
      const answer = await createPolishAnswer(sessionId, {
        question_id: questionId,
        answer_text: trimmedAnswer,
      });
      await createPolishFeedbackTask(sessionId, {
        answer_id: answer.answer_id,
      });
      await refreshPolishProgressTreeState(sessionId);
      setAnswerText("");
      await loadSession();
    } catch (submitError) {
      setAnswerError(
        submitError instanceof Error
          ? submitError.message
          : "提交回答失败，请稍后重试。",
      );
    } finally {
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
      message.success("复盘内容已复制到剪贴板。");
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
  const progressPercent = session === null ? 0 : session.progress_tree_state.progress.progress_percent;
  const currentProgressNodeKey =
    session?.progress_tree_state.current_priority?.progress_node_ref ?? resolveCurrentWorkbenchProgressNodeKey(progressNodes);
  const headerChips = session === null ? [] : buildWorkbenchHeaderChips(session, progressPercent);
  const isProgressTreeInsufficient = session?.progress_tree_status === "insufficient_context";

  useEffect(() => {
    setExpandedProgressNodeKeys(new Set(collectDefaultExpandedProgressNodeKeys(progressNodes)));
  }, [session]);

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

  const renderProgressNode = (node: WorkbenchProgressNode, level = 0) => {
    const isActive = node.key === currentProgressNodeKey;
    const isExpandable = Boolean(node.children && node.children.length > 0);
    const isExpanded = expandedProgressNodeKeys.has(node.key);
    const cardClassName = [
      isActive ? styles.nodeCardActive : styles.nodeCard,
      level > 0 ? styles.nodeCardChild : "",
    ].filter(Boolean).join(" ");

    return (
      <div className={styles.nodeBranch} key={node.key}>
        <button
          className={cardClassName}
          type="button"
          disabled={!isExpandable}
          aria-expanded={isExpandable ? isExpanded : undefined}
          onClick={isExpandable ? () => toggleProgressNode(node.key) : undefined}
        >
          <span>
            <Typography.Text strong>{node.title}</Typography.Text>
            {node.detail ? (
              <Typography.Text type="secondary">
                {node.detail} · {progressNodeStatusLabel(node.status)}
              </Typography.Text>
            ) : (
              <Typography.Text type="secondary">{progressNodeStatusLabel(node.status)}</Typography.Text>
            )}
            {isActive ? (
              <Tag
                color={node.status === "completed" ? "success" : "processing"}
                style={{ width: "fit-content", margin: 0 }}
              >
                当前优先级
              </Tag>
            ) : null}
          </span>
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
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate("/interview")}
                >
                  返回模拟面试列表
                </Button>
                <Button
                  icon={<CopyOutlined />}
                  loading={copyingSession}
                  onClick={() => void copySessionContent()}
                >
                  复制复盘内容
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
                <Typography.Text className={styles.progressLabel}>
                  整体进度：{progressPercent}%
                </Typography.Text>
                <Progress percent={progressPercent} showInfo={false} strokeColor="#2563eb" trailColor="#e4ecf7" />
              </div>

              <div className={styles.nodeList} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.progressNodeList}>
                {isProgressTreeInsufficient ? (
                  <Alert
                    type="warning"
                    showIcon
                    message="岗位或简历内容不足，暂无法生成进展树。"
                    description="请补充当前绑定的岗位职责、岗位要求和简历正文后重新发起模拟面试。"
                  />
                ) : (
                  progressNodes.map((node) => renderProgressNode(node))
                )}
              </div>
            </aside>

            <main className={styles.conversationPanel} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.conversationPanel}>
              <div className={styles.conversationHeader}>
                <Typography.Title level={4} className={styles.panelTitle}>
                  对话与反馈
                </Typography.Title>
                {hasQuestion ? null : (
                  <Button
                    type="primary"
                    onClick={() => {
                      void createQuestion();
                    }}
                    loading={creatingQuestion}
                    disabled={isProgressTreeInsufficient}
                  >
                    生成题目
                  </Button>
                )}
              </div>

              <div className={styles.chatScroll} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.chatScroll}>
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
                      <Typography.Text>{turn.question_text || FALLBACK_QUESTION_TEXT}</Typography.Text>
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
                      turn.answers.map((answer) => (
                        <section key={answer.answer_id} style={{ display: "grid", gap: 10 }}>
                          <div className={styles.answerBubble}>
                            <Typography.Text>{answer.answer_text || FALLBACK_ANSWER_TEXT}</Typography.Text>
                          </div>
                          <section className={styles.feedbackAccordion} aria-label="反馈区域">
                            <div className={styles.feedbackItem}>
                              <Typography.Text>{answer.feedback_text || FALLBACK_FEEDBACK_TEXT}</Typography.Text>
                            </div>
                          </section>
                        </section>
                      ))
                    )}
                  </section>
                ))}
              </div>

              <div className={styles.composer} data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.composer}>
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
                  placeholder="请输入你的回答"
                  maxLength={2000}
                  disabled={submittingAnswer || creatingQuestion || !hasQuestion}
                />
                <div className={styles.composerActions}>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    loading={submittingAnswer}
                    disabled={submittingAnswer || creatingQuestion || !hasQuestion}
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
