import {
  INTERVIEW_CREATE_BUTTON_STATE,
  INTERVIEW_CREATE_ENTRY_KIND,
  INTERVIEW_CREATE_FIELD_KEYS,
  INTERVIEW_CREATE_MODE_FIELD_KEY,
  INTERVIEW_CREATE_PENDING_LOG_EVENTS,
  INTERVIEW_CREATE_PENDING_STATUS,
  INTERVIEW_CREATE_SUCCESS_ACTIONS,
  INTERVIEW_LIST_HEADER_CONTROL_ORDER,
  INTERVIEW_LIST_HEADER_TEXT_STATE,
  INTERVIEW_LIST_ACTIONS,
  INTERVIEW_LIST_ACTION_TOOLTIPS,
  INTERVIEW_LIST_CONFIRM_COPY,
  INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY,
  INTERVIEW_LIST_TABLE_COLUMN_WIDTHS,
  INTERVIEW_LIST_TABLE_SCROLL_X,
  INTERVIEW_SEARCH_PLACEHOLDER,
  INTERVIEW_SESSION_WORKBENCH_FIELDS,
  INTERVIEW_SUPPORTED_MODES,
  INTERVIEW_FORBIDDEN_NATIVE_DIALOG_APIS,
  INTERVIEW_WORKBENCH_DISABLED_ACTIONS,
  INTERVIEW_WORKBENCH_END_CONFIRM_COPY,
  INTERVIEW_WORKBENCH_FEEDBACK_ITEMS,
  INTERVIEW_WORKBENCH_HERO_ACTION_COPY,
  INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY,
  INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT,
  INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS,
  INTERVIEW_WORKBENCH_DETAIL_WIDTH_POLICY,
  INTERVIEW_WORKBENCH_LAYOUT_AREAS,
  INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS,
  INTERVIEW_WORKBENCH_LEFT_FULL_WIDTH_MESSAGE_KINDS,
  INTERVIEW_WORKBENCH_NORMAL_STATE_FORBIDDEN_COPY,
  INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_HEADER_LAYOUT,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_CLOSE_TRIGGERS,
  INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS,
  INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_PLACEMENT,
  INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT,
  INTERVIEW_PROGRESS_TREE_LEFT_LIST_FIELDS,
  INTERVIEW_PROGRESS_TREE_NODE_STATUS_LIGHT_TONES,
  INTERVIEW_PROGRESS_TREE_NODE_STATUS_PLACEMENT,
  INTERVIEW_PROGRESS_TREE_SCROLL_CLASS,
  INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT,
  INTERVIEW_WORKBENCH_CURRENT_QUESTION_COMPOSER_PLACEMENT,
  INTERVIEW_WORKBENCH_CANDIDATE_REVIEW_ITEMS,
  INTERVIEW_WORKBENCH_KEYBOARD_SHORTCUTS,
  INTERVIEW_WORKBENCH_PRIMARY_ACTIONS,
  INTERVIEW_WORKBENCH_SCROLL_REGIONS,
  INTERVIEW_WORKBENCH_SEND_BUTTON_TOOLTIP,
  INTERVIEW_WORKBENCH_STATE_REGIONS,
  INTERVIEW_WORKBENCH_STATE_MACHINE,
  buildPolishBindingOptions,
  buildPolishSessionPath,
  buildPolishSessionClipboardMarkdown,
  buildPolishSessionCreateRequest,
  buildInterviewCreatePendingDescription,
  buildCandidateReviewViewModel,
  buildFeedbackCardViewModel,
  mapFeedbackCodeToDisplay,
  buildPolishSessionReportDialogViewModel,
  buildProgressTreeNodeClipboardMarkdown,
  buildProgressTreeContextMenuItems,
  canEndPolishSessionSummary,
  filterVisiblePolishSessions,
  filterPolishSessionsBySearch,
  hasPolishSessionReport,
  buildProgressTreeContextBannerContent,
  buildProgressTreeContextBannerExpandedSections,
  buildProgressTreeNodeDetailViewModel,
  buildWorkbenchProgressNodeTitleMeta,
  buildWorkbenchProgressNodes,
  canAutoCreateQuestionFromProgressNode,
  collectDefaultExpandedProgressNodeKeys,
  canFollowUpCurrentQuestion,
  canMarkCurrentQuestionCompleted,
  deriveComposerActionViewModel,
  deriveWorkbenchQuestionActionState,
  deriveWorkbenchMachineState,
  canRegenerateQuestionForCurrentNode,
  deriveRegenerateQuestionDisabledReason,
  INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_DISABLED_WITHOUT_HISTORY,
  INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_UNSUPPORTED,
  INTERVIEW_WORKBENCH_REGENERATE_CURRENT_NODE_NO_NODE_TOOLTIP,
  INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_DISABLED_WITHOUT_FEEDBACK,
  INTERVIEW_WORKBENCH_REGENERATE_CURRENT_QUESTION_BUTTON,
  INTERVIEW_WORKBENCH_REGENERATE_NODE_BUTTON,
  INTERVIEW_WORKBENCH_SEND_ANSWER_PLACEHOLDER,
  INTERVIEW_WORKBENCH_SEND_RETRY_PLACEHOLDER,
  getInterviewCreateAvailability,
  getWorkbenchProgressNodeQuestionTargetRef,
  getWorkbenchProgressNodeStatusLightTone,
  isQuestionNode,
  normalizeInterviewTopicTitle,
  normalizeProgressTreeDetailCopy,
  resolveProgressTreeRecoveryAction,
  isProgressTreePendingGeneration,
  resolveCurrentQuestionId,
  buildQuestionConversationAutoScrollTrigger,
  shouldAutoScrollQuestionConversation,
  shouldCollapseCurrentQuestionText,
  buildStickyQuestionContextViewModel,
  resolveCurrentWorkbenchProgressNodeKey,
  resolveProgressTreeDetailNodeRef,
  resolveWorkbenchQuestionFocusId,
  resolveProgressTreeSelectedNodeRefAfterClick,
  canSubmitAnswerFromKeyboard,
  getWorkbenchChatMessageAlignmentClassName,
  shouldCloseProgressTreeContextMenuFromKeyboard,
  shouldSubmitAnswerFromKeyboard,
  shouldConfirmBeforeRegenerateQuestion,
  shouldAutoCreateQuestionForProgressNode,
  shouldShowProgressTreeContextBannerToggle,
  toNextRecommendedActionLabel,
  type PolishBindingOption,
} from "./InterviewPage";
import {
  POLISH_API_PATHS,
  completePolishQuestion,
  confirmPolishCandidate,
  createPolishSession,
  dismissPolishCandidate,
  endPolishSession,
  fetchPolishCandidates,
  fetchPolishSession,
  fetchPolishSessions,
  fetchPolishTopics,
  generatePolishSessionReport,
  generateInitialPolishProgressTree,
  softDeletePolishSession,
} from "../../entities/polish/api/polishApi";
import type { JobSummary } from "../../entities/job/model/types";
import type {
  CreatePolishSessionRequest,
  PolishCandidate,
  PolishCandidateActionResult,
  PolishProgressTreeNode,
  PolishSessionAnswer,
  PolishSessionDetail,
  PolishSessionSummary,
  PolishTopic,
} from "../../entities/polish/model/types";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type CreateButtonIsEnabled = Expect<Equal<typeof INTERVIEW_CREATE_BUTTON_STATE, "enabled">>;
type CreateEntryUsesDrawer = Expect<Equal<typeof INTERVIEW_CREATE_ENTRY_KIND, "drawer">>;
type CreateFieldKeys = Expect<
  Equal<
    typeof INTERVIEW_CREATE_FIELD_KEYS,
    readonly ["mode", "resume_job_binding_id", "polish_theme", "topic_id", "custom_topic_text"]
  >
>;
type CreateSuccessRefreshesList = Expect<
  Equal<typeof INTERVIEW_CREATE_SUCCESS_ACTIONS, readonly ["navigate_to_workbench"]>
>;
type CreatePendingStatusIsVisible = Expect<
  Equal<
    typeof INTERVIEW_CREATE_PENDING_STATUS,
    {
      readonly message: "正在创建模拟面试";
      readonly logHint: "后端日志可搜索 polish_session_create_started / polish_session_create_completed / polish_session_create_failed。";
    }
  >
>;
type CreatePendingBackendLogEventsAreStable = Expect<
  Equal<
    typeof INTERVIEW_CREATE_PENDING_LOG_EVENTS,
    readonly [
      "polish_session_create_started",
      "polish_session_create_completed",
      "polish_session_create_failed",
    ]
  >
>;
type CreateModeFieldIsVisible = Expect<Equal<typeof INTERVIEW_CREATE_MODE_FIELD_KEY, "mode">>;
type SupportedModesArePolishOnly = Expect<
  Equal<typeof INTERVIEW_SUPPORTED_MODES, readonly [{ readonly value: "polish"; readonly label: "打磨模式 / Polish" }]>
>;
type InterviewListHeaderMatchesAssetPages = Expect<
  Equal<typeof INTERVIEW_LIST_HEADER_CONTROL_ORDER, readonly ["actions", "search"]>
>;
type InterviewListHeaderTextIsRemoved = Expect<Equal<typeof INTERVIEW_LIST_HEADER_TEXT_STATE, "removed">>;
type InterviewListActionsAreComplete = Expect<
  Equal<typeof INTERVIEW_LIST_ACTIONS, readonly ["enter", "generate_report", "view_report", "end", "delete"]>
>;
type InterviewListActionTooltipsAreStable = Expect<
  Equal<
    typeof INTERVIEW_LIST_ACTION_TOOLTIPS,
    {
      readonly enter: "进入模拟面试";
      readonly generateReport: "生成面试报告";
      readonly viewReport: "查看面试报告";
      readonly viewReportUnavailable: "面试报告尚未生成";
      readonly end: "结束模拟面试";
      readonly delete: "删除模拟面试";
      readonly ended: "模拟面试已结束";
    }
  >
>;
type InterviewListConfirmCopyIsStable = Expect<
  Equal<
    typeof INTERVIEW_LIST_CONFIRM_COPY,
    {
      readonly endTitle: "确认结束模拟面试";
      readonly endContent: "结束后将停止当前模拟面试，已产生的题目、回答和反馈会保留。";
      readonly deleteTitle: "确认删除模拟面试";
      readonly deleteContent: "删除后该模拟面试将从列表中移除，已产生的数据仅标记为删除，不会被物理删除。";
      readonly okEnd: "确认结束";
      readonly okDelete: "确认删除";
      readonly cancel: "取消";
    }
  >
>;
type InterviewListSearchPlaceholderIsStable = Expect<
  Equal<typeof INTERVIEW_SEARCH_PLACEHOLDER, "搜索模拟面试名称、岗位、简历、主题">
>;
type InterviewListTableColumnWidthsAreStable = Expect<
  Equal<
    typeof INTERVIEW_LIST_TABLE_COLUMN_WIDTHS,
    {
      readonly title: 220;
      readonly mode: 118;
      readonly status: 96;
      readonly binding_label: 280;
      readonly topic: 240;
      readonly updated_at: 168;
      readonly actions: 188;
    }
  >
>;
type InterviewListTableScrollWidthIsStable = Expect<Equal<typeof INTERVIEW_LIST_TABLE_SCROLL_X, 1310>>;
type InterviewListTableCellTextPolicyIsStable = Expect<
  Equal<
    typeof INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY,
    { readonly overflow: "single_line_ellipsis"; readonly hover: "tooltip" }
  >
>;

type WorkbenchFieldsAreStable = Expect<
  Equal<
    typeof INTERVIEW_SESSION_WORKBENCH_FIELDS,
    readonly ["title", "mode", "status", "topic", "binding", "created_at", "updated_at"]
  >
>;
type WorkbenchLayoutAreasAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_LAYOUT_AREAS,
    readonly ["top_summary", "progress_panel", "conversation_panel", "feedback_accordion", "current_question_answer"]
  >
>;
type WorkbenchLayoutTestIdsAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS,
    {
      readonly root: "interview-workbench-viewport";
      readonly progressPanel: "interview-workbench-progress-panel";
      readonly progressNodeList: "interview-workbench-progress-node-list";
      readonly conversationPanel: "interview-workbench-conversation-panel";
      readonly chatScroll: "interview-workbench-chat-scroll";
      readonly currentQuestionComposer: "interview-workbench-current-question-composer";
    }
  >
>;
type WorkbenchScrollRegionsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_SCROLL_REGIONS, readonly ["progress_node_list", "chat_scroll"]>
>;
type WorkbenchLeftDetailUsesFullWidth = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_LEFT_FULL_WIDTH_MESSAGE_KINDS, readonly ["progress_context", "system_question", "feedback"]>
>;
type WorkbenchHeroActionsStayOnSummaryRowEnd = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT, "summary_row_end">
>;
type WorkbenchHeroActionsUseIconTooltipButtons = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY, "icon_only_with_tooltip">
>;
type WorkbenchHeroActionCopyMatchesActualBehavior = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_HERO_ACTION_COPY,
    readonly ["复制完整模拟面试上下文", "结束模拟面试", "返回模拟面试列表"]
  >
>;
type WorkbenchEndConfirmCopyIsStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_END_CONFIRM_COPY,
    {
      readonly title: "确认结束模拟面试";
      readonly content: "结束后将停止当前模拟面试，已产生的题目、回答和反馈会保留。";
      readonly okText: "确认结束";
      readonly cancelText: "取消";
    }
  >
>;
type NativeDialogApisAreForbidden = Expect<
  Equal<
    typeof INTERVIEW_FORBIDDEN_NATIVE_DIALOG_APIS,
    readonly ["alert", "confirm", "prompt", "window.alert", "window.confirm", "window.prompt"]
  >
>;
type WorkbenchProgressHeaderCopyOmitsPercentText = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY, readonly ["模拟面试进度"]>
>;
type ProgressTreeDetailPlacementIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT, "conversation_context_banner">
>;
type ProgressTreeContextBannerCopyIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE, "当前节点上下文">
>;
type ProgressTreeContextBannerHeaderLayoutIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_HEADER_LAYOUT, "label_and_node_title_same_row">
>;
type ProgressTreeContextBannerEmptyCopyIsStable = Expect<
  Equal<
    typeof INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY,
    "请选择一个进展节点查看本轮训练目标。"
  >
>;
type ProgressTreeContextBannerToggleCopyIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY, { readonly expand: "展开"; readonly collapse: "收起" }>
>;
type ProgressTreeLeftListFieldsAreStable = Expect<
  Equal<
    typeof INTERVIEW_PROGRESS_TREE_LEFT_LIST_FIELDS,
    readonly ["category_header", "node_title", "node_status", "current_priority", "question_entry"]
  >
>;
type ProgressTreeNodeStatusPlacementIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_NODE_STATUS_PLACEMENT, "node_row_trailing_status_light">
>;
type ProgressTreeNodeStatusLightTonesAreStable = Expect<
  Equal<
    typeof INTERVIEW_PROGRESS_TREE_NODE_STATUS_LIGHT_TONES,
    { readonly completed: "green"; readonly in_progress: "blue"; readonly pending: "orange" }
  >
>;
type WorkbenchChatBubbleAlignmentIsStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT,
    {
      readonly progress_context: "left";
      readonly system_question: "left";
      readonly feedback: "left";
      readonly user_answer: "right";
      readonly user_answer_placeholder: "right";
    }
  >
>;
type WorkbenchKeyboardShortcutsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_KEYBOARD_SHORTCUTS, { readonly send_answer: "Ctrl+Enter" }>
>;
type ProgressTreeScrollClassIsScoped = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_SCROLL_CLASS, "progressTreeScroll">
>;
type WorkbenchHeaderChipsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS, readonly ["岗位", "简历", "当前节点", "能力主题", "进度", "当前节点表现"]>
>;
type WorkbenchFeedbackItemsAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_FEEDBACK_ITEMS,
    readonly [
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
      "下一轮训练建议",
    ]
  >
>;
type WorkbenchCandidateReviewItemsAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_CANDIDATE_REVIEW_ITEMS,
    readonly ["candidate_type", "status", "title", "summary", "confidence_level", "evidence_excerpt", "confirm", "dismiss"]
  >
>;
type WorkbenchPrimaryActionsAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_PRIMARY_ACTIONS,
    readonly ["send_answer"]
  >
>;
type WorkbenchDisabledActionsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_DISABLED_ACTIONS, readonly []>
>;
type WorkbenchForbiddenCopyIsTracked = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_NORMAL_STATE_FORBIDDEN_COPY,
    readonly [
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
    ]
  >
>;
type WorkbenchStateRegionsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_STATE_REGIONS, readonly ["loading", "error", "not_found"]>
>;

type CreateApiReturnsSessionDetail = Expect<
  Equal<Awaited<ReturnType<typeof createPolishSession>>, PolishSessionDetail>
>;
type GenerateInitialProgressTreeApiReturnsSessionDetail = Expect<
  Equal<Awaited<ReturnType<typeof generateInitialPolishProgressTree>>, PolishSessionDetail>
>;
type DetailApiReturnsSessionDetail = Expect<
  Equal<Awaited<ReturnType<typeof fetchPolishSession>>, PolishSessionDetail>
>;
type CandidateListApiReturnsCandidates = Expect<
  Equal<Awaited<ReturnType<typeof fetchPolishCandidates>>, PolishCandidate[]>
>;
type CandidateConfirmApiReturnsActionResult = Expect<
  Equal<Awaited<ReturnType<typeof confirmPolishCandidate>>, PolishCandidateActionResult>
>;
type CandidateDismissApiReturnsActionResult = Expect<
  Equal<Awaited<ReturnType<typeof dismissPolishCandidate>>, PolishCandidateActionResult>
>;
type ListApiReturnsSessionSummaries = Expect<
  Equal<Awaited<ReturnType<typeof fetchPolishSessions>>, PolishSessionSummary[]>
>;
type TopicApiReturnsControlledCatalog = Expect<
  Equal<Awaited<ReturnType<typeof fetchPolishTopics>>, PolishTopic[]>
