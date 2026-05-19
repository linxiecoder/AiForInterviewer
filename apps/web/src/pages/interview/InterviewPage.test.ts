import {
  INTERVIEW_CREATE_BUTTON_STATE,
  INTERVIEW_CREATE_ENTRY_KIND,
  INTERVIEW_CREATE_FIELD_KEYS,
  INTERVIEW_CREATE_MODE_FIELD_KEY,
  INTERVIEW_CREATE_SUCCESS_ACTIONS,
  INTERVIEW_SESSION_WORKBENCH_FIELDS,
  INTERVIEW_SUPPORTED_MODES,
  INTERVIEW_WORKBENCH_DISABLED_ACTIONS,
  INTERVIEW_WORKBENCH_FEEDBACK_ITEMS,
  INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS,
  INTERVIEW_WORKBENCH_LAYOUT_AREAS,
  INTERVIEW_WORKBENCH_LAYOUT_TEST_IDS,
  INTERVIEW_WORKBENCH_NORMAL_STATE_FORBIDDEN_COPY,
  INTERVIEW_WORKBENCH_PRIMARY_ACTIONS,
  INTERVIEW_WORKBENCH_PROGRESS_NODE_TITLES,
  INTERVIEW_WORKBENCH_SCROLL_REGIONS,
  INTERVIEW_WORKBENCH_STATE_REGIONS,
  buildPolishBindingOptions,
  buildPolishSessionPath,
  buildPolishSessionCreateRequest,
  getInterviewCreateAvailability,
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
    readonly ["mode", "resume_job_binding_id", "topic_id", "subtopic_id", "custom_topic_text"]
  >
>;
type CreateSuccessRefreshesList = Expect<
  Equal<typeof INTERVIEW_CREATE_SUCCESS_ACTIONS, readonly ["navigate_to_workbench"]>
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
type WorkbenchHeaderChipsAreStable = Expect<
  Equal<typeof INTERVIEW_WORKBENCH_HEADER_CHIP_KEYS, readonly ["岗位", "简历", "当前节点", "进度", "当前节点表现"]>
>;
type WorkbenchProgressNodesAreStable = Expect<
  Equal<
    typeof INTERVIEW_WORKBENCH_PROGRESS_NODE_TITLES,
    readonly [
      "项目经历",
      "Java 多线程与并发",
      "数据库事务与一致性",
      "消息可靠性与缓存一致性",
      "订单状态一致性",
    ]
  >
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
  topic_id: "topic_project_depth",
  subtopic_id: "subtopic_project_impact",
  custom_topic_text: "  支付系统项目表达  ",
});

const payloadShape: CreatePolishSessionRequest = createPayload;
const sessionWorkbenchPath = buildPolishSessionPath("ses_001");

type ReadyAllowsSubmit = Expect<Equal<typeof readyAvailability.canSubmit, true>>;
type NoPrerequisiteBlocksSubmit = Expect<Equal<typeof noPrerequisiteAvailability.canSubmit, false>>;
type CreatePayloadDoesNotSubmitMode = Expect<Equal<"mode" extends keyof typeof createPayload ? true : false, false>>;
type SessionWorkbenchPathIsStable = Expect<Equal<typeof sessionWorkbenchPath, "/interview/ses_001">>;

void payloadShape;
void sessionWorkbenchPath;
