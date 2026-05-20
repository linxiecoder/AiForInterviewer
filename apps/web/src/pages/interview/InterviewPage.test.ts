import {
  INTERVIEW_CREATE_BUTTON_STATE,
  INTERVIEW_CREATE_ENTRY_KIND,
  INTERVIEW_CREATE_FIELD_KEYS,
  INTERVIEW_CREATE_MODE_FIELD_KEY,
  INTERVIEW_CREATE_PENDING_LOG_EVENTS,
  INTERVIEW_CREATE_PENDING_STATUS,
  INTERVIEW_CREATE_SUCCESS_ACTIONS,
  INTERVIEW_SESSION_WORKBENCH_FIELDS,
  INTERVIEW_SUPPORTED_MODES,
  INTERVIEW_WORKBENCH_DISABLED_ACTIONS,
  INTERVIEW_WORKBENCH_FEEDBACK_ITEMS,
  INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT,
  INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS,
  INTERVIEW_WORKBENCH_LAYOUT_AREAS,
  INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS,
  INTERVIEW_WORKBENCH_NORMAL_STATE_FORBIDDEN_COPY,
  INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_CARD_EMPTY_COPY,
  INTERVIEW_PROGRESS_TREE_CONTEXT_CARD_TITLE,
  INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT,
  INTERVIEW_PROGRESS_TREE_LEFT_LIST_FIELDS,
  INTERVIEW_PROGRESS_TREE_SCROLL_CLASS,
  INTERVIEW_WORKBENCH_PRIMARY_ACTIONS,
  INTERVIEW_WORKBENCH_SCROLL_REGIONS,
  INTERVIEW_WORKBENCH_STATE_REGIONS,
  buildPolishBindingOptions,
  buildPolishSessionPath,
  buildPolishSessionCreateRequest,
  buildInterviewCreatePendingDescription,
  buildProgressTreeNodeDetailViewModel,
  buildWorkbenchProgressNodes,
  collectDefaultExpandedProgressNodeKeys,
  getInterviewCreateAvailability,
  getWorkbenchProgressNodeQuestionTargetRef,
  normalizeInterviewTopicTitle,
  normalizeProgressTreeDetailCopy,
  resolveCurrentWorkbenchProgressNodeKey,
  resolveProgressTreeDetailNodeRef,
  resolveProgressTreeSelectedNodeRefAfterClick,
  type PolishBindingOption,
} from "./InterviewPage";
import {
  POLISH_API_PATHS,
  createPolishSession,
  fetchPolishSession,
  fetchPolishTopics,
} from "../../entities/polish/api/polishApi";
import type { JobSummary } from "../../entities/job/model/types";
import type {
  CreatePolishSessionRequest,
  PolishProgressTreeNode,
  PolishSessionDetail,
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
    readonly ["mode", "resume_job_binding_id", "topic_id", "custom_topic_text"]
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
type WorkbenchFieldsAreStable = Expect<
  Equal<
    typeof INTERVIEW_SESSION_WORKBENCH_FIELDS,
    readonly ["title", "mode", "status", "topic", "binding", "created_at", "updated_at"]
  >
>;
type WorkbenchLayoutAreasAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_LAYOUT_AREAS,
    readonly ["top_summary", "progress_panel", "conversation_panel", "feedback_accordion", "bottom_composer"]
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
      readonly composer: "interview-workbench-composer";
    }
  >
>;
type WorkbenchScrollRegionsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_SCROLL_REGIONS, readonly ["progress_node_list", "chat_scroll"]>
>;
type WorkbenchHeroActionsStayOnTitleRowEnd = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HERO_ACTION_PLACEMENT, "title_row_end">
>;
type WorkbenchProgressHeaderCopyOmitsPercentText = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_PROGRESS_HEADER_COPY, readonly ["模拟面试进度"]>
>;
type ProgressTreeDetailPlacementIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT, "conversation_context_card">
>;
type ProgressTreeContextCardCopyIsStable = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_CONTEXT_CARD_TITLE, "当前节点上下文">
>;
type ProgressTreeContextCardEmptyCopyIsStable = Expect<
  Equal<
    typeof INTERVIEW_PROGRESS_TREE_CONTEXT_CARD_EMPTY_COPY,
    "请选择一个进展节点查看训练目标、建议第一题和追问方向。"
  >
>;
type ProgressTreeLeftListFieldsAreStable = Expect<
  Equal<
    typeof INTERVIEW_PROGRESS_TREE_LEFT_LIST_FIELDS,
    readonly ["category_header", "node_title", "node_code", "node_status", "current_priority", "question_entry"]
  >
>;
type ProgressTreeScrollClassIsScoped = Expect<
  Equal<typeof INTERVIEW_PROGRESS_TREE_SCROLL_CLASS, "progressTreeScroll">
>;
type WorkbenchHeaderChipsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS, readonly ["岗位", "简历", "当前节点", "进度", "当前节点表现"]>
>;
type WorkbenchFeedbackItemsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_FEEDBACK_ITEMS, readonly ["点评", "打分", "失分点评价", "参考回答", "考点解析", "技术原理扩展"]>
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
  topic_id: "topic_authenticity_contribution",
  custom_topic_text: "  支付系统项目表达  ",
});
const createPendingDescription = buildInterviewCreatePendingDescription(12);