>;
type PolishSessionCreatePathIsStable = Expect<Equal<typeof POLISH_API_PATHS.sessions, "/polish-sessions">>;
type PolishSessionDetailPathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.sessionDetail>, `/polish-sessions/${string}`>
>;
type PolishQuestionCompletePathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.completeQuestion>, `/polish-sessions/${string}/questions/${string}/complete`>
>;
type PolishSessionEndPathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.endSession>, `/polish-sessions/${string}/end`>
>;
type PolishSessionReportTaskPathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.sessionReport>, `/polish-sessions/${string}/report`>
>;
type PolishSessionSoftDeletePathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.softDeleteSession>, `/polish-sessions/${string}/delete`>
>;
type PolishQuestionCompleteReturnsSession = Expect<
  Equal<Awaited<ReturnType<typeof completePolishQuestion>>, PolishSessionDetail>
>;
type PolishSessionEndReturnsSession = Expect<
  Equal<Awaited<ReturnType<typeof endPolishSession>>, PolishSessionDetail>
>;
type PolishSessionReportTaskReturnsSession = Expect<
  Equal<Awaited<ReturnType<typeof generatePolishSessionReport>>, PolishSessionDetail>
>;
type PolishSessionSoftDeleteReturnsSession = Expect<
  Equal<Awaited<ReturnType<typeof softDeletePolishSession>>, PolishSessionDetail>
>;
type PolishCandidateListPathIsStable = Expect<Equal<typeof POLISH_API_PATHS.candidates, "/polish-candidates">>;
type PolishCandidateDetailPathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.candidateDetail>, `/polish-candidates/${string}`>
>;
type PolishCandidateConfirmPathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.confirmCandidate>, `/polish-candidates/${string}/confirm`>
>;
type PolishCandidateDismissPathIsStable = Expect<
  Equal<ReturnType<typeof POLISH_API_PATHS.dismissCandidate>, `/polish-candidates/${string}/dismiss`>
>;
type PolishTopicListPathIsStable = Expect<Equal<typeof POLISH_API_PATHS.topics, "/polish-topics">>;

const sampleJobs = [
  {
    job_id: "job_001",
    title: "后端工程师",
    company: "ACME",
    department: null,
    application_status: "interviewing",
    current_version_ref: {
      resource_type: "job",
      resource_id: "job_001",
      version_id: "job_ver_001",
    },
    archived_at: null,
    binding_summary: {
      status: "bound",
      resume_job_binding_id: "bind_001",
      resume_id: "res_001",
      resume_title: "后端简历",
      resume_version_ref: {
        resource_type: "resume",
        resource_id: "res_001",
        version_id: "res_ver_001",
      },
      bound_at: "2026-05-19T10:00:00Z",
    },
    latest_match_summary: { status: "not_started" },
    status: "active",
    record_version: 1,
    created_at: "2026-05-19T09:00:00Z",
    updated_at: "2026-05-19T10:00:00Z",
  },
] satisfies JobSummary[];

const bindingOptions = buildPolishBindingOptions(sampleJobs);
const readyAvailability = getInterviewCreateAvailability({
  loading: false,
  error: null,
  bindingOptions: bindingOptions.slice(0, 1) as [PolishBindingOption],
});
const noPrerequisiteAvailability = getInterviewCreateAvailability({
  loading: false,
  error: null,
  bindingOptions: [],
});
const createPayload = buildPolishSessionCreateRequest({
  resume_job_binding_id: "bind_001",
  polish_theme: "mixed",
  topic_id: "topic_authenticity_contribution",
  custom_topic_text: "  支付系统项目表达  ",
});
const createPendingDescription = buildInterviewCreatePendingDescription(12);

const payloadShape: CreatePolishSessionRequest = createPayload;
const sessionWorkbenchPath = buildPolishSessionPath("ses_001");

function buildTestSessionSummary(overrides: Partial<PolishSessionSummary> = {}): PolishSessionSummary {
  return {
    id: "ses_summary_001",
    session_id: "ses_summary_001",
    title: "经历真实性与贡献边界",
    mode: "polish",
    status: "running",
    resume_job_binding_id: "bind_001",
    resume_id: "res_001",
    resume_version_id: "res_ver_001",
    job_id: "job_001",
    job_version_id: "job_ver_001",
    job_title: "AI 工程化岗位",
    job_company: "ACME",
    resume_title: "分布式系统简历",
    binding_label: "AI 工程化岗位 / 分布式系统简历",
    topic_id: "topic_001",
    subtopic_id: null,
    custom_topic_text_summary: "混合检索主题",
    created_at: "2026-05-20T10:00:00Z",
    updated_at: "2026-05-20T10:00:00Z",
    ...overrides,
  };
}

type TestProgressTreeNode = PolishProgressTreeNode & {
  basis_type?: string | null;
  category?: string | null;
  common_loss_risks?: string[] | null;
  confidence_level?: string | null;
  coverage_points?: string[] | string | null;
  depth_goal?: string | null;
  display_category_title?: string | null;
  display_title?: string | null;
  exam_point?: string | null;
  expected_answer_signals?: string[] | null;
  first_question?: string | null;
  follow_up_directions?: string[] | null;
  follow_up_focus?: string[] | string | null;
  grounding_status?: string | null;
  jd_basis?: string | null;
  node_code?: string | null;
  preparation_goal?: string | null;
  recommended_first_question?: string | null;
  red_flags?: string[] | null;
  related_match_gaps?: string[] | null;
  resume_signal?: string | null;
  sub_points?: string[] | string | null;
};

function buildTestProgressNode(
  progressNodeRef: string,
  title: string,
  category: string,
  displayCategoryTitle: string,
): TestProgressTreeNode {
  return {
    progress_node_ref: progressNodeRef,
    title,
    display_title: title,
    category,
    display_category_title: displayCategoryTitle,
    expected_capability: `${title} 能力`,
    related_job_requirements: [],
    related_resume_evidence: [],
    missing_points: [],
    children: [],
  };
}

function buildTestSession(
  nodes: TestProgressTreeNode[],
  currentProgressNodeRef: string | null = null,
): PolishSessionDetail {
  return {
    session_id: "ses_progress_tree_test",
    mode: "polish",
    session_status: "active",
    resume_job_binding_id: "bind_001",
    resume_id: "res_001",
    resume_version_id: "res_ver_001",
    job_id: "job_001",
    job_version_id: "job_ver_001",
    job_title: "后端工程师",
    job_company: "ACME",
    resume_title: "后端简历",
    binding_label: "后端工程师 / 后端简历",
    turns: [],
    progress_tree_status: "ready",
    progress_percent: 0,
    progress_tree_plan: {
      status: "ready",
      context_digest: "digest",
      nodes,
    },
    progress_tree_state: {
      status: "ready",
      node_states: nodes.map((node) => ({
        progress_node_ref: node.progress_node_ref,
        status: node.progress_node_ref === currentProgressNodeRef ? "in_progress" : "pending",
        completed_questions_count: 0,
        latest_feedback_summary: null,
      })),
      current_priority: currentProgressNodeRef
        ? {
            progress_node_ref: currentProgressNodeRef,
            title: "当前节点",
            expected_capability: "当前能力",
          }
        : null,
      updated_from_turns_count: 0,
      progress: { progress_percent: 0 },
    },
    topic_ref: {
      topic_id: "topic_authenticity_contribution",
      title: "经历真实性与贡献拷问",
    },
    subtopic_ref: null,
    custom_topic_text_summary: null,
    created_at: "2026-05-20T10:00:00Z",
    updated_at: "2026-05-20T10:00:00Z",
  };
}

function buildQuestionAnswer(overrides: Partial<PolishSessionAnswer> = {}): PolishSessionAnswer {
  return {
    answer_id: "ans_default",
    answer_round: 1,
    answer_text: "默认作答内容",
    answer_created_at: "2026-05-21T10:01:00Z",
    feedback_text: "",
    feedback_id: null,
    score_result_id: null,
    feedback_created_at: null,
    ...overrides,
  };
}

function assertContract(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function test_interview_list_toolbar_uses_shared_actions_and_search(): void {
  const sessions = [
    buildTestSessionSummary(),
    buildTestSessionSummary({
      id: "ses_summary_002",
      session_id: "ses_summary_002",
      title: "高并发缓存一致性",
      job_title: "后端架构师",
      resume_title: "缓存治理简历",
      binding_label: "后端架构师 / 缓存治理简历",
      custom_topic_text_summary: "缓存一致性主题",
    }),
  ];

  assertContract(INTERVIEW_LIST_HEADER_TEXT_STATE === "removed", "模拟面试列表工具栏不应展示额外标题和说明文案");
  assertContract(INTERVIEW_LIST_HEADER_CONTROL_ORDER.join(",") === "actions,search", "模拟面试列表工具栏应与简历、岗位页一样左操作右搜索");
  assertContract(INTERVIEW_SEARCH_PLACEHOLDER === "搜索模拟面试名称、岗位、简历、主题", "模拟面试搜索框应使用稳定暗纹提示");
  assertContract(INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.binding_label === 280, "绑定关系列应加宽以减少换行");
  assertContract(INTERVIEW_LIST_TABLE_COLUMN_WIDTHS.topic === 240, "主题列应保留足够宽度");
  assertContract(INTERVIEW_LIST_TABLE_SCROLL_X === 1310, "模拟面试列表应使用稳定横向表格宽度");
  assertContract(INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY.overflow === "single_line_ellipsis", "表格文本超出一行应省略");
  assertContract(INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY.hover === "tooltip", "表格文本 hover 应展示全文");
  assertContract(filterPolishSessionsBySearch(sessions, "缓存").map((session) => session.session_id).join(",") === "ses_summary_002", "模拟面试搜索应匹配名称、岗位、简历或主题");
  assertContract(filterPolishSessionsBySearch(sessions, "分布式系统").length === 1, "模拟面试搜索应匹配简历标题");
  assertContract(filterPolishSessionsBySearch(sessions, "").length === 2, "空搜索应保留全部模拟面试记录");
}

function test_interview_list_actions_cover_report_end_and_soft_delete(): void {
  const runningWithoutReport = buildTestSessionSummary();
  const endedSession = buildTestSessionSummary({
    id: "ses_summary_ended",
    session_id: "ses_summary_ended",
    status: "ended",
  });
  const runningWithReport = buildTestSessionSummary({
    id: "ses_summary_report",
    session_id: "ses_summary_report",
    report_id: "report_summary_001",
    report_status: "available",
    report_generated_at: "2026-05-20T11:00:00Z",
  });
  const deletedSession = buildTestSessionSummary({
    id: "ses_summary_deleted",
    session_id: "ses_summary_deleted",
    status: "deleted",
  });
  const reportDialog = buildPolishSessionReportDialogViewModel(runningWithReport);

  assertContract(INTERVIEW_LIST_ACTIONS.join(",") === "enter,generate_report,view_report,end,delete", "操作列应包含进入、生成报告、查看报告、结束、删除");
  assertContract(INTERVIEW_LIST_ACTION_TOOLTIPS.generateReport === "生成面试报告", "生成报告按钮应有 hover 说明");
  assertContract(INTERVIEW_LIST_ACTION_TOOLTIPS.viewReportUnavailable === "面试报告尚未生成", "无报告时查看报告应明确不可用原因");
  assertContract(!hasPolishSessionReport(runningWithoutReport), "无 report_id 的会话不应允许误导式查看报告");
  assertContract(hasPolishSessionReport(runningWithReport), "有 report_id 的会话应允许查看报告");
  assertContract(canEndPolishSessionSummary(runningWithoutReport), "running 会话应允许结束");
  assertContract(!canEndPolishSessionSummary(endedSession), "已结束会话不应继续展示可用结束操作");
  assertContract(filterVisiblePolishSessions([runningWithoutReport, deletedSession]).length === 1, "软删除记录不应进入普通列表");
  assertContract(reportDialog?.title === "面试报告", "查看报告应打开系统内报告弹窗视图模型");
  assertContract(reportDialog?.reportId === "report_summary_001", "报告弹窗应使用真实 report_id，不臆造报告内容");
  assertContract(Boolean(reportDialog?.emptyDescription.includes("尚未返回可展示分项")), "无报告分项时应说明未返回内容而不是伪造报告");
  assertContract(POLISH_API_PATHS.sessionReport("ses_report") === "/polish-sessions/ses_report/report", "生成报告应命中会话报告生成接口");
  assertContract(POLISH_API_PATHS.softDeleteSession("ses_report") === "/polish-sessions/ses_report/delete", "删除应命中软删除接口");
}

function test_progress_tree_groups_flat_nodes_by_display_category_title(): void {
  const groupedNodes = buildWorkbenchProgressNodes(
    buildTestSession([
      buildTestProgressNode("node_resume_1", "智能辅助平台架构", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_resume_2", "混合检索优化", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_gap_1", "AI Agent 规划机制", "jd_gap_learning", "补齐学习类"),
      buildTestProgressNode("node_gap_2", "高可用架构设计", "jd_gap_learning", "补齐学习类"),
    ]),
  );

  const deepDiveGroup = groupedNodes.find((node) => node.title === "深度打磨类");
  const gapLearningGroup = groupedNodes.find((node) => node.title === "补齐学习类");
  assertContract(deepDiveGroup?.children?.map((node) => node.title).join(",") === "智能辅助平台架构,混合检索优化", "深度打磨类分组不正确");
  assertContract(gapLearningGroup?.children?.map((node) => node.title).join(",") === "AI Agent 规划机制,高可用架构设计", "补齐学习类分组不正确");
}

function test_progress_tree_group_header_is_not_question_target(): void {
  const groupedNodes = buildWorkbenchProgressNodes(
    buildTestSession([
      buildTestProgressNode("node_resume_1", "智能辅助平台架构", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_gap_1", "AI Agent 规划机制", "jd_gap_learning", "补齐学习类"),
    ]),
  );
  const groupHeader = groupedNodes[0];
  const realNode = groupHeader.children?.[0];

  assertContract(getWorkbenchProgressNodeQuestionTargetRef(groupHeader) === null, "分类标题不应成为生成题目目标");
  assertContract(getWorkbenchProgressNodeQuestionTargetRef(realNode) === "node_resume_1", "真实节点应传递 progress_node_ref");
}

function test_progress_node_context_renders_as_compact_banner(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_detail_1", "混合检索策略设计与优化", "resume_deep_dive", "深度打磨类"),
      display_title: "混合检索策略设计与优化",
      expected_capability: "能解释召回、排序、重排和评估指标之间的取舍。",
      depth_goal: "能解释召回、排序、重排和评估指标之间的取舍。",
      first_question: "如果让你设计混合检索链路，你会如何分层？",
      follow_up_focus: ["如何处理召回不足", "如何验证排序质量"],
      expected_answer_signals: ["能给出指标闭环", "能说明线上降级策略"],
      common_loss_risks: ["只描述工具名称，缺少系统取舍"],
      resume_signal: "简历中提到检索服务优化经验",
      jd_basis: "JD 要求具备搜索架构和效果评估能力",
    },
  ], "node_detail_1");

  const listNode = buildWorkbenchProgressNodes(session)[0]?.children?.[0];
  const selectedRef = resolveProgressTreeDetailNodeRef(session, null);
  const bannerContent = buildProgressTreeContextBannerContent(session, selectedRef);
  const visibleCopy = [
    INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE,
    bannerContent.title,
    bannerContent.depthRequirement,
    bannerContent.emptyDescription,
  ].join(" ");

  assertContract(INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT === "conversation_context_banner", "节点上下文应位于右侧对话区顶部公告条");
  assertContract(visibleCopy.includes("当前节点上下文"), "公告条应显示当前节点上下文标题");
  assertContract(listNode?.detail !== "能解释召回、排序、重排和评估指标之间的取舍。", "左侧进展树区域不应继续渲染长详情");
  assertContract(bannerContent.title === "混合检索策略设计与优化", "公告条应显示当前节点名称");
  assertContract(bannerContent.depthRequirement === "能解释召回、排序、重排和评估指标之间的取舍。", "公告条应显示深度要求");
  assertContract(!visibleCopy.includes("展开更多准备要点"), "公告条不应出现展开更多准备要点");
}

function test_progress_tree_context_banner_shows_technical_coverage_from_children(): void {
  const parentNode = buildTestProgressNode("node_project_parent", "项目甲设计取舍", "resume_deep_dive", "深度打磨类");
  parentNode.children = [
    {
      ...buildTestProgressNode("node_project_child_one", "贡献项一边界说明", "resume_deep_dive", "深度打磨类"),
      display_title: "贡献项一边界说明",
      exam_point: "贡献项一拆解",
    } as TestProgressTreeNode,
    {
      ...buildTestProgressNode("node_project_child_two", "贡献项二验证闭环", "resume_deep_dive", "深度打磨类"),
      display_title: "贡献项二验证闭环",
      exam_point: "贡献项二拆解",
    } as TestProgressTreeNode,
  ];
  const session = buildTestSession([parentNode], "node_project_parent");

  const detail = buildProgressTreeNodeDetailViewModel(session, "node_project_parent");
  const bannerContent = buildProgressTreeContextBannerContent(session, "node_project_parent");
  const expandedSections = buildProgressTreeContextBannerExpandedSections(bannerContent);

  assertContract(detail?.technicalCoverage.join(",") === "贡献项一边界说明,贡献项二验证闭环", "详情应优先从 children 展示技术点覆盖");
  assertContract(bannerContent.technicalCoverage.join(",") === "贡献项一边界说明,贡献项二验证闭环", "公告条应保留 children 技术点覆盖");
  assertContract(expandedSections.some((section) => section.key === "technical_coverage"), "展开区应包含技术点覆盖");
  assertContract(expandedSections.some((section) => section.title === "技术点覆盖"), "展开区应展示技术点覆盖标题");
}

function test_progress_tree_context_banner_shows_technical_coverage_points_without_children(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_project_points", "项目乙设计取舍", "resume_deep_dive", "深度打磨类"),
      coverage_points: ["贡献项一", "贡献项二"],
      sub_points: ["方案设计"],
    },
  ], "node_project_points");

  const bannerContent = buildProgressTreeContextBannerContent(session, "node_project_points");
  const expandedSections = buildProgressTreeContextBannerExpandedSections(bannerContent);

  assertContract(bannerContent.technicalCoverage.join(",") === "贡献项一,贡献项二", "无 children 时应使用 coverage_points 展示技术点覆盖");
  assertContract(expandedSections.some((section) => section.key === "technical_coverage"), "coverage_points 应进入展开区");
}

