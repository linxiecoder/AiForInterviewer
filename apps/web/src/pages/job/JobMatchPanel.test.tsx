import {
  JOB_MATCH_ANALYSIS_API_PATHS,
} from "../../entities/job/api/jobApi";
import {
  JOB_MATCH_DIMENSION_LABELS,
  JOB_MATCH_DIMENSION_ORDER,
  JOB_MATCH_GAP_RISK_HELPER,
  JOB_MATCH_COPY_STATES,
  JOB_MATCH_FOLLOW_UP_ANCHOR_TEXT,
  JOB_MATCH_MARKDOWN_SECTION_HEADINGS,
  JOB_MATCH_PANEL_STATES,
  JOB_MATCH_RESULT_FIELD_KEYS,
  buildJobMatchMarkdownReport,
  getJobMatchPanelAvailability,
} from "./JobMatchPanel";
import type {
  CreateJobMatchAnalysisRequest,
  JobMatchAnalysis,
  JobMatchDimensionKey,
} from "../../entities/job/model/types";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type JobMatchDimensionOrder = typeof JOB_MATCH_DIMENSION_ORDER;

type JobMatchDimensionOrderMatchesBackendContract = Expect<
  Equal<
    JobMatchDimensionOrder,
    readonly [
      "requirement_alignment",
      "experience_evidence",
      "skill_coverage",
      "gap_risk",
      "readiness_actions",
    ]
  >
>;

type JobMatchResultFieldKeys = typeof JOB_MATCH_RESULT_FIELD_KEYS;

type JobMatchResultShowsRequiredFields = Expect<
  Equal<
    JobMatchResultFieldKeys,
    readonly [
      "overall_score",
      "overall_level",
      "confidence",
      "summary",
      "dimension_scores",
      "missing_requirements",
      "interview_focus",
      "suggested_questions",
    ]
  >
>;

type JobMatchPanelStateKeys = typeof JOB_MATCH_PANEL_STATES;

type JobMatchPanelCoversRequiredStates = Expect<
  Equal<JobMatchPanelStateKeys, readonly ["empty", "loading", "error", "result"]>
>;

type GapRiskLabelUsesRiskControl = Expect<
  Equal<(typeof JOB_MATCH_DIMENSION_LABELS)["gap_risk"], "缺口风险控制">
>;

type GapRiskHelperStatesLowerRisk = Expect<
  Equal<typeof JOB_MATCH_GAP_RISK_HELPER, "分数越高，缺口风险越低。">
>;

type JobMatchCopyStatesCoverRequiredUiStates = Expect<
  Equal<typeof JOB_MATCH_COPY_STATES, readonly ["idle", "copying", "copied", "failed"]>
>;

type JobMatchMarkdownSectionsCoverCopyReport = Expect<
  Equal<
    typeof JOB_MATCH_MARKDOWN_SECTION_HEADINGS,
    readonly [
      "# 岗位匹配分析",
      "## 总览",
      "## 维度评分",
      "## 明显缺口",
      "## 面试追问重点",
      "## 建议问题",
      "## 后续使用",
    ]
  >
>;

type JobMatchFollowUpAnchorTextIsStable = Expect<
  Equal<
    typeof JOB_MATCH_FOLLOW_UP_ANCHOR_TEXT,
    "该匹配分析可作为后续模拟面试的输入，帮助生成更聚焦的追问与训练重点。"
  >
>;

type JobMatchCreateApiPathIsStable = Expect<
  Equal<typeof JOB_MATCH_ANALYSIS_API_PATHS.create, "/job-match-analyses">
>;

type JobMatchLatestApiPathIsStable = Expect<
  Equal<typeof JOB_MATCH_ANALYSIS_API_PATHS.latest, "/job-match-analyses/latest">
>;

const noBinding = getJobMatchPanelAvailability(null);
const readyBinding = getJobMatchPanelAvailability("bind_001");

type NoBindingDisablesCreate = Expect<Equal<typeof noBinding.canCreate, false>>;
type ReadyBindingEnablesCreate = Expect<Equal<typeof readyBinding.canCreate, true>>;

const createRequest = {
  resume_job_binding_id: "bind_001",
} satisfies CreateJobMatchAnalysisRequest;

const sampleAnalysis = {
  analysis_id: "score_001",
  resume_job_binding_id: "bind_001",
  resume_id: "resume_001",
  resume_version_id: "resume_version_001",
  job_id: "job_001",
  job_version_id: "job_version_001",
  status: "completed",
  overall_score: 82,
  overall_level: "strong_match",
  confidence: "high",
  result_payload: {
    overall_score: 82,
    overall_level: "strong_match",
    confidence: "high",
    summary: "岗位要求与简历证据匹配度较高。",
    dimension_scores: JOB_MATCH_DIMENSION_ORDER.map((key: JobMatchDimensionKey) => ({
      key,
      score: key === "gap_risk" ? 12 : 10,
      max_score: key === "gap_risk" ? 15 : 20,
      rationale: key === "gap_risk" ? JOB_MATCH_GAP_RISK_HELPER : "有可验证证据。",
      supporting_evidence: [{ chunk_id: "resume:summary:001" }],
      gaps: key === "gap_risk" ? ["面试中确认项目深度。"] : [],
      confidence: key === "readiness_actions" ? "medium" : "high",
    })),
    matched_requirements: [],
    missing_requirements: [
      {
        requirement_chunk_id: "job:requirement:001",
        reason: "简历证据不足。",
        confidence: "medium",
        evidence_insufficient: false,
      },
    ],
    resume_evidence: [],
    risk_flags: [],
    interview_focus: ["核实核心项目深度。"],
    suggested_questions: ["这个项目中你具体负责哪一部分？"],
    markdown_report: "# Job Match",
  },
  markdown_report_text: "# Job Match",
  score_rule_version: "job_match.v1",
  prompt_version: "job_match.prompt.v1",
  model_name: "fake_llm_job_match_v1",
  source_digest: "sha256:test",
  created_at: "2026-05-18T10:00:00Z",
  updated_at: "2026-05-18T10:00:00Z",
} satisfies JobMatchAnalysis;

const markdownReport = buildJobMatchMarkdownReport(sampleAnalysis);
const emptyMarkdownReport = buildJobMatchMarkdownReport({
  ...sampleAnalysis,
  result_payload: {
    ...sampleAnalysis.result_payload,
    missing_requirements: [],
    interview_focus: [],
    suggested_questions: [],
  },
});

const markdownReportString: string = markdownReport;
const emptyMarkdownReportString: string = emptyMarkdownReport;

void createRequest;
void sampleAnalysis;
void markdownReportString;
void emptyMarkdownReportString;
