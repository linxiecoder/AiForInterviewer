import {
  ArrowLeftOutlined,
  CloseCircleOutlined,
  CopyOutlined,
  DeleteOutlined,
  DownOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LeftOutlined,
  PlusOutlined,
  ReloadOutlined,
  RightOutlined,
  SearchOutlined,
  SendOutlined,
  StopOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Modal,
  Popover,
  Progress,
  Tabs,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useRef, useState } from "react";
import type {
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
  ReactElement,
  ReactNode,
} from "react";
import { useRouteController } from "../../app/routes/router";
import { fetchJobs } from "../../entities/job/api/jobApi";
import type { JobSummary } from "../../entities/job/model/types";
import {
  completePolishQuestion,
  confirmPolishCandidate,
  createPolishAnswer,
  createPolishFeedbackTask,
  createPolishFeedbackNextQuestionTask,
  createPolishSession,
  dismissPolishCandidate,
  endPolishSession,
  fetchPolishAiTaskResult,
  fetchPolishCandidates,
  fetchPolishSession,
  fetchPolishSessions,
  fetchPolishTopics,
  generatePolishSessionReport,
  generateInitialPolishProgressTree,
  refreshPolishProgressTreeState,
  softDeletePolishSession,
} from "../../entities/polish/api/polishApi";
import type {
  CreatePolishSessionRequest,
  PolishCandidate,
  PolishFeedbackPayload,
  PolishQuestionSource,
  PolishTheme,
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
export const POLISH_THEME_OPTIONS = [
  { value: "technical", label: "技术打磨" },
  { value: "communication", label: "表达能力" },
  { value: "mixed", label: "混合" },
] as const satisfies readonly { value: PolishTheme; label: string }[];
export const INTERVIEW_CREATE_FIELD_KEYS = [
  "mode",
  "resume_job_binding_id",
  "polish_theme",
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
export const POLISH_AI_TASK_RUNNING_STATUSES = ["queued", "running"] as const;
export const POLISH_AI_TASK_FINAL_STATUSES = [
  "succeeded",
  "partial",
  "low_confidence",
  "validation_failed",
  "source_unavailable",
  "generation_failed",
  "timed_out",
  "cancelled",
] as const;
const POLISH_FEEDBACK_TASK_POLL_INTERVAL_MS = 600;
const POLISH_FEEDBACK_TASK_POLL_ATTEMPTS = 20;
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
  actions: 188,
} as const;
export const INTERVIEW_LIST_TABLE_SCROLL_X = 1310 as const;
export const INTERVIEW_LIST_ACTIONS = [
  "enter",
  "generate_report",
  "view_report",
  "end",
  "delete",
] as const;
export const INTERVIEW_LIST_ACTION_TOOLTIPS = {
  enter: "进入模拟面试",
  generateReport: "生成面试报告",
  viewReport: "查看面试报告",
  viewReportUnavailable: "面试报告尚未生成",
  end: "结束模拟面试",
  delete: "删除模拟面试",
  ended: "模拟面试已结束",
} as const;
export const INTERVIEW_LIST_CONFIRM_COPY = {
  endTitle: "确认结束模拟面试",
  endContent: "结束后将停止当前模拟面试，已产生的题目、回答和反馈会保留。",
  deleteTitle: "确认删除模拟面试",
  deleteContent: "删除后该模拟面试将从列表中移除，已产生的数据仅标记为删除，不会被物理删除。",
  okEnd: "确认结束",
  okDelete: "确认删除",
  cancel: "取消",
} as const;
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
  "current_question_answer",
] as const;
export const INTERVIEW_WORKBENCH_LAYOUT_VARIANT = "layout_b_resizable_progress_fixed_composer" as const;
export const INTERVIEW_WORKBENCH_LAYOUT_B_GRID_AREAS = [
  "summary_bar",
  "left_progress_tree",
  "right_conversation_header",
  "right_chat_scroll",
  "right_sticky_merged_context_card",
  "right_feedback_sheet",
  "right_fixed_next_action_bar",
  "right_fixed_composer",
] as const;
export const INTERVIEW_WORKBENCH_MERGED_CONTEXT_CARD_LAYOUT = {
  layoutArea: "right_sticky_merged_context_card",
  progressContext: "merged_into_current_question_card",
  currentQuestion: "same_sticky_card",
  behavior: "compact_sticky_popover",
} as const;
export const INTERVIEW_WORKBENCH_STICKY_CONTEXT_CARD_DISPLAY_POLICY = {
  metaLayout: "question_first_status_only",
  questionPrefix: "题干：",
  collapsedQuestionLines: 2,
  questionInlineToggle: "removed",
  expandControl: "single_context_toggle",
  toggleIcon: "progress_tree_chevron",
  duplicatedNodeThemeCategory: "moved_to_summary_bar",
  focusedQuestionBubble: "rendered_in_chat_flow",
} as const;
export const INTERVIEW_WORKBENCH_LAYOUT_B_SCROLL_POLICY = {
  root: "viewport_locked",
  progressPanel: "independent_scroll",
  chatScroll: "independent_auto_scroll",
  composer: "outside_chat_scroll",
} as const;
export const INTERVIEW_WORKBENCH_CHAT_SCROLL_PADDING_POLICY = {
  top: 0,
  horizontal: 20,
  bottom: 24,
  stickyCardOwnPadding: true,
} as const;
export const INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS = {
  root: "interview-workbench-viewport",
  progressPanel: "interview-workbench-progress-panel",
  progressNodeList: "interview-workbench-progress-node-list",
  conversationPanel: "interview-workbench-conversation-panel",
  chatScroll: "interview-workbench-chat-scroll",
  feedbackPanel: "interview-workbench-feedback-sheet",
  currentQuestionComposer: "interview-workbench-current-question-composer",
} as const;
export const INTERVIEW_WORKBENCH_SCROLL_REGIONS = ["progress_node_list", "chat_scroll"] as const;
export const INTERVIEW_PROGRESS_TREE_SCROLL_CLASS = "progressTreeScroll" as const;
export const INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT = "summary_row_end" as const;
export const INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY = "icon_only_with_tooltip" as const;
export const INTERVIEW_WORKBENCH_HERO_ACTION_COPY = [
  "复制完整模拟面试上下文",
  "结束模拟面试",
  "返回模拟面试列表",
] as const;
export const INTERVIEW_WORKBENCH_END_CONFIRM_COPY = {
  title: "确认结束模拟面试",
  content: "结束后将停止当前模拟面试，已产生的题目、回答和反馈会保留。",
  okText: "确认结束",
  cancelText: "取消",
} as const;
export const INTERVIEW_FORBIDDEN_NATIVE_DIALOG_APIS = [
  "alert",
  "confirm",
  "prompt",
  "window.alert",
  "window.confirm",
  "window.prompt",
] as const;
export const INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY = ["模拟面试进度"] as const;
export const INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS = [
  "岗位",
  "简历",
  "当前节点",
  "能力主题",
  "分类",
  "进度",
  "当前节点表现",
] as const;
export const INTERVIEW_WORKBENCH_FEEDBACK_ITEMS = [
  "总体点评",
  "打分",
  "得分点",
  "失分点",
  "参考回答",
  "考点解析",
  "技术原理扩展",
  "同题回答效果",
  "项目一致性检查",
  "同场相似内容检查",
  "项目资产更新候选",
  "权重说明",
  "面试意图",
  "技术短板",
  "表达短板",
  "高阶参考答案",
  "口语化范本",
  "多次回答改进",
  "下一轮重答重点",
  "下一轮打磨建议",
] as const;
export const INTERVIEW_WORKBENCH_CANDIDATE_REVIEW_ITEMS = [
  "candidate_type",
  "status",
  "title",
  "summary",
  "confidence_level",
  "evidence_excerpt",
  "confirm",
  "dismiss",
] as const;
export type WorkbenchMachineState =
  | "creatingQuestion"
  | "questionReady"
  | "feedbackGenerating"
  | "feedbackReady"
  | "feedbackFailedAnswerSaved"
  | "progressRefreshFailed";
export const INTERVIEW_WORKBENCH_STATE_MACHINE: readonly WorkbenchMachineState[] = [
  "creatingQuestion",
  "questionReady",
  "feedbackGenerating",
  "feedbackReady",
  "feedbackFailedAnswerSaved",
  "progressRefreshFailed",
] as const;
const WORKBENCH_MACHINE_STATE_COPY: Record<WorkbenchMachineState, { label: string; description: string; color: string }> = {
  creatingQuestion: { label: "正在生成题目", description: "题目生成中，请稍候。", color: "processing" },
  questionReady: { label: "当前题目", description: "在当前题目区域继续作答。", color: "default" },
  feedbackGenerating: { label: "正在生成反馈", description: "回答已保存，正在生成点评和下一步建议。", color: "processing" },
  feedbackReady: { label: "反馈已生成", description: "本轮反馈和下一步建议已同步。", color: "success" },
  feedbackFailedAnswerSaved: { label: "反馈生成失败", description: "回答已保存，可重试生成反馈或继续补充回答。", color: "warning" },
  progressRefreshFailed: { label: "进展刷新失败", description: "题目、回答和反馈已保留，仅进展树状态刷新失败。", color: "warning" },
};
const NEXT_RECOMMENDED_ACTION_LABELS: Record<string, string> = {
  answer_again: "再答一版",
  continue_same_question: "继续打磨本题",
  retry_same_question: "重答同题",
  generate_reference_answer: "查看参考回答",
  explain_knowledge_point: "查看考点解析",
  expand_technical_principle: "展开技术原理",
  generate_next_round_suggestion: "生成下一轮建议",
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
export const INTERVIEW_WORKBENCH_CURRENT_QUESTION_COMPOSER_PLACEMENT = "right_panel_bottom_fixed" as const;
export const INTERVIEW_WORKBENCH_NEXT_ACTION_PLACEMENT = "fixed_above_current_question_composer" as const;
export const INTERVIEW_WORKBENCH_FEEDBACK_CARD_INTERACTION_POLICY = {
  feedbackCard: "readonly",
  nextActions: "composer_action_bar",
  candidateActions: "feedback_panel",
} as const;
export const INTERVIEW_WORKBENCH_LAYOUT_B_FEEDBACK_PANEL_WIDTH_POLICY = {
  defaultCollapsed: 48,
  default: 430,
  min: 220,
  max: 520,
} as const;
export const INTERVIEW_WORKBENCH_FEEDBACK_PANEL_RESIZE_HANDLE_POLICY = {
  owner: "feedback_panel",
  edge: "left",
  position: "absolute_panel_edge",
  visualCentering: "translateX(-50%)",
} as const;
export const INTERVIEW_WORKBENCH_FEEDBACK_PANEL_TAB_LAYOUT_POLICY = {
  columns: "repeat(4, minmax(0, 1fr))",
  alignment: "center",
  safeInset: "panel_horizontal_padding",
} as const;
export const INTERVIEW_WORKBENCH_LAYOUT_B_PROGRESS_PANEL_WIDTH_POLICY = {
  defaultCollapsed: 48,
  default: 320,
  min: 320,
  max: 520,
} as const;
export const INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICIES = {
  allOpen: {
    questionBubbleMaxWidth: "min(88%, 920px)",
    answerBubbleMaxWidth: "min(88%, 920px)",
    feedbackBubbleMaxWidth: "min(88%, 920px)",
  },
  progressCollapsed: {
    questionBubbleMaxWidth: "min(92%, 1100px)",
    answerBubbleMaxWidth: "min(92%, 1100px)",
    feedbackBubbleMaxWidth: "min(92%, 1100px)",
  },
  feedbackCollapsed: {
    questionBubbleMaxWidth: "min(92%, 1100px)",
    answerBubbleMaxWidth: "min(92%, 1100px)",
    feedbackBubbleMaxWidth: "min(92%, 1100px)",
  },
  bothCollapsed: {
    questionBubbleMaxWidth: "min(96%, 1320px)",
    answerBubbleMaxWidth: "min(96%, 1320px)",
    feedbackBubbleMaxWidth: "min(96%, 1320px)",
  },
} as const;
export const INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY = {
  allOpen: "allOpen",
  progressCollapsed: "progressCollapsed",
  feedbackCollapsed: "feedbackCollapsed",
  bothCollapsed: "bothCollapsed",
} as const;
export const INTERVIEW_WORKBENCH_QUICK_REVIEW_CARD_LAYOUT_POLICY = {
  widthSource: "answer_bubble_max_width",
  primaryRow: "label_score_maturity_status_link",
  actionTreatment: "weak_text_link",
} as const;
export const INTERVIEW_WORKBENCH_ROUND_META_LABEL_POLICY = {
  answer: "compact_pill",
  feedback: "compact_pill",
} as const;
export const INTERVIEW_WORKBENCH_DISABLED_ACTIONS = [] as const;
export const INTERVIEW_WORKBENCH_STATE_REGIONS = ["loading", "error", "not_found"] as const;
export const INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT = {
  progress_context: "left",
  system_question: "left",
  feedback: "left",
  user_answer: "right",
  user_answer_placeholder: "right",
} as const;
const FEEDBACK_CODE_DISPLAY_MAP: Record<string, string> = {
  pending: "待处理",
  generated: "已生成",
  failed: "生成失败",
  complete: "已完成",
  completed: "已完成",
  in_progress: "进行中",
  inprogress: "进行中",
  done: "完成",
  conflict: "冲突",
  ambiguous: "不确定",
  consistent: "一致",
  insufficient_asset_context: "项目素材不足，回答与资产库证据不够一致",
  polish_answer: "回答打磨",
  polish_answ: "回答打磨",
  retry_same_question: "重答同题",
  continue_same_question: "继续本题",
  provide_more_answer_detail: "补充回答细节",
  answer_again: "重新作答",
  reference_answer: "参考回答",
  loss_points: "失分点",
  scoring: "评分",
  consistency_check: "项目一致性检查",
  major: "主要失分",
  minor: "轻微失分",
  critical: "严重失分",
  warning: "轻微风险",
  notice: "提示",
};
const FEEDBACK_LOSS_POINTS_TABLE_COLUMNS = ["序号", "严重程度", "扣分", "问题", "修正建议"] as const;
export const INTERVIEW_WORKBENCH_LOSS_POINT_TABLE_COLUMN_WIDTHS = {
  index: "44px",
  severity: "96px",
  deduction: "64px",
  issue: "34%",
  suggestion: "42%",
} as const;
const CODE_NOT_AVAILABLE_TEXT = "未知状态";
const FEEDBACK_REFERENCE_SECTION_FALLBACK = "暂无参考回答";
const FEEDBACK_LOSS_POINTS_TABLE_EMPTY_TEXT = "暂无明确失分点";
export const INTERVIEW_WORKBENCH_LEFT_FULL_WIDTH_MESSAGE_KINDS = [
  "progress_context",
  "system_question",
  "feedback",
] as const;
export const INTERVIEW_WORKBENCH_DETAIL_WIDTH_POLICY = {
  conversationPanel: "fills_available_grid_column",
  chatScroll: "full_width_message_list",
  leftDetailContent: "full_width_left_content",
  userAnswerContent: "right_aligned_capped_content",
} as const;
export const INTERVIEW_WORKBENCH_KEYBOARD_SHORTCUTS = {
  send_answer: "Ctrl+Enter",
} as const;
export const INTERVIEW_WORKBENCH_SEND_BUTTON_TOOLTIP = "发送，快捷键 Ctrl + Enter / ⌘ + Enter" as const;
export const INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_PLACEMENT = "fixed_at_pointer" as const;
export const INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_CLOSE_TRIGGERS = [
  "outside_pointer_down",
  "escape",
  "scroll",
  "select",
] as const;
export const INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS = {
  generateQuestion: "生成题目",
  markQuestionCompleted: "标记为已完成",
  copyNodeInfo: "复制节点信息",
} as const;
export const INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_BUTTON = "追问本题" as const;
export const INTERVIEW_WORKBENCH_REGENERATE_CURRENT_QUESTION_BUTTON = "换一道题" as const;
export const INTERVIEW_WORKBENCH_REGENERATE_NODE_BUTTON = "为当前节点出题" as const;
export const INTERVIEW_WORKBENCH_REGENERATE_CURRENT_NODE_NO_NODE_TOOLTIP = "无法定位当前节点，暂不能出题" as const;
export const INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_BUTTON = "标记完成" as const;
export const INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_DISABLED_WITHOUT_HISTORY = "先提交一轮回答后再追问" as const;
export const INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_UNSUPPORTED = "当前接口暂不支持追问生成" as const;
export const INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_DISABLED_WITHOUT_FEEDBACK = "生成反馈后才能标记完成" as const;
export const INTERVIEW_WORKBENCH_SEND_ANSWER_PLACEHOLDER = "请输入当前题目的回答" as const;
export const INTERVIEW_WORKBENCH_SEND_RETRY_PLACEHOLDER = "继续输入新的回答，本次将作为重答/继续打磨" as const;
export const INTERVIEW_WORKBENCH_SEND_DISABLED_PLACEHOLDER = "请选择左侧已有题目的节点后作答" as const;
export const INTERVIEW_WORKBENCH_REGRADE_CONFIRM_TITLE = "确认重新生成题目" as const;
export const INTERVIEW_WORKBENCH_REGRADE_CONFIRM_DESCRIPTION =
  "输入区有未发送内容，继续操作会保留草稿，但可能不再适配当前题目。是否继续？" as const;
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
export type WorkbenchProgressNodeStatus = keyof typeof WORKBENCH_PROGRESS_NODE_STATUS_TEXT;
export type WorkbenchProgressNodeKind = "group" | "node" | "question";
export type WorkbenchQuestionStatus = "in_progress" | "completed";
export type WorkbenchProgressNode = {
  key: string;
  kind: WorkbenchProgressNodeKind;
  title: string;
  status: WorkbenchProgressNodeStatus;
  detail?: string;
  nodeCode?: string | null;
  questionTargetRef?: string;
  questionId?: string;
  children?: WorkbenchProgressNode[];
};

export type WorkbenchChatMessageKind = keyof typeof INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT;
export type WorkbenchChatMessageAlignmentClassName = "messageRowLeft" | "messageRowRight";
export type WorkbenchProgressTreeContextMenuItemKey =
  | "mark_question_completed"
  | "copy_node_info";
export type WorkbenchProgressTreeContextMenuItem = {
  key: WorkbenchProgressTreeContextMenuItemKey;
  label: string;
  disabled: boolean;
};

export type WorkbenchCurrentQuestionState = {
  questionId: string;
  progressNodeRef: string | null;
  status: WorkbenchQuestionStatus;
};

export type WorkbenchQuestionActionState = {
  currentQuestionId: string | null;
  currentQuestionStatus: WorkbenchQuestionStatus | null;
  currentQuestionProgressNodeRef: string | null;
  currentQuestionLatestAnswerId: string | null;
  currentQuestionLatestFeedbackId: string | null;
  hasCurrentQuestionAnswer: boolean;
  hasCurrentQuestionFeedback: boolean;
  isQuestionNode: boolean;
  hasCurrentQuestion: boolean;
  isCurrentQuestionCompleted: boolean;
  canSendAnswer: boolean;
  canGenerateQuestion: boolean;
  canRegenerateQuestion: boolean;
  canMarkQuestionCompleted: boolean;
};

export type AnswerSubmissionKeyDraft = {
  sessionId: string;
  questionId: string;
  answerText: string;
  idempotencyKey: string;
};

export function resolveAnswerSubmissionKeyDraft(
  current: AnswerSubmissionKeyDraft | null,
  params: {
    sessionId: string;
    questionId: string;
    answerText: string;
  },
  createKey: () => string = createAnswerSubmissionIdempotencyKey,
): AnswerSubmissionKeyDraft {
  if (
    current !== null &&
    current.sessionId === params.sessionId &&
    current.questionId === params.questionId &&
    current.answerText === params.answerText
  ) {
    return current;
  }
  return {
    ...params,
    idempotencyKey: createKey(),
  };
}

function createAnswerSubmissionIdempotencyKey(): string {
  const browserCrypto = globalThis.crypto;
  if (browserCrypto && typeof browserCrypto.randomUUID === "function") {
    return `polish-answer-${browserCrypto.randomUUID()}`;
  }
  return `polish-answer-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

export type WorkbenchFeedbackPanelTab = "summary" | "lossPoints" | "referenceAnswer" | "candidate";

export type WorkbenchFeedbackPanelTabItem = {
  key: WorkbenchFeedbackPanelTab;
  label: string;
  disabled: boolean;
};

const PROGRESS_PANEL_DEFAULT_WIDTH = INTERVIEW_WORKBENCH_LAYOUT_B_PROGRESS_PANEL_WIDTH_POLICY.default;
const PROGRESS_PANEL_MIN_WIDTH = INTERVIEW_WORKBENCH_LAYOUT_B_PROGRESS_PANEL_WIDTH_POLICY.min;
const PROGRESS_PANEL_MAX_WIDTH = INTERVIEW_WORKBENCH_LAYOUT_B_PROGRESS_PANEL_WIDTH_POLICY.max;

type ProgressTreeDisplayNode = PolishProgressTreeNode & {
  basis_type?: string | null;
  category?: string | null;
  common_loss_risks?: string[] | string | null;
  confidence_level?: string | null;
  coverage_points?: string[] | string | null;
  depth_goal?: string | null;
  display_category_title?: string | null;
  display_title?: string | null;
  exam_point?: string | null;
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
  sub_points?: string[] | string | null;
};

type ProgressTreeContextMenuState = {
  nodeKey: string;
  x: number;
  y: number;
} | null;

export const INTERVIEW_PROGRESS_TREE_CATEGORY_TITLE_BY_CATEGORY = {
  resume_deep_dive: "深度打磨类",
  jd_gap_learning: "补齐学习类",
} as const;
export const INTERVIEW_PROGRESS_TREE_OTHER_CATEGORY_TITLE = "其他打磨项";
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE = "当前节点上下文";
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_HEADER_LAYOUT = "label_and_node_title_same_row" as const;
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY = "请选择一个进展节点查看本轮打磨目标。";
export const INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY = {
  expand: "展开更多上下文",
  collapse: "收起上下文",
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
  technicalCoverage: string[];
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
  technicalCoverage: string[];
  emptyDescription?: string;
};

type ProgressTreeContextBannerSectionKey =
  | "depth_requirement"
  | "technical_coverage"
  | "follow_up_directions"
  | "loss_risks";

export type ProgressTreeContextBannerSection = {
  key: ProgressTreeContextBannerSectionKey;
  title: string;
  items: string[];
};

const WORKBENCH_STICKY_QUESTION_TEXT_COLLAPSE_THRESHOLD = 130;
const WORKBENCH_STICKY_NODE_EMPTY_TITLE = "请选择左侧节点";
const WORKBENCH_STICKY_NODE_EMPTY_DESCRIPTION = "请选择左侧节点。";
const WORKBENCH_STICKY_NODE_WITHOUT_SELECTED_QUESTION_HINT = "该节点暂无选中题目，可在下方为当前节点出题。";

export type WorkbenchQuestionConversationAutoScrollTrigger = {
  focusedQuestionId: string | null;
  selectedProgressNodeRef: string | null;
  latestAnswerId: string | null;
  latestFeedbackId: string | null;
};

export type WorkbenchStickyQuestionContextViewModel = {
  focusedQuestionId: string | null;
  selectedQuestionId: string | null;
  progressNodeRef: string | null;
  progressNodeTitle: string;
  capabilityThemeLabel: string;
  nodeCategoryLabel: string;
  nodeStatusLabel: string;
  nodeSummary: string | null;
  emptyDescription: string | null;
  nonQuestionHint: string | null;
  shouldShowQuestionContext: boolean;
  questionIndexLabel: string | null;
  questionText: string | null;
  feedbackStatusLabel: string | null;
};

export type WorkbenchSelectedAnswerContextViewModel = {
  questionId: string;
  questionIndex: number;
  questionLabel: string;
  answerId: string;
  answerIndex: number;
  answerLabel: string;
  answerTimeLabel: string;
  feedbackStatusLabel: string;
};

export type WorkbenchAnswerQuickReviewViewModel = {
  answerId: string;
  scoreLabel: string;
  maturityLabel: string;
  suggestion: string;
  statusLabel: string;
  createdAtLabel: string;
};

export type WorkbenchTimelineEventKind =
  | "system_question"
  | "user_answer"
  | "quick_review"
  | "system_hint";

export type WorkbenchTimelineEventViewModel = {
  id: string;
  kind: WorkbenchTimelineEventKind;
  alignment: "left" | "right";
  questionId: string;
  answerId: string | null;
  metaLabel: string;
  text: string;
  quickReview: WorkbenchAnswerQuickReviewViewModel | null;
  pinnedQuestionContext: boolean;
};

export type WorkbenchTimelineViewModel = {
  events: WorkbenchTimelineEventViewModel[];
};

type WorkbenchStickyQuestionContextOptions = {
  selectedProgressNode?: WorkbenchProgressNode | null;
  selectedProgressNodeDetailRef?: string | null;
};

export type WorkbenchStickyQuestionContextMetaItem = {
  key: "node" | "theme" | "category" | "status" | "question" | "feedback";
  label: string;
  value: string;
};

export function buildQuestionConversationAutoScrollTrigger(params: WorkbenchQuestionConversationAutoScrollTrigger): string | null {
  if (
    params.focusedQuestionId === null &&
    params.selectedProgressNodeRef === null &&
    params.latestAnswerId === null &&
    params.latestFeedbackId === null
  ) {
    return null;
  }
  return [
    params.focusedQuestionId ?? "",
    params.selectedProgressNodeRef ?? "",
    params.latestAnswerId ?? "",
    params.latestFeedbackId ?? "",
  ].join("|");
}

export function shouldAutoScrollQuestionConversation(params: {
  nextTrigger: string | null;
  previousTrigger: string | null;
  hasUserManuallyScrolled: boolean;
}): boolean {
  if (params.nextTrigger === null) {
    return false;
  }
  if (params.nextTrigger === params.previousTrigger) {
    return false;
  }
  return true;
}

export function shouldCollapseCurrentQuestionText(
  questionText: string,
  options: { isExpanded?: boolean; threshold?: number } = {},
): boolean {
  const isExpanded = options.isExpanded ?? false;
  const threshold = options.threshold ?? WORKBENCH_STICKY_QUESTION_TEXT_COLLAPSE_THRESHOLD;
  if (questionText.length <= threshold) {
    return false;
  }
  return !isExpanded;
}

export function shouldRenderQuestionBubbleInConversation(
  _questionId: string,
  _focusedQuestionIdWithStickyContext: string | null,
): boolean {
  return true;
}

type InterviewListError = {
  message: string;
  details: string;
  unauthorized: boolean;
};

type InterviewCreateFormValues = {
  mode?: "polish";
  resume_job_binding_id?: string;
  polish_theme?: PolishTheme;
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
    polish_theme: values.polish_theme ?? "mixed",
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

export function isPolishAiTaskRunningStatus(status: string | null | undefined): boolean {
  return POLISH_AI_TASK_RUNNING_STATUSES.includes(status as (typeof POLISH_AI_TASK_RUNNING_STATUSES)[number]);
}

export function isPolishAiTaskFinalStatus(status: string | null | undefined): boolean {
  return POLISH_AI_TASK_FINAL_STATUSES.includes(status as (typeof POLISH_AI_TASK_FINAL_STATUSES)[number]);
}

async function waitForPolishFeedbackTaskResult(aiTaskId: string): Promise<void> {
  for (let attempt = 0; attempt < POLISH_FEEDBACK_TASK_POLL_ATTEMPTS; attempt += 1) {
    const result = await fetchPolishAiTaskResult(aiTaskId);
    if (isPolishAiTaskFinalStatus(result.status)) {
      return;
    }
    await delay(POLISH_FEEDBACK_TASK_POLL_INTERVAL_MS);
  }
  throw new Error("反馈生成仍在进行中，请稍后刷新查看结果。");
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export function mapFeedbackCodeToDisplay(code: string | null | undefined): {
  text: string;
  rawCode: string | null;
  isKnownCode: boolean;
} {
  const trimmedCode = toOptionalText(code);
  if (trimmedCode === null) {
    return {
      text: CODE_NOT_AVAILABLE_TEXT,
      rawCode: null,
      isKnownCode: false,
    };
  }

  const normalizedCode = trimmedCode.toLowerCase();
  const mappedText = FEEDBACK_CODE_DISPLAY_MAP[normalizedCode];
  if (mappedText !== undefined) {
    return {
      text: mappedText,
      rawCode: trimmedCode,
      isKnownCode: true,
    };
  }

  return {
    text: CODE_NOT_AVAILABLE_TEXT,
    rawCode: trimmedCode,
    isKnownCode: false,
  };
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
      session.polish_theme_label,
      session.polish_theme,
      session.topic_id,
      session.subtopic_id,
      session.custom_topic_text_summary,
      session.session_id,
    ].some((value) => (value ?? "").toLowerCase().includes(keyword)),
  );
}

export function filterVisiblePolishSessions(sessions: readonly PolishSessionSummary[]): PolishSessionSummary[] {
  return sessions.filter((session) => session.status !== "deleted");
}

export function hasPolishSessionReport(session: PolishSessionSummary): boolean {
  return Boolean(session.report_id && session.report_status !== "failed");
}

export function canEndPolishSessionSummary(session: PolishSessionSummary): boolean {
  return session.status === "running";
}

export function buildPolishSessionReportDialogViewModel(session: PolishSessionSummary): {
  title: "面试报告";
  reportId: string;
  reportStatus: string;
  generatedAt: string | null;
  emptyDescription: string;
} | null {
  if (!hasPolishSessionReport(session) || !session.report_id) {
    return null;
  }
  return {
    title: "面试报告",
    reportId: session.report_id,
    reportStatus: session.report_status ?? "unknown",
    generatedAt: session.report_generated_at ?? null,
    emptyDescription: "当前报告尚未返回可展示分项，暂不臆造报告内容。",
  };
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

function toPolishThemeLabel(session: { polish_theme_label?: string | null; polish_theme?: string | null }): string {
  if (session.polish_theme_label) {
    return session.polish_theme_label;
  }
  const themeOption = POLISH_THEME_OPTIONS.find((option) => option.value === session.polish_theme);
  return themeOption?.label ?? session.polish_theme ?? "混合";
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

type PolishSessionTurnForClipboard = PolishSessionDetail["turns"][number];

type ProgressTreePathInfo = {
  categoryTitle: string | null;
  nodeTitle: string | null;
  pathLabel: string;
};

const WORKBENCH_PROGRESS_NODE_KIND_LABELS: Record<WorkbenchProgressNodeKind, string> = {
  group: "分类",
  node: "能力节点",
  question: "题目",
};

export function buildPolishSessionClipboardMarkdown(session: PolishSessionDetail): string {
  const progressPercent = getSessionProgressPercent(session);
  const rows: string[] = [
    "# 模拟面试基本信息",
    "",
    `- 岗位信息：${toDisplayJobTitle(session)}`,
    `- 简历信息：${toDisplayResumeTitle(session)}`,
    `- 当前节点：${toCurrentNodeLabel(session)}`,
    `- 能力主题：${toPolishThemeLabel(session)}`,
    `- 打磨主题：${toTopicLabel(session)}`,
    `- 当前进度：${progressPercent}%`,
    `- 当前节点表现：${WORKBENCH_NODE_SCORE_PLACEHOLDER}`,
    `- 当前模拟面试状态：${toSessionStatusLabel(session.session_status)}`,
    `- 创建时间：${toDisplayDate(session.created_at)}`,
    `- 更新时间：${toDisplayDate(session.updated_at)}`,
    `- 复制时间：${toDisplayDate(new Date().toISOString())}`,
    "",
    "# 进展树",
    "",
    ...buildProgressTreeClipboardRows(session),
    "",
    "# 题目信息",
    "",
  ];

  if (session.turns.length === 0) {
    rows.push("暂无题目。");
    return rows.join("\n");
  }

  session.turns.forEach((turn, turnIndex) => {
    const pathInfo = resolveProgressTreePathInfo(session, turn.progress_node_ref);
    const questionTitle = pathInfo.nodeTitle ?? `题目 ${turnIndex + 1}`;
    rows.push(`## 题目 ${turnIndex + 1}：${questionTitle}`);
    rows.push("");
    rows.push(`- 所属分类：${pathInfo.categoryTitle ?? "未关联分类"}`);
    rows.push(`- 所属节点：${pathInfo.pathLabel}`);
    rows.push(`- 状态：${progressNodeStatusLabel(resolveQuestionTurnStatus(session, turn))}`);
    rows.push(`- 创建时间：${toDisplayDate(turn.question_created_at)}`);
    appendQuestionDetailMarkdown(rows, turn, "###");
    if (turnIndex < session.turns.length - 1) {
      rows.push("");
    }
  });

  return rows.join("\n");
}

