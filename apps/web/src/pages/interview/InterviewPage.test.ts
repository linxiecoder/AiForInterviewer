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
  INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY,
  INTERVIEW_LIST_TABLE_COLUMN_WIDTHS,
  INTERVIEW_LIST_TABLE_SCROLL_X,
  INTERVIEW_SEARCH_PLACEHOLDER,
  INTERVIEW_SESSION_WORKBENCH_FIELDS,
  INTERVIEW_SUPPORTED_MODES,
  INTERVIEW_WORKBENCH_DISABLED_ACTIONS,
  INTERVIEW_WORKBENCH_FEEDBACK_ITEMS,
  INTERVIEW_WORKBENCH_HERO_ACTION_COPY,
  INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY,
  INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT,
  INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS,
  INTERVIEW_WORKBENCH_LAYOUT_AREAS,
  INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS,
  INTERVIEW_WORKBENCH_NORMAL_STATE_FORBIDDEN_COPY,
  INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_EMPTY_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_HEADER_LAYOUT,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TITLE,
  INTERVIEW_PROGRESS_TREE_CONTEXT_BANNER_TOGGLE_COPY,
  INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT,
  INTERVIEW_PROGRESS_TREE_LEFT_LIST_FIELDS,
  INTERVIEW_PROGRESS_TREE_NODE_STATUS_LIGHT_TONES,
  INTERVIEW_PROGRESS_TREE_NODE_STATUS_PLACEMENT,
  INTERVIEW_PROGRESS_TREE_SCROLL_CLASS,
  INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT,
  INTERVIEW_WORKBENCH_CURRENT_QUESTION_COMPOSER_PLACEMENT,
  INTERVIEW_WORKBENCH_KEYBOARD_SHORTCUTS,
  INTERVIEW_WORKBENCH_PRIMARY_ACTIONS,
  INTERVIEW_WORKBENCH_SCROLL_REGIONS,
  INTERVIEW_WORKBENCH_STATE_REGIONS,
  INTERVIEW_WORKBENCH_STATE_MACHINE,
  buildPolishBindingOptions,
  buildPolishSessionPath,
  buildPolishSessionClipboardMarkdown,
  buildPolishSessionCreateRequest,
  buildInterviewCreatePendingDescription,
  buildFeedbackCardViewModel,
  filterPolishSessionsBySearch,
  buildProgressTreeContextBannerContent,
  buildProgressTreeContextBannerExpandedSections,
  buildProgressTreeNodeDetailViewModel,
  buildWorkbenchProgressNodeTitleMeta,
  buildWorkbenchProgressNodes,
  canAutoCreateQuestionFromProgressNode,
  collectDefaultExpandedProgressNodeKeys,
  deriveWorkbenchMachineState,
  getInterviewCreateAvailability,
  getWorkbenchProgressNodeQuestionTargetRef,
  getWorkbenchProgressNodeStatusLightTone,
  normalizeInterviewTopicTitle,
  normalizeProgressTreeDetailCopy,
  resolveCurrentQuestionId,
  resolveCurrentWorkbenchProgressNodeKey,
  resolveProgressTreeDetailNodeRef,
  resolveProgressTreeSelectedNodeRefAfterClick,
  shouldSubmitAnswerFromKeyboard,
  shouldAutoCreateQuestionForProgressNode,
  shouldShowProgressTreeContextBannerToggle,
  toNextRecommendedActionLabel,
  type PolishBindingOption,
} from "./InterviewPage";
import {
  POLISH_API_PATHS,
  createPolishSession,
  fetchPolishSession,
  fetchPolishSessions,
  fetchPolishTopics,
} from "../../entities/polish/api/polishApi";
import type { JobSummary } from "../../entities/job/model/types";
import type {
  CreatePolishSessionRequest,
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
      readonly actions: 88;
    }
  >