const payloadShape: CreatePolishSessionRequest = createPayload;
const sessionWorkbenchPath = buildPolishSessionPath("ses_001");

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

function test_progress_tree_detail_moves_to_conversation_context_card(): void {
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
  ]);

  const listNode = buildWorkbenchProgressNodes(session)[0]?.children?.[0];
  const selectedRef = resolveProgressTreeDetailNodeRef(session, "node_detail_1");
  const detail = buildProgressTreeNodeDetailViewModel(session, selectedRef);

  assertContract(INTERVIEW_PROGRESS_TREE_DETAIL_PLACEMENT === "conversation_context_card", "节点详情应迁移到右侧对话上下文卡");
  assertContract(INTERVIEW_PROGRESS_TREE_CONTEXT_CARD_TITLE === "当前节点上下文", "右侧对话区应出现当前节点上下文标题");
  assertContract(listNode?.detail !== "能解释召回、排序、重排和评估指标之间的取舍。", "左侧进展树区域不应继续渲染长详情");
  assertContract(detail?.title === "混合检索策略设计与优化", "上下文卡应显示节点标题");
  assertContract(detail?.depthRequirement === "能解释召回、排序、重排和评估指标之间的取舍。", "上下文卡应显示深度要求");
  assertContract(detail?.firstQuestion === "如果让你设计混合检索链路，你会如何分层？", "上下文卡应显示建议第一题");
  assertContract(Boolean(detail?.followUpDirections.includes("如何处理召回不足")), "上下文卡应显示追问方向");
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
  const contextDetail = buildProgressTreeNodeDetailViewModel(session, "node_compact_1");

  assertContract(listNode?.title === "混合检索策略设计与优化", "左侧真实节点应显示标题");
  assertContract(listNode?.nodeCode === "R-01", "左侧真实节点应显示 node_code");
  assertContract(listNode?.status === "pending", "左侧真实节点应显示状态");
  assertContract(listNode?.detail !== longDepthGoal, "左侧列表不应显示完整 depth_goal 长文本");
  assertContract(contextDetail?.depthRequirement === longDepthGoal, "节点详情字段应出现在右侧上下文卡数据中");
  assertContract(contextDetail?.firstQuestion === "你会如何验证混合检索效果？", "建议第一题应保留在右侧上下文卡数据中");
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

function test_progress_tree_context_card_defaults_to_current_priority(): void {
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
  const contextDetail = buildProgressTreeNodeDetailViewModel(session, selectedRef);

  assertContract(selectedRef === "node_priority", "上下文卡默认节点应优先使用 current_priority");
  assertContract(contextDetail?.title === "AI Agent 任务规划与工具调用机制", "上下文卡应默认展示 current_priority 对应节点");
  assertContract(contextDetail?.depthRequirement === "当前优先节点目标", "上下文卡应默认显示 current_priority 节点内容");
}

function test_progress_tree_context_card_updates_when_node_selected(): void {
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
  const contextDetail = buildProgressTreeNodeDetailViewModel(session, selectedRef);

  assertContract(selectedRef === "node_selected", "点击另一个真实节点后应切换上下文卡节点");
  assertContract(contextDetail?.title === "缓存一致性问题定位", "上下文卡应展示新选中节点标题");
  assertContract(contextDetail?.depthRequirement === "选中节点目标", "上下文卡应展示新选中节点详情");
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

test_progress_tree_groups_flat_nodes_by_display_category_title();
test_progress_tree_group_header_is_not_question_target();
test_progress_tree_group_headers_default_expanded_for_collapse_control();
test_progress_tree_uses_progress_node_ref_as_key_and_priority_match();
test_interview_topic_title_neutralizes_interrogation_copy();
test_progress_tree_detail_moves_to_conversation_context_card();
test_progress_tree_left_list_stays_compact();
test_progress_tree_detail_defaults_to_current_priority();
test_progress_tree_group_header_does_not_show_node_detail();
test_progress_tree_category_header_is_group_only();
test_progress_tree_context_card_defaults_to_current_priority();
test_progress_tree_context_card_updates_when_node_selected();
test_progress_tree_detail_uses_display_safe_copy();
test_progress_tree_display_safe_copy_still_applies();
test_progress_tree_detail_handles_missing_optional_fields();

type ReadyAllowsSubmit = Expect<Equal<typeof readyAvailability.canSubmit, true>>;
type NoPrerequisiteBlocksSubmit = Expect<Equal<typeof noPrerequisiteAvailability.canSubmit, false>>;
type CreatePayloadDoesNotSubmitMode = Expect<Equal<"mode" extends keyof typeof createPayload ? true : false, false>>;
type SessionWorkbenchPathIsStable = Expect<Equal<typeof sessionWorkbenchPath, "/interview/ses_001">>;

void payloadShape;
void sessionWorkbenchPath;
void createPendingDescription;