function test_progress_tree_left_list_stays_compact(): void {
  const longDepthGoal = "能完整解释索引构建、召回策略、排序质量评估、降级策略和线上监控之间的长期取舍。";
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_compact_1", "混合检索策略设计与优化", "resume_deep_dive", "深度打磨类"),
      node_code: "R-01",
      expected_capability: longDepthGoal,
      depth_goal: longDepthGoal,
      first_question: "你会如何验证混合检索效果？",
      follow_up_directions: ["如何做离线评估", "如何做线上回滚"],
    },
  ]);
  const listNode = buildWorkbenchProgressNodes(session)[0]?.children?.[0];
  const titleMeta = listNode ? buildWorkbenchProgressNodeTitleMeta(listNode) : null;
  const contextDetail = buildProgressTreeNodeDetailViewModel(session, "node_compact_1");
  const bannerContent = buildProgressTreeContextBannerContent(session, "node_compact_1");
  const bannerVisibleCopy = [bannerContent.title, bannerContent.depthRequirement].join(" ");
  const leftTitleVisibleCopy = [
    titleMeta?.title,
    titleMeta?.statusLabel,
  ].join(" ");

  assertContract(listNode?.title === "混合检索策略设计与优化", "左侧真实节点应显示标题");
  assertContract(listNode?.nodeCode === "R-01", "node_code 可保留在数据中");
  assertContract(listNode?.status === "pending", "左侧真实节点应显示状态");
  assertContract(titleMeta?.statusLabel === "未开始", "左侧节点状态应移动到节点名称同行");
  assertContract(titleMeta?.statusLightTone === "orange", "未开始状态应使用橙色点灯");
  assertContract(!leftTitleVisibleCopy.includes("R-01"), "左侧节点可见文案不应显示 node_code");
  assertContract(listNode?.detail !== longDepthGoal, "左侧列表不应显示完整 depth_goal 长文本");
  assertContract(contextDetail?.depthRequirement === longDepthGoal, "节点详情模型应继续保留 depth_goal");
  assertContract(contextDetail?.firstQuestion === "你会如何验证混合检索效果？", "建议第一题可保留在数据模型中");
  assertContract(bannerContent.depthRequirement === longDepthGoal, "公告条应展示 depth_goal");
  assertContract(!bannerVisibleCopy.includes("你会如何验证混合检索效果？"), "公告条不应展示建议第一题");
}

function test_progress_tree_detail_defaults_to_latest_turn_node(): void {
  const baseSession = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_latest", "大文件异步处理管道架构", "resume_deep_dive", "深度打磨类"),
        depth_goal: "最新题目节点目标",
      },
      {
        ...buildTestProgressNode("node_priority", "AI Agent 任务规划与工具调用机制", "jd_gap_learning", "补齐学习类"),
        depth_goal: "当前优先节点目标",
      },
    ],
    "node_priority",
  );
  const session: PolishSessionDetail = {
    ...baseSession,
    turns: [
      {
        question_id: "q_latest_detail",
        question_text: "最新题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_latest",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };

  const selectedRef = resolveProgressTreeDetailNodeRef(session, null);
  const detail = buildProgressTreeNodeDetailViewModel(session, selectedRef);

  assertContract(selectedRef === "node_latest", "详情默认节点应优先使用最新题目所在节点");
  assertContract(detail?.title === "大文件异步处理管道架构", "详情应默认显示最新题目对应节点");
  assertContract(detail?.depthRequirement === "最新题目节点目标", "详情应默认显示最新题目节点内容");
}

function test_progress_tree_group_header_does_not_show_node_detail(): void {
  const session = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_resume_1", "真实节点", "resume_deep_dive", "深度打磨类"),
        depth_goal: "真实节点目标",
      },
    ],
    "node_resume_1",
  );
  const groupedNodes = buildWorkbenchProgressNodes(session);
  const groupHeader = groupedNodes[0];
  const nextSelectedRef = resolveProgressTreeSelectedNodeRefAfterClick(groupHeader, "node_resume_1");
  const detail = buildProgressTreeNodeDetailViewModel(session, nextSelectedRef);

  assertContract(getWorkbenchProgressNodeQuestionTargetRef(groupHeader) === null, "分类标题不应触发生成题目");
  assertContract(nextSelectedRef === "node_resume_1", "点击分类标题不应改变当前选中真实节点");
  assertContract(detail?.title !== groupHeader.title, "分类标题不应展示为节点详情");
}

function test_progress_tree_category_header_is_group_only(): void {
  const session = buildTestSession(
    [
      buildTestProgressNode("node_resume_1", "真实节点一", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_resume_2", "真实节点二", "resume_deep_dive", "深度打磨类"),
    ],
    "node_resume_1",
  );
  const groupHeader = buildWorkbenchProgressNodes(session)[0];
  const nextSelectedRef = resolveProgressTreeSelectedNodeRefAfterClick(groupHeader, "node_resume_1");

  assertContract(groupHeader.title === "深度打磨类", "分类 header 应显示分类名");
  assertContract(groupHeader.detail === "2", "分类 header 应显示真实节点数量");
  assertContract(getWorkbenchProgressNodeQuestionTargetRef(groupHeader) === null, "点击分类 header 不应生成题目");
  assertContract(nextSelectedRef === "node_resume_1", "点击分类 header 不应设置为选中详情节点");
}

function test_progress_node_context_banner_defaults_to_latest_turn_node(): void {
  const baseSession = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_latest", "大文件异步处理管道架构", "resume_deep_dive", "深度打磨类"),
        depth_goal: "最新题目节点目标",
      },
      {
        ...buildTestProgressNode("node_priority", "AI Agent 任务规划与工具调用机制", "jd_gap_learning", "补齐学习类"),
        depth_goal: "当前优先节点目标",
      },
    ],
    "node_priority",
  );
  const session: PolishSessionDetail = {
    ...baseSession,
    turns: [
      {
        question_id: "q_latest_banner",
        question_text: "最新题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_latest",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };

  const selectedRef = resolveProgressTreeDetailNodeRef(session, null);
  const bannerContent = buildProgressTreeContextBannerContent(session, selectedRef);

  assertContract(selectedRef === "node_latest", "上下文公告条默认节点应优先使用最新题目所在节点");
  assertContract(bannerContent.title === "大文件异步处理管道架构", "上下文公告条应默认展示最新题目对应节点");
  assertContract(bannerContent.depthRequirement === "最新题目节点目标", "上下文公告条应默认显示最新题目节点内容");
}

function test_progress_node_context_banner_updates_when_node_selected(): void {
  const session = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_first", "大文件异步处理管道架构", "resume_deep_dive", "深度打磨类"),
        depth_goal: "第一节点目标",
      },
      {
        ...buildTestProgressNode("node_selected", "缓存一致性问题定位", "resume_deep_dive", "深度打磨类"),
        depth_goal: "选中节点目标",
      },
    ],
    "node_first",
  );
  const groupedNodes = buildWorkbenchProgressNodes(session);
  const selectedNode = groupedNodes[0]?.children?.[1];
  const selectedRef = resolveProgressTreeSelectedNodeRefAfterClick(selectedNode, "node_first");
  const bannerContent = buildProgressTreeContextBannerContent(session, selectedRef);

  assertContract(selectedRef === "node_selected", "点击另一个真实节点后应切换上下文公告条节点");
  assertContract(bannerContent.title === "缓存一致性问题定位", "上下文公告条应展示新选中节点标题");
  assertContract(bannerContent.depthRequirement === "选中节点目标", "上下文公告条应展示新选中节点深度要求");
}

function test_progress_node_context_banner_hides_question_and_detail_lists(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_compact_context", "混合检索策略设计与优化", "resume_deep_dive", "深度打磨类"),
      node_code: "R-02",
      depth_goal: "能解释召回、排序、重排和评估指标之间的取舍。",
      first_question: "如果让你设计混合检索链路，你会如何分层？",
      follow_up_focus: ["如何处理召回不足", "如何验证排序质量"],
      expected_answer_signals: ["能给出指标闭环"],
      common_loss_risks: ["只描述工具名称，缺少系统取舍"],
      resume_signal: "简历中提到检索服务优化经验",
      jd_basis: "JD 要求具备搜索架构和效果评估能力",
    },
  ]);
  const bannerContent = buildProgressTreeContextBannerContent(session, "node_compact_context");
  const visibleCopy = [
    INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE,
    bannerContent.title,
    bannerContent.depthRequirement,
    bannerContent.emptyDescription,
  ].join(" ");

  assertContract(bannerContent.title === "混合检索策略设计与优化", "公告条应只显示节点名称，不拼接 node_code");
  assertContract(bannerContent.depthRequirement === "能解释召回、排序、重排和评估指标之间的取舍。", "公告条应显示深度要求");
  for (const hiddenCopy of [
    "建议第一题",
    "如果让你设计混合检索链路，你会如何分层？",
    "追问方向",
    "好回答信号",
    "常见失分风险",
    "简历线索",
    "岗位依据",
    "如何处理召回不足",
    "能给出指标闭环",
    "只描述工具名称，缺少系统取舍",
    "简历中提到检索服务优化经验",
    "JD 要求具备搜索架构和效果评估能力",
    "展开更多准备要点",
  ]) {
    assertContract(!visibleCopy.includes(hiddenCopy), `公告条不应展示 ${hiddenCopy}`);
  }
}

function test_workbench_hero_actions_are_icon_only_and_copy_session_content(): void {
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT === "summary_row_end", "顶部按钮组应位于状态摘要行右侧");
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY === "icon_only_with_tooltip", "顶部按钮应只展示图标，文字通过 Tooltip 和 aria-label 提供");
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_COPY[0] === "复制完整模拟面试上下文", "顶部第一个按钮应为复制");
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_COPY[1] === "结束模拟面试", "顶部第二个按钮应为结束模拟面试");
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_COPY[2] === "返回模拟面试列表", "顶部第三个按钮应为返回");
  assertContract(INTERVIEW_WORKBENCH_END_CONFIRM_COPY.title === "确认结束模拟面试", "结束按钮应打开系统内确认弹窗");
  assertContract(INTERVIEW_WORKBENCH_END_CONFIRM_COPY.okText === "确认结束", "系统弹窗主按钮应明确表达确认结束");
  assertContract(INTERVIEW_FORBIDDEN_NATIVE_DIALOG_APIS.includes("window.confirm"), "禁止原生弹窗清单应覆盖 window.confirm");
}

function test_progress_tree_node_status_uses_row_trailing_lights(): void {
  const session = buildTestSession(
    [
      buildTestProgressNode("node_pending", "待开始节点", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_active", "进行中节点", "resume_deep_dive", "深度打磨类"),
    ],
    "node_active",
  );
  const realNodes = buildWorkbenchProgressNodes(session)[0]?.children ?? [];
  const pendingMeta = buildWorkbenchProgressNodeTitleMeta(realNodes[0]);
  const activeMeta = buildWorkbenchProgressNodeTitleMeta(realNodes[1]);

  assertContract(INTERVIEW_PROGRESS_TREE_NODE_STATUS_PLACEMENT === "node_row_trailing_status_light", "节点状态应位于节点栏目最右侧并使用点灯");
  assertContract(pendingMeta.statusLabel === "未开始", "待开始节点应显示未开始状态");
  assertContract(pendingMeta.statusLightTone === "orange", "待开始节点应使用橙色点灯");
  assertContract(activeMeta.statusLabel === "进行中", "当前节点应显示进行中状态");
  assertContract(activeMeta.statusLightTone === "blue", "进行中节点应使用蓝色点灯");
  assertContract(getWorkbenchProgressNodeStatusLightTone("completed") === "green", "已完成节点应使用绿色点灯");
  assertContract(getWorkbenchProgressNodeStatusLightTone("pending") === "orange", "未开始节点应使用橙色点灯");
}

function test_progress_tree_pending_and_failed_states_use_generation_action(): void {
  assertContract(isProgressTreePendingGeneration("pending"), "pending 状态应识别为初始进展树待生成");
  assertContract(isProgressTreePendingGeneration("generating"), "generating 状态应识别为初始进展树生成中");
  assertContract(!isProgressTreePendingGeneration("ready"), "ready 状态不应识别为待生成");
  assertContract(resolveProgressTreeRecoveryAction("pending") === "generate", "pending 状态应调用初始生成入口");
  assertContract(resolveProgressTreeRecoveryAction("failed") === "generate", "failed 状态应允许重试初始生成");
  assertContract(resolveProgressTreeRecoveryAction("refresh_failed") === "refresh", "refresh_failed 状态应继续刷新现有进展树状态");
  assertContract(resolveProgressTreeRecoveryAction("ready") === "none", "ready 状态不应展示恢复操作");
}

function test_progress_node_context_banner_supports_expand_toggle_for_depth(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_expand_context", "混合检索策略设计与优化", "resume_deep_dive", "深度打磨类"),
      depth_goal: "从双路召回设计、融合排序公式、向量模型领域适配、阈值调优等方面展开深挖，验证候选人对检索增强全链路的掌控力。",
      follow_up_focus: ["如何验证融合排序收益", "如何处理召回不足"],
      common_loss_risks: ["只讲工具链，不说明阈值调优依据"],
      expected_answer_signals: ["能给出评估闭环"],
      first_question: "你会如何设计第一题？",
      resume_signal: "简历中提到搜索优化",
      jd_basis: "岗位要求检索增强能力",
    },
  ]);
  const bannerContent = buildProgressTreeContextBannerContent(session, "node_expand_context");
  const emptyBanner = buildProgressTreeContextBannerContent(session, "missing_node");
  const expandedSections = buildProgressTreeContextBannerExpandedSections(bannerContent);
  const expandedCopy = expandedSections.flatMap((section) => [section.title, ...section.items]).join(" ");

  assertContract(shouldShowProgressTreeContextBannerToggle(bannerContent), "有深度要求时公告条应支持展开");
  assertContract(!shouldShowProgressTreeContextBannerToggle(emptyBanner), "空态公告条不应显示展开入口");
  assertContract(INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_HEADER_LAYOUT === "label_and_node_title_same_row", "公告条标题和节点名称应固定在同一行");
  assertContract(INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY.expand === "展开", "公告条展开按钮文案应为展开");
  assertContract(INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY.collapse === "收起", "公告条收起按钮文案应为收起");
  assertContract(expandedSections.map((section) => section.key).join(",") === "depth_requirement,technical_coverage,follow_up_directions,loss_risks", "展开后应显示深度要求、技术点覆盖、连续追问方向、常见失分风险");
  assertContract(expandedCopy.includes("深度要求"), "展开后应展示深度要求标题");
  assertContract(expandedCopy.includes("技术点覆盖"), "展开后应展示技术点覆盖标题");
  assertContract(expandedCopy.includes("连续追问方向"), "展开后应展示连续追问方向标题");
  assertContract(expandedCopy.includes("常见失分风险"), "展开后应展示常见失分风险标题");
  assertContract(expandedCopy.includes("如何验证融合排序收益"), "展开后应展示追问方向内容");
  assertContract(expandedCopy.includes("只讲工具链，不说明阈值调优依据"), "展开后应展示常见失分风险内容");
  for (const hiddenCopy of ["建议第一题", "你会如何设计第一题？", "好回答信号", "简历线索", "岗位依据", "简历中提到搜索优化", "岗位要求检索增强能力"]) {
    assertContract(!expandedCopy.includes(hiddenCopy), `展开后不应展示 ${hiddenCopy}`);
  }
}

function test_workbench_chat_bubble_alignment_keeps_system_left_and_user_right(): void {
  assertContract(INTERVIEW_WORKBENCH_DETAIL_WIDTH_POLICY.conversationPanel === "fills_available_grid_column", "右侧对话详情 section 应占满剩余 grid 宽度");
  assertContract(INTERVIEW_WORKBENCH_DETAIL_WIDTH_POLICY.chatScroll === "full_width_message_list", "消息列表容器不应复用回答卡 max-width");
  assertContract(INTERVIEW_WORKBENCH_DETAIL_WIDTH_POLICY.leftDetailContent === "full_width_left_content", "系统题目、上下文、反馈应在完整详情区内靠左铺开");
  assertContract(INTERVIEW_WORKBENCH_DETAIL_WIDTH_POLICY.userAnswerContent === "right_aligned_capped_content", "用户回答仍应右对齐并保留宽度上限");
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.system_question === "left", "系统题目应位于聊天区左侧");
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.user_answer === "right", "用户回答及暂无回答占位应位于聊天区右侧");
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.progress_context === "left", "当前节点上下文应位于聊天区左侧");
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.feedback === "left", "反馈卡应位于聊天区左侧");
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.user_answer_placeholder === "right", "暂无回答占位应复用用户回答右对齐");
  assertContract(getWorkbenchChatMessageAlignmentClassName("system_question") === "messageRowLeft", "系统题目应使用左对齐行容器");
  assertContract(getWorkbenchChatMessageAlignmentClassName("progress_context") === "messageRowLeft", "当前节点上下文应使用左对齐行容器");
  assertContract(getWorkbenchChatMessageAlignmentClassName("feedback") === "messageRowLeft", "反馈卡应使用左对齐行容器");
  assertContract(getWorkbenchChatMessageAlignmentClassName("user_answer") === "messageRowRight", "用户回答应使用右对齐行容器");
  assertContract(getWorkbenchChatMessageAlignmentClassName("user_answer_placeholder") === "messageRowRight", "暂无回答应使用右对齐行容器");
}