>;
type InterviewListTableScrollWidthIsStable = Expect<Equal<typeof INTERVIEW_LIST_TABLE_SCROLL_X, 1210>>;
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
type WorkbenchHeroActionsStayOnSummaryRowEnd = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT, "summary_row_end">
>;
type WorkbenchHeroActionsUseIconTooltipButtons = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HERO_ACTION_ICON_POLICY, "icon_only_with_tooltip">
>;
type WorkbenchHeroActionCopyMatchesActualBehavior = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_HERO_ACTION_COPY,
    readonly ["返回模拟面试列表", "复制模拟面试内容"]
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
  Equal<typeof INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT, { readonly system_question: "left"; readonly user_answer: "right" }>
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
  Equal<typeof INTERVIEW_WORKBENCH_FEEDBACK_ITEMS, readonly ["点评", "打分", "失分点评价", "参考回答", "考点解析", "技术原理扩展", "权重说明", "面试意图", "技术短板", "表达短板", "P7 级参考答案", "口语化范本", "下一轮训练建议"]>
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
type DetailApiReturnsSessionDetail = Expect<
  Equal<Awaited<ReturnType<typeof fetchPolishSession>>, PolishSessionDetail>
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
  depth_goal?: string | null;
  display_category_title?: string | null;
  display_title?: string | null;
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
  assertContract(INTERVIEW_LIST_TABLE_SCROLL_X === 1210, "模拟面试列表应使用稳定横向表格宽度");
  assertContract(INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY.overflow === "single_line_ellipsis", "表格文本超出一行应省略");
  assertContract(INTERVIEW_LIST_TABLE_CELL_TEXT_POLICY.hover === "tooltip", "表格文本 hover 应展示全文");
  assertContract(filterPolishSessionsBySearch(sessions, "缓存").map((session) => session.session_id).join(",") === "ses_summary_002", "模拟面试搜索应匹配名称、岗位、简历或主题");
  assertContract(filterPolishSessionsBySearch(sessions, "分布式系统").length === 1, "模拟面试搜索应匹配简历标题");
  assertContract(filterPolishSessionsBySearch(sessions, "").length === 2, "空搜索应保留全部模拟面试记录");
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

function test_progress_tree_detail_defaults_to_current_priority(): void {
  const session = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_first", "大文件异步处理管道架构", "resume_deep_dive", "深度打磨类"),
        depth_goal: "第一节点目标",
      },
      {
        ...buildTestProgressNode("node_priority", "AI Agent 任务规划与工具调用机制", "jd_gap_learning", "补齐学习类"),
        depth_goal: "当前优先节点目标",
      },
    ],
    "node_priority",
  );

  const selectedRef = resolveProgressTreeDetailNodeRef(session, null);
  const detail = buildProgressTreeNodeDetailViewModel(session, selectedRef);

  assertContract(selectedRef === "node_priority", "详情默认节点应优先使用 current_priority");
  assertContract(detail?.title === "AI Agent 任务规划与工具调用机制", "详情应默认显示 current_priority 对应节点");
  assertContract(detail?.depthRequirement === "当前优先节点目标", "详情应默认显示 current_priority 节点内容");
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

function test_progress_node_context_banner_defaults_to_current_priority(): void {
  const session = buildTestSession(
    [
      {
        ...buildTestProgressNode("node_first", "大文件异步处理管道架构", "resume_deep_dive", "深度打磨类"),
        depth_goal: "第一节点目标",
      },
      {
        ...buildTestProgressNode("node_priority", "AI Agent 任务规划与工具调用机制", "jd_gap_learning", "补齐学习类"),
        depth_goal: "当前优先节点目标",
      },
    ],
    "node_priority",
  );

  const selectedRef = resolveProgressTreeDetailNodeRef(session, null);
  const bannerContent = buildProgressTreeContextBannerContent(session, selectedRef);

  assertContract(selectedRef === "node_priority", "上下文公告条默认节点应优先使用 current_priority");
  assertContract(bannerContent.title === "AI Agent 任务规划与工具调用机制", "上下文公告条应默认展示 current_priority 对应节点");
  assertContract(bannerContent.depthRequirement === "当前优先节点目标", "上下文公告条应默认显示 current_priority 节点内容");
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
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_COPY[0] === "返回模拟面试列表", "返回按钮文案应稳定");
  assertContract(INTERVIEW_WORKBENCH_HERO_ACTION_COPY[1] === "复制模拟面试内容", "复制按钮文案应匹配实际复制内容");
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
  assertContract(expandedSections.map((section) => section.key).join(",") === "depth_requirement,follow_up_directions,loss_risks", "展开后应只显示深度要求、连续追问方向、常见失分风险");
  assertContract(expandedCopy.includes("深度要求"), "展开后应展示深度要求标题");
  assertContract(expandedCopy.includes("连续追问方向"), "展开后应展示连续追问方向标题");
  assertContract(expandedCopy.includes("常见失分风险"), "展开后应展示常见失分风险标题");
  assertContract(expandedCopy.includes("如何验证融合排序收益"), "展开后应展示追问方向内容");
  assertContract(expandedCopy.includes("只讲工具链，不说明阈值调优依据"), "展开后应展示常见失分风险内容");
  for (const hiddenCopy of ["建议第一题", "你会如何设计第一题？", "好回答信号", "简历线索", "岗位依据", "简历中提到搜索优化", "岗位要求检索增强能力"]) {
    assertContract(!expandedCopy.includes(hiddenCopy), `展开后不应展示 ${hiddenCopy}`);
  }
}

