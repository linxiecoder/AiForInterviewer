import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, Button, Card, Empty, List, Space, Tag, Typography, message } from "antd";
import { CopyOutlined, ReloadOutlined } from "@ant-design/icons";
import {
  createJobMatchAnalysis,
  fetchLatestJobMatchAnalysis,
} from "../../entities/job/api/jobApi";
import type {
  JobMatchAnalysis,
  JobMatchConfidence,
  JobMatchDimensionScore,
  JobMatchDimensionKey,
  JobMatchMissingRequirement,
  JobMatchOverallLevel,
} from "../../entities/job/model/types";
import { isApiHttpError } from "../../shared/api/errors";
import { EmptyState } from "../../shared/ui/EmptyState";
import { LoadingState } from "../../shared/ui/LoadingState";

export const JOB_MATCH_DIMENSION_ORDER = [
  "requirement_alignment",
  "experience_evidence",
  "skill_coverage",
  "gap_risk",
  "readiness_actions",
] as const satisfies readonly JobMatchDimensionKey[];

export const JOB_MATCH_DIMENSION_LABELS = {
  requirement_alignment: "岗位要求匹配",
  experience_evidence: "经验证据强度",
  skill_coverage: "技能覆盖",
  gap_risk: "缺口风险控制",
  readiness_actions: "准备行动清晰度",
} as const satisfies Record<JobMatchDimensionKey, string>;

export const JOB_MATCH_GAP_RISK_HELPER = "分数越高，缺口风险越低。";

export const JOB_MATCH_COPY_STATES = ["idle", "copying", "copied", "failed"] as const;

export const JOB_MATCH_MARKDOWN_SECTION_HEADINGS = [
  "# 岗位匹配分析",
  "## 总览",
  "## 维度评分",
  "## 明显缺口",
  "## 面试追问重点",
  "## 建议问题",
  "## 后续使用",
] as const;

export const JOB_MATCH_FOLLOW_UP_ANCHOR_TEXT =
  "该匹配分析可作为后续模拟面试的输入，帮助生成更聚焦的追问与训练重点。";

export const JOB_MATCH_RESULT_FIELD_KEYS = [
  "overall_score",
  "overall_level",
  "confidence",
  "summary",
  "dimension_scores",
  "missing_requirements",
  "interview_focus",
  "suggested_questions",
] as const;

export const JOB_MATCH_PANEL_STATES = ["empty", "loading", "error", "result"] as const;

type JobMatchPanelAvailability =
  | { kind: "no_binding"; canCreate: false }
  | { kind: "ready"; canCreate: true; bindingId: string };

export function getJobMatchPanelAvailability(
  bindingId: null | undefined,
): Extract<JobMatchPanelAvailability, { kind: "no_binding" }>;
export function getJobMatchPanelAvailability(
  bindingId: string,
): Extract<JobMatchPanelAvailability, { kind: "ready" }>;
export function getJobMatchPanelAvailability(
  bindingId: string | null | undefined,
): JobMatchPanelAvailability;
export function getJobMatchPanelAvailability(
  bindingId: string | null | undefined,
): JobMatchPanelAvailability {
  if (typeof bindingId !== "string" || bindingId.trim().length === 0) {
    return { kind: "no_binding", canCreate: false };
  }
  return { kind: "ready", canCreate: true, bindingId };
}

type JobMatchPanelProps = {
  bindingId: string | null | undefined;
  bindingLabel?: string | null;
  onAnalysisCreated?: (analysis: JobMatchAnalysis) => void;
};

type JobMatchResultViewProps = {
  analysis: JobMatchAnalysis;
  copyDisabled?: boolean;
};

type CopyState = (typeof JOB_MATCH_COPY_STATES)[number];