function test_question_node_clipboard_includes_full_question_answer_and_feedback(): void {
  const session: PolishSessionDetail = {
    ...buildTestSession([
      buildTestProgressNode("node_clipboard_question", "混合检索策略设计", "resume_deep_dive", "深度打磨类"),
    ], "node_clipboard_question"),
    turns: [
      {
        question_id: "q_clipboard_question",
        question_text: "请完整说明你会如何设计混合检索策略，包括召回、重排、降级和效果验证。",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_clipboard_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [
          {
            answer_id: "ans_clipboard_question",
            answer_round: 1,
            answer_text: "我会先用 BM25 和向量召回，再用交叉编码器重排，并用无结果兜底保证可用性。",
            answer_created_at: "2026-05-21T10:01:00Z",
            feedback_text: "回答覆盖主链路，但需要补充线上指标和回滚策略。",
            feedback_id: "fb_clipboard_question",
            score_result_id: null,
            feedback_created_at: "2026-05-21T10:02:00Z",
          },
        ],
      },
    ],
  };
  const questionNode = buildWorkbenchProgressNodes(session)[0]?.children?.[0]?.children?.[0];
  const markdown = buildProgressTreeNodeClipboardMarkdown(session, questionNode);

  assertContract(isQuestionNode(questionNode), "测试目标必须是题目节点");
  assertContract(markdown.includes("# 节点信息"), "右键复制仍应输出节点信息标题");
  assertContract(markdown.includes("节点标题：题目 1"), "题目节点复制应保留节点标题");
  assertContract(markdown.includes("所属节点：深度打磨类 / 混合检索策略设计"), "题目节点复制应包含所属节点路径");
  assertContract(markdown.includes("请完整说明你会如何设计混合检索策略，包括召回、重排、降级和效果验证。"), "题目节点复制应包含完整题目正文");
  assertContract(markdown.includes("我会先用 BM25 和向量召回，再用交叉编码器重排，并用无结果兜底保证可用性。"), "题目节点复制应包含完整回答");
  assertContract(markdown.includes("回答覆盖主链路，但需要补充线上指标和回滚策略。"), "题目节点复制应包含完整反馈");
  assertContract(!markdown.includes("说明：请完整说明你会如何设计混合检索策略"), "题目节点复制不应只输出短摘要说明");
}

function test_question_node_clipboard_uses_answer_and_feedback_placeholders(): void {
  const session: PolishSessionDetail = {
    ...buildTestSession([
      buildTestProgressNode("node_clipboard_empty_question", "Prompt 工程与幻觉控制", "resume_deep_dive", "深度打磨类"),
    ], "node_clipboard_empty_question"),
    turns: [
      {
        question_id: "q_clipboard_empty_question",
        question_text: "请说明你如何降低大模型回答中的幻觉风险。",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_clipboard_empty_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const questionNode = buildWorkbenchProgressNodes(session)[0]?.children?.[0]?.children?.[0];
  const markdown = buildProgressTreeNodeClipboardMarkdown(session, questionNode);

  assertContract(markdown.includes("请说明你如何降低大模型回答中的幻觉风险。"), "无回答题目也应复制完整题干");
  assertContract(markdown.includes("暂无回答"), "无回答时应输出稳定占位");
  assertContract(markdown.includes("本轮反馈尚未生成"), "无反馈时应输出稳定占位");
}

function test_progress_tree_click_auto_generates_only_for_nodes_without_question(): void {
  const session = buildTestSession(
    [
      buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_without_question", "待生成节点", "jd_gap_learning", "补齐学习类"),
    ],
    "node_with_question",
  );
  const sessionWithTurn: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const groupedNodes = buildWorkbenchProgressNodes(sessionWithTurn);
  const realNodes = groupedNodes.flatMap((group) => group.children ?? []);
  const nodeWithQuestion = realNodes.find((node) => node.key === "node_with_question");
  const nodeWithoutQuestion = realNodes.find((node) => node.key === "node_without_question");

  const sessionWithHistoricalTurn: PolishSessionDetail = {
    ...sessionWithTurn,
    turns: [
      ...sessionWithTurn.turns,
      {
        question_id: "q_current_other",
        question_text: "其他节点当前题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:02:00Z",
        progress_node_ref: "node_without_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const refreshFailedSession: PolishSessionDetail = {
    ...session,
    progress_tree_status: "refresh_failed",
  };

  assertContract(!shouldAutoCreateQuestionForProgressNode(sessionWithTurn, "node_with_question"), "active question 位于该节点时不应重复自动生成题");
  assertContract(!shouldAutoCreateQuestionForProgressNode(sessionWithTurn, "node_without_question"), "无题目的真实节点点击后也只选择栏目");
  assertContract(!shouldAutoCreateQuestionForProgressNode(sessionWithHistoricalTurn, "node_with_question"), "只有历史题目但无 active question 的节点点击后也只选择栏目");
  assertContract(!shouldAutoCreateQuestionForProgressNode(sessionWithTurn, null), "空节点 ref 不应生成题");
  assertContract(!canAutoCreateQuestionFromProgressNode({
    session: refreshFailedSession,
    progressNodeRef: "node_without_question",
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
  }), "refresh_failed 但 plan 可展示时，点击节点仍不应自动生成题");
  assertContract(nodeWithQuestion?.children?.some((node) => node.key === "question:q_existing") === true, "题目记录应挂到自己的 progress_node_ref 节点下");
  assertContract(!nodeWithoutQuestion?.children?.some((node) => node.kind === "question"), "其他节点不应承载已有题目记录");
  assertContract(resolveCurrentQuestionId(sessionWithTurn, "node_with_question") === "q_existing", "当前题目应可按选中节点解析");
}

function test_workbench_question_actions_follow_current_question_status(): void {
  const session = buildTestSession(
    [
      buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_without_question", "待生成节点", "jd_gap_learning", "补齐学习类"),
    ],
    "node_with_question",
  );
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const completedSession: PolishSessionDetail = {
    ...sessionWithQuestion,
    progress_tree_state: {
      ...sessionWithQuestion.progress_tree_state,
      node_states: sessionWithQuestion.progress_tree_state.node_states.map((nodeState) =>
        nodeState.progress_node_ref === "node_with_question"
          ? { ...nodeState, status: "completed", completed_questions_count: 1 }
          : nodeState,
      ),
      completed_focus_refs: [
        {
          question_id: "q_existing",
          progress_node_ref: "node_with_question",
          focus_key: "focus_existing",
          source: "manual_question_complete",
        },
      ],
    },
  };

  const progressNodes = buildWorkbenchProgressNodes(sessionWithQuestion);
  const parentNodeWithQuestion = progressNodes[0]?.children?.[0] ?? null;
  const questionNode = parentNodeWithQuestion?.children?.[0] ?? null;
  const noQuestionNode = progressNodes[0]?.children?.[1] ?? null;

  const noQuestionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: noQuestionNode,
    progressNodeRef: "node_without_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const parentNodeQuestionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: parentNodeWithQuestion,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const inProgressQuestionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const completedQuestionState = deriveWorkbenchQuestionActionState({
    session: completedSession,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });

  assertContract(noQuestionState.hasCurrentQuestion === false, "无题目节点应识别为无当前题目");
  assertContract(noQuestionState.isQuestionNode === false, "无题目节点不应被识别为题目节点");
  assertContract(noQuestionState.canSendAnswer === false, "无题目节点不允许提交回答");
  assertContract(noQuestionState.canGenerateQuestion === true, "无题目节点应允许生成题目");
  assertContract(noQuestionState.canMarkQuestionCompleted === false, "无题目节点不允许标记完成");
  assertContract(parentNodeQuestionState.hasCurrentQuestion === true, "父节点已有题目时应识别为当前节点有题");
  assertContract(parentNodeQuestionState.isQuestionNode === false, "父节点有题也不应被当作题目节点");
  assertContract(parentNodeQuestionState.canSendAnswer === false, "父节点有题但未选中题目 entry 时不允许提交回答");
  assertContract(parentNodeQuestionState.canGenerateQuestion === false, "父节点已有未完成题目时不允许重复生成题目");
  assertContract(parentNodeQuestionState.canMarkQuestionCompleted === true, "父节点已有未完成题目时允许标记完成");
  assertContract(inProgressQuestionState.isQuestionNode === true, "选中题目 entry 时应识别为题目节点");
  assertContract(inProgressQuestionState.hasCurrentQuestion === true, "已有未完成题目应识别为当前题目");
  assertContract(inProgressQuestionState.currentQuestionStatus === "in_progress", "已有未完成题目状态应为 in_progress");
  assertContract(inProgressQuestionState.canSendAnswer === true, "已有未完成题目应允许提交回答");
  assertContract(inProgressQuestionState.canGenerateQuestion === false, "已有未完成题目不允许重复生成题目");
  assertContract(inProgressQuestionState.canMarkQuestionCompleted === true, "已有未完成题目应允许标记完成");
  assertContract(completedQuestionState.currentQuestionStatus === "completed", "已完成题目状态应为 completed");
  assertContract(completedQuestionState.canGenerateQuestion === true, "已有已完成题目应允许生成题目");
  assertContract(completedQuestionState.canMarkQuestionCompleted === false, "已有已完成题目不允许重复标记完成");
}

function test_workbench_composer_primary_button_stays_send_for_selected_question(): void {
  const session = buildTestSession(
    [
      buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_without_question", "待生成节点", "jd_gap_learning", "补齐学习类"),
    ],
    "node_with_question",
  );
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };

  const progressNodes = buildWorkbenchProgressNodes(sessionWithQuestion);
  const questionNode = progressNodes[0]?.children?.[0]?.children?.[0] ?? null;
  const questionActionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const composerActionState = deriveComposerActionViewModel({
    session: sessionWithQuestion,
    questionActionState,
    answerText: "",
  isFollowUpQuestionApiSupported: true,
});

  assertContract(composerActionState.sendAnswerButtonLabel === "发送", "选中题目时主按钮应保持发送");
  assertContract(
    composerActionState.sendAnswerPlaceholder === INTERVIEW_WORKBENCH_SEND_ANSWER_PLACEHOLDER,
    "选中未回答题目时主输入框应使用普通回答占位文案",
  );
  assertContract(
    composerActionState.regenerateQuestionButtonCopy === INTERVIEW_WORKBENCH_REGENERATE_CURRENT_QUESTION_BUTTON,
    "选中题目时次级按钮应显示换一道题",
  );
}

function test_workbench_composer_send_remains_retry_when_question_has_answer(): void {
  const session = buildTestSession([
    buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
  ], "node_with_question");
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [buildQuestionAnswer({
          feedback_text: "上次回答不完整",
        })],
      },
    ],
  };
  const progressNodes = buildWorkbenchProgressNodes(sessionWithQuestion);
  const questionNode = progressNodes[0]?.children?.[0]?.children?.[0] ?? null;
  const questionActionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const composerActionState = deriveComposerActionViewModel({
    session: sessionWithQuestion,
    questionActionState,
    answerText: "继续补充细节",
    isFollowUpQuestionApiSupported: true,
  });

  assertContract(
    composerActionState.sendAnswerPlaceholder === INTERVIEW_WORKBENCH_SEND_RETRY_PLACEHOLDER,
    "有历史回答时应提示继续打磨语义",
  );
  assertContract(
    composerActionState.canFollowUpCurrentQuestion === true,
    "composer state 应允许在有回答历史时追问本题",
  );
  assertContract(
    canFollowUpCurrentQuestion({
      isQuestionNode: true,
      canSendAnswer: true,
      hasCurrentQuestionAnswer: questionActionState.hasCurrentQuestionAnswer,
      hasCurrentQuestionFeedback: questionActionState.hasCurrentQuestionFeedback,
      isFollowUpQuestionApiSupported: true,
    })
      === true,
    "有历史回答时可执行追问",
  );
  assertContract(
    canFollowUpCurrentQuestion({
      isQuestionNode: true,
      canSendAnswer: true,
      hasCurrentQuestionAnswer: questionActionState.hasCurrentQuestionAnswer,
      hasCurrentQuestionFeedback: questionActionState.hasCurrentQuestionFeedback,
      isFollowUpQuestionApiSupported: false,
    }) === false,
    "接口关闭时可追问能力应关闭",
  );
}

function test_workbench_composer_follow_up_disabled_without_history_or_contract(): void {
  const session = buildTestSession([
    buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
  ], "node_with_question");
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const progressNodes = buildWorkbenchProgressNodes(sessionWithQuestion);
  const questionNode = progressNodes[0]?.children?.[0]?.children?.[0] ?? null;
  const questionActionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const composerActionStateNoHistory = deriveComposerActionViewModel({
    session: sessionWithQuestion,
    questionActionState,
    answerText: "",
    isFollowUpQuestionApiSupported: true,
  });
  const composerActionStateWithoutContract = deriveComposerActionViewModel({
    session: sessionWithQuestion,
    questionActionState,
    answerText: "",
    isFollowUpQuestionApiSupported: false,
  });

  assertContract(
    composerActionStateNoHistory.canFollowUpCurrentQuestion === false,
    "无历史回答或反馈时应禁用追问本题",
  );
  assertContract(
    composerActionStateNoHistory.followUpCurrentQuestionDisabledReason === INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_DISABLED_WITHOUT_HISTORY,
    "无历史时应显示先提交再追问提示",
  );
  assertContract(
    composerActionStateWithoutContract.followUpCurrentQuestionDisabledReason === INTERVIEW_WORKBENCH_FOLLOW_UP_CURRENT_QUESTION_UNSUPPORTED,
    "接口不支持时应显示 contract 缺口提示",
  );
}

function test_workbench_composer_regenerate_available_for_current_question_without_completion(): void {
  const session = buildTestSession([
    buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
  ], "node_with_question");
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const progressNodes = buildWorkbenchProgressNodes(sessionWithQuestion);
  const questionNode = progressNodes[0]?.children?.[0]?.children?.[0] ?? null;
  const questionActionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const composerActionState = deriveComposerActionViewModel({
    session: sessionWithQuestion,
    questionActionState,
    answerText: "",
    selectedProgressNodeRef: "node_with_question",
  });

  assertContract(
    questionActionState.canGenerateQuestion === false,
    "未完成题目不应允许生成下一题",
  );
  assertContract(
    questionActionState.canRegenerateQuestion === true,
    "换题按钮不应被未完成态禁用",
  );
  assertContract(
    composerActionState.canRegenerateCurrentQuestion === true,
    "选中未完成题目时“换一道题”应可用",
  );
  assertContract(
    composerActionState.regenerateQuestionButtonCopy === INTERVIEW_WORKBENCH_REGENERATE_CURRENT_QUESTION_BUTTON,
    "未完成题目时次级按钮文案应为换一道题",
  );
  assertContract(
    composerActionState.regenerateQuestionDisabledReason === null,
    "可用时不应有换题禁用文案",
  );
}

function test_workbench_composer_regenerate_for_node_without_selected_question_and_no_node_ref(): void {
  const session = buildTestSession([
    buildTestProgressNode("node_without_question", "待生成节点", "jd_gap_learning", "补齐学习类"),
  ], "node_without_question");
  const progressNodes = buildWorkbenchProgressNodes(session);
  const selectedNode = progressNodes[0]?.children?.[0] ?? null;
  const actionState = deriveWorkbenchQuestionActionState({
    session,
    selectedProgressNode: selectedNode,
    progressNodeRef: "node_without_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const composerActionState = deriveComposerActionViewModel({
    session,
    questionActionState: actionState,
    answerText: "",
    selectedProgressNodeRef: "node_without_question",
  });

  assertContract(actionState.canRegenerateQuestion === true, "能力节点可点击为当前节点出题");
  assertContract(
    composerActionState.regenerateQuestionButtonCopy === INTERVIEW_WORKBENCH_REGENERATE_NODE_BUTTON,
    "非题目节点时按钮应显示为当前节点出题",
  );
  assertContract(
    !canRegenerateQuestionForCurrentNode({
      canCreateQuestionTask: true,
      isQuestionNode: true,
      currentQuestionProgressNodeRef: null,
      selectedProgressNodeRef: null,
    }),
    "无法定位当前题目与当前节点时应禁用换题",
  );
  assertContract(
    deriveRegenerateQuestionDisabledReason({
      canCreateQuestionTask: false,
      isQuestionNode: true,
      currentQuestionProgressNodeRef: null,
      selectedProgressNodeRef: null,
    }) === INTERVIEW_WORKBENCH_REGENERATE_CURRENT_NODE_NO_NODE_TOOLTIP,
    "定位失败时应返回明确中文提示",
  );
  assertContract(
    canRegenerateQuestionForCurrentNode({
      canCreateQuestionTask: true,
      isQuestionNode: true,
      currentQuestionProgressNodeRef: null,
      selectedProgressNodeRef: "node_without_question",
    }),
    "题目节点缺失所属进度节点时可由 selected_progress_node_ref 兜底",
  );
}

function test_workbench_composer_regenerate_preserves_draft_guard(): void {
  assertContract(
    !shouldConfirmBeforeRegenerateQuestion(""),
    "空草稿不应要求“换题”前确认",
  );
  assertContract(
    !shouldConfirmBeforeRegenerateQuestion("   "),
    "空白草稿不需要确认弹窗",
  );
  assertContract(
    shouldConfirmBeforeRegenerateQuestion("继续提问之前的草稿"),
    "有草稿时应要求“换题”前确认",
  );
}