export function buildProgressTreeNodeClipboardMarkdown(
  session: PolishSessionDetail,
  node: WorkbenchProgressNode | null | undefined,
): string {
  if (!node) {
    return ["# 节点信息", "", "节点标题：未选中节点", "节点类型：未知", "状态：未知"].join("\n");
  }

  if (isQuestionNode(node)) {
    const turn = session.turns.find((item) => item.question_id === node.questionId) ?? null;
    const pathInfo = resolveProgressTreePathInfo(session, turn?.progress_node_ref ?? node.questionTargetRef);
    const rows = [
      "# 节点信息",
      "",
      `节点标题：${node.title}`,
      `节点类型：${WORKBENCH_PROGRESS_NODE_KIND_LABELS[node.kind]}`,
      `题目状态：${progressNodeStatusLabel(node.status)}`,
      `能力主题：${toPolishThemeLabel(session)}`,
      `所属节点：${pathInfo.pathLabel}`,
    ];

    if (turn === null) {
      rows.push("", "## 题目正文", "", node.detail || FALLBACK_QUESTION_TEXT);
      rows.push("", "## 用户回答", "", FALLBACK_ANSWER_TEXT);
      rows.push("", "## 本轮反馈", "", FALLBACK_FEEDBACK_TEXT);
      return rows.join("\n");
    }

    appendQuestionDetailMarkdown(rows, turn, "##");
    return rows.join("\n");
  }

  const pathInfo = node.kind === "node"
    ? resolveProgressTreePathInfo(session, node.questionTargetRef ?? node.key)
    : null;
  const questionNodes = collectQuestionNodes(node);
  const rows = [
    "# 节点信息",
    "",
    `节点标题：${node.title}`,
    `节点类型：${WORKBENCH_PROGRESS_NODE_KIND_LABELS[node.kind]}`,
    `状态：${progressNodeStatusLabel(node.status)}`,
    `所属节点：${pathInfo?.pathLabel ?? node.title}`,
  ];
  if (node.detail) {
    rows.push(`说明：${node.detail}`);
  }

  rows.push("", "## 下属题目");
  if (questionNodes.length === 0) {
    rows.push("- 暂无题目");
  } else {
    questionNodes.forEach((questionNode) => {
      rows.push(
        `- ${questionNode.title} · ${progressNodeStatusLabel(questionNode.status)}${
          questionNode.detail ? ` · ${questionNode.detail}` : ""
        }`,
      );
    });
  }

  return rows.join("\n");
}

function appendQuestionDetailMarkdown(
  rows: string[],
  turn: PolishSessionTurnForClipboard,
  headingPrefix: "##" | "###",
): void {
  rows.push("");
  rows.push(`${headingPrefix} 题目正文`);
  rows.push("");
  rows.push(toClipboardText(turn.question_text, FALLBACK_QUESTION_TEXT));
  rows.push("");
  rows.push(`${headingPrefix} 用户回答`);
  rows.push("");
  if (turn.answers.length === 0) {
    rows.push(FALLBACK_ANSWER_TEXT);
  } else {
    turn.answers.forEach((answer) => {
      rows.push(`#### 回答 ${answer.answer_round}`);
      rows.push("");
      rows.push(toClipboardText(answer.answer_text, FALLBACK_ANSWER_TEXT));
      rows.push("");
    });
    trimTrailingEmptyRows(rows);
  }

  rows.push("");
  rows.push(`${headingPrefix} 本轮反馈`);
  rows.push("");
  if (turn.answers.length === 0) {
    rows.push(FALLBACK_FEEDBACK_TEXT);
    return;
  }
  turn.answers.forEach((answer) => {
    rows.push(`#### 反馈 ${answer.answer_round}`);
    rows.push("");
    rows.push(toClipboardText(answer.feedback_text || answer.feedback_payload?.feedback_text, FALLBACK_FEEDBACK_TEXT));
    rows.push("");
  });
  trimTrailingEmptyRows(rows);
}

function buildProgressTreeClipboardRows(session: PolishSessionDetail): string[] {
  const progressNodes = buildWorkbenchProgressNodes(session);
  if (progressNodes.length === 0) {
    return ["- 进展树暂未生成"];
  }

  const currentPriorityRef = session.progress_tree_state.current_priority?.progress_node_ref ?? null;
  const rows: string[] = [];
  const appendNode = (node: WorkbenchProgressNode, depth: number) => {
    const indent = "  ".repeat(depth);
    const isCurrentPriority = node.kind === "node" && node.questionTargetRef === currentPriorityRef;
    rows.push(
      `${indent}- ${node.title} · ${progressNodeStatusLabel(node.status)}${
        isCurrentPriority ? " · 当前优先" : ""
      }`,
    );
    node.children?.forEach((child) => appendNode(child, depth + 1));
  };

  progressNodes.forEach((node) => appendNode(node, 0));
  return rows;
}

function collectQuestionNodes(node: WorkbenchProgressNode): WorkbenchProgressNode[] {
  const children = node.children ?? [];
  return [
    ...(isQuestionNode(node) ? [node] : []),
    ...children.flatMap((child) => collectQuestionNodes(child)),
  ];
}

function resolveProgressTreePathInfo(
  session: PolishSessionDetail,
  progressNodeRef: string | null | undefined,
): ProgressTreePathInfo {
  const path = findProgressTreeNodePathByRef(session.progress_tree_plan.nodes, progressNodeRef);
  if (path === null || path.length === 0) {
    return {
      categoryTitle: null,
      nodeTitle: null,
      pathLabel: "未关联节点",
    };
  }

  const categoryTitle = resolveProgressTreePathCategoryTitle(path);
  const pathTitles = path.map((item) => resolveProgressNodeTitle(item));
  return {
    categoryTitle,
    nodeTitle: pathTitles[pathTitles.length - 1] ?? null,
    pathLabel: [categoryTitle, ...pathTitles].filter(Boolean).join(" / "),
  };
}

function findProgressTreeNodePathByRef(
  nodes: readonly PolishProgressTreeNode[],
  progressNodeRef: string | null | undefined,
  ancestors: readonly PolishProgressTreeNode[] = [],
): PolishProgressTreeNode[] | null {
  if (!progressNodeRef) {
    return null;
  }

  for (const node of nodes) {
    const nextPath = [...ancestors, node];
    if (node.progress_node_ref === progressNodeRef) {
      return nextPath;
    }
    const childPath = findProgressTreeNodePathByRef(node.children ?? [], progressNodeRef, nextPath);
    if (childPath !== null) {
      return childPath;
    }
  }

  return null;
}

function resolveProgressTreePathCategoryTitle(path: readonly PolishProgressTreeNode[]): string {
  for (const node of path) {
    const displayNode = node as ProgressTreeDisplayNode;
    const displayCategoryTitle = toSafeProgressTreeText(displayNode.display_category_title);
    if (displayCategoryTitle) {
      return displayCategoryTitle;
    }
    if (displayNode.category === "resume_deep_dive" || displayNode.category === "jd_gap_learning") {
      return INTERVIEW_PROGRESS_TREE_CATEGORY_TITLE_BY_CATEGORY[displayNode.category];
    }
  }
  return INTERVIEW_PROGRESS_TREE_OTHER_CATEGORY_TITLE;
}

function getSessionProgressPercent(session: PolishSessionDetail): number {
  return Math.max(0, Math.min(100, session.progress_tree_state.progress?.progress_percent ?? session.progress_percent ?? 0));
}

function toSessionStatusLabel(status: string | null | undefined): string {
  if (status === "ended" || status === "completed") {
    return "已结束";
  }
  if (status === "active" || status === "running" || status === "in_progress") {
    return "进行中";
  }
  return status?.trim() || "未知";
}

function toClipboardText(value: string | null | undefined, fallback: string): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : fallback;
}

function trimTrailingEmptyRows(rows: string[]): void {
  while (rows[rows.length - 1] === "") {
    rows.pop();
  }
}

type PolishSessionReadableHeader = PolishSessionDetail | PolishSessionSummary;

export function toDisplayJobTitle(session: PolishSessionReadableHeader): string {
  return session.job_title || FALLBACK_JOB_TITLE;
}

export function toDisplayResumeTitle(session: PolishSessionReadableHeader): string {
  return session.resume_title || FALLBACK_RESUME_TITLE;
}

export function resolveCurrentQuestionId(
  session: PolishSessionDetail,
  progressNodeRef: string | null = null,
): string | null {
  return resolveCurrentQuestionState(session, progressNodeRef)?.questionId ?? null;
}

export function buildStickyQuestionContextViewModel(
  session: PolishSessionDetail | null,
  focusedQuestionId: string | null,
  selectedProgressNodeRef: string | null,
  options: WorkbenchStickyQuestionContextOptions = {},
):
  | WorkbenchStickyQuestionContextViewModel
  | null {
  if (session === null) {
    return null;
  }

  const selectedProgressNode = options.selectedProgressNode ?? null;
  const focusedTurn = focusedQuestionId === null
    ? null
    : session.turns.find((item) => item.question_id === focusedQuestionId) ?? null;
  const hasExplicitSelectedProgressNode = Object.prototype.hasOwnProperty.call(options, "selectedProgressNode");
  const progressNodeRef =
    options.selectedProgressNodeDetailRef ??
    selectedProgressNodeRef ??
    getWorkbenchProgressNodeQuestionTargetRef(selectedProgressNode) ??
    (hasExplicitSelectedProgressNode ? null : focusedTurn?.progress_node_ref) ??
    session.progress_tree_state.current_priority?.progress_node_ref ??
    null;
  const selectedNode = findProgressTreeNodeByRef(
    session.progress_tree_plan.nodes,
    progressNodeRef,
  );
  const nodeTitle = selectedNode === null
    ? WORKBENCH_STICKY_NODE_EMPTY_TITLE
    : resolveProgressNodeTitle(selectedNode);
  const nodeCategory = selectedNode === null
    ? "未选择节点分类"
    : resolveProgressNodeCategoryTitle(selectedNode);
  const nodeStatusLabel = resolveStickyProgressNodeStatusLabel(session, progressNodeRef, selectedProgressNode);
  const nodeSummary = resolveStickyProgressNodeSummary(session, progressNodeRef);
  const selectedQuestionState = resolveQuestionNodeState(session, selectedProgressNode);
  const focusedQuestionBelongsToProgressNode = focusedTurn !== null && (
    progressNodeRef === null ||
    focusedTurn.progress_node_ref === progressNodeRef
  );
  const selectedQuestionId = hasExplicitSelectedProgressNode
    ? selectedQuestionState?.questionId ?? (focusedQuestionBelongsToProgressNode ? focusedTurn?.question_id ?? null : null)
    : focusedQuestionId;
  const selectedQuestionIndex = selectedQuestionId === null
    ? -1
    : session.turns.findIndex((turn) => turn.question_id === selectedQuestionId);
  const turn = selectedQuestionIndex === -1 ? null : session.turns[selectedQuestionIndex];
  const latestAnswer = turn !== null && turn.answers.length > 0 ? turn.answers[turn.answers.length - 1] : null;
  const feedbackStatusLabel = turn === null
    ? null
    : mapFeedbackCodeToDisplay(latestAnswer?.feedback_payload?.status ?? null).text;

  return {
    focusedQuestionId: turn?.question_id ?? null,
    selectedQuestionId: turn?.question_id ?? null,
    progressNodeRef,
    progressNodeTitle: nodeTitle,
    capabilityThemeLabel: toPolishThemeLabel(session),
    nodeCategoryLabel: nodeCategory,
    nodeStatusLabel,
    nodeSummary,
    emptyDescription: selectedNode === null ? WORKBENCH_STICKY_NODE_EMPTY_DESCRIPTION : null,
    nonQuestionHint: turn === null && selectedNode !== null ? WORKBENCH_STICKY_NODE_WITHOUT_SELECTED_QUESTION_HINT : null,
    shouldShowQuestionContext: turn !== null,
    questionIndexLabel: turn === null ? null : `题目 ${selectedQuestionIndex + 1}`,
    questionText: turn === null ? null : turn.question_text || FALLBACK_QUESTION_TEXT,
    feedbackStatusLabel,
  };
}

export function buildStickyQuestionContextCompactMetaItems(
  stickyQuestionContext: WorkbenchStickyQuestionContextViewModel,
): WorkbenchStickyQuestionContextMetaItem[] {
  const items: WorkbenchStickyQuestionContextMetaItem[] = [
    { key: "status", label: "状态", value: stickyQuestionContext.nodeStatusLabel },
  ];
  if (stickyQuestionContext.feedbackStatusLabel !== null) {
    items.push({ key: "feedback", label: "反馈", value: stickyQuestionContext.feedbackStatusLabel });
  }
  return items;
}

function resolveStickyProgressNodeStatusLabel(
  session: PolishSessionDetail,
  progressNodeRef: string | null,
  selectedProgressNode: WorkbenchProgressNode | null,
): string {
  const stateStatus = progressNodeRef === null
    ? null
    : session.progress_tree_state.node_states.find((item) => item.progress_node_ref === progressNodeRef)?.status ?? null;
  return progressNodeStatusLabel((stateStatus ?? selectedProgressNode?.status ?? "pending") as WorkbenchProgressNode["status"]);
}