function toErrorMessage(error: unknown): string {
  if (isApiHttpError(error)) {
    const reason = typeof error.details?.reason === "string" ? error.details.reason : "";
    if (error.code === "validation_failed") {
      return reason
        ? `评分结果校验失败：${reason}`
        : "评分结果校验失败，请稍后重试或补充简历/岗位证据。";
    }
    return reason ? `${error.safeMessage}：${reason}` : error.safeMessage;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "岗位匹配分析请求失败，请稍后重试。";
}

function overallLevelLabel(level: JobMatchOverallLevel | null): string {
  switch (level) {
    case "strong_match":
      return "强匹配";
    case "medium_match":
      return "中等匹配";
    case "weak_match":
      return "弱匹配";
    case "insufficient_evidence":
      return "证据不足";
    default:
      return "未知";
  }
}

function confidenceLabel(confidence: JobMatchConfidence | null): string {
  switch (confidence) {
    case "high":
      return "高";
    case "medium":
      return "中";
    case "low":
      return "低";
    case "insufficient":
      return "证据不足";
    default:
      return "未知";
  }
}

function confidenceColor(confidence: JobMatchConfidence | null): string {
  switch (confidence) {
    case "high":
      return "green";
    case "medium":
      return "blue";
    case "low":
      return "orange";
    case "insufficient":
      return "red";
    default:
      return "default";
  }
}

function levelColor(level: JobMatchOverallLevel | null): string {
  switch (level) {
    case "strong_match":
      return "green";
    case "medium_match":
      return "blue";
    case "weak_match":
      return "orange";
    case "insufficient_evidence":
      return "red";
    default:
      return "default";
  }
}

function toInlineText(value: string | null | undefined): string {
  const text = (value ?? "").replace(/\s+/g, " ").trim();
  return text.length > 0 ? text : "-";
}

function toListMarkdown<T>(
  items: readonly T[] | null | undefined,
  renderItem: (item: T) => string,
  emptyText: string,
): string {
  if (!items || items.length === 0) {
    return `- ${emptyText}`;
  }
  return items.map(renderItem).join("\n");
}

function dimensionToMarkdown(dimension: JobMatchDimensionScore): string {
  const gaps =
    dimension.gaps.length > 0
      ? dimension.gaps.map((gap) => toInlineText(gap)).join("；")
      : "无明确缺口";
  const helper = dimension.key === "gap_risk" ? `；${JOB_MATCH_GAP_RISK_HELPER}` : "";
  return [
    `- ${JOB_MATCH_DIMENSION_LABELS[dimension.key]}：${dimension.score} / ${dimension.max_score}`,
    `  - 置信度：${confidenceLabel(dimension.confidence)}${helper}`,
    `  - 说明：${toInlineText(dimension.rationale)}`,
    `  - 缺口：${gaps}`,
  ].join("\n");
}

function missingRequirementToMarkdown(item: JobMatchMissingRequirement): string {
  const source = item.requirement_chunk_id ?? "evidence_insufficient";
  return `- ${toInlineText(item.reason)}（来源：${source}；置信度：${confidenceLabel(item.confidence)}）`;
}

export function buildJobMatchMarkdownReport(analysis: JobMatchAnalysis): string {
  const payload = analysis.result_payload;
  const overallScore = analysis.overall_score ?? payload.overall_score;
  const overallLevel = analysis.overall_level ?? payload.overall_level;
  const confidence = analysis.confidence ?? payload.confidence;
  const dimensionScores = [...payload.dimension_scores].sort(
    (left, right) =>
      JOB_MATCH_DIMENSION_ORDER.indexOf(left.key) -
      JOB_MATCH_DIMENSION_ORDER.indexOf(right.key),
  );

  return [
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[0],
    "",
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[1],
    "",
    `- 总分：${overallScore ?? "-"} / 100`,
    `- 匹配等级：${overallLevelLabel(overallLevel)}`,
    `- 置信度：${confidenceLabel(confidence)}`,
    `- 摘要：${toInlineText(payload.summary)}`,
    `- 分析 ID：${analysis.analysis_id}`,
    `- 生成时间：${toInlineText(analysis.created_at)}`,
    "",
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[2],
    "",
    toListMarkdown(dimensionScores, dimensionToMarkdown, "暂无维度评分。"),
    "",
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[3],
    "",
    toListMarkdown(payload.missing_requirements, missingRequirementToMarkdown, "暂无明确缺口。"),
    "",
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[4],
    "",
    toListMarkdown(payload.interview_focus, (item) => `- ${toInlineText(item)}`, "暂无面试追问重点。"),
    "",
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[5],
    "",
    toListMarkdown(payload.suggested_questions, (item) => `- ${toInlineText(item)}`, "暂无建议问题。"),
    "",
    JOB_MATCH_MARKDOWN_SECTION_HEADINGS[6],
    "",
    `- ${JOB_MATCH_FOLLOW_UP_ANCHOR_TEXT}`,
  ].join("\n");
}

export function JobMatchResultView({ analysis, copyDisabled = false }: JobMatchResultViewProps) {
  const payload = analysis.result_payload;
  const overallScore = analysis.overall_score ?? payload.overall_score;
  const overallLevel = analysis.overall_level ?? payload.overall_level;
  const confidence = analysis.confidence ?? payload.confidence;
  const dimensionScores = useMemo(
    () =>
      [...payload.dimension_scores].sort(
        (left, right) =>
          JOB_MATCH_DIMENSION_ORDER.indexOf(left.key) -
          JOB_MATCH_DIMENSION_ORDER.indexOf(right.key),
      ),
    [payload.dimension_scores],
  );
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const [copyError, setCopyError] = useState<string | null>(null);
  const copyResetTimerRef = useRef<number | null>(null);
  const isCopyDisabled = copyDisabled || copyState === "copying";

  useEffect(() => {
    setCopyState("idle");
    setCopyError(null);
    if (copyResetTimerRef.current !== null) {
      window.clearTimeout(copyResetTimerRef.current);
      copyResetTimerRef.current = null;
    }

    return () => {
      if (copyResetTimerRef.current !== null) {
        window.clearTimeout(copyResetTimerRef.current);
        copyResetTimerRef.current = null;
      }
    };
  }, [analysis.analysis_id]);

  const copyMarkdownReport = async () => {
    if (isCopyDisabled) {
      return;
    }
    if (!navigator.clipboard?.writeText) {
      setCopyState("failed");
      setCopyError("当前浏览器不支持剪贴板写入，请手动复制结果内容。");
      return;
    }

    setCopyState("copying");
    setCopyError(null);
    try {
      await navigator.clipboard.writeText(buildJobMatchMarkdownReport(analysis));
      setCopyState("copied");
      copyResetTimerRef.current = window.setTimeout(() => {
        setCopyState("idle");
      }, 2200);
    } catch (error) {
      const message = error instanceof Error ? error.message : "复制失败，请检查浏览器权限。";
      setCopyState("failed");
      setCopyError(message);
    }
  };

  return (
    <Space direction="vertical" size={12} style={{ width: "100%" }}>
      <div>
        <Space align="baseline" wrap>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {overallScore ?? "-"}
          </Typography.Title>
          <Typography.Text type="secondary">/ 100</Typography.Text>
          <Tag color={levelColor(overallLevel)}>{overallLevelLabel(overallLevel)}</Tag>
          <Tag color={confidenceColor(confidence)}>置信度：{confidenceLabel(confidence)}</Tag>
        </Space>
        <Typography.Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
          {payload.summary}
        </Typography.Paragraph>
      </div>

      <Alert
        type="info"
        showIcon
        message="可作为模拟面试输入"
        description={JOB_MATCH_FOLLOW_UP_ANCHOR_TEXT}
      />

      <Space wrap>
        <Button
          icon={<CopyOutlined />}
          loading={copyState === "copying"}
          disabled={isCopyDisabled}
          onClick={() => {
            void copyMarkdownReport();
          }}
        >
          {copyState === "copied" ? "已复制" : "复制 Markdown"}
        </Button>
        {copyState === "copied" ? <Tag color="green">已复制到剪贴板</Tag> : null}
        {copyState === "failed" && copyError !== null ? <Tag color="red">{copyError}</Tag> : null}
      </Space>

      <div>
        <Typography.Text strong>维度评分</Typography.Text>
        <List
          size="small"
          dataSource={dimensionScores}
          renderItem={(dimension) => (
            <List.Item>
              <Space direction="vertical" size={2} style={{ width: "100%" }}>
                <Space wrap>
                  <Typography.Text strong>{JOB_MATCH_DIMENSION_LABELS[dimension.key]}</Typography.Text>
                  <Tag>{dimension.score} / {dimension.max_score}</Tag>
                  <Tag color={confidenceColor(dimension.confidence)}>
                    {confidenceLabel(dimension.confidence)}
                  </Tag>
                </Space>
                {dimension.key === "gap_risk" ? (
                  <Typography.Text type="secondary">{JOB_MATCH_GAP_RISK_HELPER}</Typography.Text>
                ) : null}
                <Typography.Text type="secondary">{dimension.rationale}</Typography.Text>
                {dimension.gaps.length > 0 ? (
                  <Typography.Text type="secondary">缺口：{dimension.gaps.join("；")}</Typography.Text>
                ) : null}
              </Space>
            </List.Item>
          )}
        />
      </div>

      <div>
        <Typography.Text strong>明显缺口</Typography.Text>
        {payload.missing_requirements.length === 0 ? (
          <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
            暂无明确缺口，建议在面试中继续核实证据深度。
          </Typography.Paragraph>
        ) : (
          <List
            size="small"
            dataSource={payload.missing_requirements}
            renderItem={(item) => (
              <List.Item>
                <Space direction="vertical" size={2}>
                  <Typography.Text>{item.reason}</Typography.Text>
                  <Typography.Text type="secondary">
                    来源：{item.requirement_chunk_id ?? "evidence_insufficient"} · 置信度：
                    {confidenceLabel(item.confidence)}
                  </Typography.Text>
                </Space>
              </List.Item>
            )}
          />
        )}
      </div>

      <div>
        <Typography.Text strong>面试追问重点</Typography.Text>
        {payload.interview_focus.length === 0 ? (
          <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
            暂无追问重点。
          </Typography.Paragraph>
        ) : (
          <List size="small" dataSource={payload.interview_focus} renderItem={(item) => <List.Item>{item}</List.Item>} />
        )}
      </div>

      <div>
        <Typography.Text strong>建议问题</Typography.Text>
        {payload.suggested_questions.length === 0 ? (
          <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
            暂无建议问题。
          </Typography.Paragraph>
        ) : (
          <List size="small" dataSource={payload.suggested_questions} renderItem={(item) => <List.Item>{item}</List.Item>} />
        )}
      </div>
    </Space>
  );
}

export function JobMatchPanel({
  bindingId,
  bindingLabel,
  onAnalysisCreated,
}: JobMatchPanelProps) {
  const availability = getJobMatchPanelAvailability(bindingId);
  const activeBindingId = availability.kind === "ready" ? availability.bindingId : null;
  const [analysis, setAnalysis] = useState<JobMatchAnalysis | null>(null);
  const [isLatestLoading, setIsLatestLoading] = useState<boolean>(false);
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [latestLoaded, setLatestLoaded] = useState<boolean>(false);

  const loadLatestAnalysis = async (targetBindingId: string) => {
    setIsLatestLoading(true);
    setErrorMessage(null);
    try {
      const latest = await fetchLatestJobMatchAnalysis(targetBindingId);
      setAnalysis(latest);
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setLatestLoaded(true);
      setIsLatestLoading(false);
    }
  };

  useEffect(() => {
    setAnalysis(null);
    setErrorMessage(null);
    setLatestLoaded(false);

    if (activeBindingId === null) {
      setIsLatestLoading(false);
      setLatestLoaded(true);
      return;
    }

    let isActive = true;
    setIsLatestLoading(true);
    void fetchLatestJobMatchAnalysis(activeBindingId)
      .then((latest) => {
        if (isActive) {
          setAnalysis(latest);
        }
      })
      .catch((error) => {
        if (isActive) {
          setErrorMessage(toErrorMessage(error));
        }
      })
      .finally(() => {
        if (isActive) {
          setLatestLoaded(true);
          setIsLatestLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [activeBindingId]);

  const createAnalysis = async () => {
    if (activeBindingId === null || isCreating) {
      return;
    }
    setIsCreating(true);
    setErrorMessage(null);
    try {
      const created = await createJobMatchAnalysis({
        resume_job_binding_id: activeBindingId,
      });
      setAnalysis(created);
      onAnalysisCreated?.(created);
      message.success("已生成匹配分析");
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
      message.error("匹配分析生成失败");
    } finally {
      setLatestLoaded(true);
      setIsCreating(false);
    }
  };

  return (
    <Card
      size="small"
      title="岗位匹配分析"
      extra={
        activeBindingId === null ? null : (
          <Button
            size="small"
            icon={<ReloadOutlined />}
            loading={isLatestLoading}
            onClick={() => {
              void loadLatestAnalysis(activeBindingId);
            }}
          >
            刷新
          </Button>
        )
      }
    >
      {activeBindingId === null ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="需要先绑定简历，才能生成岗位匹配分析。"
        />
      ) : null}

      {activeBindingId !== null && bindingLabel ? (
        <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
          当前绑定：{bindingLabel}
        </Typography.Paragraph>
      ) : null}

      {activeBindingId !== null && isLatestLoading && analysis === null ? (
        <LoadingState compact message="正在读取最近一次匹配分析..." />
      ) : null}

      {activeBindingId !== null && errorMessage !== null ? (
        <Alert
          type="error"
          showIcon
          message="岗位匹配分析不可用"
          description={errorMessage}
          action={
            <Space>
              <Button
                size="small"
                onClick={() => {
                  void loadLatestAnalysis(activeBindingId);
                }}
              >
                重新读取
              </Button>
              <Button
                size="small"
                type="primary"
                loading={isCreating}
                onClick={() => {
                  void createAnalysis();
                }}
              >
                重新生成
              </Button>
            </Space>
          }
          style={{ marginBottom: 12 }}
        />
      ) : null}

      {activeBindingId !== null && latestLoaded && analysis === null && errorMessage === null ? (
        <EmptyState
          compact
          title="暂无匹配分析"
          description="当前岗位已绑定简历，可以生成一次岗位匹配分析。"
          action={
            <Button
              type="primary"
              loading={isCreating}
              disabled={!availability.canCreate || isCreating}
              onClick={() => {
                void createAnalysis();
              }}
            >
              生成匹配分析
            </Button>
          }
        />
      ) : null}

      {analysis !== null ? (
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          {isLatestLoading ? (
            <Typography.Text type="secondary">正在刷新最近一次结果...</Typography.Text>
          ) : null}
          <JobMatchResultView analysis={analysis} copyDisabled={isCreating || isLatestLoading} />
          <Button
            type="primary"
            loading={isCreating}
            disabled={isCreating}
            onClick={() => {
              void createAnalysis();
            }}
          >
            重新生成匹配分析
          </Button>
        </Space>
      ) : null}
    </Card>
  );
}