function test_workbench_composer_mark_completed_and_regenerate_confirmation_gate(): void {
  const session = buildTestSession([
    buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
  ], "node_with_question");
  const sessionWithoutFeedback: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [buildQuestionAnswer({
          feedback_text: "上次回答",
        })],
      },
    ],
  };
  const sessionWithFeedback: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [buildQuestionAnswer({
          feedback_id: "fb_1",
          feedback_created_at: "2026-05-21T10:03:00Z",
          feedback_text: "回复完整",
          feedback_payload: {
            status: "generated",
            feedback_id: "fb_1",
          },
        })],
      },
    ],
  };
  const progressNodes = buildWorkbenchProgressNodes(session);
  const questionNode = progressNodes[0]?.children?.[0]?.children?.[0] ?? null;
  const stateWithoutFeedback = deriveWorkbenchQuestionActionState({
    session: sessionWithoutFeedback,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const stateWithFeedback = deriveWorkbenchQuestionActionState({
    session: sessionWithFeedback,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const composerWithoutFeedback = deriveComposerActionViewModel({
    session: sessionWithoutFeedback,
    questionActionState: stateWithoutFeedback,
    answerText: "",
    isFollowUpQuestionApiSupported: true,
  });
  const composerWithFeedback = deriveComposerActionViewModel({
    session: sessionWithFeedback,
    questionActionState: stateWithFeedback,
    answerText: "",
    isFollowUpQuestionApiSupported: true,
  });

  assertContract(
    canMarkCurrentQuestionCompleted({
      hasCurrentQuestion: stateWithoutFeedback.hasCurrentQuestion,
      hasCurrentQuestionFeedback: stateWithoutFeedback.hasCurrentQuestionFeedback,
      isCurrentQuestionCompleted: stateWithoutFeedback.isCurrentQuestionCompleted,
    }) === false,
    "无反馈时不应可标记完成",
  );
  assertContract(
    composerWithoutFeedback.markCurrentQuestionCompletedDisabledReason === INTERVIEW_WORKBENCH_MARK_QUESTION_COMPLETED_DISABLED_WITHOUT_FEEDBACK,
    "无反馈时按钮应给出提示",
  );
  assertContract(
    composerWithFeedback.canMarkCurrentQuestionCompleted,
    "有反馈时按钮应可点",
  );
  assertContract(
    !shouldConfirmBeforeRegenerateQuestion(""),
    "空草稿无需再次确认",
  );
  assertContract(
    !shouldConfirmBeforeRegenerateQuestion("   "),
    "空白草稿无需再次确认",
  );
  assertContract(
    shouldConfirmBeforeRegenerateQuestion("继续提问之前的草稿"),
    "存在草稿需弹确认",
  );
}

function test_progress_tree_context_menu_items_follow_question_action_state(): void {
  const session = buildTestSession(
    [
      buildTestProgressNode("node_with_question", "混合检索与幻觉控制", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_without_question", "待生成节点", "jd_gap_learning", "补齐学习类"),
    ],
    "node_with_question",
  );
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const progressNodes = buildWorkbenchProgressNodes(sessionWithQuestion);
  const parentNodeWithQuestion = progressNodes[0]?.children?.[0] ?? null;
  const noQuestionNode = progressNodes[0]?.children?.[1] ?? null;
  const questionNode = parentNodeWithQuestion?.children?.[0] ?? null;
  const parentNodeQuestionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: parentNodeWithQuestion,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const noQuestionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: noQuestionNode,
    progressNodeRef: "node_without_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const questionState = deriveWorkbenchQuestionActionState({
    session: sessionWithQuestion,
    selectedProgressNode: questionNode,
    progressNodeRef: "node_with_question",
    canShowProgressTree: true,
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
    completingQuestion: false,
    endingSession: false,
  });
  const parentMenuItems = buildProgressTreeContextMenuItems(parentNodeWithQuestion, parentNodeQuestionState);
  const noQuestionMenuItems = buildProgressTreeContextMenuItems(noQuestionNode, noQuestionState);
  const questionMenuItems = buildProgressTreeContextMenuItems(questionNode, questionState);

  assertContract(INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_PLACEMENT === "fixed_at_pointer", "右键菜单应按鼠标位置 fixed 渲染");
  assertContract(parentMenuItems.length >= 3, "右键父节点菜单内容不能为空");
  assertContract(questionMenuItems.length >= 3, "右键题目节点菜单内容不能为空");
  assertContract(parentMenuItems.map((item) => item.label).join(",").includes(INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS.generateQuestion), "菜单应包含生成题目");
  assertContract(parentMenuItems.map((item) => item.label).join(",").includes(INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS.markQuestionCompleted), "菜单应包含标记完成");
  assertContract(parentMenuItems.map((item) => item.label).join(",").includes(INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_ITEMS.copyNodeInfo), "菜单应包含复制节点信息");
  assertContract(parentMenuItems.find((item) => item.key === "generate_question")?.disabled === !parentNodeQuestionState.canGenerateQuestion, "父节点生成题目禁用态应复用底部按钮规则");
  assertContract(parentMenuItems.find((item) => item.key === "mark_question_completed")?.disabled === !parentNodeQuestionState.canMarkQuestionCompleted, "父节点标记完成禁用态应复用底部按钮规则");
  assertContract(noQuestionMenuItems.find((item) => item.key === "generate_question")?.disabled === !noQuestionState.canGenerateQuestion, "无题节点生成题目禁用态应复用底部按钮规则");
  assertContract(noQuestionMenuItems.find((item) => item.key === "mark_question_completed")?.disabled === !noQuestionState.canMarkQuestionCompleted, "无题节点标记完成禁用态应复用底部按钮规则");
  assertContract(questionMenuItems.find((item) => item.key === "generate_question")?.disabled === !questionState.canGenerateQuestion, "题目节点生成题目禁用态应复用底部按钮规则");
  assertContract(questionMenuItems.find((item) => item.key === "mark_question_completed")?.disabled === !questionState.canMarkQuestionCompleted, "题目节点标记完成禁用态应复用底部按钮规则");
  assertContract(parentMenuItems.find((item) => item.key === "copy_node_info")?.disabled === false, "父节点复制信息应可用");
  assertContract(questionMenuItems.find((item) => item.key === "copy_node_info")?.disabled === false, "题目节点复制信息应可用");
}

function test_progress_tree_context_menu_closes_on_escape_and_external_events(): void {
  assertContract(INTERVIEW_PROGRESS_TREE_CONTEXT_MENU_CLOSE_TRIGGERS.join(",") === "outside_pointer_down,escape,scroll,select", "右键菜单关闭触发器应覆盖外部点击、Escape、滚动和选择菜单项");
  assertContract(shouldCloseProgressTreeContextMenuFromKeyboard({ key: "Escape" }), "Escape 应关闭进展树右键菜单");
  assertContract(!shouldCloseProgressTreeContextMenuFromKeyboard({ key: "Enter" }), "Enter 不应作为右键菜单全局关闭快捷键");
}

function test_progress_tree_question_entry_is_selectable_by_node_type(): void {
  const session = buildTestSession([
    buildTestProgressNode("node_with_question", "已有题目节点", "resume_deep_dive", "深度打磨类"),
  ]);
  const sessionWithQuestion: PolishSessionDetail = {
    ...session,
    turns: [
      {
        question_id: "q_existing",
        question_text: "已有题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_with_question",
        evidence_refs: [],
        context_digest: "digest",
        answers: [],
      },
    ],
  };
  const questionNode = buildWorkbenchProgressNodes(sessionWithQuestion)[0]?.children?.[0]?.children?.[0];
  const selectedRef = resolveProgressTreeSelectedNodeRefAfterClick(questionNode, null);

  assertContract(isQuestionNode(questionNode), "题目 entry 应通过 node.kind 识别为题目节点");
  assertContract(selectedRef === "node_with_question", "点击题目节点应选中其 progress_node_ref");
}

function test_progress_tree_click_focuses_latest_question_for_node(): void {
  const baseSession = buildTestSession([
    buildTestProgressNode("node_focus", "混合检索策略设计", "resume_deep_dive", "深度打磨类"),
  ]);
  const session: PolishSessionDetail = {
    ...baseSession,
    turns: [
      {
        question_id: "q_focus_old",
        question_text: "旧题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_focus",
        evidence_refs: [],
        context_digest: "digest-old",
        answers: [],
      },
      {
        question_id: "q_focus_latest",
        question_text: "最新题目",
        question_sources: [],
        question_created_at: "2026-05-21T10:05:00Z",
        progress_node_ref: "node_focus",
        evidence_refs: [],
        context_digest: "digest-latest",
        answers: [],
      },
    ],
  };
  const progressNode = buildWorkbenchProgressNodes(session)[0]?.children?.[0] ?? null;
  const oldQuestionNode = progressNode?.children?.find((node) => node.key === "question:q_focus_old") ?? null;

  assertContract(resolveWorkbenchQuestionFocusId(session, progressNode, "node_focus") === "q_focus_latest", "点击进展节点应定位到该节点最新题目");
  assertContract(resolveWorkbenchQuestionFocusId(session, oldQuestionNode, "node_focus") === "q_focus_old", "点击题目节点应定位到该题目");
}

function test_workbench_chat_auto_scroll_trigger_changes_on_focus_and_feedback(): void {
  const firstFocus = buildQuestionConversationAutoScrollTrigger({
    focusedQuestionId: "q_1",
    selectedProgressNodeRef: "node_1",
    latestAnswerId: "ans_1",
  });
  const nextAnswerFocus = buildQuestionConversationAutoScrollTrigger({
    focusedQuestionId: "q_1",
    selectedProgressNodeRef: "node_1",
    latestAnswerId: "ans_2",
  });
  const nextQuestionFocus = buildQuestionConversationAutoScrollTrigger({
    focusedQuestionId: "q_2",
    selectedProgressNodeRef: "node_2",
    latestAnswerId: null,
  });

  assertContract(firstFocus !== null && nextAnswerFocus !== null && nextQuestionFocus !== null, "自动滚动 trigger 在有效上下文下应可构建");
  assertContract(firstFocus !== nextAnswerFocus, "同题目新增反馈后 trigger 应变化");
  assertContract(firstFocus !== nextQuestionFocus, "切换题目后 trigger 应变化");
}

function test_workbench_chat_auto_scroll_respects_manual_scroll_when_question_not_changed(): void {
  const currentTrigger = buildQuestionConversationAutoScrollTrigger({
    focusedQuestionId: "q_1",
    selectedProgressNodeRef: "node_1",
    latestAnswerId: "ans_1",
  });
  const sameTrigger = buildQuestionConversationAutoScrollTrigger({
    focusedQuestionId: "q_1",
    selectedProgressNodeRef: "node_1",
    latestAnswerId: "ans_1",
  });

  assertContract(currentTrigger !== null && sameTrigger !== null, "同题目应可构建稳定 trigger");
  assertContract(
    shouldAutoScrollQuestionConversation({
      nextTrigger: sameTrigger,
      previousTrigger: currentTrigger,
      hasUserManuallyScrolled: true,
    }) === false,
    "同题目且用户手动滚动时不应再次自动滚动",
  );
  assertContract(
    shouldAutoScrollQuestionConversation({
      nextTrigger: sameTrigger,
      previousTrigger: currentTrigger,
      hasUserManuallyScrolled: false,
    }) === true,
    "同题目且未手动滚动时可复用上次定位策略",
  );
}

function test_workbench_sticky_header_view_model_matches_current_question_context(): void {
  const session = {
    ...buildTestSession([
      buildTestProgressNode("node_focus", "混合检索策略设计", "resume_deep_dive", "深度打磨类"),
    ]),
    turns: [
      {
        question_id: "q_focus",
        question_text: "如果让你在高并发检索中平衡召回率与精确率，你会如何设计并优先优化？",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_focus",
        evidence_refs: [],
        context_digest: "digest",
        answers: [
          {
            answer_id: "ans_1",
            answer_round: 1,
            answer_text: "答：我会先从 query rewrite 开始，结合多路召回再重排。",
            answer_created_at: "2026-05-21T10:01:00Z",
            feedback_text: "回复完整。",
            feedback_id: "fb_1",
            score_result_id: "score_1",
            feedback_created_at: "2026-05-21T10:02:00Z",
            feedback_payload: {
              feedback_id: "fb_1",
              feedback_text: "回复完整。",
              status: "generated" as const,
            },
          },
        ],
      },
    ],
  };
  const stickyContext = buildStickyQuestionContextViewModel(session, "q_focus", "node_focus");

  assertContract(stickyContext?.progressNodeTitle === "混合检索策略设计", "sticky header 应包含当前节点上下文");
  assertContract(stickyContext?.capabilityTheme === "深度打磨类", "sticky header 应包含当前能力主题");
  assertContract(stickyContext?.questionIndexLabel === "题目 1", "sticky header 应包含题目编号");
  assertContract(
    stickyContext?.questionText === "如果让你在高并发检索中平衡召回率与精确率，你会如何设计并优先优化？",
    "sticky header 应包含题目正文",
  );
  assertContract(stickyContext?.feedbackStatusLabel === mapFeedbackCodeToDisplay("generated").text, "sticky header 应复用反馈状态中文映射");
}

function test_workbench_sticky_question_text_collapse_behavior(): void {
  assertContract(
    shouldCollapseCurrentQuestionText("短题干示例", { isExpanded: false }) === false,
    "短题干不应默认折叠",
  );
  const longText = "请结合你的实际项目经验，完整回答以下问题，要求覆盖架构演进路径、指标体系、故障回滚策略、上线流程与持续优化机制。".repeat(6);
  assertContract(shouldCollapseCurrentQuestionText(longText, { isExpanded: false }) === true, "长题干默认应折叠");
  assertContract(shouldCollapseCurrentQuestionText(longText, { isExpanded: true }) === false, "展开后长题干应完整展示");
}

function test_authenticated_frontend_smoke_fixture_covers_list_and_workbench_metadata(): void {
  const smokeSessionSummary = buildTestSessionSummary({
    id: "ses_auth_smoke",
    session_id: "ses_auth_smoke",
    title: "认证 smoke 模拟面试",
    job_title: "后端工程师",
    resume_title: "后端简历",
    binding_label: "后端工程师 / 后端简历",
    custom_topic_text_summary: "认证前端 smoke 主题",
  });
  const baseDetail = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_auth_smoke", "认证工作台 smoke 节点", "resume_deep_dive", "深度打磨类"),
        depth_goal: "验证登录后的题目与 metadata 详情不会让工作台白屏。",
      },
    ],
    "node_auth_smoke",
  );
  const detailWithMetadata: PolishSessionDetail = {
    ...baseDetail,
    session_id: "ses_auth_smoke",
    turns: [
      {
        question_id: "q_auth_smoke_metadata",
        question_text: "请说明你如何验证登录后的前端工作台路径。",
        question_sources: [
          {
            index: 1,
            source_type: "progress_node",
            title: "认证 smoke 节点",
            excerpt: "覆盖认证后的列表、详情和题目 metadata。",
            ref_id: "node_auth_smoke",
            availability: "available",
          },
        ],
        question_created_at: "2026-05-21T10:20:00Z",
        progress_node_ref: "node_auth_smoke",
        evidence_refs: ["node_auth_smoke"],
        context_digest: "auth-smoke-digest",
        question_metadata: {
          question_pattern: "authenticated_frontend_smoke",
          confidence_level: "medium",
          low_confidence_flags: [],
          expected_answer_dimensions: ["authenticated_list", "workbench_detail"],
          quality_score: 88,
          source_availability: "available",
        },
        answers: [],
      },
    ],
  };
  const detailWithoutMetadata: PolishSessionDetail = {
    ...baseDetail,
    session_id: "ses_auth_smoke_legacy",
    turns: [
      {
        question_id: "q_auth_smoke_legacy",
        question_text: "旧题目缺少 metadata 时也应稳定展示。",
        question_sources: [],
        question_created_at: "2026-05-21T10:25:00Z",
        progress_node_ref: "node_auth_smoke",
        evidence_refs: [],
        context_digest: null,
        answers: [],
      },
    ],
  };

  const list = [smokeSessionSummary];
  const groupedNodesWithMetadata = buildWorkbenchProgressNodes(detailWithMetadata);
  const groupedNodesWithoutMetadata = buildWorkbenchProgressNodes(detailWithoutMetadata);
  const clipboardWithMetadata = buildPolishSessionClipboardMarkdown(detailWithMetadata);
  const clipboardWithoutMetadata = buildPolishSessionClipboardMarkdown(detailWithoutMetadata);
  const metadata = detailWithMetadata.turns[0].question_metadata;

  assertContract(POLISH_API_PATHS.sessions === "/polish-sessions", "列表 smoke 应命中 polish session list API");
  assertContract(POLISH_API_PATHS.sessionDetail("ses_auth_smoke") === "/polish-sessions/ses_auth_smoke", "工作台 smoke 应命中 session detail API");
  assertContract(POLISH_API_PATHS.completeQuestion("ses_auth_smoke", "q_auth_smoke_metadata") === "/polish-sessions/ses_auth_smoke/questions/q_auth_smoke_metadata/complete", "标记完成应命中 question complete API");
  assertContract(POLISH_API_PATHS.endSession("ses_auth_smoke") === "/polish-sessions/ses_auth_smoke/end", "结束模拟面试应命中 session end API");
  assertContract(filterPolishSessionsBySearch(list, "认证").length === 1, "认证后的列表响应应可被 /interview 列表消费");
  assertContract(groupedNodesWithMetadata[0]?.children?.[0]?.children?.[0]?.key === "question:q_auth_smoke_metadata", "带 metadata 的题目应挂入工作台进展树");
  assertContract(groupedNodesWithoutMetadata[0]?.children?.[0]?.children?.[0]?.key === "question:q_auth_smoke_legacy", "缺 metadata 的旧题目也应挂入工作台进展树");
  assertContract(resolveCurrentQuestionId(detailWithMetadata, "node_auth_smoke") === "q_auth_smoke_metadata", "带 metadata 的工作台详情应可解析当前题目");
  assertContract(resolveCurrentQuestionId(detailWithoutMetadata, "node_auth_smoke") === "q_auth_smoke_legacy", "缺 metadata 的工作台详情应可解析当前题目");
  assertContract(metadata?.question_pattern === "authenticated_frontend_smoke", "前端类型应允许 session detail 携带 question_metadata");
  assertContract(clipboardWithMetadata.includes("请说明你如何验证登录后的前端工作台路径。"), "带 metadata 的详情应可生成复制内容");
  assertContract(clipboardWithoutMetadata.includes("旧题目缺少 metadata 时也应稳定展示。"), "缺 metadata 的详情应可生成复制内容");
}

function test_waiting_answer_bar_is_removed_from_workbench_contract(): void {
  const machineState = deriveWorkbenchMachineState({
    session: buildTestSession([buildTestProgressNode("node_current", "当前题目节点", "resume_deep_dive", "深度打磨类")], "node_current"),
    creatingQuestion: false,
    feedbackGenerating: false,
    failureState: null,
  });

  assertContract(INTERVIEW_WORKBENCH_CURRENT_QUESTION_COMPOSER_PLACEMENT === "right_panel_bottom_fixed", "回答输入区应固定在右侧详情区底部");
  assertContract(!INTERVIEW_WORKBENCH_STATE_MACHINE.map(String).includes("waitingAnswer"), "状态机不应再暴露等待回答栏");
  assertContract(String(machineState) !== "waitingAnswer", "无反馈时也不应回退到等待回答栏状态");
  assertContract(!INTERVIEW_WORKBENCH_LAYOUT_AREAS.includes("bottom_composer" as never), "布局不应再包含底部等待回答栏");
}