function resolveStickyProgressNodeSummary(
  session: PolishSessionDetail,
  progressNodeRef: string | null,
): string | null {
  if (progressNodeRef === null) {
    return null;
  }
  const bannerContent = buildProgressTreeContextBannerContent(session, progressNodeRef);
  const depthRequirement = bannerContent.depthRequirement?.trim();
  if (depthRequirement) {
    return depthRequirement;
  }
  const expandedSections = buildProgressTreeContextBannerExpandedSections(bannerContent);
  return expandedSections.flatMap((section) => section.items)[0] ?? null;
}

export function resolveCurrentQuestionState(
  session: PolishSessionDetail,
  progressNodeRef: string | null = null,
): WorkbenchCurrentQuestionState | null {
  const turn = progressNodeRef !== null
    ? getLatestTurnForProgressNode(session, progressNodeRef)
    : getLatestTurn(session);
  if (turn === null) {
    return null;
  }
  return {
    questionId: turn.question_id,
    progressNodeRef: turn.progress_node_ref ?? null,
    status: resolveQuestionTurnStatus(session, turn),
  };
}

function getLatestTurn(session: PolishSessionDetail) {
  return session.turns.length > 0 ? session.turns[session.turns.length - 1] : null;
}

function getLatestTurnForProgressNode(session: PolishSessionDetail, progressNodeRef: string) {
  const matchingTurns = session.turns.filter((turn) => turn.progress_node_ref === progressNodeRef);
  return matchingTurns.length > 0 ? matchingTurns[matchingTurns.length - 1] : null;
}

function resolveQuestionLatestAnswer(
  session: PolishSessionDetail,
  questionId: string | null,
): PolishSessionAnswer | null {
  if (questionId === null) {
    return null;
  }
  const questionTurn = session.turns.find((turn) => turn.question_id === questionId) ?? null;
  if (questionTurn === null) {
    return null;
  }
  return questionTurn.answers.length > 0 ? questionTurn.answers[questionTurn.answers.length - 1] : null;
}

function resolveQuestionTurnStatus(
  session: PolishSessionDetail,
  turn: PolishSessionDetail["turns"][number],
): WorkbenchQuestionStatus {
  return isQuestionCompleted(session, turn) ? "completed" : "in_progress";
}

function isQuestionCompleted(
  session: PolishSessionDetail,
  turn: PolishSessionDetail["turns"][number],
): boolean {
  const completedFocusRefs = session.progress_tree_state.completed_focus_refs ?? [];
  if (completedFocusRefs.some((item) => item.question_id === turn.question_id)) {
    return true;
  }
  if (completedFocusRefs.some((item) => item.progress_node_ref === turn.progress_node_ref)) {
    return false;
  }
  if (!turn.progress_node_ref || completedFocusRefs.length > 0) {
    return false;
  }
  const nodeState = session.progress_tree_state.node_states.find(
    (item) => item.progress_node_ref === turn.progress_node_ref,
  );
  return nodeState?.status === "completed" && nodeState.completed_questions_count > 0;
}

export function isQuestionNode(
  node: WorkbenchProgressNode | null | undefined,
): node is WorkbenchProgressNode & { kind: "question"; questionId: string } {
  return node?.kind === "question" && typeof node.questionId === "string" && node.questionId.length > 0;
}

export function resolveQuestionNodeState(
  session: PolishSessionDetail,
  node: WorkbenchProgressNode | null | undefined,
): WorkbenchCurrentQuestionState | null {
  if (!isQuestionNode(node)) {
    return null;
  }
  const turn = session.turns.find((item) => item.question_id === node.questionId) ?? null;
  if (turn === null) {
    return null;
  }
  return {
    questionId: turn.question_id,
    progressNodeRef: turn.progress_node_ref ?? node.questionTargetRef ?? null,
    status: resolveQuestionTurnStatus(session, turn),
  };
}

export function canFollowUpCurrentQuestion(params: {
  isQuestionNode: boolean;
  canSendAnswer: boolean;
  hasCurrentQuestionAnswer: boolean;
  hasCurrentQuestionFeedback: boolean;
  isFollowUpQuestionApiSupported: boolean;
}): boolean {
  return Boolean(
    params.isQuestionNode &&
    params.canSendAnswer &&
    params.isFollowUpQuestionApiSupported &&
    (params.hasCurrentQuestionAnswer || params.hasCurrentQuestionFeedback),
  );
}

export function canRegenerateQuestionForCurrentNode(params: {
  canCreateQuestionTask: boolean;
  isQuestionNode: boolean;
  currentQuestionProgressNodeRef: string | null;
  selectedProgressNodeRef: string | null;
}): boolean {
  if (!params.canCreateQuestionTask) {
    return false;
  }
  return params.isQuestionNode
    ? params.currentQuestionProgressNodeRef !== null || params.selectedProgressNodeRef !== null
    : params.selectedProgressNodeRef !== null;
}

export function deriveRegenerateQuestionDisabledReason(params: {
  canCreateQuestionTask: boolean;
  isQuestionNode: boolean;
  currentQuestionProgressNodeRef: string | null;
  selectedProgressNodeRef: string | null;
}): string | null {
  if (params.canCreateQuestionTask) {
    return null;
  }
  if (params.currentQuestionProgressNodeRef === null && params.selectedProgressNodeRef === null) {
    return INTERVIEW_WORKBENCH_REGENERATE_CURRENT_NODE_NO_NODE_TOOLTIP;
  }
  return params.isQuestionNode
    ? "当前题目上下文异常，暂不可执行换题"
    : "题目生成中，暂不可执行换题";
}

export function canMarkCurrentQuestionCompleted(params: {
  hasCurrentQuestion: boolean;
  hasCurrentQuestionFeedback: boolean;
  isCurrentQuestionCompleted: boolean;
}): boolean {
  return Boolean(params.hasCurrentQuestion && params.hasCurrentQuestionFeedback && !params.isCurrentQuestionCompleted);
}

export function shouldConfirmBeforeRegenerateQuestion(answerText: string): boolean {
  return answerText.trim().length > 0;
}

export type WorkbenchQuestionComposerActionViewModel = {
  sendAnswerButtonLabel: "发送" | "发送回答";
  sendAnswerPlaceholder: string;
  showFollowUpCurrentQuestionButton: boolean;
  canFollowUpCurrentQuestion: boolean;
  canRegenerateCurrentQuestion: boolean;
  regenerateQuestionDisabledReason: string | null;
  canMarkCurrentQuestionCompleted: boolean;
  followUpCurrentQuestionDisabledReason: string | null;
  markCurrentQuestionCompletedDisabledReason: string;
  shouldConfirmBeforeRegenerateQuestion: boolean;
  regenerateQuestionButtonCopy: string;
  followUpQuestionParentQuestionId: string | null;
  followUpQuestionParentAnswerId: string | null;
  followUpQuestionParentFeedbackId: string | null;
};

export function deriveComposerActionViewModel(params: {
  session: PolishSessionDetail | null;
  questionActionState: WorkbenchQuestionActionState;
  answerText: string;
  isFollowUpQuestionApiSupported?: boolean;
  selectedProgressNodeRef?: string | null;
}): WorkbenchQuestionComposerActionViewModel {
  const isFollowUpQuestionApiSupported = params.isFollowUpQuestionApiSupported ?? false;

  const canFollowUpCurrentQuestionResult = canFollowUpCurrentQuestion({
    isQuestionNode: params.questionActionState.isQuestionNode,
    canSendAnswer: params.questionActionState.canSendAnswer,
    hasCurrentQuestionAnswer: params.questionActionState.hasCurrentQuestionAnswer,
    hasCurrentQuestionFeedback: params.questionActionState.hasCurrentQuestionFeedback,
    isFollowUpQuestionApiSupported,
  });

  const sendAnswerPlaceholder = params.questionActionState.canSendAnswer
    ? (params.questionActionState.hasCurrentQuestionAnswer
      ? INTERVIEW_WORKBENCH_SEND_RETRY_PLACEHOLDER
      : INTERVIEW_WORKBENCH_SEND_ANSWER_PLACEHOLDER)
    : INTERVIEW_WORKBENCH_SEND_DISABLED_PLACEHOLDER;

  const canCreateQuestionTask = params.questionActionState.canSendAnswer || params.questionActionState.canGenerateQuestion;
  const canRegenerateCurrentQuestion = canRegenerateQuestionForCurrentNode({
    canCreateQuestionTask,
    isQuestionNode: params.questionActionState.isQuestionNode,
    currentQuestionProgressNodeRef: params.questionActionState.currentQuestionProgressNodeRef,
    selectedProgressNodeRef: params.selectedProgressNodeRef ?? null,
  });
  const regenerateQuestionDisabledReason = deriveRegenerateQuestionDisabledReason({
    canCreateQuestionTask,
    isQuestionNode: params.questionActionState.isQuestionNode,
    currentQuestionProgressNodeRef: params.questionActionState.currentQuestionProgressNodeRef,
    selectedProgressNodeRef: params.selectedProgressNodeRef ?? null,
  });
  const regenerateQuestionButtonCopy = params.questionActionState.isQuestionNode
    ? INTERVIEW_WORKBENCH_REGENERATE_CURRENT_QUESTION_BUTTON
    : INTERVIEW_WORKBENCH_REGENERATE_NODE_BUTTON;

  const canMark = canMarkCurrentQuestionCompleted({
    hasCurrentQuestion: params.questionActionState.hasCurrentQuestion,
    hasCurrentQuestionFeedback: params.questionActionState.hasCurrentQuestionFeedback,
    isCurrentQuestionCompleted: params.questionActionState.isCurrentQuestionCompleted,
  });

  return {
    sendAnswerButtonLabel: "发送",
    sendAnswerPlaceholder,
    showFollowUpCurrentQuestionButton: params.questionActionState.isQuestionNode,
    canFollowUpCurrentQuestion: canFollowUpCurrentQuestionResult,
    canRegenerateCurrentQuestion,
    regenerateQuestionDisabledReason,
    canMarkCurrentQuestionCompleted: canMark,
    followUpCurrentQuestionDisabledReason: !params.questionActionState.canSendAnswer
      ? INTERVIEW_WORKBENCH_SEND_DISABLED_PLACEHOLDER
      : (!isFollowUpQuestionApiSupported
        ? INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_UNSUPPORTED
        : !canFollowUpCurrentQuestionResult
          ? INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_DISABLED_WITHOUT_HISTORY
          : null),
    markCurrentQuestionCompletedDisabledReason: canMark
      ? ""
      : INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_DISABLED_WITHOUT_FEEDBACK,
    shouldConfirmBeforeRegenerateQuestion: shouldConfirmBeforeRegenerateQuestion(params.answerText),
    regenerateQuestionButtonCopy,
    followUpQuestionParentQuestionId: params.questionActionState.currentQuestionId,
    followUpQuestionParentAnswerId: params.questionActionState.currentQuestionLatestAnswerId,
    followUpQuestionParentFeedbackId: params.questionActionState.currentQuestionLatestFeedbackId,
  };
}

export function deriveWorkbenchQuestionActionState(params: {
  session: PolishSessionDetail | null;
  selectedProgressNode: WorkbenchProgressNode | null;
  progressNodeRef: string | null;
  canShowProgressTree: boolean;
  creatingQuestion: boolean;
  submittingAnswer: boolean;
  feedbackGenerating: boolean;
  completingQuestion: boolean;
  endingSession: boolean;
}): WorkbenchQuestionActionState {
  const selectedQuestionState = params.session === null
    ? null
    : resolveQuestionNodeState(params.session, params.selectedProgressNode);
  const currentQuestionState = params.session === null
    ? null
    : selectedQuestionState ?? resolveCurrentQuestionState(params.session, params.progressNodeRef);
  const isSelectedQuestionNode = selectedQuestionState !== null;
  const hasCurrentQuestion = currentQuestionState !== null;
  const isCurrentQuestionCompleted = currentQuestionState?.status === "completed";
  const currentQuestionLatestAnswer = params.session === null
    ? null
    : resolveQuestionLatestAnswer(params.session, currentQuestionState?.questionId ?? null);
  const hasCurrentQuestionAnswer = currentQuestionLatestAnswer !== null;
  const hasCurrentQuestionFeedback = answerHasGeneratedFeedback(currentQuestionLatestAnswer);
  const isBusy =
    params.creatingQuestion ||
    params.submittingAnswer ||
    params.feedbackGenerating ||
    params.completingQuestion ||
    params.endingSession;
  const canUseSession = params.session !== null && !isPolishSessionEnded(params.session) && !isBusy;

  return {
    currentQuestionId: currentQuestionState?.questionId ?? null,
    currentQuestionStatus: currentQuestionState?.status ?? null,
    currentQuestionProgressNodeRef: currentQuestionState?.progressNodeRef ?? null,
    currentQuestionLatestAnswerId: currentQuestionLatestAnswer?.answer_id ?? null,
    currentQuestionLatestFeedbackId: currentQuestionLatestAnswer?.feedback_id ?? currentQuestionLatestAnswer?.feedback_payload?.feedback_id ?? null,
    hasCurrentQuestionAnswer,
    hasCurrentQuestionFeedback,
    isQuestionNode: isSelectedQuestionNode,
    hasCurrentQuestion,
    isCurrentQuestionCompleted,
    canSendAnswer: canUseSession && isSelectedQuestionNode,
    canRegenerateQuestion: canRegenerateQuestionForCurrentNode({
      canCreateQuestionTask: canUseSession,
      isQuestionNode: isSelectedQuestionNode,
      currentQuestionProgressNodeRef: currentQuestionState?.progressNodeRef ?? null,
      selectedProgressNodeRef: params.progressNodeRef,
    }),
    canGenerateQuestion:
      canUseSession &&
      params.canShowProgressTree &&
      !(hasCurrentQuestion && !isCurrentQuestionCompleted),
    canMarkQuestionCompleted: canUseSession && canMarkCurrentQuestionCompleted({
      hasCurrentQuestion,
      hasCurrentQuestionFeedback,
      isCurrentQuestionCompleted,
    }),
  };
}

export function shouldAutoCreateQuestionForProgressNode(
  session: PolishSessionDetail,
  progressNodeRef: string | null,
): boolean {
  void session;
  void progressNodeRef;
  return false;
}

export function canAutoCreateQuestionFromProgressNode(params: {
  session: PolishSessionDetail;
  progressNodeRef: string | null;
  creatingQuestion: boolean;
  submittingAnswer: boolean;
  feedbackGenerating: boolean;
}): boolean {
  const canUseProgressTreePlan = ["ready", "refresh_failed"].includes(params.session.progress_tree_status);
  return Boolean(
    params.progressNodeRef &&
      canUseProgressTreePlan &&
      shouldAutoCreateQuestionForProgressNode(params.session, params.progressNodeRef) &&
      !params.creatingQuestion &&
      !params.submittingAnswer &&
      !params.feedbackGenerating,
  );
}

export function isProgressTreePendingGeneration(status: string | null | undefined): boolean {
  return status === "pending" || status === "generating";
}

export function resolveProgressTreeRecoveryAction(
  status: string | null | undefined,
): "generate" | "refresh" | "none" {
  if (status === "pending" || status === "failed") {
    return "generate";
  }
  if (status === "refresh_failed") {
    return "refresh";
  }
  return "none";
}

export interface ProgressWriteErrorRecovery {
  action: "reload_session";
  message: string;
  failureState: "progressRefreshFailed";
}

export function resolveProgressWriteErrorRecovery(error: unknown): ProgressWriteErrorRecovery | null {
  const errorCode = isApiHttpError(error)
    ? error.code
    : typeof error === "object" && error !== null && "code" in error && typeof error.code === "string"
      ? error.code
      : null;
  if (errorCode !== "stale_version_conflict") {
    return null;
  }
  return {
    action: "reload_session",
    failureState: "progressRefreshFailed",
    message: "会话状态已刷新，请基于最新进展继续操作。",
  };
}

function isPolishSessionEnded(session: PolishSessionDetail | null): boolean {
  return session?.session_status === "ended";
}

function resolveQuestionGenerationProgressNodeRef(
  session: PolishSessionDetail,
  explicitProgressNodeRef: string | null | undefined,
  selectedProgressNodeRef: string | null,
): string | null {
  return (
    explicitProgressNodeRef ??
    selectedProgressNodeRef ??
    session.progress_tree_state.current_priority?.progress_node_ref ??
    null
  );
}

function buildSelectedCategoryPath(
  nodes: readonly PolishProgressTreeNode[],
  progressNodeRef: string | null,
): string[] {
  if (progressNodeRef === null) {
    return [];
  }
  for (const node of nodes) {
    const currentPath = [resolveProgressNodeCategoryTitle(node), resolveProgressNodeTitle(node)]
      .filter((item, index, list) => item && list.indexOf(item) === index);
    if (node.progress_node_ref === progressNodeRef) {
      return currentPath;
    }
    const childPath = buildSelectedCategoryPath(node.children ?? [], progressNodeRef);
    if (childPath.length > 0) {
      return [resolveProgressNodeCategoryTitle(node), ...childPath]
        .filter((item, index, list) => item && list.indexOf(item) === index);
    }
  }
  return [];
}

function completedFocusRefsForProgressNode(
  session: PolishSessionDetail,
  progressNodeRef: string | null,
): string[] {
  return (session.progress_tree_state.completed_focus_refs ?? [])
    .filter((item) => item.focus_key && (!progressNodeRef || !item.progress_node_ref || item.progress_node_ref === progressNodeRef))
    .map((item) => item.focus_key!)
    .filter((item, index, list) => list.indexOf(item) === index);
}

function getLatestAnswer(session: PolishSessionDetail): PolishSessionAnswer | null {
  const latestTurn = getLatestTurn(session);
  if (latestTurn === null || latestTurn.answers.length === 0) {
    return null;
  }
  return latestTurn.answers[latestTurn.answers.length - 1];
}