function test_workbench_chat_bubble_alignment_keeps_system_left_and_user_right(): void {
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.system_question === "left", "系统题目应位于聊天区左侧");
  assertContract(INTERVIEW_WORKBENCH_CHAT_BUBBLE_ALIGNMENT.user_answer === "right", "用户回答及暂无回答占位应位于聊天区右侧");
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
  assertContract(shouldAutoCreateQuestionForProgressNode(sessionWithTurn, "node_without_question"), "无题目的真实节点点击后应自动生成题");
  assertContract(shouldAutoCreateQuestionForProgressNode(sessionWithHistoricalTurn, "node_with_question"), "只有历史题目但无 active question 的节点仍应可生成新题");
  assertContract(!shouldAutoCreateQuestionForProgressNode(sessionWithTurn, null), "空节点 ref 不应生成题");
  assertContract(canAutoCreateQuestionFromProgressNode({
    session: refreshFailedSession,
    progressNodeRef: "node_without_question",
    creatingQuestion: false,
    submittingAnswer: false,
    feedbackGenerating: false,
  }), "refresh_failed 但 plan 可展示时仍应允许点击节点生成题");
  assertContract(nodeWithQuestion?.children?.some((node) => node.key === "question:q_existing") === true, "题目记录应挂到自己的 progress_node_ref 节点下");
  assertContract(!nodeWithoutQuestion?.children?.some((node) => node.kind === "question"), "其他节点不应承载已有题目记录");
  assertContract(resolveCurrentQuestionId(sessionWithTurn, "node_with_question") === "q_existing", "当前题目应可按选中节点解析");
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
  assertContract(shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true }), "Ctrl+Enter 应触发发送");
  assertContract(!shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: false }), "单独 Enter 不应触发发送");
  assertContract(!shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true, shiftKey: true }), "Ctrl+Shift+Enter 不应触发发送");
  assertContract(!shouldSubmitAnswerFromKeyboard({ key: "Enter", ctrlKey: true, isComposing: true }), "输入法组合态不应触发发送");
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
      contract_id: "P-POLISH-005",
      contract_ids: ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005", "P-POLISH-009"],
      status: "generated",
      feedback_id: "fb_001",
      feedback_text: "结构完整，但技术取舍需要补充替代方案。",
      feedback_summary: "补充替代方案和量化结果。",
      polish_theme: "mixed",
      polish_theme_label: "混合",
      explicit_weight: 60,
      implicit_weight: 40,
      weight_explanation: "本轮按显性技术 60%、隐性表达 40% 综合打磨。",
      interview_intent: "同时观察技术链路和表达结构。",
      explicit_score: 70,
      implicit_score: 76,
      technical_gaps: ["幂等键设计还不够具体"],
      communication_gaps: ["背景压缩可以更短"],
      p7_reference_answer: "从 owner 视角补齐状态机、失败兜底和指标复盘。",
      oral_script: "我会先用 30 秒交代背景，再说明我的职责和关键取舍。",
      next_training_suggestions: ["下一轮用 60/40 权重再答一版"],
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
      knowledge_points: [
        {
          title: "STAR + 技术决策链路",
          explanation: "覆盖场景、任务、行动、结果和技术取舍。",
        },
      ],
      technical_principles: [
        {
          title: "可观测结果优先",
          explanation: "用指标、日志、告警或压测结果支撑方案价值。",
        },
      ],
      next_recommended_actions: ["provide_more_answer_detail", "generate_next_question"],
      candidate_refs: [{ resource_type: "weakness_candidate", resource_id: "weak_001" }],
      validation_result_ref: { resource_type: "validation_result", resource_id: "val_001" },
      trace_refs: [{ trace_type: "feedback", trace_ref_id: "fb_001" }],
      low_confidence_flags: [{ flag_id: "needs_more_metrics", reason: "missing_metrics" }],
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const visibleCopy = [
    card.title,
    card.status,
    card.contractId,
    ...card.contractIds,
    ...card.sections.flatMap((section) => [section.title, ...section.items]),
    ...card.traceItems,
  ].join(" ");

  assertContract(card.sections.map((section) => section.title).join(",") === "点评,打分,失分点评价,参考回答,考点解析,技术原理扩展,权重说明,面试意图,技术短板,表达短板,P7 级参考答案,口语化范本,下一轮训练建议", "反馈卡应展示旧模块和主题化模块");
  assertContract(visibleCopy.includes("P-POLISH-005"), "反馈卡应展示 contract_id / contract_ids");
  assertContract(visibleCopy.includes("72"), "反馈卡应展示 score_result 分值");
  assertContract(visibleCopy.includes("技术取舍说明不足"), "反馈卡应展示 loss_points");
  assertContract(visibleCopy.includes("先讲业务目标"), "反馈卡应展示 reference_answer");
  assertContract(visibleCopy.includes("STAR + 技术决策链路"), "反馈卡应展示 knowledge_points");
  assertContract(visibleCopy.includes("可观测结果优先"), "反馈卡应展示 technical_principles");
  assertContract(visibleCopy.includes("显性技术 60%、隐性表达 40%"), "反馈卡应展示权重说明");
  assertContract(visibleCopy.includes("同时观察技术链路和表达结构"), "反馈卡应展示面试意图");
  assertContract(visibleCopy.includes("幂等键设计还不够具体"), "反馈卡应展示技术短板");
  assertContract(visibleCopy.includes("背景压缩可以更短"), "反馈卡应展示表达短板");
  assertContract(visibleCopy.includes("owner 视角"), "反馈卡应展示 P7 级参考答案");
  assertContract(visibleCopy.includes("30 秒交代背景"), "反馈卡应展示口语化范本");
  assertContract(visibleCopy.includes("下一轮用 60/40 权重再答一版"), "反馈卡应展示下一轮训练建议");
  assertContract(visibleCopy.includes("weakness_candidate:weak_001"), "反馈卡应保留 candidate_refs");
  assertContract(visibleCopy.includes("validation_result:val_001"), "反馈卡应保留 validation_result_ref");
  assertContract(visibleCopy.includes("feedback:fb_001"), "反馈卡应保留 trace_refs");
  assertContract(visibleCopy.includes("needs_more_metrics"), "反馈卡应保留 low_confidence_flags");
  assertContract(card.nextActions.join(",") === "provide_more_answer_detail,generate_next_question", "下一步建议应去重并保持 contract enum");
  assertContract(toNextRecommendedActionLabel("provide_more_answer_detail") === "补充回答细节", "contract enum 应映射为按钮文案");
  assertContract(toNextRecommendedActionLabel("generate_next_question") === "生成下一题", "生成下一题 enum 应映射为按钮文案");
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
      contract_id: "P-POLISH-005",
      contract_ids: ["P-POLISH-005"],
      status: "generated",
      feedback_id: "fb_legacy",
      feedback_text: "旧版反馈仍应可展示。",
      feedback_summary: "旧版总结。",
      score_result: null,
      loss_points: [],
      reference_answer: null,
      knowledge_points: [],
      technical_principles: [],
      next_recommended_actions: ["generate_next_question"],
      candidate_refs: [],
      validation_result_ref: null,
      trace_refs: [],
      low_confidence_flags: [],
    },
  };

  const card = buildFeedbackCardViewModel(answer);
  const titles = card.sections.map((section) => section.title);
  const visibleCopy = card.sections.flatMap((section) => [section.title, ...section.items]).join(" ");

  assertContract(titles.includes("点评"), "旧 payload 应继续展示旧反馈区块");
  assertContract(visibleCopy.includes("旧版反馈仍应可展示"), "旧 payload 应继续展示 feedback_text");
  assertContract(!titles.includes("权重说明"), "旧 payload 缺主题字段时不应展示权重说明");
  assertContract(!titles.includes("面试意图"), "旧 payload 缺主题字段时不应展示面试意图");
  assertContract(!titles.includes("技术短板"), "旧 payload 缺主题字段时不应展示技术短板");
  assertContract(!titles.includes("表达短板"), "旧 payload 缺主题字段时不应展示表达短板");
  assertContract(card.nextActions.join(",") === "generate_next_question", "旧 payload 应继续保留下一步 action");
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
test_progress_tree_groups_flat_nodes_by_display_category_title();
test_progress_tree_group_header_is_not_question_target();
test_progress_tree_group_headers_default_expanded_for_collapse_control();
test_progress_tree_uses_progress_node_ref_as_key_and_priority_match();
test_interview_topic_title_neutralizes_interrogation_copy();
test_progress_node_context_renders_as_compact_banner();
test_progress_tree_left_list_stays_compact();
test_progress_tree_detail_defaults_to_current_priority();
test_progress_tree_group_header_does_not_show_node_detail();
test_progress_tree_category_header_is_group_only();
test_progress_node_context_banner_defaults_to_current_priority();
test_progress_node_context_banner_updates_when_node_selected();
test_progress_node_context_banner_hides_question_and_detail_lists();
test_workbench_hero_actions_are_icon_only_and_copy_session_content();
test_progress_tree_node_status_uses_row_trailing_lights();
test_progress_node_context_banner_supports_expand_toggle_for_depth();
test_workbench_chat_bubble_alignment_keeps_system_left_and_user_right();
test_workbench_ctrl_enter_submits_answer();
test_waiting_answer_bar_is_removed_from_workbench_contract();
test_progress_tree_click_auto_generates_only_for_nodes_without_question();
test_authenticated_frontend_smoke_fixture_covers_list_and_workbench_metadata();
test_feedback_card_view_model_uses_contract_payload_sections_and_actions();
test_feedback_card_view_model_hides_theme_sections_for_legacy_payload();
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