function test_workbench_ctrl_enter_submits_answer(): void {
  assertContract(INTERVIEW_WORKBENCH_KEYBOARD_SHORTCUTS.send_answer === "Ctrl+Enter", "发送快捷键应登记为 Ctrl+Enter");
  assertContract(INTERVIEW_WORKBENCH_SEND_BUTTON_TOOLTIP === "发送，快捷键 Ctrl + Enter / ⌘ + Enter", "发送按钮 tooltip 应展示 Windows/macOS 快捷键");
  assertContract(shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true }), "Ctrl+Enter 应触发发送");
  assertContract(shouldSubmitAnswerFromKeyboard({ key: "Enter", metaKey: true }), "⌘+Enter 应触发发送");
  assertContract(!shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: false }), "单独 Enter 不应触发发送");
  assertContract(!shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true, shiftKey: true }), "Ctrl+Shift+Enter 不应触发发送");
  assertContract(!shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true, isComposing: true }), "输入法组合态不应触发发送");
  assertContract(canSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true }, true), "允许发送时 Ctrl+Enter 应提交");
  assertContract(canSubmitAnswerFromKeyboard({ key: "Enter", metaKey: true }, true), "允许发送时 ⌘+Enter 应提交");
  assertContract(!canSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true }, false), "禁用发送时 Ctrl+Enter 不应绕过 canSendAnswer");
  assertContract(!canSubmitAnswerFromKeyboard({ key: "Enter", metaKey: true }, false), "禁用发送时 ⌘+Enter 不应绕过 canSendAnswer");
  assertContract(!canSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: false }, true), "普通 Enter 应继续保留换行行为");
}