function answerHasGeneratedFeedback(answer: PolishSessionAnswer | null): boolean {
  const feedbackStatus = resolvePolishFeedbackStatus(toOptionalText(answer?.feedback_payload?.status));
  return Boolean(answer?.feedback_id || answer?.feedback_created_at || feedbackStatus !== "pending");
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

function toCurrentNodeCategoryLabel(session: PolishSessionDetail): string {
  const currentNodeRef = resolveSessionCurrentProgressNodeRef(session);
  return resolveProgressTreePathInfo(session, currentNodeRef).categoryTitle ?? "未关联分类";
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
  return answerHasGeneratedFeedback(latestAnswer) ? "feedbackReady" : "questionReady";
}

export function buildWorkbenchProgressNodes(
  session: PolishSessionDetail,
): WorkbenchProgressNode[] {
  const questionNodesByRef = buildQuestionProgressNodesByRef(session);
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
      questionNodesByRef,
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

function buildQuestionProgressNodesByRef(session: PolishSessionDetail): Map<string, WorkbenchProgressNode[]> {
  const questionNodesByRef = new Map<string, WorkbenchProgressNode[]>();
  for (const [turnIndex, turn] of session.turns.entries()) {
    if (!turn.progress_node_ref) {
      continue;
    }
    const shortQuestion = turn.question_text.length > 24 ? `${turn.question_text.slice(0, 21)}...` : turn.question_text;
    const questionNode: WorkbenchProgressNode = {
      key: `question:${turn.question_id}`,
      kind: "question",
      title: `题目 ${turnIndex + 1}`,
      status: resolveQuestionTurnStatus(session, turn),
      detail: shortQuestion,
      questionId: turn.question_id,
      questionTargetRef: turn.progress_node_ref ?? undefined,
    };
    questionNodesByRef.set(turn.progress_node_ref, [
      ...(questionNodesByRef.get(turn.progress_node_ref) ?? []),
      questionNode,
    ]);
  }
  return questionNodesByRef;
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

function buildProgressNodeTechnicalCoverage(node: PolishProgressTreeNode): string[] {
  const childCoverage = node.children
    .map((childNode) =>
      firstSafeProgressTreeText(
        (childNode as ProgressTreeDisplayNode).display_title,
        (childNode as ProgressTreeDisplayNode).exam_point,
        childNode.title,
      ),
    )
    .filter((item): item is string => item !== null);
  if (childCoverage.length > 0) {
    return childCoverage.slice(0, 8);
  }

  const displayNode = node as ProgressTreeDisplayNode;
  const coveragePoints = firstSafeProgressTreeTextList(displayNode.coverage_points, displayNode.sub_points);
  if (coveragePoints.length > 0) {
    return coveragePoints.slice(0, 8);
  }

  return firstSafeProgressTreeTextList(displayNode.follow_up_focus, displayNode.follow_up_directions).slice(0, 5);
}

export function resolveProgressTreeDetailNodeRef(
  session: PolishSessionDetail,
  selectedProgressNodeRef: string | null,
): string | null {
  const planNodes = flattenProgressTreePlanNodes(session.progress_tree_plan.nodes);
  if (selectedProgressNodeRef && planNodes.some((node) => node.progress_node_ref === selectedProgressNodeRef)) {
    return selectedProgressNodeRef;
  }

  const currentSessionRef = resolveSessionCurrentProgressNodeRef(session);
  if (currentSessionRef && planNodes.some((node) => node.progress_node_ref === currentSessionRef)) {
    return currentSessionRef;
  }

  const currentPriorityRef = session.progress_tree_state.current_priority?.progress_node_ref ?? null;
  if (currentPriorityRef && planNodes.some((node) => node.progress_node_ref === currentPriorityRef)) {
    return currentPriorityRef;
  }

  return planNodes[0]?.progress_node_ref ?? null;
}

export function resolveWorkbenchQuestionFocusId(
  session: PolishSessionDetail,
  selectedProgressNode: WorkbenchProgressNode | null,
  progressNodeRef: string | null,
): string | null {
  return (
    resolveQuestionNodeState(session, selectedProgressNode)?.questionId ??
    resolveCurrentQuestionState(session, progressNodeRef)?.questionId ??
    null
  );
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
  const technicalCoverage = buildProgressNodeTechnicalCoverage(node);
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
      technicalCoverage.length > 0 ||
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
    technicalCoverage,
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
      technicalCoverage: [],
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
  const technicalCoverage = buildProgressNodeTechnicalCoverage(node);

  return {
    title,
    depthRequirement,
    followUpDirections,
    lossRisks,
    technicalCoverage,
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
    ...buildProgressTreeContextBannerListSection("technical_coverage", "技术点覆盖", content.technicalCoverage),
    ...buildProgressTreeContextBannerListSection("follow_up_directions", "连续追问方向", content.followUpDirections),
    ...buildProgressTreeContextBannerListSection("loss_risks", "常见失分风险", content.lossRisks),
  ];
}

function toWorkbenchProgressNode(params: {
  node: PolishProgressTreeNode;
  stateByRef: Map<string, WorkbenchProgressNodeStatus>;
  questionNodesByRef: Map<string, WorkbenchProgressNode[]>;
  level: number;
}): WorkbenchProgressNode {
  const children = params.node.children.map((childNode) =>
    toWorkbenchProgressNode({
      node: childNode,
      stateByRef: params.stateByRef,
      questionNodesByRef: params.questionNodesByRef,
      level: params.level + 1,
    }),
  );
  const attachedQuestionNodes = params.questionNodesByRef.get(params.node.progress_node_ref) ?? [];
  const mergedChildren = [...children, ...attachedQuestionNodes];
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
  if (node?.kind === "node") {
    return node.questionTargetRef ?? node.key;
  }
  if (isQuestionNode(node)) {
    return node.questionTargetRef ?? null;
  }
  return null;
}

export function resolveProgressTreeSelectedNodeRefAfterClick(
  node: WorkbenchProgressNode | null | undefined,
  currentSelectedProgressNodeRef: string | null,
): string | null {
  if (node?.kind === "node") {
    return node.key;
  }
  if (isQuestionNode(node)) {
    return node.questionTargetRef ?? currentSelectedProgressNodeRef;
  }
  return currentSelectedProgressNodeRef;
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

export function findWorkbenchProgressNodeByKey(
  nodes: readonly WorkbenchProgressNode[],
  nodeKey: string | null,
): WorkbenchProgressNode | null {
  if (nodeKey === null) {
    return null;
  }
  return flattenWorkbenchProgressNodes(nodes).find((node) => node.key === nodeKey) ?? null;
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
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  isComposing?: boolean;
}): boolean {
  return event.key === "Enter" && Boolean(event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey && !event.isComposing;
}

export function canSubmitAnswerFromKeyboard(
  event: {
    key: string;
    ctrlKey?: boolean;
    metaKey?: boolean;
    shiftKey?: boolean;
    altKey?: boolean;
    isComposing?: boolean;
  },
  canSendAnswer: boolean,
): boolean {
  return canSendAnswer && shouldSubmitAnswerFromKeyboard(event);
}

export function getWorkbenchChatMessageAlignmentClassName(
  kind: WorkbenchChatMessageKind,
): WorkbenchChatMessageAlignmentClassName {
  return INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT[kind] === "right" ? "messageRowRight" : "messageRowLeft";
}

function resolveMessageWidthPolicy(
  isProgressPanelCollapsed: boolean,
  isFeedbackPanelCollapsed: boolean,
): keyof typeof INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY {
  if (isProgressPanelCollapsed && isFeedbackPanelCollapsed) {
    return INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY.bothCollapsed;
  }
  if (isProgressPanelCollapsed) {
    return INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY.progressCollapsed;
  }
  if (isFeedbackPanelCollapsed) {
    return INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY.feedbackCollapsed;
  }
  return INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY.allOpen;
}

function resolveMessageWidthStyle(policy: keyof typeof INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICY): CSSProperties {
  const widthProfile = INTERVIEW_WORKBENCH_MESSAGE_WIDTH_POLICIES[policy];
  return {
    "--workbench-question-bubble-max-width": widthProfile.questionBubbleMaxWidth,
    "--workbench-answer-bubble-max-width": widthProfile.answerBubbleMaxWidth,
    "--workbench-feedback-bubble-max-width": widthProfile.feedbackBubbleMaxWidth,
  } as CSSProperties;
}

export function buildProgressTreeContextMenuItems(
  node: WorkbenchProgressNode | null | undefined,
  actionState: Pick<WorkbenchQuestionActionState, "canMarkQuestionCompleted">,
): WorkbenchProgressTreeContextMenuItem[] {
  return [
    {
      key: "mark_question_completed",
      label: INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS.markQuestionCompleted,
      disabled: !actionState.canMarkQuestionCompleted,
    },
    {
      key: "copy_node_info",
      label: INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS.copyNodeInfo,
      disabled: node === null || node === undefined,
    },
  ];
}

export function shouldCloseProgressTreeContextMenuFromKeyboard(event: { key: string }): boolean {
  return event.key === "Escape";
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
    { key: "theme", label: "能力主题", value: toPolishThemeLabel(session) },
    { key: "category", label: "分类", value: toCurrentNodeCategoryLabel(session) },
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

export function toNextRecommendedActionLabel(action: PolishRecommendedAction): string {
  return NEXT_RECOMMENDED_ACTION_LABELS[action] ?? action;
}

function normalizeRoundNumber(round: number | null | undefined): number {
  if (typeof round !== "number" || !Number.isFinite(round) || round < 1) {
    return 1;
  }
  return Math.floor(round);
}

export function buildAnswerRoundMetaLabel(round: number | null | undefined): string {
  return `回答 #${normalizeRoundNumber(round)}`;
}

export function buildFeedbackRoundMetaLabel(round: number | null | undefined): string {
  return `反馈 #${normalizeRoundNumber(round)}`;
}

export function buildWorkbenchFixedNextActionBarViewModel(
  answer: PolishSessionAnswer | null | undefined,
): WorkbenchFixedNextActionBarViewModel | null {
  if (answer === null || answer === undefined) {
    return null;
  }
  const actions = getAnswerNextRecommendedActions(answer).map((action) => ({
    action,
    label: toNextRecommendedActionLabel(action),
  }));
  if (actions.length === 0) {
    return null;
  }
  return {
    placement: INTERVIEW_WORKBENCH_NEXT_ACTION_PLACEMENT,
    actions,
  };
}

type WorkbenchStatusChipTone = "success" | "warning" | "processing" | "default" | "blue" | "orange";

type FeedbackSectionKey =
  | "failed_status"
  | "feedback"
  | "score"
  | "positive_evidence_points"
  | "loss_points"
  | "reference_answer"
  | "weight_explanation"
  | "interview_intent"
  | "technical_gaps"
  | "communication_gaps"
  | "p7_reference_answer"
  | "oral_script"
  | "retry_delta"
  | "next_retry_focus"
  | "next_polish_suggestions"
  | "asset_consistency_check";

export type FeedbackLossPointTableRow = {
  index: number;
  severity: string;
  deduction: string;
  issue: string;
  suggestion: string;
};

export type FeedbackCardSectionViewModel = {
  key: FeedbackSectionKey;
  title: string;
  items: string[];
  defaultOpen: boolean;
  tone?: "default" | "warning";
  tableColumns?: readonly string[];
  tableRows?: readonly FeedbackLossPointTableRow[];
};

export type FeedbackCardViewModel = {
  title: string;
  status: string;
  contractId: string | null;
  contractIds: string[];
  sections: FeedbackCardSectionViewModel[];
  nextActions: PolishRecommendedAction[];
  traceItems: string[];
};

export type WorkbenchFixedNextActionBarViewModel = {
  placement: typeof INTERVIEW_WORKBENCH_NEXT_ACTION_PLACEMENT;
  actions: Array<{
    action: PolishRecommendedAction;
    label: string;
  }>;
};

export type CandidateReviewItemViewModel = {
  candidateId: string;
  typeLabel: string;
  statusLabel: string;
  statusTone: WorkbenchStatusChipTone;
  title: string;
  summary: string;
  evidenceExcerpt: string | null;
  confidenceLabel: string | null;
  canConfirm: boolean;
  canDismiss: boolean;
  mergeHint: string | null;
};

export type CandidateReviewViewModel = {
  items: CandidateReviewItemViewModel[];
  pendingCount: number;
  settledCount: number;
  mergeHint: string | null;
};

export type WorkbenchCandidateActionBarViewModel = {
  placement: typeof INTERVIEW_WORKBENCH_NEXT_ACTION_PLACEMENT;
  pendingCount: number;
  items: Array<{
    candidateId: string;
    title: string;
    typeLabel: string;
    confirmLabel: "确认候选";
    dismissLabel: "忽略候选";
  }>;
};

const CANDIDATE_TYPE_LABELS: Record<string, string> = {
  weakness_candidate: "薄弱项候选",
  asset_candidate: "资产候选",
  training_suggestion_candidate: "后续打磨建议候选",
  oral_script_candidate: "口语化候选",
  polished_answer_candidate: "高阶回答候选",
};

const CANDIDATE_STATUS_LABELS: Record<string, string> = {
  candidate: "待确认",
  confirmed: "已确认",
  dismissed: "已忽略",
  merged: "已合并",
  archived: "已归档",
};

const CANDIDATE_STATUS_TONES: Record<string, WorkbenchStatusChipTone> = {
  candidate: "processing",
  confirmed: "success",
  dismissed: "default",
  merged: "blue",
  archived: "orange",
};

const WORKBENCH_STATUS_CHIP_CLASS_NAMES = {
  success: "statusChipSuccess",
  warning: "statusChipWarning",
  processing: "statusChipProcessing",
  default: "statusChipDefault",
  blue: "statusChipBlue",
  orange: "statusChipOrange",
} as const;

const WORKBENCH_STATUS_CHIP_DOT_CLASS_NAMES = {
  success: "statusChipSuccessDot",
  warning: "statusChipWarningDot",
  processing: "statusChipProcessingDot",
  default: "statusChipDefaultDot",
  blue: "statusChipBlueDot",
  orange: "statusChipOrangeDot",
} as const;

function resolveStatusChipClassName(tone: WorkbenchStatusChipTone): string {
  return styles[WORKBENCH_STATUS_CHIP_CLASS_NAMES[tone]];
}

function resolveStatusChipDotClassName(tone: WorkbenchStatusChipTone): string {
  return styles[WORKBENCH_STATUS_CHIP_DOT_CLASS_NAMES[tone]];
}

function renderStatusChip(tone: WorkbenchStatusChipTone, label: string): ReactElement {
  return (
    <span className={resolveStatusChipClassName(tone)}>
      <span className={`${styles.statusChipDot} ${resolveStatusChipDotClassName(tone)}`} />
      <span className={styles.statusChipLabel}>{label}</span>
    </span>
  );
}

export function buildFeedbackCardViewModel(answer: PolishSessionAnswer): FeedbackCardViewModel {
  const payload = answer.feedback_payload;
  const contractIds = Array.from(
    new Set((payload?.contract_ids ?? []).map((item) => toOptionalText(item)).filter((item): item is string => item !== null)),
  );
  const contractId = contractIds[0] ?? null;
  const status = resolvePolishFeedbackStatus(toOptionalText(payload?.status));
  if (status === "failed") {
    return {
      title: "反馈生成失败",
      status,
      contractId,
      contractIds,
      sections: [
        {
          key: "failed_status",
          title: "失败状态",
          items: buildFailedFeedbackItems(payload),
          defaultOpen: true,
          tone: "warning",
        },
      ],
      nextActions: getAnswerNextRecommendedActions(answer),
      traceItems: [],
    };
  }
  return {
    title: buildFeedbackRoundMetaLabel(answer.answer_round),
    status,
    contractId,
    contractIds,
    sections: [
      {
        key: "feedback",
        title: "总体点评",
        items: buildOverallFeedbackItems(payload, answer.feedback_text),
        defaultOpen: true,
      },
      {
        key: "score",
        title: "打分",
        items: buildScoreResultItems(payload, answer.score_result_id),
        defaultOpen: true,
      },
      ...buildStructuredEvidenceSections(payload),
      {
        key: "loss_points",
        title: "失分点",
        items: [],
        tableColumns: FEEDBACK_LOSS_POINTS_TABLE_COLUMNS,
        tableRows: buildLossPointRows(payload),
        defaultOpen: false,
      },
      {
        key: "reference_answer",
        title: "参考回答",
        items: buildReferenceAnswerItems(payload?.reference_answer),
        defaultOpen: false,
      },
      ...buildAssetConsistencySections(payload),
      ...buildThemeFeedbackSections(payload),
      ...buildRetryFeedbackSections(payload),
      ...buildNextPolishFeedbackSections(payload),
    ],
    nextActions: getAnswerNextRecommendedActions(answer),
    traceItems: buildFeedbackTraceItems(),
  };
}

function resolvePolishFeedbackStatus(
  status: string | null | undefined,
): "pending" | "generated" | "failed" {
  const normalizedStatus = status?.trim().toLowerCase();
  if (normalizedStatus === "pending" || normalizedStatus === "generated") {
    return normalizedStatus;
  }
  if (
    normalizedStatus === "failed" ||
    normalizedStatus === "generation_failed" ||
    normalizedStatus === "validation_failed" ||
    normalizedStatus === "timed_out" ||
    normalizedStatus === "cancelled" ||
    normalizedStatus === "source_unavailable" ||
    normalizedStatus?.includes("failed") === true ||
    normalizedStatus?.includes("timeout") === true ||
    normalizedStatus?.includes("cancelled") === true
  ) {
    return "failed";
  }
  return "pending";
}

const LOSS_POINT_SUGGESTION_FALLBACK = "建议补充该点的设计依据、关键步骤和验证方式。";

function sanitizeFeedbackDisplayText(value: string | null | undefined, fallback: string): string {
  const text = value?.trim();
  if (!text) {
    return fallback;
  }
  const normalized = text.toLowerCase();
  if (text === "-" || text === "修正建议待补充" || normalized === "undefined" || normalized === "null") {
    return fallback;
  }
  return text;
}

function getLossPointTableRowFallbackValue(text: string | null, fallback: string): string {
  return sanitizeFeedbackDisplayText(text, fallback);
}

function pickFirstRecordText(record: Record<string, unknown>, fieldNames: string[]): string | null {
  for (const field of fieldNames) {
    const text = toOptionalText(record[field]);
    if (text !== null) {
      return text;
    }
  }
  return null;
}

function normalizeLossPointDeductionValue(value: unknown): string {
  const text = toOptionalText(value);
  if (text === null) {
    return "0";
  }
  const numericValue = Number(text);
  if (Number.isFinite(numericValue)) {
    return String(Math.trunc(Math.abs(numericValue)));
  }
  return "0";
}

function mapFeedbackRecordText(fieldName: string, rawText: string | null): string | null {
  if (rawText === null) {
    return null;
  }
  const normalizedField = fieldName.toLowerCase();
  if (["severity", "status", "score_type", "type", "action", "result_type"].includes(normalizedField)) {
    return mapFeedbackCodeToDisplay(rawText).text;
  }
  return rawText;
}

function resolveLossPointSuggestion(record: Record<string, unknown> | null, payload: PolishFeedbackPayload | undefined): string {
  const directSuggestion = record === null
    ? null
    : pickFirstRecordText(record, ["suggestion", "fix", "recommendation", "improvement"]);
  const sanitizedDirectSuggestion = sanitizeFeedbackDisplayText(directSuggestion, "");
  if (sanitizedDirectSuggestion) {
    return sanitizedDirectSuggestion;
  }

  const retryFocusRecord = toRecord(payload?.next_retry_focus);
  const retryFocusSuggestion = retryFocusRecord === null
    ? null
    : pickFirstRecordText(retryFocusRecord, ["suggested_action", "suggestion", "action", "focus"]);
  const sanitizedRetrySuggestion = sanitizeFeedbackDisplayText(retryFocusSuggestion, "");
  if (sanitizedRetrySuggestion) {
    return sanitizedRetrySuggestion;
  }

  const referenceSuggestion = sanitizeFeedbackDisplayText(buildReferenceAnswerItems(payload?.reference_answer)[0], "");
  if (referenceSuggestion) {
    return `可参考：${referenceSuggestion}`;
  }

  return LOSS_POINT_SUGGESTION_FALLBACK;
}

function buildLossPointRows(payload: PolishFeedbackPayload | undefined): FeedbackLossPointTableRow[] {
  const values = payload?.loss_points;
  if (!Array.isArray(values) || values.length === 0) {
    return [];
  }
  return values.map((value, index) => {
    const record = toRecord(value);
    if (record === null) {
      return {
        index: index + 1,
        severity: CODE_NOT_AVAILABLE_TEXT,
        deduction: "0",
        issue: getLossPointTableRowFallbackValue(toOptionalText(value), "问题待补充"),
        suggestion: resolveLossPointSuggestion(null, payload),
      };
    }
    const severityCode = pickFirstRecordText(record, ["severity", "level", "criticality"]);
    const severity = mapFeedbackCodeToDisplay(severityCode).text;
    const deduction = normalizeLossPointDeductionValue(
      pickFirstRecordText(record, ["deduction", "deducted_points"]) ?? (record.score_delta as unknown),
    );
    const issue = getLossPointTableRowFallbackValue(
      pickFirstRecordText(record, ["reason", "description", "content", "message"]),
      "问题待补充",
    );
    return {
      index: index + 1,
      severity,
      deduction,
      issue,
      suggestion: resolveLossPointSuggestion(record, payload),
    };
  });
}

function buildFailedFeedbackItems(payload: PolishFeedbackPayload | undefined): string[] {
  const validationErrors = Array.isArray(payload?.validation_errors)
    ? payload.validation_errors.map((item) => toOptionalText(item)).filter((item): item is string => item !== null)
    : [];
  const errorCode = toOptionalText(payload?.error?.code);
  const codes = Array.from(new Set([...(errorCode ? [errorCode] : []), ...validationErrors]));
  return dedupeTextItems([
    "反馈生成超时或失败，可重试",
    payload?.retryable === true ? "可重试：是" : null,
    ...codes.map((code) => `错误码：${code}`),
  ]);
}

function resolveFeedbackStatusTone(status: string): WorkbenchStatusChipTone {
  if (status === "generated") {
    return "success";
  }
  if (status === "failed") {
    return "warning";
  }
  if (status === "pending") {
    return "processing";
  }
  return "default";
}

function getTimestampParts(value: string | null | undefined): { date: string; time: string } | null {
  const text = value?.trim();
  if (!text) {
    return null;
  }
  const directMatch = text.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})/);
  if (directMatch) {
    return {
      date: directMatch[1],
      time: directMatch[2],
    };
  }
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  const pad = (valueToPad: number) => String(valueToPad).padStart(2, "0");
  return {
    date: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    time: `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`,
  };
}

function formatWorkbenchTimelineTime(
  value: string | null | undefined,
  baseDate: string | null,
  missingLabel = "时间未知",
): string {
  const parts = getTimestampParts(value);
  if (parts === null) {
    return missingLabel;
  }
  return baseDate !== null && parts.date === baseDate ? parts.time : `${parts.date} ${parts.time}`;
}

function getFeedbackGeneratedAt(answer: PolishSessionAnswer): string | null {
  const payloadGeneratedAt = toOptionalText((answer.feedback_payload as Record<string, unknown> | undefined)?.generated_at);
  return answer.feedback_created_at ?? payloadGeneratedAt;
}

function getFeedbackScoreValue(payload: PolishFeedbackPayload | undefined): number | null {
  const scoreRecord = toRecord(payload?.score_result);
  if (scoreRecord === null) {
    return null;
  }
  const rawScore = scoreRecord.score_value ?? scoreRecord.score ?? scoreRecord.total_score;
  const score = typeof rawScore === "number" ? rawScore : Number(toOptionalText(rawScore));
  return Number.isFinite(score) ? Math.round(score) : null;
}

function buildQuickReviewActionCopy(actions: readonly string[]): { maturityLabel: string; suggestion: string } | null {
  if (actions.includes("answer_again")) {
    return {
      maturityLabel: "偏低",
      suggestion: "当前回答成熟度偏低，建议重新组织一版回答。",
    };
  }
  if (actions.includes("continue_same_question") || actions.includes("provide_more_answer_detail")) {
    return {
      maturityLabel: "待加强",
      suggestion: actions.includes("provide_more_answer_detail")
        ? "当前回答需要补充关键细节，建议继续完善本题。"
        : "当前回答仍有关键缺口，建议继续打磨本题。",
    };
  }
  if (actions.some((action) => String(action) === "move_next_node" || String(action).includes("move_next_node"))) {
    return {
      maturityLabel: "节点成熟",
      suggestion: "当前节点成熟度较高，建议切换到下一个节点。",
    };
  }
  return null;
}

function buildQuickReviewScoreCopy(score: number | null): { maturityLabel: string; suggestion: string } {
  if (score === null) {
    return {
      maturityLabel: "待评估",
      suggestion: "反馈尚未生成，请稍后查看完整反馈。",
    };
  }
  if (score < 60) {
    return {
      maturityLabel: "偏低",
      suggestion: "当前回答成熟度低，建议继续打磨本题。",
    };
  }
  if (score < 75) {
    return {
      maturityLabel: "待加强",
      suggestion: "当前回答框架可用，但关键细节不足，建议继续补充一版。",
    };
  }
  if (score < 85) {
    return {
      maturityLabel: "较成熟",
      suggestion: "当前回答已覆盖主要点，可针对失分点再优化一轮。",
    };
  }
  if (score <= 92) {
    return {
      maturityLabel: "成熟",
      suggestion: "当前回答成熟度较高，建议换一道题继续验证。",
    };
  }
  return {
    maturityLabel: "成熟",
    suggestion: "当前回答质量较高，可进入下一题或下一节点。",
  };
}

export function buildAnswerQuickReviewViewModel(
  answer: PolishSessionAnswer,
  baseDate: string | null = getTimestampParts(answer.answer_created_at)?.date ?? null,
): WorkbenchAnswerQuickReviewViewModel {
  const score = getFeedbackScoreValue(answer.feedback_payload);
  const status = resolvePolishFeedbackStatus(toOptionalText(answer.feedback_payload?.status));
  const actionCopy = buildQuickReviewActionCopy(getAnswerNextRecommendedActions(answer));
  const scoreCopy = buildQuickReviewScoreCopy(score);
  const feedbackGeneratedAt = getFeedbackGeneratedAt(answer);
  return {
    answerId: answer.answer_id,
    scoreLabel: score === null ? "暂无评分" : `${score} / 100`,
    maturityLabel: actionCopy?.maturityLabel ?? scoreCopy.maturityLabel,
    suggestion: sanitizeFeedbackDisplayText(actionCopy?.suggestion ?? scoreCopy.suggestion, "反馈尚未生成，请稍后查看完整反馈。"),
    statusLabel: mapFeedbackCodeToDisplay(status).text,
    createdAtLabel: feedbackGeneratedAt === null
      ? "反馈时间未知"
      : formatWorkbenchTimelineTime(feedbackGeneratedAt, baseDate),
  };
}

export function findSelectedAnswerContext(
  session: PolishSessionDetail | null,
  selectedAnswerId: string | null,
): { turn: PolishSessionDetail["turns"][number]; turnIndex: number; answer: PolishSessionAnswer; answerIndex: number } | null {
  if (session === null || selectedAnswerId === null) {
    return null;
  }
  for (const [turnIndex, turn] of session.turns.entries()) {
    const answerIndex = turn.answers.findIndex((answer) => answer.answer_id === selectedAnswerId);
    if (answerIndex !== -1) {
      return {
        turn,
        turnIndex,
        answer: turn.answers[answerIndex],
        answerIndex,
      };
    }
  }
  return null;
}

export function resolveLatestAnswerIdForQuestion(
  session: PolishSessionDetail | null,
  questionId: string | null,
): string | null {
  if (session === null || questionId === null) {
    return null;
  }
  const turn = session.turns.find((item) => item.question_id === questionId);
  if (turn === undefined || turn.answers.length === 0) {
    return null;
  }
  return turn.answers[turn.answers.length - 1].answer_id;
}

export function buildSelectedAnswerFeedbackMetaViewModel(
  session: PolishSessionDetail | null,
  selectedAnswerId: string | null,
): WorkbenchSelectedAnswerContextViewModel | null {
  const context = findSelectedAnswerContext(session, selectedAnswerId);
  if (context === null) {
    return null;
  }
  return {
    questionId: context.turn.question_id,
    questionIndex: context.turnIndex + 1,
    questionLabel: `题目 ${context.turnIndex + 1}`,
    answerId: context.answer.answer_id,
    answerIndex: context.answerIndex + 1,
    answerLabel: buildAnswerRoundMetaLabel(context.answer.answer_round),
    answerTimeLabel: formatWorkbenchTimelineTime(
      context.answer.answer_created_at,
      getTimestampParts(context.turn.question_created_at)?.date ?? null,
    ),
    feedbackStatusLabel: mapFeedbackCodeToDisplay(
      resolvePolishFeedbackStatus(toOptionalText(context.answer.feedback_payload?.status)),
    ).text,
  };
}

export function buildInterviewTimelineViewModel(
  session: PolishSessionDetail | null,
  pinnedQuestionId: string | null,
): WorkbenchTimelineViewModel {
  if (session === null) {
    return { events: [] };
  }
  const baseDate = getTimestampParts(session.turns[0]?.question_created_at)?.date ?? null;
  const events: WorkbenchTimelineEventViewModel[] = [];
  for (const [turnIndex, turn] of session.turns.entries()) {
    const questionIsPinned = pinnedQuestionId !== null && turn.question_id === pinnedQuestionId;
    events.push({
      id: `question:${turn.question_id}`,
      kind: "system_question",
      alignment: "left",
      questionId: turn.question_id,
      answerId: null,
      metaLabel: `${formatWorkbenchTimelineTime(turn.question_created_at, baseDate)} · 系统提问 · 题目 ${turnIndex + 1}`,
      text: turn.question_text || FALLBACK_QUESTION_TEXT,
      quickReview: null,
      pinnedQuestionContext: questionIsPinned,
    });
    if (turn.answers.length === 0) {
      events.push({
        id: `answer-placeholder:${turn.question_id}`,
        kind: "system_hint",
        alignment: "left",
        questionId: turn.question_id,
        answerId: null,
        metaLabel: `${formatWorkbenchTimelineTime(turn.question_created_at, baseDate)} · 等待回答`,
        text: FALLBACK_ANSWER_TEXT,
        quickReview: null,
        pinnedQuestionContext: false,
      });
      continue;
    }
    for (const answer of turn.answers) {
      const quickReview = buildAnswerQuickReviewViewModel(answer, baseDate);
      events.push({
        id: `answer:${answer.answer_id}`,
        kind: "user_answer",
        alignment: "right",
        questionId: turn.question_id,
        answerId: answer.answer_id,
        metaLabel: `${formatWorkbenchTimelineTime(answer.answer_created_at, baseDate)} · ${buildAnswerRoundMetaLabel(answer.answer_round)}`,
        text: answer.answer_text || FALLBACK_ANSWER_TEXT,
        quickReview: null,
        pinnedQuestionContext: false,
      });
      events.push({
        id: `quick-review:${answer.answer_id}`,
        kind: "quick_review",
        alignment: "left",
        questionId: turn.question_id,
        answerId: answer.answer_id,
        metaLabel: `${quickReview.createdAtLabel} · 简评 · ${buildAnswerRoundMetaLabel(answer.answer_round)}`,
        text: quickReview.suggestion,
        quickReview,
        pinnedQuestionContext: false,
      });
    }
  }
  return { events };
}

export function buildCandidateReviewViewModel(
  candidates: readonly PolishCandidate[] | null | undefined,
): CandidateReviewViewModel {
  const records = Array.isArray(candidates) ? candidates : [];
  const items = records.map((candidate) => {
    const candidateType = toOptionalText(candidate.candidate_type) ?? "candidate";
    const status = toOptionalText(candidate.status) ?? "candidate";
    const title = toOptionalText(candidate.title) ?? CANDIDATE_TYPE_LABELS[candidateType] ?? "候选对象";
    const summary = toOptionalText(candidate.summary) ?? "该候选对象暂无摘要，可根据证据片段判断是否沉淀。";
    const evidenceExcerpt = toOptionalText(candidate.evidence_excerpt);
    const confidence = toOptionalText(candidate.confidence_level);
    const mergeTarget = toOptionalText(candidate.merge_target_candidate_id);
    return {
      candidateId: candidate.candidate_id,
      typeLabel: CANDIDATE_TYPE_LABELS[candidateType] ?? candidateType,
      statusLabel: CANDIDATE_STATUS_LABELS[status] ?? status,
      statusTone: CANDIDATE_STATUS_TONES[status] ?? "default",
      title,
      summary,
      evidenceExcerpt,
      confidenceLabel: confidence ? `置信度：${confidence}` : null,
      canConfirm: status === "candidate",
      canDismiss: status === "candidate",
      mergeHint: mergeTarget ? "右侧反馈面板提供候选确认或忽略入口。" : null,
    };
  });
  return {
    items,
    pendingCount: items.filter((item) => item.canConfirm || item.canDismiss).length,
    settledCount: items.filter((item) => !item.canConfirm && !item.canDismiss).length,
    mergeHint: items.length > 0
      ? "右侧反馈面板提供候选确认或忽略入口。"
      : null,
  };
}

export function buildWorkbenchCandidateActionBarViewModel(
  candidateReview: CandidateReviewViewModel | null | undefined,
): WorkbenchCandidateActionBarViewModel | null {
  const pendingItems = (candidateReview?.items ?? []).filter((item) => item.canConfirm || item.canDismiss);
  if (pendingItems.length === 0) {
    return null;
  }
  return {
    placement: INTERVIEW_WORKBENCH_NEXT_ACTION_PLACEMENT,
    pendingCount: pendingItems.length,
    items: pendingItems.map((item) => ({
      candidateId: item.candidateId,
      title: item.title,
      typeLabel: item.typeLabel,
      confirmLabel: "确认候选",
      dismissLabel: "忽略候选",
    })),
  };
}

export function buildFeedbackPanelTabs(params: {
  hasSummary: boolean;
  hasLossPoints: boolean;
  hasReferenceAnswer: boolean;
  hasCandidateItems: boolean;
  lossPointCount: number;
  candidateCount: number;
}): WorkbenchFeedbackPanelTabItem[] {
  return [
    { key: "summary", label: "总评", disabled: !params.hasSummary },
    { key: "lossPoints", label: `失分点 ${params.lossPointCount}`, disabled: !params.hasLossPoints },
    {
      key: "referenceAnswer",
      label: "参考回答",
      disabled: !params.hasReferenceAnswer,
    },
    {
      key: "candidate",
      label: `资产候选 ${params.candidateCount}`,
      disabled: !params.hasCandidateItems,
    },
  ];
}

function candidateBelongsToAnswer(candidate: PolishCandidate, answer: PolishSessionAnswer): boolean {
  if (candidate.answer_id && candidate.answer_id === answer.answer_id) {
    return true;
  }
  return Boolean(candidate.feedback_id && answer.feedback_id && candidate.feedback_id === answer.feedback_id);
}

function buildOverallFeedbackItems(payload: PolishFeedbackPayload | undefined, answerFeedbackText: string): string[] {
  if (payload?.status === "pending") {
    return [FALLBACK_FEEDBACK_TEXT];
  }
  const answerSummary = payload?.answer_summary;
  const mainGaps = Array.isArray(answerSummary?.main_gaps)
    ? answerSummary.main_gaps.map((gap) => toOptionalText(gap)).filter((gap): gap is string => gap !== null)
    : [];
  const items = dedupeTextItems([
    payload?.feedback_text || answerFeedbackText,
    answerSummary?.coverage ? `覆盖情况：${answerSummary.coverage}` : null,
    ...mainGaps.map((gap) => `主要缺口：${gap}`),
  ]);
  return items.length > 0 ? items : [FALLBACK_FEEDBACK_TEXT];
}

function buildStructuredEvidenceSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  if (!payload) {
    return [];
  }
  return [
    buildOptionalFeedbackSection("positive_evidence_points", "得分点", buildOptionalRecordListItems(payload.positive_evidence_points, [
      ["title", "得分点"],
      ["evidence_excerpt", "回答证据"],
      ["dimension_id", "关联维度"],
      ["related_dimension", "关联维度"],
      ["evidence_source", "证据来源"],
    ]), false),
  ].filter((section): section is FeedbackCardSectionViewModel => section !== null);
}

function buildAssetConsistencySections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  const check = payload?.asset_consistency_check;
  if (!check) {
    return [];
  }
  const status = toOptionalText(check.status);
  const needsClarification = status === "conflict" || status === "ambiguous";
  const conflicts = buildOptionalRecordListItems(check.conflicts, [
    ["title", "冲突"],
    ["field", "字段"],
    ["current_value", "当前记录"],
    ["proposed_value", "本轮回答"],
    ["reason", "原因"],
  ]).map((item) => `冲突项：${item}`);
  const questions = compactTextList(check.clarification_questions).map((item) => `澄清问题：${item}`);
  return [
    {
      key: "asset_consistency_check",
      title: "项目一致性检查",
      items: dedupeTextItems([
        status ? `状态：${mapFeedbackCodeToDisplay(status).text}` : null,
        check.matched_project_name ? `匹配项目：${check.matched_project_name}` : null,
        needsClarification ? "需要澄清后再沉淀为资产" : null,
        ...conflicts,
        ...questions,
      ]),
      defaultOpen: needsClarification,
      tone: needsClarification ? "warning" : "default",
    },
  ];
}

function buildThemeFeedbackSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  if (!payload) {
    return [];
  }
  return [
    buildOptionalFeedbackSection("weight_explanation", "权重说明", dedupeTextItems([
      payload.polish_theme_label ? `主题：${payload.polish_theme_label}` : null,
      typeof payload.explicit_weight === "number" ? `显性技术权重：${payload.explicit_weight}%` : null,
      typeof payload.implicit_weight === "number" ? `隐性表达权重：${payload.implicit_weight}%` : null,
      payload.weight_explanation,
    ]), true),
    buildOptionalFeedbackSection("interview_intent", "面试意图", compactTextList(payload.interview_intent), false),
    buildOptionalFeedbackSection("technical_gaps", "技术短板", compactTextList(payload.technical_gaps), false),
    buildOptionalFeedbackSection("communication_gaps", "表达短板", compactTextList(payload.communication_gaps), false),
    buildOptionalFeedbackSection("p7_reference_answer", "高阶参考答案", compactTextList(payload.p7_reference_answer), false),
    buildOptionalFeedbackSection("oral_script", "口语化范本", compactTextList(payload.oral_script), false),
  ].filter((section): section is FeedbackCardSectionViewModel => section !== null);
}

function buildRetryFeedbackSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  if (!payload) {
    return [];
  }
  return [
    buildOptionalFeedbackSection("retry_delta", "多次回答改进", buildRetryDeltaItems(payload), false),
    buildOptionalFeedbackSection("next_retry_focus", "下一轮重答重点", buildOptionalRecordListItems(payload.next_retry_focus, [
      ["focus_area", "重点"],
      ["priority", "优先级"],
      ["related_dimension", "关联维度"],
      ["suggested_action", "建议动作"],
    ]), false),
  ].filter((section): section is FeedbackCardSectionViewModel => section !== null);
}

function buildNextPolishFeedbackSections(payload: PolishFeedbackPayload | undefined): FeedbackCardSectionViewModel[] {
  if (!payload) {
    return [];
  }
  return [
    buildOptionalFeedbackSection("next_polish_suggestions", "下一轮打磨建议", compactTextList(payload.next_polish_suggestions ?? payload.next_training_suggestions), false),
  ].filter((section): section is FeedbackCardSectionViewModel => section !== null);
}

function buildOptionalFeedbackSection(
  key: FeedbackSectionKey,
  title: string,
  items: string[],
  defaultOpen: boolean,
  tone?: "default" | "warning",
): FeedbackCardSectionViewModel | null {
  return items.length > 0 ? { key, title, items, defaultOpen, tone } : null;
}

function compactTextList(value: string | string[] | null | undefined): string[] {
  if (Array.isArray(value)) {
    return dedupeTextItems(value);
  }
  return dedupeTextItems([value]);
}

function buildRetryDeltaItems(payload: PolishFeedbackPayload): string[] {
  const dimensionDeltaItems = Object.entries(payload.dimension_delta ?? {})
    .filter(([key]) => isUserVisibleFeedbackRecordKey(key))
    .map(([key, value]) => {
      const text = toOptionalText(value);
      return text ? `维度变化：${key} ${text}` : null;
    });
  return dedupeTextItems([
    typeof payload.score_delta === "number" ? `分数变化：${payload.score_delta > 0 ? "+" : ""}${payload.score_delta}` : null,
    payload.mastery_status ? `掌握状态：${payload.mastery_status}` : null,
    ...compactTextList(payload.improved_points).map((item) => `已改进：${item}`),
    ...compactTextList(payload.remaining_gaps).map((item) => `仍需补齐：${item}`),
    ...compactTextList(payload.repeated_loss_points).map((item) => `重复失分：${item}`),
    ...compactTextList(payload.regressed_points).map((item) => `退步点：${item}`),
    ...dimensionDeltaItems,
  ]);
}

function buildScoreResultItems(payload: PolishFeedbackPayload | undefined, fallbackScoreResultId: string | null): string[] {
  const score = payload?.score_result;
  if (!score) {
    return fallbackScoreResultId ? [`score_result_id：${fallbackScoreResultId}`] : ["暂无打分结果"];
  }
  const scoreType = mapFeedbackCodeToDisplay(score.score_type).text;
  return dedupeTextItems([
    typeof score.score_value === "number" ? `总分 ${score.score_value} / 100` : null,
    score.score_type ? `评分类型：${scoreType}` : null,
    score.confidence_level ? `置信度：${score.confidence_level}` : null,
    score.score_result_id ? `score_result_id：${score.score_result_id}` : fallbackScoreResultId ? `score_result_id：${fallbackScoreResultId}` : null,
    score.rubric_version ? `rubric_version：${score.rubric_version}` : null,
  ]);
}

function buildReferenceAnswerItems(value: unknown): string[] {
  const record = toRecord(value);
  if (record === null) {
    return [FEEDBACK_REFERENCE_SECTION_FALLBACK];
  }

  const summary = toOptionalText(record.summary);
  const sectionsValue = Array.isArray(record.sections)
    ? record.sections
    : Array.isArray(record.reference_answer_sections)
      ? record.reference_answer_sections
      : [];
  const sections = Array.isArray(sectionsValue) ? sectionsValue : [];

  if (sections.length > 0) {
    const sectionItems = sections.flatMap((section) => buildReferenceAnswerSectionItems(section));
    if (summary !== null) {
      return [summary, ...sectionItems];
    }
    return sectionItems.length > 0 ? sectionItems : [FEEDBACK_REFERENCE_SECTION_FALLBACK];
  }

  const outline = Array.isArray(record.outline)
    ? record.outline.map(toOptionalText).filter((item): item is string => Boolean(item))
    : [];
  const fallbackItems = Array.isArray(record.sections)
    ? record.sections.flatMap((section) => buildReferenceAnswerSectionItems(section))
    : [];
  const paragraphItems = dedupeTextItems([summary, ...outline, ...fallbackItems]);
  return paragraphItems.length > 0 ? paragraphItems : [FEEDBACK_REFERENCE_SECTION_FALLBACK];
}

function buildReferenceAnswerSectionItems(value: unknown): string[] {
  const section = toRecord(value);
  if (section === null) {
    const text = toOptionalText(value);
    return text ? [text] : [];
  }
  const title = toOptionalText(section.title);
  const content = toOptionalText(section.content);
  if (title === null && content === null) {
    return [];
  }
  if (title === null) {
    return [content ?? FEEDBACK_REFERENCE_SECTION_FALLBACK];
  }
  if (content === null) {
    return [title];
  }
  return [`${title}：${content}`];
}

function buildRecordListItems(
  values: unknown,
  fieldLabels: Array<[string, string]>,
  fallback: string,
): string[] {
  if (!Array.isArray(values) || values.length === 0) {
    return [fallback];
  }
  const items = values.flatMap((value) => buildRecordItems(value, fieldLabels));
  return items.length > 0 ? items : [fallback];
}

function buildOptionalRecordListItems(
  values: unknown,
  fieldLabels: Array<[string, string]>,
): string[] {
  if (!Array.isArray(values) || values.length === 0) {
    return [];
  }
  return dedupeTextItems(values.flatMap((value) => buildRecordItems(value, fieldLabels)));
}

function buildRecordItems(value: unknown, fieldLabels: Array<[string, string]>): string[] {
  const record = toRecord(value);
  if (record === null) {
    const text = toOptionalText(value);
    return text ? [text] : [];
  }
  const preferredItems = fieldLabels
    .map(([field, label]) => {
      const text = toOptionalText(record[field]);
      const mappedText = mapFeedbackRecordText(field, text);
      return mappedText ? `${label}：${mappedText}` : null;
    })
    .filter((item): item is string => item !== null);
  if (preferredItems.length > 0) {
    return preferredItems;
  }
  return Object.entries(record)
    .filter(([key]) => isUserVisibleFeedbackRecordKey(key))
    .map(([key, item]) => {
      const text = toOptionalText(item);
      const mappedText = mapFeedbackRecordText(key, text);
      return mappedText ? `${key}：${mappedText}` : null;
    })
    .filter((item): item is string => item !== null)
    .slice(0, 6);
}

function buildFeedbackTraceItems(): string[] {
  return [];
}

function isUserVisibleFeedbackRecordKey(key: string): boolean {
  const normalized = key.toLowerCase();
  return ![
    "trace",
    "internal",
    "fake",
    "raw",
    "prompt",
    "completion",
    "provider",
    "candidate",
    "private",
    "secret",
    "hidden",
    "token",
    "api_key",
    "cookie",
  ].some((privateMarker) => normalized.includes(privateMarker));
}

function toRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function toOptionalText(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed || null;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return null;
}

function dedupeTextItems(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const text = toOptionalText(value);
    if (!text || seen.has(text)) {
      continue;
    }
    seen.add(text);
    result.push(text);
  }
  return result;
}

function renderFeedbackSectionContent(section: FeedbackCardSectionViewModel): ReactNode {
  if (section.key === "loss_points" && section.tableRows !== undefined) {
    if (section.tableRows.length === 0) {
      return (
        <div className={styles.feedbackSectionTextList}>
          <Typography.Text type="secondary">{FEEDBACK_LOSS_POINTS_TABLE_EMPTY_TEXT}</Typography.Text>
        </div>
      );
    }
    const severityChipToneClass = (severity: string): string => {
      if (severity === "主要失分" || severity === "严重失分") {
        return styles.feedbackLossPointSeverityChipCritical;
      }
      if (severity === "轻微失分") {
        return styles.feedbackLossPointSeverityChipMinor;
      }
      return styles.feedbackLossPointSeverityChipDefault;
    };
    return (
      <div className={styles.feedbackSectionLossPointCards}>
        {section.tableRows.map((row) => (
          <article key={`${section.key}:${row.index}`} className={styles.feedbackLossPointCard}>
            <div className={styles.feedbackLossPointCardHeader}>
              <Typography.Text strong className={styles.feedbackLossPointCardHeaderTitle}>
                {`失分点 ${row.index}`}
              </Typography.Text>
              <div className={styles.feedbackLossPointCardHeaderMeta}>
                <Tag className={`${styles.feedbackLossPointChip} ${severityChipToneClass(row.severity)}`}>{row.severity}</Tag>
                <Tag className={`${styles.feedbackLossPointChip} ${styles.feedbackLossPointDeductionChip}`}>{`扣分 ${row.deduction}`}</Tag>
              </div>
            </div>
            <div className={styles.feedbackLossPointCardBody}>
              <div className={styles.feedbackLossPointCardField}>
                <Typography.Text type="secondary" className={styles.feedbackLossPointCardFieldLabel}>
                  问题
                </Typography.Text>
                <Typography.Paragraph className={styles.feedbackLossPointCardFieldValue} ellipsis={false}>
                  {row.issue}
                </Typography.Paragraph>
              </div>
              <div className={styles.feedbackLossPointCardField}>
                <Typography.Text type="secondary" className={styles.feedbackLossPointCardFieldLabel}>
                  修正建议
                </Typography.Text>
                <Typography.Paragraph className={styles.feedbackLossPointCardFieldValue} ellipsis={false}>
                  {row.suggestion}
                </Typography.Paragraph>
              </div>
            </div>
          </article>
        ))}
      </div>
    );
  }

  if (section.key === "reference_answer") {
    const paragraphs = section.items.length > 0 ? section.items : [FEEDBACK_REFERENCE_SECTION_FALLBACK];
    return (
      <div className={styles.feedbackSectionTextList}>
        {paragraphs.map((paragraph) => (
          <Typography.Paragraph key={`${section.key}:${paragraph}`} className={styles.feedbackSectionParagraph}>
            {paragraph}
          </Typography.Paragraph>
        ))}
      </div>
    );
  }

  return (
    <ul className={styles.feedbackSectionItems}>
      {section.items.map((item) => (
        <li key={`${section.key}:${item}`}>{item}</li>
      ))}
    </ul>
  );
}

export type CandidateListProps = {
  pendingCount: number;
  settledCount: number;
  mergeHint: string | null;
  items: readonly CandidateReviewItemViewModel[];
  emptyMessage: string;
  candidateActionKey: string | null;
  isSessionEnded: boolean;
  onCandidateAction: (candidateId: string, action: "confirm" | "dismiss") => void;
};