function test_feedback_card_view_model_uses_contract_payload_sections_and_actions(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_001",
    answer_round: 2,
    answer_text: "我负责 FastAPI 接口编排，并通过错误率和延迟指标验证上线结果。",
    answer_created_at: "2026-05-20T10:10:00Z",
    feedback_text: "结构完整，但技术取舍需要补充替代方案。",
    feedback_id: "fb_001",
    score_result_id: "score_001",
    feedback_created_at: "2026-05-20T10:11:00Z",
    feedback_payload: {
      contract_ids: ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005", "P-POLISH-009"],
      status: "generated",
      feedback_id: "fb_001",
      feedback_text: "结构完整，但技术取舍需要补充替代方案。",
      polish_theme: "mixed",
      polish_theme_label: "混合",
      explicit_weight: 60,
      implicit_weight: 40,
      weight_explanation: "本轮按显性技术 60%、隐性表达 40% 综合打磨。",
      interview_intent: "同时观察技术链路和表达结构。",
      technical_gaps: ["幂等键设计还不够具体"],
      communication_gaps: ["背景压缩可以更短"],
      positive_evidence_points: [
        {
          title: "回答中已有可复用表达",
          evidence_excerpt: "我负责 FastAPI 接口编排",
          dimension_id: "answer_structure",
          trace_id: "trace_should_not_render",
          internal_notes: "internal_should_not_render",
          internal_debug_marker: "fake_should_not_render",
        },
        {
          raw_prompt: "raw_prompt_should_not_render",
          completion: "completion_should_not_render",
          provider_payload: "provider_payload_should_not_render",
          candidate_ref: "candidate_ref_should_not_render",
        },
      ],
      p7_reference_answer: "从 owner 视角补齐状态机、失败兜底和指标复盘。",
      oral_script: "我会先用 30 秒交代背景，再说明我的职责和关键取舍。",
      next_training_suggestions: ["下一轮用 60/40 权重再答一版"],
      mastery_status: "improving",
      score_delta: 8,
      dimension_delta: {
        technical_depth: 6,
        answer_structure: 4,
      },
      improved_points: ["补充接口幂等说明"],
      remaining_gaps: ["失败补偿仍需更具体"],
      repeated_loss_points: ["技术取舍说明不足"],
      regressed_points: [],
      next_retry_focus: [
        {
          focus_area: "失败补偿仍需更具体",
          priority: 1,
          related_dimension: "technical_depth",
          internal_trace_ref: "retry_trace_should_not_render",
        },
      ],
      score_result: {
        score_result_id: "score_001",
        score_type: "polish_answer",
        score_value: 72,
        confidence_level: "medium",
      },
      loss_points: [
        {
          title: "技术取舍说明不足",
          deducted_points: 12,
          reason: "需要说明替代方案、失败路径和验证指标。",
          answer_excerpt: "我负责 FastAPI 接口编排",
        },
      ],
      reference_answer: {
        summary: "先讲业务目标，再讲本人职责、方案取舍和结果指标。",
        outline: ["背景与约束", "关键技术方案", "量化结果"],
      },
      next_recommended_actions: ["provide_more_answer_detail", "generate_next_question"],
      validation_result_ref: { resource_type: "validation_result", resource_id: "val_001" },
      trace_refs: [{ trace_type: "feedback", trace_ref_id: "fb_001" }],
      low_confidence_flags: [{ flag_id: "needs_more_metrics", reason: "missing_metrics" }],
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const contractIds = card.contractIds;
  const visibleCopy = [
    card.title,
    card.status,
    ...card.sections.flatMap((section) => [section.title, ...section.items]),
    ...card.traceItems,
  ].join(" ");
  const lossSection = card.sections.find((section) => section.key === "loss_points");
  const lossTableValues = (lossSection?.tableRows ?? [])
    .map((row) => `${row.severity} ${row.deduction} ${row.issue} ${row.suggestion}`)
    .join(" ");

  assertContract(card.sections.map((section) => section.title).join(",") === "总体点评,打分,得分点,失分点,参考回答,权重说明,面试意图,技术短板,表达短板,高阶参考答案,口语化范本,多次回答改进,下一轮重答重点,下一轮训练建议", "反馈卡应展示 final payload 和结构化反馈模块");
  assertContract(card.contractId === "P-POLISH-003", "反馈卡应保留首个 contract_id 用于调试兜底");
  assertContract(contractIds.includes("P-POLISH-005"), "反馈卡应保留完整 contract_ids 便于 debug");
  assertContract(!visibleCopy.includes("P-POLISH-005"), "反馈卡默认不展示 contract_id raw code");
  assertContract(visibleCopy.includes("72"), "反馈卡应展示 score_result 分值");
  assertContract(visibleCopy.includes("回答中已有可复用表达"), "反馈卡应展示 positive_evidence_points 得分点");
  assertContract(visibleCopy.includes("技术取舍说明不足"), "反馈卡应展示 loss_points");
  assertContract(visibleCopy.includes("先讲业务目标"), "反馈卡应展示 reference_answer");
  assertContract(visibleCopy.includes("显性技术 60%、隐性表达 40%"), "反馈卡应展示权重说明");
  assertContract(visibleCopy.includes("同时观察技术链路和表达结构"), "反馈卡应展示面试意图");
  assertContract(visibleCopy.includes("幂等键设计还不够具体"), "反馈卡应展示技术短板");
  assertContract(visibleCopy.includes("背景压缩可以更短"), "反馈卡应展示表达短板");
  assertContract(visibleCopy.includes("owner 视角"), "反馈卡应展示高阶参考答案");
  assertContract(visibleCopy.includes("30 秒交代背景"), "反馈卡应展示口语化范本");
  assertContract(visibleCopy.includes("分数变化：+8"), "反馈卡应展示 retry score_delta payload");
  assertContract(visibleCopy.includes("已改进：补充接口幂等说明"), "反馈卡应展示 improved_points");
  assertContract(visibleCopy.includes("仍需补齐：失败补偿仍需更具体"), "反馈卡应展示 remaining_gaps");
  assertContract(visibleCopy.includes("重复失分：技术取舍说明不足"), "反馈卡应展示 repeated_loss_points");
  assertContract(visibleCopy.includes("重点：失败补偿仍需更具体"), "反馈卡应展示 next_retry_focus");
  assertContract(visibleCopy.includes("下一轮用 60/40 权重再答一版"), "反馈卡应展示下一轮训练建议");
  assertContract(lossTableValues.includes("主要失分"), "失分表格应展示中文严重程度");
  assertContract(lossTableValues.includes("12"), "失分表格应展示扣分数值");
  assertContract(card.traceItems.length === 0, "反馈卡 view model 不应暴露 trace 引用字段");
  assertContract(!visibleCopy.includes("trace_should_not_render"), "反馈卡不应暴露 trace 字段");
  assertContract(!visibleCopy.includes("internal_should_not_render"), "反馈卡不应暴露 internal 字段");
  assertContract(!visibleCopy.includes("fake_should_not_render"), "反馈卡不应暴露 fake 字段");
  assertContract(!visibleCopy.includes("raw_prompt_should_not_render"), "反馈卡不应暴露 raw prompt 字段");
  assertContract(!visibleCopy.includes("completion_should_not_render"), "反馈卡不应暴露 completion 字段");
  assertContract(!visibleCopy.includes("provider_payload_should_not_render"), "反馈卡不应暴露 provider payload 字段");
  assertContract(!visibleCopy.includes("candidate_ref_should_not_render"), "反馈卡不应暴露 candidate ref 字段");
  assertContract(!visibleCopy.includes("weakness_candidate:weak_001"), "反馈卡不应暴露 candidate ref");
  assertContract(!visibleCopy.includes("feedback:fb_001"), "反馈卡不应暴露 trace_refs");
  assertContract(card.nextActions.join(",") === "provide_more_answer_detail,generate_next_question", "下一步建议应去重并保持 contract enum");
  assertContract(toNextRecommendedActionLabel("provide_more_answer_detail") === "补充回答细节", "contract enum 应映射为按钮文案");
  assertContract(toNextRecommendedActionLabel("generate_next_question") === "生成下一题", "生成下一题 enum 应映射为按钮文案");
}

function test_generated_feedback_card_view_model_shows_phase6_payload_sections(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_phase6",
    answer_round: 3,
    answer_text: "我负责订单系统接口编排，并补齐幂等和回滚策略。",
    answer_created_at: "2026-05-29T10:10:00Z",
    feedback_text: "回答结构清晰，但项目一致性和重复表达需要澄清。",
    feedback_id: "fb_phase6",
    score_result_id: "score_phase6",
    feedback_created_at: "2026-05-29T10:11:00Z",
    feedback_payload: {
      status: "generated",
      feedback_text: "回答结构清晰，但项目一致性和重复表达需要澄清。",
      answer_summary: {
        coverage: "覆盖了接口编排、幂等策略和上线验证。",
        main_gaps: ["缺少项目时间线澄清", "重复使用上一轮缓存表述"],
      },
      score_result: {
        score_type: "polish_answer",
        score_value: 82,
        confidence_level: "high",
      },
      loss_points: [
        {
          loss_point_id: "lp_tradeoff",
          title: "技术取舍说明不足",
          severity: "major",
          deduction: 10,
          reason: "需要比较同步、异步和补偿方案。",
          answer_excerpt: "我补齐幂等和回滚策略",
          related_dimension: "technical_depth",
        },
      ],
      reference_answer: {
        sections: [
          {
            section_id: "sec_tradeoff",
            title: "方案取舍",
            content: "先说明业务目标，再比较同步链路、异步补偿和失败回滚。",
            addresses_loss_point_ids: ["lp_tradeoff"],
          },
        ],
      },
      asset_consistency_check: {
        status: "conflict",
        matched_project_name: "订单履约系统改造",
        conflicts: [
          {
            title: "项目时间线冲突",
            reason: "本轮回答和资产库中的上线月份不一致。",
          },
        ],
        clarification_questions: ["请确认订单履约系统到底在几月上线？"],
      },
      next_recommended_actions: ["retry_same_question", "generate_next_question"],
      raw_prompt: "raw_prompt_should_not_render",
      provider_payload: "provider_payload_should_not_render",
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const visibleCopy = [
    card.status,
    ...card.sections.flatMap((section) => [section.title, ...section.items]),
    ...card.nextActions.map(toNextRecommendedActionLabel),
  ].join(" ");
  const projectConsistencySection = card.sections.find((section) => section.key === "asset_consistency_check");

  assertContract(card.status === "generated", "generated payload 应保持 generated 状态");
  assertContract(visibleCopy.includes("总体点评"), "generated payload 应展示总体点评区块");
  assertContract(visibleCopy.includes("覆盖了接口编排"), "总体点评应展示 answer_summary.coverage");
  assertContract(visibleCopy.includes("主要缺口：缺少项目时间线澄清"), "总体点评应展示 answer_summary.main_gaps");
  assertContract(visibleCopy.includes("分数：82"), "打分应展示 score_result.score_value");
  assertContract(visibleCopy.includes("评分类型：回答打磨"), "打分应展示中文 score_type");
  assertContract(visibleCopy.includes("置信度：high"), "打分应展示 score_result.confidence_level");
  const lossPointsSection = card.sections.find((section) => section.key === "loss_points");
  const lossRows = lossPointsSection?.tableRows ?? [];
  assertContract(lossRows.length === 1, "失分点应保留表格化 rows");
  assertContract(lossRows[0]?.severity === "主要失分", "失分点表格应展示中文严重程度");
  assertContract(lossRows[0]?.deduction === "10", "失分点表格应展示扣分数值");
  assertContract(lossRows[0]?.issue.includes("需要比较同步、异步和补偿方案。"), "失分点表格应保留问题字段");
  assertContract(visibleCopy.includes("方案取舍"), "参考回答应展示 sections");
  assertContract(!visibleCopy.includes("本段修正："), "参考回答不再展示 addresses_loss_point_ids 映射描述");
  assertContract(!visibleCopy.includes("sec_tradeoff"), "参考回答不应展示 section_id");
  assertContract(projectConsistencySection?.tone === "warning", "项目一致性 conflict 应使用 warning 样式");
  assertContract(visibleCopy.includes("需要澄清后再沉淀为资产"), "项目一致性 conflict 应提示先澄清再沉淀");
  assertContract(visibleCopy.includes("请确认订单履约系统到底在几月上线？"), "项目一致性检查应展示 clarification question");
  assertContract(visibleCopy.includes("重答同题"), "下一步建议应复用 action label 映射");
  assertContract(!visibleCopy.includes("已写入资产"), "项目资产更新候选不应伪装为正式资产");
  assertContract(!visibleCopy.includes("确认写入"), "本阶段不应出现确认写资产入口文案");
  assertContract(!visibleCopy.includes("private_note_should_not_render"), "反馈卡不应暴露 private 字段");
  assertContract(!visibleCopy.includes("raw_prompt_should_not_render"), "反馈卡不应暴露 raw prompt");
  assertContract(!visibleCopy.includes("provider_payload_should_not_render"), "反馈卡不应暴露 provider payload");
}

function test_map_feedback_code_to_display_to_chinese_by_default(): void {
  assertContract(mapFeedbackCodeToDisplay("polish_answ").text === "回答打磨", "polish_answ 应映射为中文");
  assertContract(mapFeedbackCodeToDisplay("major").text === "主要失分", "major 应映射为中文");
  assertContract(
    mapFeedbackCodeToDisplay("insufficient_asset_context").text ===
      "项目素材不足，回答与资产库证据不够一致",
    "insufficient_asset_context 应映射为中文",
  );
  assertContract(mapFeedbackCodeToDisplay("P-POLISH-003").text === "未知状态", "原始代码应有未知状态兜底");
}

function test_feedback_card_view_model_hides_raw_feedback_codes(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_code_guard",
    answer_round: 1,
    answer_text: "我会先说明背景再给出技术策略。",
    answer_created_at: "2026-06-02T09:00:00Z",
    feedback_text: "结构完整，但仍有表达改进空间。",
    feedback_id: "fb_raw_codes",
    score_result_id: "score_raw_codes",
    feedback_created_at: "2026-06-02T09:01:00Z",
    feedback_payload: {
      contract_ids: ["P-POLISH-003", "P-POLISH-004"],
      status: "generated",
      feedback_text: "结构完整，但仍有表达改进空间。",
      score_result: {
        score_type: "polish_answ",
        score_value: 75,
        confidence_level: "medium",
      },
      loss_points: [
        {
          severity: "major",
          deduction: 5,
          reason: "表达层次有待梳理。",
        },
      ],
      asset_consistency_check: {
        status: "insufficient_asset_context",
      },
      next_recommended_actions: ["generate_next_question"],
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const visibleCopy = [
    card.title,
    card.status,
    ...card.sections.flatMap((section) => [section.title, ...section.items]),
    ...card.nextActions.map(toNextRecommendedActionLabel),
    ...(card.sections.find((section) => section.key === "loss_points")?.tableRows
      ?.map((row) => `${row.severity} ${row.deduction} ${row.issue}`) ?? []),
  ].join(" ");
  const hasContractId = visibleCopy.includes("P-POLISH-003") || visibleCopy.includes("P-POLISH-004");

  assertContract(!hasContractId, "反馈卡默认不直接展示 contract_id");
  assertContract(!visibleCopy.includes("polish_answ"), "反馈卡默认不展示 score_type raw code");
  assertContract(!visibleCopy.includes("major"), "反馈卡默认不展示 severity raw code");
  assertContract(!visibleCopy.includes("insufficient_asset_context"), "反馈卡默认不展示 consistency raw code");
  assertContract(visibleCopy.includes("评分类型：回答打磨"), "评分类型应显示中文文案");
  assertContract(visibleCopy.includes("主要失分"), "失分点严重程度应显示中文文案");
}

function test_feedback_card_view_model_renders_loss_points_as_table_rows(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_loss_table",
    answer_round: 2,
    answer_text: "我会先讲需求，再设计方案。",
    answer_created_at: "2026-06-02T10:00:00Z",
    feedback_text: "可以更完整地覆盖关键权衡。",
    feedback_id: "fb_loss_table",
    score_result_id: "score_loss_table",
    feedback_created_at: "2026-06-02T10:01:00Z",
    feedback_payload: {
      status: "generated",
      loss_points: [
        {
          severity: "major",
          deduction: 9,
          reason: "缺少方案对比。",
          suggestion: "补充优缺点对比。",
        },
        {
          severity: "minor",
          deduction: 3,
          reason: "措辞仍偏复杂。",
          suggestion: "补充一句简短总结。",
        },
      ],
      score_result: null,
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const lossSection = card.sections.find((section) => section.key === "loss_points");
  const rows = lossSection?.tableRows ?? [];
  const rowsCopy = rows
    .map((row) => `${row.index}-${row.severity}-${row.deduction}-${row.issue}-${row.suggestion}`)
    .join(" ");

  assertContract(rows.length === 2, "多条 loss_points 应渲染为 2 条表格行");
  assertContract(rows[0]?.index === 1, "loss_points 表格行应保留序号");
  assertContract(rows[0]?.severity === "主要失分", "第一条严重程度应中文");
  assertContract(rows[0]?.deduction === "9", "第一条扣分应展示数值");
  assertContract(rows[1]?.severity === "轻微失分", "第二条严重程度应中文");
  assertContract(rows[1]?.deduction === "3", "第二条扣分应展示数值");
  assertContract(rowsCopy.includes("缺少方案对比。"), "修正建议/问题应显示");
  assertContract(rowsCopy.includes("补充优缺点对比。"), "修正建议字段应显示");
}

function test_feedback_card_reference_answer_sections_assemble_to_paragraphs(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_reference_sections",
    answer_round: 1,
    answer_text: "这是一道结构化问题。",
    answer_created_at: "2026-06-02T11:00:00Z",
    feedback_text: "参考回答可直接复述。",
    feedback_id: "fb_reference_sections",
    score_result_id: null,
    feedback_created_at: "2026-06-02T11:01:00Z",
    feedback_payload: {
      status: "generated",
      reference_answer: {
        summary: "先说明动机，再给出实现步骤。",
        sections: [
          { section_id: "s1", title: "背景", content: "从岗位需求出发。" },
          { section_id: "s2", content: "给出可执行的解决方案。" },
        ],
      },
      score_result: null,
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const referenceSection = card.sections.find((section) => section.key === "reference_answer");
  const items = referenceSection?.items ?? [];
  const sectionText = items.join(" ");

  assertContract(referenceSection !== undefined, "应生成参考回答区块");
  assertContract(sectionText.includes("先说明动机"), "参考回答应优先展示 summary");
  assertContract(sectionText.includes("背景：从岗位需求出发。"), "参考回答 sections 应拼接为正文");
  assertContract(sectionText.includes("给出可执行的解决方案。"), "参考回答可包含仅 content 的 section");
  assertContract(!sectionText.includes("section_id"), "参考回答不应展示 section_id");
  assertContract(!sectionText.includes("s1"), "参考回答不应展示 section_id 符号");
}

function test_generated_feedback_card_view_model_handles_missing_phase6_fields(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_sparse_generated",
    answer_round: 1,
    answer_text: "回答已保存。",
    answer_created_at: "2026-05-29T10:00:00Z",
    feedback_text: "",
    feedback_id: "fb_sparse",
    score_result_id: null,
    feedback_created_at: "2026-05-29T10:01:00Z",
    feedback_payload: {
      status: "generated",
      feedback_text: "后端只返回了总体点评。",
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const visibleCopy = card.sections.flatMap((section) => [section.title, ...section.items]).join(" ");

  assertContract(visibleCopy.includes("后端只返回了总体点评"), "generated payload 缺字段时仍应展示已有反馈");
  assertContract(visibleCopy.includes("暂无打分结果"), "generated payload 缺 score_result 时应展示稳定空态");
}

function test_candidate_review_view_model_keeps_candidate_review_user_visible_and_action_only(): void {
  const candidates: PolishCandidate[] = [
    {
      candidate_id: "cand_weak_001",
      candidate_type: "weakness_candidate",
      status: "candidate",
      title: "指标表达薄弱",
      summary: "回答缺少上线指标和验证方式。",
      evidence_excerpt: "没有说明延迟、错误率或告警结果。",
      confidence_level: "medium",
      answer_id: "ans_feedback_001",
      feedback_id: "fb_001",
      merge_target_candidate_id: "cand_weak_existing",
      trace_refs: [{ trace_ref_id: "trace_should_not_render", trace_type: "feedback", created_at: "2026-05-22T10:00:00Z" }],
      candidate_payload: {
        raw_prompt: "raw_prompt_should_not_render",
        completion: "completion_should_not_render",
        provider_payload: "provider_payload_should_not_render",
        hidden_rubric: "hidden_rubric_should_not_render",
        secret: "secret_should_not_render",
      },
    },
    {
      candidate_id: "cand_asset_001",
      candidate_type: "asset_candidate",
      status: "confirmed",
      title: "可复用项目表达",
      summary: "已经由后端确认并写入正式资产。",
      confidence_level: "high",
      answer_id: "ans_feedback_001",
      feedback_id: "fb_001",
    },
  ];

  const viewModel = buildCandidateReviewViewModel(candidates);
  const emptyViewModel = buildCandidateReviewViewModel(undefined);
  const visibleCopy = viewModel.items
    .flatMap((item) => [
      item.candidateId,
      item.typeLabel,
      item.statusLabel,
      item.title,
      item.summary,
      item.evidenceExcerpt,
      item.confidenceLabel,
      item.mergeHint,
    ])
    .join(" ");

  assertContract(emptyViewModel.items.length === 0, "旧 session 没有 candidates 时不应崩溃");
  assertContract(viewModel.items.length === 2, "候选确认入口应展示 answer 关联 candidates");
  assertContract(viewModel.pendingCount === 1, "candidate 状态应进入待确认计数");
  assertContract(viewModel.settledCount === 1, "confirmed 状态应进入已处理计数");
  assertContract(viewModel.items[0].typeLabel === "薄弱项候选", "candidate type 应映射为用户可读文案");
  assertContract(viewModel.items[0].statusLabel === "待确认", "candidate status 应映射为用户可读文案");
  assertContract(viewModel.items[0].canConfirm, "待确认 candidate 应允许调用后端 confirm endpoint");
  assertContract(viewModel.items[0].canDismiss, "待确认 candidate 应允许调用后端 dismiss endpoint");
  assertContract(!viewModel.items[1].canConfirm, "已确认 candidate 不应再次展示确认动作");
  assertContract(!viewModel.items[1].canDismiss, "已确认 candidate 不应再次展示忽略动作");
  assertContract(String(viewModel.mergeHint).includes("合并"), "后端支持 merge 时应展示基础合并提示");
  assertContract(visibleCopy.includes("指标表达薄弱"), "候选确认入口应展示标题");
  assertContract(visibleCopy.includes("回答缺少上线指标"), "候选确认入口应展示摘要");
  assertContract(visibleCopy.includes("没有说明延迟"), "候选确认入口应展示用户可见证据片段");
  assertContract(!visibleCopy.includes("trace_should_not_render"), "候选确认入口不应暴露 internal trace");
  assertContract(!visibleCopy.includes("raw_prompt_should_not_render"), "候选确认入口不应暴露 raw prompt");
  assertContract(!visibleCopy.includes("completion_should_not_render"), "候选确认入口不应暴露 completion");
  assertContract(!visibleCopy.includes("provider_payload_should_not_render"), "候选确认入口不应暴露 provider payload");
  assertContract(!visibleCopy.includes("hidden_rubric_should_not_render"), "候选确认入口不应暴露 hidden rubric");
  assertContract(!visibleCopy.includes("secret_should_not_render"), "候选确认入口不应暴露 secret");
  assertContract(POLISH_API_PATHS.candidates === "/polish-candidates", "候选列表必须调用后端 candidate list endpoint");
  assertContract(
    POLISH_API_PATHS.confirmCandidate("cand_weak_001") === "/polish-candidates/cand_weak_001/confirm",
    "确认操作必须调用后端 confirm endpoint",
  );
  assertContract(
    POLISH_API_PATHS.dismissCandidate("cand_weak_001") === "/polish-candidates/cand_weak_001/dismiss",
    "忽略操作必须调用后端 dismiss endpoint",
  );
}

function test_feedback_card_view_model_hides_theme_sections_for_legacy_payload(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_legacy",
    answer_round: 1,
    answer_text: "我负责接口改造，并说明了上线结果。",
    answer_created_at: "2026-05-20T10:00:00Z",
    feedback_text: "旧版反馈仍应可展示。",
    feedback_id: "fb_legacy",
    score_result_id: null,
    feedback_created_at: "2026-05-20T10:01:00Z",
    feedback_payload: {
      contract_ids: ["P-POLISH-005"],
      status: "generated",
      feedback_id: "fb_legacy",
      feedback_text: "旧版反馈仍应可展示。",
      score_result: {
        score_result_id: "score_legacy",
        score_type: "polish_answer",
        score_value: 68,
        confidence_level: "medium",
      },
      loss_points: [
        {
          title: "旧失分点",
          deducted_points: 8,
          reason: "旧 payload 仍可展示失分原因。",
        },
      ],
      reference_answer: {
        summary: "旧参考回答摘要。",
        outline: ["先说结论", "补充证据"],
      },
      next_recommended_actions: ["generate_next_question"],
      validation_result_ref: null,
      trace_refs: [],
      low_confidence_flags: [],
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const titles = card.sections.map((section) => section.title);
  const visibleCopy = card.sections.flatMap((section) => [section.title, ...section.items]).join(" ");

  assertContract(titles.includes("总体点评"), "旧 payload 应继续展示旧反馈区块");
  assertContract(visibleCopy.includes("旧版反馈仍应可展示"), "旧 payload 应继续展示 feedback_text");
  assertContract(visibleCopy.includes("68"), "旧 payload 应继续展示 score_result");
  assertContract(visibleCopy.includes("旧失分点"), "旧 payload 应继续展示 loss_points");
  assertContract(visibleCopy.includes("旧参考回答摘要"), "旧 payload 应继续展示 reference_answer");
  assertContract(!titles.includes("得分点"), "旧 payload 缺 positive_evidence_points 时不应展示得分点空区块");
  assertContract(!titles.includes("权重说明"), "旧 payload 缺主题字段时不应展示权重说明");
  assertContract(!titles.includes("面试意图"), "旧 payload 缺主题字段时不应展示面试意图");
  assertContract(!titles.includes("技术短板"), "旧 payload 缺主题字段时不应展示技术短板");
  assertContract(!titles.includes("表达短板"), "旧 payload 缺主题字段时不应展示表达短板");
  assertContract(!titles.includes("高阶参考答案"), "旧 payload 缺 p7_reference_answer 时不应展示高阶参考答案空区块");
  assertContract(!titles.includes("口语化范本"), "旧 payload 缺 oral_script 时不应展示口语化范本空区块");
  assertContract(!titles.includes("多次回答改进"), "旧 payload 缺 retry delta 时不应展示多次回答改进空区块");
  assertContract(!titles.includes("下一轮重答重点"), "旧 payload 缺 next_retry_focus 时不应展示下一轮重答重点空区块");
  assertContract(card.nextActions.join(",") === "generate_next_question", "旧 payload 应继续保留下一步 action");
}

function test_feedback_card_view_model_handles_pending_payload(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_pending",
    answer_round: 1,
    answer_text: "回答已保存，反馈仍在生成。",
    answer_created_at: "2026-05-20T10:00:00Z",
    feedback_text: "",
    feedback_id: null,
    score_result_id: null,
    feedback_created_at: null,
    feedback_payload: {
      status: "pending",
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const titles = card.sections.map((section) => section.title);
  const visibleCopy = card.sections.flatMap((section) => [section.title, ...section.items]).join(" ");

  assertContract(card.status === "pending", "pending payload 应保持 pending 状态");
  assertContract(visibleCopy.includes("本轮反馈尚未生成"), "pending payload 缺 feedback_text 时应使用稳定 fallback");
  assertContract(visibleCopy.includes("暂无打分结果"), "pending payload 缺 score_result 时不应崩溃");
  assertContract(!titles.includes("得分点"), "pending payload 不应展示空得分点");
  assertContract(!titles.includes("高阶参考答案"), "pending payload 不应展示空高阶参考答案");
  assertContract(!titles.includes("口语化范本"), "pending payload 不应展示空口语化范本");
  assertContract(!titles.includes("多次回答改进"), "pending payload 不应展示空 retry delta");
  assertContract(!titles.includes("下一轮重答重点"), "pending payload 不应展示空下一轮重答重点");
}

function test_feedback_card_view_model_handles_failed_payload(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_failed",
    answer_round: 1,
    answer_text: "回答已保存，但真实 provider 超时。",
    answer_created_at: "2026-05-30T10:00:00Z",
    feedback_text: "反馈生成失败，可重试",
    feedback_id: null,
    score_result_id: null,
    feedback_created_at: null,
    feedback_payload: {
      status: "failed",
      feedback_text: "反馈生成失败，可重试",
      user_visible_status: "反馈生成失败，可重试",
      retryable: true,
      validation_errors: ["llm_transport_timeout"],
      error: {
        code: "llm_transport_timeout",
        metadata: {
          provider_payload: "provider_payload_should_not_render",
          raw_prompt: "raw_prompt_should_not_render",
        },
      },
      score_result: null,
      loss_points: [],
      reference_answer: null,
      raw_provider_payload: "raw_provider_payload_should_not_render",
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const titles = card.sections.map((section) => section.title);
  const visibleCopy = [
    card.title,
    card.status,
    ...card.sections.flatMap((section) => [section.title, ...section.items]),
    ...card.nextActions.map(toNextRecommendedActionLabel),
  ].join(" ");

  assertContract(card.status === "failed", "failed payload 应保持失败态");
  assertContract(card.title === "反馈生成失败", "失败反馈卡标题应明确展示反馈生成失败");
  assertContract(titles.join(",") === "失败状态", "failed 不应展开打分/失分点/参考回答等空 section");
  assertContract(visibleCopy.includes("反馈生成超时或失败，可重试"), "失败态应展示可重试提示");
  assertContract(visibleCopy.includes("错误码：llm_transport_timeout"), "失败态应展示简要 validation error");
  assertContract(visibleCopy.includes("可重试：是"), "retryable=true 时应提示可重试");
  assertContract(!visibleCopy.includes("本轮反馈尚未生成"), "failed 不应展示 pending 空态");
  assertContract(!visibleCopy.includes("暂无打分结果"), "failed 不应展示空打分 section");
  assertContract(!visibleCopy.includes("暂无明确失分点"), "failed 不应展示空失分点 section");
  assertContract(!visibleCopy.includes("暂无参考回答"), "failed 不应展示空参考回答 section");
  assertContract(!visibleCopy.includes("provider_payload_should_not_render"), "失败态不应暴露 provider payload");
  assertContract(!visibleCopy.includes("raw_prompt_should_not_render"), "失败态不应暴露 raw prompt");
  assertContract(!visibleCopy.includes("raw_provider_payload_should_not_render"), "失败态不应暴露 raw provider payload");
}

function test_feedback_card_view_model_does_not_calculate_score_on_frontend(): void {
  const answer: PolishSessionAnswer = {
    answer_id: "ans_feedback_score_calc",
    answer_round: 1,
    answer_text: "回答文本。",
    answer_created_at: "2026-05-20T10:00:00Z",
    feedback_text: "只展示后端 payload。",
    feedback_id: "fb_score_calc",
    score_result_id: null,
    feedback_created_at: "2026-05-20T10:01:00Z",
  feedback_payload: {
      status: "generated",
      feedback_text: "只展示后端 payload。",
      score_result: null,
      next_recommended_actions: [],
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const scoreSection = card.sections.find((section) => section.key === "score");
  const visibleCopy = card.sections.flatMap((section) => [section.title, ...section.items]).join(" ");

  assertContract(scoreSection?.items.join(",") === "暂无打分结果", "无 score_result 时不应由前端计算综合分");
  assertContract(!visibleCopy.includes("显性技术得分"), "无 score_result 时不应展示显性分字段");
  assertContract(!visibleCopy.includes("隐性表达得分"), "无 score_result 时不应展示隐性分字段");
  assertContract(!visibleCopy.includes("分数："), "无 score_result 时不应展示前端计算综合分");
}

function test_clipboard_markdown_stays_compatible_with_structured_feedback_payload(): void {
  const session: PolishSessionDetail = {
    ...buildTestSession([
      buildTestProgressNode("node_clipboard", "剪贴板兼容节点", "resume_deep_dive", "深度打磨类"),
    ], "node_clipboard"),
    session_id: "ses_clipboard_structured",
    turns: [
      {
        question_id: "q_clipboard",
        question_text: "请说明结构化反馈如何复制。",
        question_sources: [],
        question_created_at: "2026-05-20T10:00:00Z",
        progress_node_ref: "node_clipboard",
        answers: [
          {
            answer_id: "ans_clipboard",
            answer_round: 1,
            answer_text: "我会保持用户可见反馈文本兼容。",
            answer_created_at: "2026-05-20T10:01:00Z",
            feedback_text: "结构化反馈用户可见文本。",
            feedback_id: "fb_clipboard",
            score_result_id: "score_clipboard",
            feedback_created_at: "2026-05-20T10:02:00Z",
            feedback_payload: {
              status: "generated",
              feedback_text: "结构化反馈用户可见文本。",
              positive_evidence_points: [
                {
                  title: "已有清晰结论",
                  evidence_excerpt: "保持用户可见反馈文本兼容",
                },
              ],
              p7_reference_answer: "高阶参考答案仍留在 card view model 中展示。",
              oral_script: "口语化范本仍留在 card view model 中展示。",
              next_recommended_actions: [],
            },
          },
        ],
      },
    ],
  };

  const markdown = buildPolishSessionClipboardMarkdown(session);

  assertContract(markdown.includes("### 题目正文"), "clipboard markdown 应继续包含题干分区");
  assertContract(markdown.includes("请说明结构化反馈如何复制。"), "clipboard markdown 应继续包含题干");
  assertContract(markdown.includes("我会保持用户可见反馈文本兼容。"), "clipboard markdown 应继续包含回答文本");
  assertContract(markdown.includes("结构化反馈用户可见文本。"), "clipboard markdown 应继续使用 feedback_text");
  assertContract(!markdown.includes("positive_evidence_points"), "clipboard markdown 不应泄漏结构化字段名");
}

function test_session_clipboard_markdown_includes_full_context_tree_and_all_questions(): void {
  const parentNode: TestProgressTreeNode = {
    ...buildTestProgressNode("node_parent_clipboard", "混合检索与幻觉控制", "resume_deep_dive", "深度打磨类"),
    children: [
      buildTestProgressNode("node_question_one", "混合检索策略设计", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_question_two", "Prompt工程与幻觉控制", "resume_deep_dive", "深度打磨类"),
    ],
  };
  const session: PolishSessionDetail = {
    ...buildTestSession([parentNode], "node_question_one"),
    session_status: "active",
    progress_percent: 50,
    progress_tree_state: {
      ...buildTestSession([parentNode], "node_question_one").progress_tree_state,
      node_states: [
        {
          progress_node_ref: "node_parent_clipboard",
          status: "in_progress",
          completed_questions_count: 0,
          latest_feedback_summary: null,
        },
        {
          progress_node_ref: "node_question_one",
          status: "in_progress",
          completed_questions_count: 0,
          latest_feedback_summary: null,
        },
        {
          progress_node_ref: "node_question_two",
          status: "pending",
          completed_questions_count: 0,
          latest_feedback_summary: null,
        },
      ],
      current_priority: {
        progress_node_ref: "node_question_one",
        title: "混合检索策略设计",
        expected_capability: "混合检索策略设计能力",
      },
      progress: { progress_percent: 50 },
    },
    turns: [
      {
        question_id: "q_one",
        question_text: "请完整说明混合检索策略如何设计。",
        question_sources: [],
        question_created_at: "2026-05-21T10:00:00Z",
        progress_node_ref: "node_question_one",
        evidence_refs: [],
        context_digest: "digest-one",
        answers: [
          {
            answer_id: "ans_one",
            answer_round: 1,
            answer_text: "先多路召回，再重排，并按指标监控。",
            answer_created_at: "2026-05-21T10:01:00Z",
            feedback_text: "需要补充失败兜底。",
            feedback_id: "fb_one",
            score_result_id: null,
            feedback_created_at: "2026-05-21T10:02:00Z",
          },
        ],
      },
      {
        question_id: "q_two",
        question_text: "请完整说明 Prompt 幻觉控制方案。",
        question_sources: [],
        question_created_at: "2026-05-21T10:03:00Z",
        progress_node_ref: "node_question_two",
        evidence_refs: [],
        context_digest: "digest-two",
        answers: [],
      },
    ],
  };
  const markdown = buildPolishSessionClipboardMarkdown(session);

  assertContract(markdown.includes("# 模拟面试基本信息"), "顶部复制应包含模拟面试基本信息");
  assertContract(markdown.includes("# 进展树"), "顶部复制应包含进展树");
  assertContract(markdown.includes("# 题目信息"), "顶部复制应包含题目信息");
  assertContract(markdown.includes("当前模拟面试状态：进行中"), "基本信息应包含模拟面试状态");
  assertContract(markdown.includes("复制时间："), "基本信息应包含复制时间");
  assertContract(markdown.includes("- 深度打磨类 · 进行中"), "进展树应包含分类节点和状态");
  assertContract(markdown.includes("  - 混合检索与幻觉控制 · 进行中"), "进展树应保留层级关系");
  assertContract(markdown.includes("    - 混合检索策略设计 · 进行中 · 当前优先"), "进展树应标记当前优先节点");
  assertContract(markdown.includes("      - 题目 1 · 进行中"), "进展树应包含题目节点");
  assertContract(markdown.includes("    - Prompt工程与幻觉控制 · 未开始"), "进展树不应丢失折叠状态下的数据节点");
  assertContract(markdown.includes("## 题目 1：混合检索策略设计"), "题目信息应包含第一题");
  assertContract(markdown.includes("## 题目 2：Prompt工程与幻觉控制"), "题目信息应包含第二题而不是只复制当前题");
  assertContract(markdown.includes("请完整说明混合检索策略如何设计。"), "题目信息应包含第一题完整正文");
  assertContract(markdown.includes("请完整说明 Prompt 幻觉控制方案。"), "题目信息应包含第二题完整正文");
  assertContract(markdown.includes("先多路召回，再重排，并按指标监控。"), "题目信息应包含已有回答");
  assertContract(markdown.includes("本轮反馈尚未生成"), "题目信息应包含无反馈占位");
  assertContract(!markdown.startsWith("# 模拟面试内容\n\n岗位："), "顶部复制不应保留旧短格式作为主结构");
}

function test_progress_node_context_banner_ignores_group_header_click(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_real_context", "真实节点", "resume_deep_dive", "深度打磨类"),
      depth_goal: "真实节点目标",
    },
  ], "node_real_context");
  const groupHeader = buildWorkbenchProgressNodes(session)[0];
  const nextSelectedRef = resolveProgressTreeSelectedNodeRefAfterClick(groupHeader, "node_real_context");
  const bannerContent = buildProgressTreeContextBannerContent(session, nextSelectedRef);

  assertContract(getWorkbenchProgressNodeQuestionTargetRef(groupHeader) === null, "分类 header 不应成为生成题目目标");
  assertContract(nextSelectedRef === "node_real_context", "点击分类 header 不应切换当前上下文节点");
  assertContract(bannerContent.title === "真实节点", "分类 header 不应覆盖公告条节点名称");
  assertContract(bannerContent.depthRequirement === "真实节点目标", "分类 header 不应覆盖公告条深度要求");
}

function test_progress_node_context_banner_uses_safe_copy(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_safe_banner", "P7 经历真实性与贡献拷问", "resume_deep_dive", "深度打磨类"),
      display_title: "P7 经历真实性与贡献拷问",
      depth_goal: "攻击项目边界并压迫细节，准备杀招避免必挂",
    },
  ]);
  const bannerContent = buildProgressTreeContextBannerContent(session, "node_safe_banner");
  const visibleCopy = [bannerContent.title, bannerContent.depthRequirement].join(" ");

  for (const forbiddenCopy of ["P7", "攻击", "拷问", "碾压", "吊打", "火力", "红队", "必挂", "必过", "压迫", "击穿", "杀招"]) {
    assertContract(!visibleCopy.includes(forbiddenCopy), `公告条不应出现禁用词 ${forbiddenCopy}`);
  }
  assertContract(visibleCopy.includes("高阶 经历真实性与贡献边界"), "公告条标题应使用中性化表达");
  assertContract(visibleCopy.includes("追问项目边界并连续追问细节，准备关键方法避免风险较高"), "公告条深度要求应使用中性化表达");
}

function test_progress_tree_detail_uses_display_safe_copy(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_safe_copy", "经历真实性与贡献拷问", "resume_deep_dive", "深度打磨类"),
      display_title: "经历真实性与贡献拷问",
      depth_goal: "攻击项目边界",
      follow_up_focus: ["碾压技术细节"],
      common_loss_risks: ["必挂表达"],
    },
  ]);
  const detail = buildProgressTreeNodeDetailViewModel(session, "node_safe_copy");
  const visibleCopy = [
    detail?.title,
    detail?.depthRequirement,
    ...((detail?.followUpDirections ?? [])),
    ...((detail?.lossRisks ?? [])),
  ].join(" ");

  assertContract(!visibleCopy.includes("拷问"), "页面展示不应出现拷问");
  assertContract(!visibleCopy.includes("攻击"), "页面展示不应出现攻击");
  assertContract(!visibleCopy.includes("碾压"), "页面展示不应出现碾压");
  assertContract(!visibleCopy.includes("必挂"), "页面展示不应出现必挂");
  assertContract(visibleCopy.includes("经历真实性与贡献边界"), "页面展示应替换为经历真实性与贡献边界");
  assertContract(visibleCopy.includes("追问项目边界"), "页面展示应替换攻击为追问");
  assertContract(visibleCopy.includes("深挖技术细节"), "页面展示应替换碾压为深挖");
  assertContract(visibleCopy.includes("风险较高表达"), "页面展示应替换必挂为风险较高");
  assertContract(normalizeProgressTreeDetailCopy("P7 红队压迫") === "高阶 反向检验连续追问", "详情文案应统一中性化");
}

function test_progress_tree_display_safe_copy_still_applies(): void {
  const session = buildTestSession([
    {
      ...buildTestProgressNode("node_safe_copy", "P7 经历真实性与贡献拷问", "resume_deep_dive", "深度打磨类"),
      display_title: "P7 经历真实性与贡献拷问",
      depth_goal: "攻击项目边界并压迫细节",
      follow_up_focus: ["碾压技术细节"],
      common_loss_risks: ["必挂表达"],
      expected_answer_signals: ["必过表达"],
    },
  ]);
  const detail = buildProgressTreeNodeDetailViewModel(session, "node_safe_copy");
  const visibleCopy = [
    detail?.title,
    detail?.depthRequirement,
    ...((detail?.followUpDirections ?? [])),
    ...((detail?.lossRisks ?? [])),
    ...((detail?.answerSignals ?? [])),
  ].join(" ");

  for (const forbiddenCopy of ["P7", "攻击", "拷问", "碾压", "压迫", "必挂", "必过"]) {
    assertContract(!visibleCopy.includes(forbiddenCopy), `页面展示不应出现 ${forbiddenCopy}`);
  }
  assertContract(visibleCopy.includes("高阶 经历真实性与贡献边界"), "页面展示应替换 P7 和拷问");
  assertContract(visibleCopy.includes("追问项目边界并连续追问细节"), "页面展示应替换攻击和压迫");
  assertContract(visibleCopy.includes("深挖技术细节"), "页面展示应替换碾压");
  assertContract(visibleCopy.includes("风险较高表达"), "页面展示应替换必挂");
  assertContract(visibleCopy.includes("准备较充分表达"), "页面展示应替换必过");
}

function test_progress_tree_detail_handles_missing_optional_fields(): void {
  const session = buildTestSession([
    {
      progress_node_ref: "node_missing_fields",
      title: "缺字段节点",
      expected_capability: "",
      related_job_requirements: [],
      related_resume_evidence: [],
      missing_points: [],
      children: [],
    },
  ]);
  const detail = buildProgressTreeNodeDetailViewModel(session, "node_missing_fields");
  const visibleCopy = [
    detail?.title ?? "",
    detail?.emptyDescription ?? "",
    detail?.depthRequirement ?? "",
    detail?.firstQuestion ?? "",
    ...((detail?.followUpDirections ?? [])),
    ...((detail?.answerSignals ?? [])),
    ...((detail?.lossRisks ?? [])),
    ...((detail?.resumeEvidence ?? [])),
    ...((detail?.jobEvidence ?? [])),
  ].join(" ");

  assertContract(detail?.hasAnyDetail === false, "缺少详情字段时应识别为空详情");
  assertContract(visibleCopy.includes("该节点暂无完整详情，可先生成题目继续打磨。"), "缺字段节点应显示合理 fallback 文案");
  assertContract(!visibleCopy.includes("undefined"), "缺字段节点不应显示 undefined");
  assertContract(!visibleCopy.includes("null"), "缺字段节点不应显示 null");
}

function test_progress_tree_group_headers_default_expanded_for_collapse_control(): void {
  const groupedNodes = buildWorkbenchProgressNodes(
    buildTestSession([
      buildTestProgressNode("node_resume_1", "智能辅助平台架构", "resume_deep_dive", "深度打磨类"),
      buildTestProgressNode("node_gap_1", "AI Agent 规划机制", "jd_gap_learning", "补齐学习类"),
    ]),
  );
  const expandedKeys = collectDefaultExpandedProgressNodeKeys(groupedNodes);

  assertContract(expandedKeys.includes("progress-group:深度打磨类"), "深度打磨类应默认展开并支持折叠");
  assertContract(expandedKeys.includes("progress-group:补齐学习类"), "补齐学习类应默认展开并支持折叠");
}

function test_progress_tree_uses_progress_node_ref_as_key_and_priority_match(): void {
  const groupedNodes = buildWorkbenchProgressNodes(
    buildTestSession(
      [
        buildTestProgressNode("node_same_title_a", "Java 服务端架构", "resume_deep_dive", "深度打磨类"),
        buildTestProgressNode("node_same_title_b", "Java 服务端架构", "resume_deep_dive", "深度打磨类"),
      ],
      "node_same_title_b",
    ),
  );
  const groupHeader = groupedNodes[0];
  const realNodes = groupHeader.children ?? [];
  const currentKey = resolveCurrentWorkbenchProgressNodeKey(groupedNodes);

  assertContract(groupHeader.key !== "node_same_title_b", "分类标题不应复用真实节点 key");
  assertContract(realNodes.map((node) => node.key).join(",") === "node_same_title_a,node_same_title_b", "真实节点 key 必须使用 progress_node_ref");
  assertContract(currentKey === "node_same_title_b", "current priority 应只匹配对应真实节点");
}

function test_interview_topic_title_neutralizes_interrogation_copy(): void {
  assertContract(
    normalizeInterviewTopicTitle("经历真实性与贡献拷问") === "经历真实性与贡献边界",
    "主题标题应使用中性化文案",
  );
}

test_interview_list_toolbar_uses_shared_actions_and_search();
test_interview_list_actions_cover_report_end_and_soft_delete();
test_progress_tree_groups_flat_nodes_by_display_category_title();
test_progress_tree_group_header_is_not_question_target();
test_progress_tree_group_headers_default_expanded_for_collapse_control();
test_progress_tree_uses_progress_node_ref_as_key_and_priority_match();
test_interview_topic_title_neutralizes_interrogation_copy();
test_progress_node_context_renders_as_compact_banner();
test_progress_tree_context_banner_shows_technical_coverage_from_children();
test_progress_tree_context_banner_shows_technical_coverage_points_without_children();
test_progress_tree_left_list_stays_compact();
test_progress_tree_detail_defaults_to_latest_turn_node();
test_progress_tree_group_header_does_not_show_node_detail();
test_progress_tree_category_header_is_group_only();
test_progress_node_context_banner_defaults_to_latest_turn_node();
test_progress_node_context_banner_updates_when_node_selected();
test_progress_node_context_banner_hides_question_and_detail_lists();
test_workbench_hero_actions_are_icon_only_and_copy_session_content();
test_progress_tree_node_status_uses_row_trailing_lights();
test_progress_node_context_banner_supports_expand_toggle_for_depth();
test_workbench_chat_bubble_alignment_keeps_system_left_and_user_right();
test_question_node_clipboard_includes_full_question_answer_and_feedback();
test_question_node_clipboard_uses_answer_and_feedback_placeholders();
test_workbench_ctrl_enter_submits_answer();
test_waiting_answer_bar_is_removed_from_workbench_contract();
test_workbench_chat_auto_scroll_trigger_changes_on_focus_and_feedback();
test_workbench_chat_auto_scroll_respects_manual_scroll_when_question_not_changed();
test_workbench_sticky_header_view_model_matches_current_question_context();
test_workbench_sticky_question_text_collapse_behavior();
  test_progress_tree_pending_and_failed_states_use_generation_action();
  test_progress_tree_click_auto_generates_only_for_nodes_without_question();
  test_workbench_question_actions_follow_current_question_status();
  test_workbench_composer_primary_button_stays_send_for_selected_question();
  test_workbench_composer_send_remains_retry_when_question_has_answer();
  test_workbench_composer_follow_up_disabled_without_history_or_contract();
  test_workbench_composer_regenerate_available_for_current_question_without_completion();
  test_workbench_composer_regenerate_for_node_without_selected_question_and_no_node_ref();
  test_workbench_composer_regenerate_preserves_draft_guard();
  test_workbench_composer_mark_completed_and_regenerate_confirmation_gate();
  test_progress_tree_context_menu_items_follow_question_action_state();
test_progress_tree_context_menu_closes_on_escape_and_external_events();
test_progress_tree_question_entry_is_selectable_by_node_type();
test_progress_tree_click_focuses_latest_question_for_node();
test_authenticated_frontend_smoke_fixture_covers_list_and_workbench_metadata();
test_map_feedback_code_to_display_to_chinese_by_default();
test_feedback_card_view_model_hides_raw_feedback_codes();
test_feedback_card_view_model_uses_contract_payload_sections_and_actions();
test_feedback_card_view_model_renders_loss_points_as_table_rows();
test_feedback_card_reference_answer_sections_assemble_to_paragraphs();
test_generated_feedback_card_view_model_shows_phase6_payload_sections();
test_generated_feedback_card_view_model_handles_missing_phase6_fields();
test_candidate_review_view_model_keeps_candidate_review_user_visible_and_action_only();
test_feedback_card_view_model_hides_theme_sections_for_legacy_payload();
test_feedback_card_view_model_handles_pending_payload();
test_feedback_card_view_model_handles_failed_payload();
test_feedback_card_view_model_does_not_calculate_score_on_frontend();
test_clipboard_markdown_stays_compatible_with_structured_feedback_payload();
test_session_clipboard_markdown_includes_full_context_tree_and_all_questions();
test_progress_node_context_banner_ignores_group_header_click();
test_progress_node_context_banner_uses_safe_copy();
test_progress_tree_detail_uses_display_safe_copy();
test_progress_tree_display_safe_copy_still_applies();
test_progress_tree_detail_handles_missing_optional_fields();

type ReadyAllowsSubmit = Expect<Equal<typeof readyAvailability.canSubmit, true>>;
type NoPrerequisiteBlocksSubmit = Expect<Equal<typeof noPrerequisiteAvailability.canSubmit, false>>;
type CreatePayloadDoesNotSubmitMode = Expect<Equal<"mode" extends keyof typeof createPayload ? true : false, false>>;
type CreatePayloadSubmitsTheme = Expect<Equal<typeof createPayload.polish_theme, "technical" | "communication" | "mixed" | null | undefined>>;
type SessionWorkbenchPathIsStable = Expect<Equal<typeof sessionWorkbenchPath, "/interview/ses_001">>;

void payloadShape;
void sessionWorkbenchPath;
void createPendingDescription;