export function CandidateList({
  pendingCount,
  settledCount,
  mergeHint,
  items,
  emptyMessage,
  candidateActionKey,
  isSessionEnded,
  onCandidateAction,
}: CandidateListProps): ReactElement {
  return (
    <>
      <div className={styles.candidateReviewSummary}>
        {`待处理 ${pendingCount} 项，已处理 ${settledCount} 项`}
      </div>
      {mergeHint ? <Alert type="info" showIcon message={mergeHint} /> : null}
      <div className={styles.candidateReviewList}>
        {items.length === 0 ? <Alert type="info" showIcon message={emptyMessage} /> : null}
        {items.map((item) => (
          <article className={styles.candidateReviewItem} key={item.candidateId}>
            <div className={styles.candidateReviewItemHeader}>
              <Space size={[6, 6]} wrap>
                <Tag className={styles.feedbackMetaTag}>{item.typeLabel}</Tag>
                {renderStatusChip(item.statusTone, item.statusLabel)}
                {item.confidenceLabel ? <Tag className={styles.feedbackMetaTag}>{item.confidenceLabel}</Tag> : null}
              </Space>
              {item.canConfirm || item.canDismiss ? (
                <div className={styles.feedbackPanelCandidateActions}>
                  <Button
                    size="small"
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    loading={candidateActionKey === `${item.candidateId}:confirm`}
                    disabled={isSessionEnded || (candidateActionKey !== null && candidateActionKey !== `${item.candidateId}:confirm`)}
                    onClick={() => onCandidateAction(item.candidateId, "confirm")}
                  >
                    确认候选
                  </Button>
                  <Button
                    size="small"
                    danger
                    icon={<CloseCircleOutlined />}
                    loading={candidateActionKey === `${item.candidateId}:dismiss`}
                    disabled={isSessionEnded || (candidateActionKey !== null && candidateActionKey !== `${item.candidateId}:dismiss`)}
                    onClick={() => onCandidateAction(item.candidateId, "dismiss")}
                  >
                    忽略候选
                  </Button>
                </div>
              ) : null}
            </div>
            <div className={styles.candidateReviewBody}>
              <Typography.Text strong className={styles.candidateReviewTitle}>{item.title}</Typography.Text>
              <Typography.Paragraph className={styles.candidateReviewText}>{item.summary}</Typography.Paragraph>
              {item.evidenceExcerpt ? (
                <Typography.Text type="secondary" className={styles.candidateReviewEvidence}>
                  {`证据片段：${item.evidenceExcerpt}`}
                </Typography.Text>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

export type ResultCardProps = {
  activeTab: WorkbenchFeedbackPanelTab;
  feedbackCard: FeedbackCardViewModel | null;
  summarySections: readonly FeedbackCardSectionViewModel[];
  lossPointsSection: FeedbackCardSectionViewModel | null;
  referenceAnswerSection: FeedbackCardSectionViewModel | null;
};

export function ResultCard({
  activeTab,
  feedbackCard,
  summarySections,
  lossPointsSection,
  referenceAnswerSection,
}: ResultCardProps): ReactElement {
  if (activeTab === "summary") {
    return (
      <div className={styles.feedbackPanelSummarySections}>
        {summarySections.length > 0 ? (
          summarySections.map((section) => (
            <section
              className={`${styles.feedbackPanelSection} ${section.tone === "warning" ? styles.feedbackSectionWarning : ""}`}
              key={section.key}
            >
              {renderFeedbackSectionContent(section)}
            </section>
          ))
        ) : (
          <Alert type="info" showIcon message={feedbackCard === null ? "当前回答暂无反馈" : "当前回答暂无总评内容"} />
        )}
      </div>
    );
  }

  if (activeTab === "lossPoints") {
    return (
      <div className={styles.feedbackPanelSummarySections}>
        {lossPointsSection === null ? (
          <Alert type="info" showIcon message="当前未生成失分点" />
        ) : lossPointsSection.tableRows === undefined || lossPointsSection.tableRows.length === 0 ? (
          <Alert type="info" showIcon message="当前回答暂无失分点" />
        ) : (
          <>{renderFeedbackSectionContent(lossPointsSection)}</>
        )}
      </div>
    );
  }

  if (activeTab === "referenceAnswer") {
    return (
      <div className={styles.feedbackPanelSummarySections}>
        {referenceAnswerSection === null ? (
          <Alert type="info" showIcon message="当前未生成参考回答" />
        ) : (
          <>{renderFeedbackSectionContent(referenceAnswerSection)}</>
        )}
      </div>
    );
  }

  return <div />;
}

export type FeedbackFormProps = {
  answerError: string | null;
  showNextActionBar: boolean;
  fixedNextActionBar: WorkbenchFixedNextActionBarViewModel | null;
  creatingQuestion: boolean;
  submittingAnswer: boolean;
  feedbackGenerating: boolean;
  completingQuestion: boolean;
  isSessionEnded: boolean;
  answerText: string;
  canSendAnswer: boolean;
  canCreateFeedbackNextQuestion: boolean;
  composerActionState: WorkbenchQuestionComposerActionViewModel;
  onAnswerTextChange: (value: string) => void;
  onSendAnswer: () => void;
  onCreateFeedbackNextQuestion: () => void;
  onCompleteCurrentQuestion: () => void;
};

export function FeedbackForm({
  answerError,
  showNextActionBar,
  fixedNextActionBar,
  creatingQuestion,
  submittingAnswer,
  feedbackGenerating,
  completingQuestion,
  isSessionEnded,
  answerText,
  canSendAnswer,
  canCreateFeedbackNextQuestion,
  composerActionState,
  onAnswerTextChange,
  onSendAnswer,
  onCreateFeedbackNextQuestion,
  onCompleteCurrentQuestion,
}: FeedbackFormProps): ReactElement {
  return (
    <div
      className={styles.currentQuestionComposer}
      data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.currentQuestionComposer}
      data-layout-area="right_fixed_composer"
    >
      {answerError !== null ? <Alert type="error" showIcon message={answerError} /> : null}
      {showNextActionBar ? (
        <div
          className={styles.currentQuestionNextActionBar}
          data-layout-area="right_fixed_next_action_bar"
          aria-label="输入区操作"
        >
          {fixedNextActionBar !== null ? (
            <div className={styles.currentQuestionActionGroup}>
              <Typography.Text strong className={styles.currentQuestionNextActionTitle}>
                下一步建议
              </Typography.Text>
              <div className={styles.currentQuestionNextActionButtons}>
                {fixedNextActionBar.actions.map((item) => (
                  <Tag
                    key={`${fixedNextActionBar.placement}:${item.action}`}
                    className={styles.currentQuestionNextActionTag}
                  >
                    {item.label}
                  </Tag>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
      <Input.TextArea
        className={styles.currentQuestionComposerInput}
        rows={4}
        value={answerText}
        onChange={(event) => onAnswerTextChange(event.target.value)}
        onKeyDown={(event) => {
          if (canSubmitAnswerFromKeyboard({
            key: event.key,
            ctrlKey: event.ctrlKey,
            metaKey: event.metaKey,
            shiftKey: event.shiftKey,
            altKey: event.altKey,
            isComposing: event.nativeEvent.isComposing,
          }, canSendAnswer)) {
            event.preventDefault();
            onSendAnswer();
          }
        }}
        placeholder={composerActionState.sendAnswerPlaceholder}
        maxLength={2000}
        disabled={!canSendAnswer}
      />
      <div className={styles.currentQuestionComposerActions}>
        <div className={styles.currentQuestionComposerLeftActions}>
          <Tooltip
            title={canCreateFeedbackNextQuestion
              ? "由后端根据当前反馈策略决定是否生成下一题"
              : "需要当前题目已有反馈后才能请求生成下一题"}
          >
            <span>
              <Button
                icon={<PlusOutlined />}
                loading={creatingQuestion}
                disabled={!canCreateFeedbackNextQuestion}
                onClick={onCreateFeedbackNextQuestion}
              >
                生成下一题
              </Button>
            </span>
          </Tooltip>
          <Tooltip
            title={composerActionState.canMarkCurrentQuestionCompleted
              ? INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_BUTTON
              : composerActionState.markCurrentQuestionCompletedDisabledReason}
          >
            <span>
              <Button
                icon={<CheckCircleOutlined />}
                loading={completingQuestion}
                disabled={!composerActionState.canMarkCurrentQuestionCompleted}
                onClick={onCompleteCurrentQuestion}
              >
                {INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_BUTTON}
              </Button>
            </span>
          </Tooltip>
        </div>
        <Tooltip title={INTERVIEW_WORKBENCH_SEND_BUTTON_TOOLTIP}>
          <span
            className={styles.sendButtonTooltipAnchor}
            tabIndex={0}
            aria-label={INTERVIEW_WORKBENCH_SEND_BUTTON_TOOLTIP}
          >
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={submittingAnswer || feedbackGenerating}
              disabled={!canSendAnswer}
              aria-label={INTERVIEW_WORKBENCH_SEND_BUTTON_TOOLTIP}
              onClick={onSendAnswer}
            >
              {composerActionState.sendAnswerButtonLabel}
            </Button>
          </span>
        </Tooltip>
      </div>
    </div>
  );
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
  const [reportGeneratingSessionId, setReportGeneratingSessionId] = useState<string | null>(null);
  const [endingListSessionId, setEndingListSessionId] = useState<string | null>(null);
  const [deletingListSessionId, setDeletingListSessionId] = useState<string | null>(null);
  const [listConfirmAction, setListConfirmAction] = useState<{
    kind: "end" | "delete";
    session: PolishSessionSummary;
  } | null>(null);
  const [reportDialogSession, setReportDialogSession] = useState<PolishSessionSummary | null>(null);
  const [createForm] = Form.useForm<InterviewCreateFormValues>();

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await fetchPolishSessions();
      setSessions(filterVisiblePolishSessions(list));
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
      polish_theme: requestPayload.polish_theme ?? null,
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

  const generateReportForSession = async (record: PolishSessionSummary) => {
    if (reportGeneratingSessionId !== null) {
      return;
    }
    setReportGeneratingSessionId(record.session_id);
    try {
      await generatePolishSessionReport(record.session_id);
      message.success("面试报告已生成。");
      await loadSessions();
    } catch (reportError) {
      message.error(reportError instanceof Error ? reportError.message : "面试报告生成失败，请稍后重试。");
    } finally {
      setReportGeneratingSessionId(null);
    }
  };

  const confirmListAction = async () => {
    if (listConfirmAction === null) {
      return;
    }
    const target = listConfirmAction.session;
    if (listConfirmAction.kind === "end") {
      setEndingListSessionId(target.session_id);
      try {
        await endPolishSession(target.session_id);
        message.success("模拟面试已结束。");
        setListConfirmAction(null);
        await loadSessions();
      } catch (endError) {
        message.error(endError instanceof Error ? endError.message : "结束模拟面试失败，请稍后重试。");
      } finally {
        setEndingListSessionId(null);
      }
      return;
    }

    setDeletingListSessionId(target.session_id);
    try {
      await softDeletePolishSession(target.session_id);
      message.success("模拟面试已删除。");
      setListConfirmAction(null);
      setSessions((current) => filterVisiblePolishSessions(current.filter((item) => item.session_id !== target.session_id)));
    } catch (deleteError) {
      message.error(deleteError instanceof Error ? deleteError.message : "删除模拟面试失败，请稍后重试。");
    } finally {
      setDeletingListSessionId(null);
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
        render: (_, record) => renderInterviewListEllipsisText(`${toPolishThemeLabel(record)} / ${record.title || "未选择"}`),
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
        render: (_, record) => {
          const canViewReport = hasPolishSessionReport(record);
          const canEnd = canEndPolishSessionSummary(record);
          const reportDialog = buildPolishSessionReportDialogViewModel(record);
          return (
            <Space size={4} className={styles.tableActions}>
              <Tooltip title={INTERVIEW_LIST_ACTION_TOOLTIPS.enter}>
                <Button
                  type="text"
                  size="small"
                  icon={<RightOutlined />}
                  aria-label={INTERVIEW_LIST_ACTION_TOOLTIPS.enter}
                  onClick={() => navigate(buildPolishSessionPath(record.session_id))}
                />
              </Tooltip>
              <Tooltip title={INTERVIEW_LIST_ACTION_TOOLTIPS.generateReport}>
                <Button
                  type="text"
                  size="small"
                  icon={<FileTextOutlined />}
                  aria-label={INTERVIEW_LIST_ACTION_TOOLTIPS.generateReport}
                  loading={reportGeneratingSessionId === record.session_id}
                  disabled={reportGeneratingSessionId !== null}
                  onClick={() => void generateReportForSession(record)}
                />
              </Tooltip>
              <Tooltip title={canViewReport ? INTERVIEW_LIST_ACTION_TOOLTIPS.viewReport : INTERVIEW_LIST_ACTION_TOOLTIPS.viewReportUnavailable}>
                <Button
                  type="text"
                  size="small"
                  icon={<FileSearchOutlined />}
                  aria-label={INTERVIEW_LIST_ACTION_TOOLTIPS.viewReport}
                  disabled={!canViewReport}
                  onClick={() => {
                    if (reportDialog === null) {
                      message.info(INTERVIEW_LIST_ACTION_TOOLTIPS.viewReportUnavailable);
                      return;
                    }
                    setReportDialogSession(record);
                  }}
                />
              </Tooltip>
              <Tooltip title={canEnd ? INTERVIEW_LIST_ACTION_TOOLTIPS.end : INTERVIEW_LIST_ACTION_TOOLTIPS.ended}>
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<StopOutlined />}
                  aria-label={INTERVIEW_LIST_ACTION_TOOLTIPS.end}
                  loading={endingListSessionId === record.session_id}
                  disabled={!canEnd || endingListSessionId !== null}
                  onClick={() => setListConfirmAction({ kind: "end", session: record })}
                />
              </Tooltip>
              <Tooltip title={INTERVIEW_LIST_ACTION_TOOLTIPS.delete}>
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  aria-label={INTERVIEW_LIST_ACTION_TOOLTIPS.delete}
                  loading={deletingListSessionId === record.session_id}
                  disabled={deletingListSessionId !== null}
                  onClick={() => setListConfirmAction({ kind: "delete", session: record })}
                />
              </Tooltip>
            </Space>
          );
        },
      },
    ],
    [deletingListSessionId, endingListSessionId, navigate, reportGeneratingSessionId],
  );
  const listConfirmLoading =
    listConfirmAction?.kind === "end"
      ? endingListSessionId === listConfirmAction.session.session_id
      : listConfirmAction?.kind === "delete"
        ? deletingListSessionId === listConfirmAction.session.session_id
        : false;
  const reportDialogViewModel =
    reportDialogSession === null ? null : buildPolishSessionReportDialogViewModel(reportDialogSession);

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
              initialValues={{ mode: "polish", polish_theme: "mixed" }}
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
                label="能力主题"
                name="polish_theme"
                rules={[{ required: true, message: "请选择能力主题" }]}
              >
                <Select
                  disabled={createSubmitLoading}
                  placeholder="选择能力主题"
                  options={POLISH_THEME_OPTIONS.map((theme) => ({
                    value: theme.value,
                    label: theme.label,
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

        <Modal
          title={
            listConfirmAction?.kind === "delete"
              ? INTERVIEW_LIST_CONFIRM_COPY.deleteTitle
              : INTERVIEW_LIST_CONFIRM_COPY.endTitle
          }
          open={listConfirmAction !== null}
          okText={
            listConfirmAction?.kind === "delete"
              ? INTERVIEW_LIST_CONFIRM_COPY.okDelete
              : INTERVIEW_LIST_CONFIRM_COPY.okEnd
          }
          cancelText={INTERVIEW_LIST_CONFIRM_COPY.cancel}
          okButtonProps={{
            danger: listConfirmAction?.kind === "delete",
            loading: listConfirmLoading,
            disabled: listConfirmLoading,
          }}
          cancelButtonProps={{ disabled: listConfirmLoading }}
          closable={!listConfirmLoading}
          keyboard={!listConfirmLoading}
          maskClosable={!listConfirmLoading}
          onCancel={() => {
            if (!listConfirmLoading) {
              setListConfirmAction(null);
            }
          }}
          onOk={() => {
            void confirmListAction();
          }}
        >
          <Typography.Paragraph>
            {listConfirmAction?.kind === "delete"
              ? INTERVIEW_LIST_CONFIRM_COPY.deleteContent
              : INTERVIEW_LIST_CONFIRM_COPY.endContent}
          </Typography.Paragraph>
        </Modal>

        <Modal
          title={reportDialogViewModel?.title ?? "面试报告"}
          open={reportDialogViewModel !== null}
          footer={null}
          onCancel={() => setReportDialogSession(null)}
        >
          {reportDialogViewModel !== null ? (
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              <Typography.Text type="secondary">报告 ID：{reportDialogViewModel.reportId}</Typography.Text>
              <Typography.Text type="secondary">报告状态：{reportDialogViewModel.reportStatus}</Typography.Text>
              <Typography.Text type="secondary">
                生成时间：{reportDialogViewModel.generatedAt ? toDisplayDate(reportDialogViewModel.generatedAt) : "-"}
              </Typography.Text>
              <Alert type="info" showIcon message={reportDialogViewModel.emptyDescription} />
            </Space>
          ) : null}
        </Modal>
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
  const [completingQuestion, setCompletingQuestion] = useState<boolean>(false);
  const [endingSession, setEndingSession] = useState<boolean>(false);
  const [endConfirmOpen, setEndConfirmOpen] = useState<boolean>(false);
  const [submittingAnswer, setSubmittingAnswer] = useState<boolean>(false);
  const [feedbackGenerating, setFeedbackGenerating] = useState<boolean>(false);
  const [workbenchFailureState, setWorkbenchFailureState] = useState<WorkbenchMachineState | null>(null);
  const [copyingSession, setCopyingSession] = useState<boolean>(false);
  const [expandedProgressNodeKeys, setExpandedProgressNodeKeys] = useState<Set<string>>(() => new Set());
  const [selectedProgressNodeRef, setSelectedProgressNodeRef] = useState<string | null>(null);
  const [selectedProgressNodeKey, setSelectedProgressNodeKey] = useState<string | null>(null);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const [selectedAnswerId, setSelectedAnswerId] = useState<string | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);
  const chatBodyRef = useRef<HTMLDivElement | null>(null);
  const chatScrollLastAutoTriggerRef = useRef<string | null>(null);
  const chatScrollManuallyScrolledRef = useRef<boolean>(false);
  const chatScrollIsAutoingRef = useRef<boolean>(false);
  const answerSubmissionKeyDraftRef = useRef<AnswerSubmissionKeyDraft | null>(null);
  const [isProgressPanelCollapsed, setProgressPanelCollapsed] = useState<boolean>(false);
  const [progressPanelWidth, setProgressPanelWidth] = useState<number>(PROGRESS_PANEL_DEFAULT_WIDTH);
  const [isFeedbackPanelCollapsed, setFeedbackPanelCollapsed] = useState<boolean>(false);
  const [feedbackPanelWidth, setFeedbackPanelWidth] = useState<number>(
    INTERVIEW_WORKBENCH_LAYOUT_B_FEEDBACK_PANEL_WIDTH_POLICY.default,
  );
  const [activeFeedbackPanelTab, setActiveFeedbackPanelTab] = useState<WorkbenchFeedbackPanelTab>("summary");
  const [isProgressNodeContextExpanded, setProgressNodeContextExpanded] = useState(false);
  const [isCurrentQuestionTextExpanded, setCurrentQuestionTextExpanded] = useState<boolean>(false);
  const [candidates, setCandidates] = useState<PolishCandidate[]>([]);
  const [candidateLoadError, setCandidateLoadError] = useState<string | null>(null);
  const [candidateActionKey, setCandidateActionKey] = useState<string | null>(null);
  const [progressTreeContextMenu, setProgressTreeContextMenu] = useState<ProgressTreeContextMenuState>(null);

  const loadCandidateRecords = async () => {
    try {
      const records = await fetchPolishCandidates({
        session_id: sessionId,
        limit: 100,
      });
      setCandidates(records);
      setCandidateLoadError(null);
    } catch (loadError) {
      setCandidates([]);
      setCandidateLoadError(
        loadError instanceof Error
          ? loadError.message
          : "候选对象加载失败，请稍后重试。",
      );
    }
  };

  const loadSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const detail = await fetchPolishSession(sessionId);
      setSession(detail);
      await loadCandidateRecords();
    } catch (loadError) {
      setSession(null);
      setCandidates([]);
      setError(parseWorkbenchError(loadError));
    } finally {
      setLoading(false);
    }
  };

  const recoverProgressWriteConflict = async (writeError: unknown): Promise<boolean> => {
    const recovery = resolveProgressWriteErrorRecovery(writeError);
    if (recovery === null) {
      return false;
    }
    setWorkbenchFailureState(recovery.failureState);
    await loadSession();
    message.warning(recovery.message);
    return true;
  };

  useEffect(() => {
    setAnswerText("");
    answerSubmissionKeyDraftRef.current = null;
    setAnswerError(null);
    setWorkbenchFailureState(null);
    setSelectedProgressNodeRef(null);
    setSelectedProgressNodeKey(null);
    setSelectedQuestionId(null);
    setSelectedAnswerId(null);
    setCandidates([]);
    setCandidateLoadError(null);
    setCandidateActionKey(null);
    setProgressTreeContextMenu(null);
    setCompletingQuestion(false);
    setEndingSession(false);
    setEndConfirmOpen(false);
    void loadSession();
  }, [sessionId]);

  const createFeedbackNextQuestion = async (feedbackId: string, progressNodeRef?: string | null) => {
    if (session === null) {
      return;
    }
    if (isPolishSessionEnded(session)) {
      setAnswerError("模拟面试已结束，不能继续生成题目。");
      return;
    }
    const targetProgressNodeRef = resolveQuestionGenerationProgressNodeRef(
      session,
      progressNodeRef,
      selectedProgressNodeDetailRef,
    );
    if (targetProgressNodeRef === null) {
      setAnswerError("请先选择一个进展栏目后再生成题目。");
      return;
    }
    setCreatingQuestion(true);
    setAnswerError(null);
    setWorkbenchFailureState(null);
    try {
      await createPolishFeedbackNextQuestionTask(sessionId, feedbackId, {
        selected_progress_node_ref: targetProgressNodeRef,
        completed_focus_refs: completedFocusRefsForProgressNode(session, targetProgressNodeRef),
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
    if (session === null) {
      setAnswerError("会话尚未加载完成，请稍后重试。");
      return;
    }
    if (isPolishSessionEnded(session)) {
      setAnswerError("模拟面试已结束，不能继续提交回答。");
      return;
    }
    const currentQuestionState = resolveQuestionNodeState(session, selectedProgressNode);
    if (currentQuestionState === null) {
      setAnswerError("请先选择左侧已有题目的节点后再提交回答。");
      return;
    }
    const trimmedAnswer = answerText.trim();
    if (!trimmedAnswer) {
      setAnswerError("请先输入回答内容。");
      return;
    }

    setAnswerError(null);
    setWorkbenchFailureState(null);
    setSubmittingAnswer(true);
    const keyDraft = resolveAnswerSubmissionKeyDraft(
      answerSubmissionKeyDraftRef.current,
      {
        sessionId,
        questionId: currentQuestionState.questionId,
        answerText: trimmedAnswer,
      },
    );
    answerSubmissionKeyDraftRef.current = keyDraft;
    try {
      const answer = await createPolishAnswer(sessionId, {
        question_id: currentQuestionState.questionId,
        answer_text: trimmedAnswer,
      }, {
        idempotencyKey: keyDraft.idempotencyKey,
      });
      setFeedbackGenerating(true);
      try {
        const feedbackTask = await createPolishFeedbackTask(sessionId, {
          answer_id: answer.answer_id,
        });
        if (isPolishAiTaskRunningStatus(feedbackTask.status)) {
          await waitForPolishFeedbackTaskResult(feedbackTask.ai_task_id);
        }
      } catch (feedbackError) {
        setWorkbenchFailureState("feedbackFailedAnswerSaved");
        setAnswerError(
          feedbackError instanceof Error
            ? `回答已保存，但反馈生成失败：${feedbackError.message}`
            : "回答已保存，但反馈生成失败，请稍后重试。",
        );
        setAnswerText(trimmedAnswer);
        await loadSession();
        return;
      } finally {
        setFeedbackGenerating(false);
      }

      try {
        const refreshed = await refreshPolishProgressTreeState(sessionId);
        setSession(refreshed);
        await loadCandidateRecords();
        setAnswerText("");
        answerSubmissionKeyDraftRef.current = null;
        if (refreshed.progress_tree_status === "refresh_failed") {
          setWorkbenchFailureState("progressRefreshFailed");
          setAnswerError("反馈已生成，但进展树刷新失败；当前题目、回答和反馈不会丢失。");
        } else {
          setWorkbenchFailureState(null);
        }
      } catch (refreshError) {
        if (await recoverProgressWriteConflict(refreshError)) {
          return;
        }
        setWorkbenchFailureState("progressRefreshFailed");
        setAnswerError(
          refreshError instanceof Error
            ? `反馈已生成，但进展树刷新失败：${refreshError.message}`
            : "反馈已生成，但进展树刷新失败；当前题目、回答和反馈不会丢失。",
        );
        setAnswerText(trimmedAnswer);
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
  const selectedProgressNode = findWorkbenchProgressNodeByKey(progressNodes, selectedProgressNodeKey);
  const progressPercent =
    session === null ? 0 : Math.max(0, Math.min(100, session.progress_tree_state?.progress?.progress_percent ?? 0));
  const currentProgressNodeKey =
    resolveCurrentWorkbenchProgressNodeKey(
      progressNodes,
      session === null ? null : resolveSessionCurrentProgressNodeRef(session),
    );
  const selectedProgressNodeDetailRef =
    session === null ? null : resolveProgressTreeDetailNodeRef(session, selectedProgressNodeRef);
  const activeFeedbackPanelWidth = isFeedbackPanelCollapsed
    ? INTERVIEW_WORKBENCH_LAYOUT_B_FEEDBACK_PANEL_WIDTH_POLICY.defaultCollapsed
    : feedbackPanelWidth;
  const stickyProgressNodeContextRef =
    session === null
      ? null
      : selectedProgressNodeRef ??
        getWorkbenchProgressNodeQuestionTargetRef(selectedProgressNode) ??
        session.progress_tree_state.current_priority?.progress_node_ref ??
        null;
  const selectedProgressNodeBanner =
    session === null || stickyProgressNodeContextRef === null
      ? null
      : buildProgressTreeContextBannerContent(session, stickyProgressNodeContextRef);
  const isSessionEnded = isPolishSessionEnded(session);
  const headerChips = session === null ? [] : buildWorkbenchHeaderChips(session, progressPercent);
  const isProgressTreeInsufficient = session?.progress_tree_status === "insufficient_context";
  const isProgressTreeReady = session?.progress_tree_status === "ready";
  const isProgressTreeRefreshFailed = session?.progress_tree_status === "refresh_failed";
  const isProgressTreePending = isProgressTreePendingGeneration(session?.progress_tree_status);
  const isProgressTreeFailed = session?.progress_tree_status === "failed";
  const hasProgressTreeNodes = progressNodes.length > 0;
  const canShowProgressTree = hasProgressTreeNodes && (isProgressTreeReady || isProgressTreeRefreshFailed);
  const questionActionState = deriveWorkbenchQuestionActionState({
    session,
    selectedProgressNode,
    progressNodeRef: selectedProgressNodeDetailRef,
    canShowProgressTree,
    creatingQuestion,
    submittingAnswer,
    feedbackGenerating,
    completingQuestion,
    endingSession,
  });
  const composerActionState = deriveComposerActionViewModel({
    session,
    questionActionState,
    answerText,
    selectedProgressNodeRef: selectedProgressNodeDetailRef,
    isFollowUpQuestionApiSupported: true,
  });
  const canSendAnswer = questionActionState.canSendAnswer;
  const fallbackFocusedQuestionId =
    session === null ? null : resolveWorkbenchQuestionFocusId(session, selectedProgressNode, selectedProgressNodeDetailRef);
  const focusedQuestionId = selectedQuestionId ?? fallbackFocusedQuestionId;
  const focusedQuestionTurn = session === null || focusedQuestionId === null
    ? null
    : session.turns.find((turn) => turn.question_id === focusedQuestionId) ?? null;
  const focusedQuestionLatestAnswerId =
    focusedQuestionTurn === null || focusedQuestionTurn.answers.length === 0
      ? null
      : focusedQuestionTurn.answers[focusedQuestionTurn.answers.length - 1].answer_id;
  const focusedQuestionLatestAnswer =
    focusedQuestionTurn === null || focusedQuestionTurn.answers.length === 0
      ? null
      : focusedQuestionTurn.answers[focusedQuestionTurn.answers.length - 1];
  const focusedQuestionLatestFeedbackId =
    focusedQuestionLatestAnswer?.feedback_id ?? focusedQuestionLatestAnswer?.feedback_payload?.feedback_id ?? null;
  const selectedAnswerContext = findSelectedAnswerContext(session, selectedAnswerId);
  const selectedAnswerFeedbackMeta = buildSelectedAnswerFeedbackMetaViewModel(session, selectedAnswerId);
  const selectedAnswer = selectedAnswerContext?.answer ?? null;
  const selectedAnswerFeedbackCard = selectedAnswer === null ? null : buildFeedbackCardViewModel(selectedAnswer);
  const fixedNextActionBar = buildWorkbenchFixedNextActionBarViewModel(focusedQuestionLatestAnswer);
  const fixedNextActionProgressNodeRef = focusedQuestionTurn?.progress_node_ref ?? selectedProgressNodeDetailRef;
  const canCreateFeedbackNextQuestion = Boolean(
    focusedQuestionLatestFeedbackId &&
      !isSessionEnded &&
      !creatingQuestion &&
      !submittingAnswer &&
      !feedbackGenerating &&
      !completingQuestion &&
      !endingSession,
  );
  const selectedCandidateReview = buildCandidateReviewViewModel(
    selectedAnswer
      ? candidates.filter((candidate) => candidateBelongsToAnswer(candidate, selectedAnswer))
      : [],
  );
  const shouldShowFixedComposerActionBar = fixedNextActionBar !== null;
  const feedbackPanelCandidateItems = {
    pending: selectedCandidateReview?.items.filter((item) => item.canConfirm || item.canDismiss) ?? [],
    settled: selectedCandidateReview?.items.filter((item) => !item.canConfirm && !item.canDismiss) ?? [],
  };
  const selectedAnswerFeedbackSummarySections = selectedAnswerFeedbackCard === null
    ? []
    : selectedAnswerFeedbackCard.sections.filter(
        (section) => section.key === "feedback" || section.key === "score" || section.key === "positive_evidence_points",
      );
  const selectedAnswerLossPointsSection = selectedAnswerFeedbackCard?.sections.find(
    (section) => section.key === "loss_points",
  ) ?? null;
  const selectedAnswerReferenceAnswerSection = selectedAnswerFeedbackCard?.sections.find(
    (section) => section.key === "reference_answer",
  ) ?? null;
  const hasSelectedAnswerFeedback = selectedAnswer !== null && (
    Boolean(selectedAnswer.feedback_id) ||
    Boolean(selectedAnswer.feedback_created_at) ||
    selectedAnswer.feedback_payload !== undefined
  );
  const timelineViewModel = buildInterviewTimelineViewModel(session, focusedQuestionId);
  const stickyQuestionContext = buildStickyQuestionContextViewModel(
    session,
    focusedQuestionId,
    selectedProgressNodeRef,
    {
      selectedProgressNode,
      selectedProgressNodeDetailRef: stickyProgressNodeContextRef,
    },
  );
  const chatScrollAutoTrigger = buildQuestionConversationAutoScrollTrigger({
    focusedQuestionId,
    selectedProgressNodeRef: selectedProgressNodeDetailRef,
    latestAnswerId: focusedQuestionLatestAnswerId,
    latestFeedbackId: focusedQuestionLatestFeedbackId,
  });
  const progressTreeContextMenuNode =
    progressTreeContextMenu === null ? null : findWorkbenchProgressNodeByKey(progressNodes, progressTreeContextMenu.nodeKey);
  const progressTreeContextMenuDetailRef =
    session === null
      ? null
      : resolveProgressTreeDetailNodeRef(
          session,
          getWorkbenchProgressNodeQuestionTargetRef(progressTreeContextMenuNode),
        );
  const progressTreeContextMenuActionState = deriveWorkbenchQuestionActionState({
    session,
    selectedProgressNode: progressTreeContextMenuNode,
    progressNodeRef: progressTreeContextMenuDetailRef,
    canShowProgressTree,
    creatingQuestion,
    submittingAnswer,
    feedbackGenerating,
    completingQuestion,
    endingSession,
  });
  const progressTreeContextMenuItems = buildProgressTreeContextMenuItems(
    progressTreeContextMenuNode,
    progressTreeContextMenuActionState,
  );
  const workbenchMachineState = deriveWorkbenchMachineState({
    session,
    creatingQuestion,
    feedbackGenerating,
    failureState: isProgressTreeRefreshFailed ? "progressRefreshFailed" : workbenchFailureState,
  });
  const workbenchMachineCopy = WORKBENCH_MACHINE_STATE_COPY[workbenchMachineState];
  const [refreshingProgressTree, setRefreshingProgressTree] = useState<boolean>(false);
  const [generatingProgressTree, setGeneratingProgressTree] = useState<boolean>(false);
  const progressTreeActionLoading = refreshingProgressTree || generatingProgressTree;
  const generateProgressTree = async () => {
    if (session === null || generatingProgressTree) {
      return;
    }
    setGeneratingProgressTree(true);
    setWorkbenchFailureState(null);
    try {
      const generated = await generateInitialPolishProgressTree(sessionId);
      setSession(generated);
      await loadCandidateRecords();
      if (generated.progress_tree_status === "failed") {
        message.warning("进展树生成失败，可稍后重试。");
      } else if (generated.progress_tree_status === "insufficient_context") {
        message.warning("岗位或简历内容不足，暂不能生成进展树。");
      } else if (generated.progress_tree_status === "ready") {
        message.success("进展树已生成。");
      }
    } catch (error) {
      if (await recoverProgressWriteConflict(error)) {
        return;
      }
      message.error(error instanceof Error ? error.message : "生成进展树失败，请稍后重试。");
    } finally {
      setGeneratingProgressTree(false);
    }
  };
  const refreshProgressTree = async () => {
    if (session === null || refreshingProgressTree) {
      return;
    }
    setRefreshingProgressTree(true);
    setWorkbenchFailureState(null);
    try {
      const refreshed = await refreshPolishProgressTreeState(sessionId);
      setSession(refreshed);
      await loadCandidateRecords();
      if (refreshed.progress_tree_status === "refresh_failed") {
        setWorkbenchFailureState("progressRefreshFailed");
        message.warning("进展树刷新失败，已保留当前题目、回答和反馈。");
      } else {
        message.success("进展树已刷新。");
      }
    } catch (error) {
      if (await recoverProgressWriteConflict(error)) {
        return;
      }
      setWorkbenchFailureState("progressRefreshFailed");
      message.error(error instanceof Error ? error.message : "刷新进展树失败，请稍后重试。");
    } finally {
      setRefreshingProgressTree(false);
    }
  };

  const completeCurrentQuestion = async (progressNodeRefOverride?: string | null) => {
    if (session === null) {
      setAnswerError("请先选择当前问题。");
      return;
    }
    if (isSessionEnded) {
      setAnswerError("模拟面试已结束，不能继续标记问题。");
      return;
    }
    const targetProgressNodeRef = progressNodeRefOverride ?? selectedProgressNodeDetailRef;
    const currentQuestionState = resolveCurrentQuestionState(session, targetProgressNodeRef);
    if (currentQuestionState === null) {
      setAnswerError("请先选择当前问题。");
      return;
    }
    if (currentQuestionState.status === "completed") {
      setAnswerError("当前问题已完成，无需重复标记。");
      return;
    }
    setCompletingQuestion(true);
    setAnswerError(null);
    try {
      const updatedSession = await completePolishQuestion(sessionId, currentQuestionState.questionId);
      setSession(updatedSession);
      await loadCandidateRecords();
      message.success("当前问题已标记为完成。");
    } catch (completeError) {
      if (await recoverProgressWriteConflict(completeError)) {
        return;
      }
      setAnswerError(
        completeError instanceof Error
          ? completeError.message
          : "标记问题完成失败，请稍后重试。",
      );
    } finally {
      setCompletingQuestion(false);
    }
  };

  const endCurrentSession = async () => {
    if (session === null || isSessionEnded) {
      return;
    }
    setEndingSession(true);
    setAnswerError(null);
    try {
      const updatedSession = await endPolishSession(sessionId);
      setSession(updatedSession);
      setEndConfirmOpen(false);
      message.success("模拟面试已结束。");
    } catch (endError) {
      if (await recoverProgressWriteConflict(endError)) {
        return;
      }
      setAnswerError(
        endError instanceof Error
          ? endError.message
          : "结束模拟面试失败，请稍后重试。",
      );
    } finally {
      setEndingSession(false);
    }
  };

  useEffect(() => {
    setExpandedProgressNodeKeys(new Set(collectDefaultExpandedProgressNodeKeys(progressNodes)));
  }, [session]);

  useEffect(() => {
    if (session === null) {
      return;
    }
    const questionExists = selectedQuestionId !== null && session.turns.some((turn) => turn.question_id === selectedQuestionId);
    const nextQuestionId = questionExists ? selectedQuestionId : fallbackFocusedQuestionId;
    const answerContext = findSelectedAnswerContext(session, selectedAnswerId);
    if (questionExists && answerContext !== null) {
      return;
    }
    setSelectedQuestionId(nextQuestionId);
    setSelectedAnswerId(resolveLatestAnswerIdForQuestion(session, nextQuestionId));
  }, [session, fallbackFocusedQuestionId, selectedQuestionId, selectedAnswerId]);

  const scrollChatToQuestion = (questionId: string | null, behavior: ScrollBehavior = "smooth") => {
    const container = chatScrollRef.current;
    if (container === null) {
      return;
    }
    chatScrollIsAutoingRef.current = true;
    if (questionId === null) {
      container.scrollTo({ top: container.scrollHeight, behavior });
    } else {
      const target = container.querySelector<HTMLElement>(`[data-workbench-question-bottom-anchor="${questionId}"]`)
        ?? Array.from(container.querySelectorAll<HTMLElement>("[data-workbench-question-id]"))
          .find((element) => element.dataset.workbenchQuestionId === questionId);

      if (target) {
        target.scrollIntoView({ block: "end", behavior });
      } else {
        container.scrollTo({ top: container.scrollHeight, behavior });
      }
    }
    window.requestAnimationFrame(() => {
      chatScrollIsAutoingRef.current = false;
    });
  };

  useEffect(() => {
    if (!hasQuestion) {
      return;
    }
    const shouldAutoScroll = shouldAutoScrollQuestionConversation({
      nextTrigger: chatScrollAutoTrigger,
      previousTrigger: chatScrollLastAutoTriggerRef.current,
      hasUserManuallyScrolled: chatScrollManuallyScrolledRef.current,
    });
    if (!shouldAutoScroll) {
      return;
    }
    const frameId = window.requestAnimationFrame(() => scrollChatToQuestion(focusedQuestionId, "auto"));
    chatScrollManuallyScrolledRef.current = false;
    chatScrollLastAutoTriggerRef.current = chatScrollAutoTrigger;
    return () => window.cancelAnimationFrame(frameId);
  }, [chatScrollAutoTrigger, hasQuestion, focusedQuestionId]);

  useEffect(() => {
    const container = chatScrollRef.current;
    if (container === null) {
      return;
    }
    const markManualScroll = () => {
      if (chatScrollIsAutoingRef.current) {
        return;
      }
      chatScrollManuallyScrolledRef.current = true;
    };

    container.addEventListener("scroll", markManualScroll, { passive: true });
    return () => {
      container.removeEventListener("scroll", markManualScroll);
    };
  }, []);

  useEffect(() => {
    setCurrentQuestionTextExpanded(false);
  }, [stickyQuestionContext?.selectedQuestionId]);

  useEffect(() => {
    setProgressNodeContextExpanded(false);
  }, [selectedProgressNodeDetailRef]);

  useEffect(() => {
    if (progressTreeContextMenu === null) {
      return undefined;
    }

    const closeContextMenu = () => setProgressTreeContextMenu(null);
    const closeContextMenuFromKeyboard = (event: KeyboardEvent) => {
      if (shouldCloseProgressTreeContextMenuFromKeyboard(event)) {
        closeContextMenu();
      }
    };

    window.addEventListener("pointerdown", closeContextMenu);
    window.addEventListener("scroll", closeContextMenu, true);
    window.addEventListener("keydown", closeContextMenuFromKeyboard);

    return () => {
      window.removeEventListener("pointerdown", closeContextMenu);
      window.removeEventListener("scroll", closeContextMenu, true);
      window.removeEventListener("keydown", closeContextMenuFromKeyboard);
    };
  }, [progressTreeContextMenu]);

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

  const startProgressPanelResize = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (isProgressPanelCollapsed) {
      return;
    }
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = progressPanelWidth;
    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const stopResize = () => {
      window.removeEventListener("pointermove", resizeProgressPanel);
      window.removeEventListener("pointerup", stopResize);
      window.removeEventListener("pointercancel", stopResize);
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
    };

    const resizeProgressPanel = (moveEvent: PointerEvent) => {
      const nextWidth = startWidth + moveEvent.clientX - startX;
      setProgressPanelWidth(
        Math.max(PROGRESS_PANEL_MIN_WIDTH, Math.min(PROGRESS_PANEL_MAX_WIDTH, Math.round(nextWidth))),
      );
    };

    window.addEventListener("pointermove", resizeProgressPanel);
    window.addEventListener("pointerup", stopResize);
    window.addEventListener("pointercancel", stopResize);
  };

  const startFeedbackPanelResize = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (isFeedbackPanelCollapsed || chatBodyRef.current === null) {
      return;
    }
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = feedbackPanelWidth;
    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const stopResize = () => {
      window.removeEventListener("pointermove", resizeFeedbackPanel);
      window.removeEventListener("pointerup", stopResize);
      window.removeEventListener("pointercancel", stopResize);
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
    };

    const resizeFeedbackPanel = (moveEvent: PointerEvent) => {
      const nextWidth = startWidth + (startX - moveEvent.clientX);
      setFeedbackPanelWidth(
        Math.max(
          INTERVIEW_WORKBENCH_LAYOUT_B_FEEDBACK_PANEL_WIDTH_POLICY.min,
          Math.min(
            INTERVIEW_WORKBENCH_LAYOUT_B_FEEDBACK_PANEL_WIDTH_POLICY.max,
            Math.round(nextWidth),
          ),
        ),
      );
    };

    window.addEventListener("pointermove", resizeFeedbackPanel);
    window.addEventListener("pointerup", stopResize);
    window.addEventListener("pointercancel", stopResize);
  };

  const runCandidateAction = async (candidateId: string, action: "confirm" | "dismiss") => {
    const actionKey = `${candidateId}:${action}`;
    setCandidateActionKey(actionKey);
    try {
      const result = action === "confirm"
        ? await confirmPolishCandidate(candidateId)
        : await dismissPolishCandidate(candidateId);
      setCandidates((currentCandidates) => {
        const exists = currentCandidates.some((candidate) => candidate.candidate_id === result.candidate.candidate_id);
        if (!exists) {
          return [result.candidate, ...currentCandidates];
        }
        return currentCandidates.map((candidate) =>
          candidate.candidate_id === result.candidate.candidate_id ? result.candidate : candidate,
        );
      });
      message.success(action === "confirm" ? "候选对象已确认。" : "候选对象已忽略。");
    } catch (actionError) {
      message.error(actionError instanceof Error ? actionError.message : "候选对象操作失败，请稍后重试。");
    } finally {
      setCandidateActionKey(null);
    }
  };

  const closeProgressTreeContextMenu = () => {
    setProgressTreeContextMenu(null);
  };

  const openProgressTreeContextMenu = (
    event: ReactMouseEvent<HTMLElement>,
    node: WorkbenchProgressNode,
  ) => {
    event.preventDefault();
    event.stopPropagation();

    const nextSelectedRef = resolveProgressTreeSelectedNodeRefAfterClick(node, selectedProgressNodeDetailRef);
    if ((node.kind === "node" || isQuestionNode(node)) && nextSelectedRef !== null) {
      setSelectedProgressNodeRef(nextSelectedRef);
      setSelectedProgressNodeKey(node.key);
    }

    const menuWidth = 224;
    const menuHeight = 176;
    const x = Math.max(8, Math.min(event.clientX, window.innerWidth - menuWidth - 8));
    const y = Math.max(8, Math.min(event.clientY, window.innerHeight - menuHeight - 8));

    setProgressTreeContextMenu({
      nodeKey: node.key,
      x,
      y,
    });
  };

  const copyProgressTreeNodeInfo = async (node: WorkbenchProgressNode) => {
    if (!window.navigator.clipboard?.writeText) {
      message.error("当前环境不支持剪贴板复制。");
      return;
    }
    if (session === null) {
      message.error("当前会话详情为空，无法复制节点信息。");
      return;
    }
    try {
      await window.navigator.clipboard.writeText(buildProgressTreeNodeClipboardMarkdown(session, node));
      message.success("节点信息已复制。");
    } catch (copyError) {
      message.error(copyError instanceof Error ? copyError.message : "复制失败，请稍后重试。");
    }
  };

  const runProgressTreeContextMenuAction = async (item: WorkbenchProgressTreeContextMenuItem) => {
    if (item.disabled || progressTreeContextMenuNode === null) {
      return;
    }
    closeProgressTreeContextMenu();
    if (item.key === "mark_question_completed") {
      await completeCurrentQuestion(progressTreeContextMenuDetailRef);
      return;
    }
    await copyProgressTreeNodeInfo(progressTreeContextMenuNode);
  };

  const renderProgressTreeContextMenu = () => {
    if (progressTreeContextMenu === null || progressTreeContextMenuNode === null) {
      return null;
    }

    return (
      <div
        className={styles.progressTreeContextMenu}
        role="menu"
        aria-label={`进展树节点操作：${progressTreeContextMenuNode.title}`}
        style={{ left: progressTreeContextMenu.x, top: progressTreeContextMenu.y }}
        onPointerDown={(event) => event.stopPropagation()}
        onContextMenu={(event) => event.preventDefault()}
      >
        <Typography.Text strong className={styles.progressTreeContextMenuTitle}>
          {progressTreeContextMenuNode.title}
        </Typography.Text>
        <div className={styles.progressTreeContextMenuList}>
          {progressTreeContextMenuItems.map((item) => (
            <button
              key={item.key}
              className={styles.progressTreeContextMenuItem}
              type="button"
              role="menuitem"
              disabled={item.disabled}
              onClick={() => {
                void runProgressTreeContextMenuAction(item);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const selectTimelineAnswer = (answerId: string | null) => {
    if (answerId === null) {
      return;
    }
    setSelectedAnswerId(answerId);
    setActiveFeedbackPanelTab("summary");
  };

  const timelineItemClassName = (event: WorkbenchTimelineEventViewModel) => [
    styles.timelineItem,
    event.alignment === "right" ? styles.timelineItemRight : styles.timelineItemLeft,
  ].join(" ");

  const timelineBubbleClassName = (event: WorkbenchTimelineEventViewModel) => [
    styles.timelineBubble,
    event.kind === "system_question" ? styles.timelineBubbleQuestion : "",
    event.kind === "system_hint" ? styles.timelineBubbleHint : "",
    event.kind === "user_answer" ? styles.timelineBubbleAnswer : "",
    event.kind === "quick_review" ? styles.timelineBubbleQuickReview : "",
    event.answerId !== null && event.answerId === selectedAnswerId ? styles.timelineBubbleSelected : "",
  ].filter(Boolean).join(" ");

  const renderTimelineEvent = (event: WorkbenchTimelineEventViewModel) => {
    const interactive = event.answerId !== null && (event.kind === "user_answer" || event.kind === "quick_review");
    return (
      <article
        key={event.id}
        className={timelineItemClassName(event)}
        data-timeline-event-kind={event.kind}
        data-answer-id={event.answerId ?? undefined}
      >
        <div className={styles.timelineMeta}>{event.metaLabel}</div>
        {interactive ? (
          <button
            type="button"
            className={timelineBubbleClassName(event)}
            onClick={() => selectTimelineAnswer(event.answerId)}
          >
            {event.quickReview === null ? (
              <Typography.Text>{event.text}</Typography.Text>
            ) : (
              <>
                <div className={styles.timelineQuickReviewSummaryRow}>
                  <Tag className={styles.feedbackRoundPill}>简评</Tag>
                  <span className={styles.timelineQuickReviewMetric}>{event.quickReview.scoreLabel}</span>
                  <span className={styles.timelineQuickReviewMetric}>{event.quickReview.maturityLabel}</span>
                  {renderStatusChip("blue", event.quickReview.statusLabel)}
                  <span className={styles.timelineQuickReviewLink}>查看完整反馈</span>
                </div>
                <Typography.Text>{event.quickReview.suggestion}</Typography.Text>
              </>
            )}
          </button>
        ) : (
          <div className={timelineBubbleClassName(event)}>
            <Typography.Text>{event.text}</Typography.Text>
          </div>
        )}
      </article>
    );
  };

  const renderCurrentQuestionContextStickyHeader = () => {
    if (stickyQuestionContext === null) {
      return null;
    }
    const stickyQuestionText =
      stickyQuestionContext.selectedQuestionId !== null ? stickyQuestionContext.questionText : null;
    const hasStickyQuestionContext = stickyQuestionText !== null;
    const isStickyContextExpanded = isProgressNodeContextExpanded;
    const stickyContextMetaItems = buildStickyQuestionContextCompactMetaItems(stickyQuestionContext);
    const selectedAnswerLabel = selectedAnswerFeedbackMeta?.answerLabel ?? "暂无回答";
    const questionSourceLabels = focusedQuestionTurn?.question_sources?.map((source) =>
      QUESTION_SOURCE_TYPE_LABELS[source.source_type] ?? source.source_type,
    ) ?? [];
    const questionSourceText = questionSourceLabels.length > 0
      ? Array.from(new Set(questionSourceLabels)).join("、")
      : "暂无来源";
    const nodeContextBlocks = [
      {
        title: "节点目标",
        items: selectedProgressNodeBanner?.depthRequirement ? [selectedProgressNodeBanner.depthRequirement] : [],
      },
      {
        title: "常见失分",
        items: selectedProgressNodeBanner?.lossRisks ?? [],
      },
      {
        title: "追问方向",
        items: selectedProgressNodeBanner?.followUpDirections ?? [],
      },
      {
        title: "证据摘要",
        items: selectedProgressNodeBanner?.technicalCoverage ?? [],
      },
    ].filter((block) => block.items.length > 0);
    const canExpandStickyContext = nodeContextBlocks.length > 0 || hasStickyQuestionContext;
    const toggleStickyContext = () => {
      const nextExpanded = !isStickyContextExpanded;
      setProgressNodeContextExpanded(nextExpanded);
      setCurrentQuestionTextExpanded(nextExpanded);
    };

    return (
      <section
        className={styles.conversationQuestionHeader}
        aria-label="当前题目与节点上下文"
        data-layout-area={INTERVIEW_WORKBENCH_MERGED_CONTEXT_CARD_LAYOUT.layoutArea}
      >
        <div className={styles.conversationQuestionHeaderCompactBar}>
          <div className={styles.conversationQuestionHeaderSummary}>
            {hasStickyQuestionContext ? (
              <Typography.Text className={styles.conversationQuestionHeaderQuestionLine}>
                <span className={styles.conversationQuestionHeaderQuestionPrefix}>
                  {`${INTERVIEW_WORKBENCH_STICKY_CONTEXT_CARD_DISPLAY_POLICY.questionPrefix}${stickyQuestionContext.questionIndexLabel} · `}
                </span>
                {stickyQuestionText}
              </Typography.Text>
            ) : (
              <Typography.Text type="secondary" className={styles.conversationQuestionHeaderQuestionLine}>
                {stickyQuestionContext.emptyDescription ?? stickyQuestionContext.nonQuestionHint}
              </Typography.Text>
            )}
            {stickyContextMetaItems.length > 0 ? (
              <div className={styles.conversationQuestionHeaderMetaRow}>
                {stickyContextMetaItems.map((item) => (
                  <span className={styles.conversationQuestionHeaderMetaItem} key={item.key}>
                    <Typography.Text type="secondary" className={styles.conversationQuestionHeaderMetaLabel}>
                      {item.label}：
                    </Typography.Text>
                    <Typography.Text className={styles.conversationQuestionHeaderValue}>{item.value}</Typography.Text>
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <button
            className={styles.conversationQuestionHeaderToggle}
            type="button"
            aria-expanded={isStickyContextExpanded}
            aria-label={isStickyContextExpanded ? "收起上下文浮层" : "展开上下文浮层"}
            disabled={!canExpandStickyContext}
            onClick={toggleStickyContext}
          >
            <span className={styles.nodeChevron}>
              {isStickyContextExpanded ? <DownOutlined /> : <RightOutlined />}
            </span>
          </button>
        </div>
        {isStickyContextExpanded ? (
          <div className={styles.conversationQuestionHeaderPopover}>
            <div className={styles.conversationQuestionHeaderPopoverGrid}>
              <section className={styles.conversationQuestionHeaderPopoverSection}>
                <Typography.Text strong className={styles.conversationQuestionHeaderPopoverTitle}>
                  节点上下文
                </Typography.Text>
                {nodeContextBlocks.length > 0 ? (
                  nodeContextBlocks.map((block) => (
                    <div className={styles.conversationQuestionHeaderPopoverBlock} key={block.title}>
                      <Typography.Text type="secondary" className={styles.conversationQuestionHeaderPopoverBlockTitle}>
                        {block.title}
                      </Typography.Text>
                      {block.items.length === 1 ? (
                        <Typography.Paragraph className={styles.conversationQuestionHeaderPopoverText}>
                          {block.items[0]}
                        </Typography.Paragraph>
                      ) : (
                        <ul className={styles.conversationQuestionHeaderPopoverList}>
                          {block.items.map((item) => (
                            <li key={`${block.title}:${item}`}>{item}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))
                ) : (
                  <Typography.Text type="secondary">该节点暂无可展开上下文。</Typography.Text>
                )}
              </section>
              {hasStickyQuestionContext ? (
                <section className={styles.conversationQuestionHeaderPopoverSection}>
                  <Typography.Text strong className={styles.conversationQuestionHeaderPopoverTitle}>
                    当前题目
                  </Typography.Text>
                  <div className={styles.conversationQuestionHeaderPopoverBlock}>
                    <Typography.Text type="secondary" className={styles.conversationQuestionHeaderPopoverBlockTitle}>
                      完整题干
                    </Typography.Text>
                    <Typography.Paragraph className={styles.conversationQuestionHeaderPopoverText}>
                      {stickyQuestionText}
                    </Typography.Paragraph>
                  </div>
                  <div className={styles.conversationQuestionHeaderPopoverBlock}>
                    <Typography.Text type="secondary" className={styles.conversationQuestionHeaderPopoverBlockTitle}>
                      题目来源
                    </Typography.Text>
                    <Typography.Text>{questionSourceText}</Typography.Text>
                  </div>
                  <div className={styles.conversationQuestionHeaderPopoverBlock}>
                    <Typography.Text type="secondary" className={styles.conversationQuestionHeaderPopoverBlockTitle}>
                      当前查看回答
                    </Typography.Text>
                    <Typography.Text>{selectedAnswerLabel}</Typography.Text>
                  </div>
                </section>
              ) : null}
            </div>
          </div>
        ) : null}
      </section>
    );
  };

  const renderCurrentQuestionFeedbackPanel = () => {
    const activeCandidates = activeFeedbackPanelTab === "candidate"
      ? feedbackPanelCandidateItems.pending
      : feedbackPanelCandidateItems.settled;
    const lossPointRows = selectedAnswerLossPointsSection?.tableRows ?? [];
    const summarySectionNodes = selectedAnswerFeedbackSummarySections;
    const hasSummary = selectedAnswerFeedbackCard !== null || summarySectionNodes.length > 0;
    const hasLossPoints = lossPointRows.length > 0;
    const hasReferenceAnswer = (selectedAnswerReferenceAnswerSection?.items.length ?? 0) > 0;
    const hasCandidateItems = (selectedCandidateReview?.items.length ?? 0) > 0;
    const feedbackPanelTabs = buildFeedbackPanelTabs({
      hasSummary,
      hasLossPoints,
      hasReferenceAnswer,
      hasCandidateItems,
      lossPointCount: lossPointRows.length,
      candidateCount: feedbackPanelCandidateItems.pending.length + feedbackPanelCandidateItems.settled.length,
    });
    const activeCandidatesTab = activeFeedbackPanelTab === "candidate";
    const candidatePanelClassName = [styles.feedbackPanel, isFeedbackPanelCollapsed ? styles.feedbackPanelCollapsed : ""].join(" ");

    if (isFeedbackPanelCollapsed) {
      return (
        <section
          className={candidatePanelClassName}
          data-layout-area="right_feedback_sheet"
          data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.feedbackPanel}
          aria-label="反馈分析侧边栏"
        >
          <button
            type="button"
            className={styles.feedbackPanelCollapsedButton}
            aria-label="展开反馈分析面板"
            onClick={() => {
              setFeedbackPanelCollapsed(false);
              if (hasCandidateItems) {
                setActiveFeedbackPanelTab("candidate");
                return;
              }
              if (hasLossPoints) {
                setActiveFeedbackPanelTab("lossPoints");
                return;
              }
              if (hasReferenceAnswer) {
                setActiveFeedbackPanelTab("referenceAnswer");
                return;
              }
              setActiveFeedbackPanelTab("summary");
            }}
          >
            <LeftOutlined />
          </button>
        </section>
      );
    }

    return (
      <section
        className={candidatePanelClassName}
        data-layout-area="right_feedback_sheet"
        data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.feedbackPanel}
        aria-label="反馈分析侧边栏"
      >
        <button
          className={styles.feedbackPanelResizeHandle}
          type="button"
          aria-label="拖拽调整反馈面板宽度"
          onPointerDown={startFeedbackPanelResize}
        />
        <div className={styles.feedbackPanelHeader}>
          <Typography.Text strong>反馈分析</Typography.Text>
          <Button
            type="text"
            size="small"
            icon={<LeftOutlined />}
            aria-label="收起反馈分析面板"
            onClick={() => {
              setFeedbackPanelCollapsed(true);
              setActiveFeedbackPanelTab("summary");
            }}
          />
        </div>
        {selectedAnswerId === null || selectedAnswer === null ? (
          <div className={styles.feedbackPanelEmpty}>
            <Typography.Text type="secondary">请选择一轮回答查看反馈分析</Typography.Text>
          </div>
        ) : !hasSelectedAnswerFeedback ? (
          <div className={styles.feedbackPanelEmpty}>
            <Typography.Text type="secondary">当前回答暂无反馈，可稍后重试生成反馈</Typography.Text>
          </div>
        ) : (
          <>
        {selectedAnswerFeedbackMeta !== null ? (
          <div className={styles.feedbackPanelSelectedMeta}>
            {`${selectedAnswerFeedbackMeta.questionLabel} · ${selectedAnswerFeedbackMeta.answerLabel} · ${selectedAnswerFeedbackMeta.answerTimeLabel} · ${selectedAnswerFeedbackMeta.feedbackStatusLabel}`}
          </div>
        ) : null}
        <Tabs
          className={styles.feedbackPanelTabs}
          activeKey={activeFeedbackPanelTab}
          onChange={(tabKey) => {
            if (tabKey === "summary" || tabKey === "lossPoints" || tabKey === "referenceAnswer" || tabKey === "candidate") {
              setActiveFeedbackPanelTab(tabKey);
            }
          }}
          items={feedbackPanelTabs}
        />
        <div className={styles.feedbackPanelContent}>
          {activeCandidatesTab ? (
            <CandidateList
              pendingCount={feedbackPanelCandidateItems.pending.length}
              settledCount={feedbackPanelCandidateItems.settled.length}
              mergeHint={selectedCandidateReview?.mergeHint ?? null}
              items={activeCandidates}
              emptyMessage="当前无候选对象"
              candidateActionKey={candidateActionKey}
              isSessionEnded={isSessionEnded}
              onCandidateAction={(candidateId, action) => {
                void runCandidateAction(candidateId, action);
              }}
            />
          ) : (
            <ResultCard
              activeTab={activeFeedbackPanelTab}
              feedbackCard={selectedAnswerFeedbackCard}
              summarySections={summarySectionNodes}
              lossPointsSection={selectedAnswerLossPointsSection}
              referenceAnswerSection={selectedAnswerReferenceAnswerSection}
            />
          )}
        </div>
          </>
        )}
      </section>
    );
  };

  const renderCurrentQuestionComposer = () => {
    return (
      <FeedbackForm
        answerError={answerError}
        showNextActionBar={shouldShowFixedComposerActionBar}
        fixedNextActionBar={fixedNextActionBar}
        creatingQuestion={creatingQuestion}
        submittingAnswer={submittingAnswer}
        feedbackGenerating={feedbackGenerating}
        completingQuestion={completingQuestion}
        isSessionEnded={isSessionEnded}
        answerText={answerText}
        canSendAnswer={canSendAnswer}
        canCreateFeedbackNextQuestion={canCreateFeedbackNextQuestion}
        composerActionState={composerActionState}
        onAnswerTextChange={setAnswerText}
        onSendAnswer={() => {
          void sendAnswer();
        }}
        onCreateFeedbackNextQuestion={() => {
          if (focusedQuestionLatestFeedbackId === null) {
            setAnswerError("当前题目还没有可授权的反馈，无法生成下一题。");
            return;
          }
          void createFeedbackNextQuestion(focusedQuestionLatestFeedbackId, fixedNextActionProgressNodeRef);
        }}
        onCompleteCurrentQuestion={() => {
          void completeCurrentQuestion();
        }}
      />
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
            onContextMenu={(event) => openProgressTreeContextMenu(event, node)}
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

    const canSelectNode = node.kind === "node" || isQuestionNode(node);
    const isActive =
      selectedProgressNodeKey !== null
        ? node.key === selectedProgressNodeKey
        : node.kind === "node" && node.key === selectedProgressNodeDetailRef;
    const isCurrentPriority = canSelectNode && node.key === currentProgressNodeKey;
    const isExpandable = Boolean(node.children && node.children.length > 0);
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
          onContextMenu={(event) => openProgressTreeContextMenu(event, node)}
          onClick={
            canSelectNode
              ? () => {
                  const nextSelectedRef = resolveProgressTreeSelectedNodeRefAfterClick(node, selectedProgressNodeDetailRef);
                  const nextQuestionId = session === null
                    ? null
                    : resolveWorkbenchQuestionFocusId(session, node, nextSelectedRef);
                  setSelectedProgressNodeRef(nextSelectedRef);
                  setSelectedProgressNodeKey(node.key);
                  setSelectedQuestionId(nextQuestionId);
                  setSelectedAnswerId(resolveLatestAnswerIdForQuestion(session, nextQuestionId));
                  chatScrollManuallyScrolledRef.current = false;
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

  const workspaceGridClassName = [
    styles.workspaceGrid,
    isProgressPanelCollapsed ? styles.workspaceGridLeftCollapsed : "",
    isFeedbackPanelCollapsed ? styles.workspaceGridRightCollapsed : "",
    isProgressPanelCollapsed && isFeedbackPanelCollapsed ? styles.workspaceGridCollapsed : "",
  ].filter(Boolean).join(" ");
  const progressPanelClassName = [
    styles.progressPanel,
    isProgressPanelCollapsed ? styles.progressPanelCollapsed : "",
  ].filter(Boolean).join(" ");
  const workspaceGridStyle = {
    "--progress-panel-width": `${progressPanelWidth}px`,
    "--feedback-panel-width": `${activeFeedbackPanelWidth}px`,
    ...resolveMessageWidthStyle(resolveMessageWidthPolicy(isProgressPanelCollapsed, isFeedbackPanelCollapsed)),
  } as CSSProperties;

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
        <div
          className={styles.workbenchRoot}
          data-layout-variant={INTERVIEW_WORKBENCH_LAYOUT_VARIANT}
          data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.root}
        >
          <section className={styles.heroPanel} data-layout-area="summary_bar">
            <div className={styles.heroHeader}>
              <div className={styles.heroSummary}>
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
                <Tooltip title={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[0]}>
                  <Button
                    shape="circle"
                    icon={<CopyOutlined />}
                    aria-label={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[0]}
                    loading={copyingSession}
                    onClick={() => void copySessionContent()}
                  />
                </Tooltip>
                <Tooltip title={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[1]}>
                  <Button
                    shape="circle"
                    danger
                    icon={<CloseCircleOutlined />}
                    aria-label={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[1]}
                    loading={endingSession}
                    disabled={isSessionEnded || endingSession}
                    onClick={() => {
                      setEndConfirmOpen(true);
                    }}
                  />
                </Tooltip>
                <Tooltip title={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[2]}>
                  <Button
                    type="primary"
                    shape="circle"
                    icon={<ArrowLeftOutlined />}
                    aria-label={INTERVIEW_WORKBENCH_HERO_ACTION_COPY[2]}
                    onClick={() => navigate("/interview")}
                  />
                </Tooltip>
              </div>
            </div>
          </section>

          <Modal
            title={INTERVIEW_WORKBENCH_END_CONFIRM_COPY.title}
            open={endConfirmOpen}
            okText={INTERVIEW_WORKBENCH_END_CONFIRM_COPY.okText}
            cancelText={INTERVIEW_WORKBENCH_END_CONFIRM_COPY.cancelText}
            okButtonProps={{ danger: true, loading: endingSession, disabled: endingSession }}
            cancelButtonProps={{ disabled: endingSession }}
            closable={!endingSession}
            keyboard={!endingSession}
            maskClosable={!endingSession}
            onCancel={() => {
              if (!endingSession) {
                setEndConfirmOpen(false);
              }
            }}
            onOk={() => {
              void endCurrentSession();
            }}
          >
            <Typography.Paragraph>{INTERVIEW_WORKBENCH_END_CONFIRM_COPY.content}</Typography.Paragraph>
          </Modal>

          <section className={workspaceGridClassName} style={workspaceGridStyle}>
            <aside
              className={progressPanelClassName}
              data-layout-area="left_progress_tree"
              data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.progressPanel}
            >
              {isProgressPanelCollapsed ? (
                <Tooltip title="展开模拟面试进度">
                  <Button
                    className={styles.progressPanelCollapsedButton}
                    shape="circle"
                    icon={<MenuUnfoldOutlined />}
                    aria-label="展开模拟面试进度"
                    onClick={() => setProgressPanelCollapsed(false)}
                  />
                </Tooltip>
              ) : (
                <>
                  <div className={styles.progressPanelHeader}>
                    <div className={styles.panelHeader}>
                      <Typography.Title level={5} className={styles.panelTitle}>
                        模拟面试进度
                      </Typography.Title>
                      <Tooltip title="收起模拟面试进度">
                        <Button
                          className={styles.progressPanelHeaderButton}
                          type="text"
                          shape="circle"
                          size="small"
                          icon={<MenuFoldOutlined />}
                          aria-label="收起模拟面试进度"
                          onClick={() => setProgressPanelCollapsed(true)}
                        />
                      </Tooltip>
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
                      ) : isProgressTreePending || isProgressTreeFailed ? (
                        <Alert
                          type={isProgressTreeFailed ? "warning" : "info"}
                          showIcon
                          message={
                            isProgressTreeFailed
                              ? "进展树生成失败，可重试。"
                              : session?.progress_tree_status === "generating"
                                ? "进展树生成中。"
                                : "进展树尚未生成。"
                          }
                          description={
                            isProgressTreeFailed
                              ? "会话已创建成功，进展树失败不会影响模拟面试记录，可点击重试生成。"
                              : "会话已创建成功，生成进展树后即可开始出题。"
                          }
                          action={
                            session?.progress_tree_status === "generating" ? undefined : (
                              <Button
                                size="small"
                                loading={generatingProgressTree}
                                onClick={generateProgressTree}
                              >
                                {isProgressTreeFailed ? "重试生成" : "生成进展树"}
                              </Button>
                            )
                          }
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
                              loading={progressTreeActionLoading}
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
                                <Button size="small" loading={progressTreeActionLoading} onClick={refreshProgressTree}>
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
                </>
              )}
            </aside>
            {isProgressPanelCollapsed ? null : (
              <button
                className={styles.progressPanelResizeHandle}
                type="button"
                aria-label="拖拽调整模拟面试进度宽度"
                onPointerDown={startProgressPanelResize}
              />
            )}

            <main
              ref={chatBodyRef}
              className={styles.conversationPanel}
              data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.conversationPanel}
            >
              <div className={styles.conversationHeader} data-layout-area="right_conversation_header">
                <div className={styles.conversationHeaderTitle}>
                  <Typography.Title level={5} className={styles.panelTitle}>
                    对话与反馈
                  </Typography.Title>
                  <Tag color={workbenchMachineCopy.color} className={styles.workbenchStateTag}>
                    {workbenchMachineCopy.label}
                  </Tag>
                </div>
              </div>

              {renderCurrentQuestionContextStickyHeader()}

              <div
                ref={chatScrollRef}
                className={styles.chatScroll}
                data-layout-area="right_chat_scroll"
                data-testid={INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS.chatScroll}
              >
                {isSessionEnded ? <Alert type="info" showIcon message="模拟面试已结束" /> : null}
                {candidateLoadError !== null ? (
                  <Alert
                    type="warning"
                    showIcon
                    message="候选对象加载失败"
                    description={candidateLoadError}
                  />
                ) : null}
                {hasQuestion ? null : (
                  <EmptyState
                    compact
                    title="暂无题目"
                    description="请先生成题目后再开始作答。"
                    reason="点击底部“生成题目”按钮，系统将基于当前主题生成题干。"
                  />
                )}
                <div className={styles.timeline}>
                  {timelineViewModel.events.map((event) => renderTimelineEvent(event))}
                </div>
                {session.turns.map((turn) => (
                  <div
                    key={`anchor:${turn.question_id}`}
                    className={styles.chatTurnBottomAnchor}
                    data-workbench-question-id={turn.question_id}
                    data-workbench-question-bottom-anchor={turn.question_id}
                  />
                ))}
              </div>
              {renderCurrentQuestionComposer()}
            </main>
            {renderCurrentQuestionFeedbackPanel()}
          </section>
          {renderProgressTreeContextMenu()}
        </div>
      )}
    </AppShell>
  );
}
