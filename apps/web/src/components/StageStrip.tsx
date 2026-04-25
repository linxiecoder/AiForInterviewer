export type WorkflowStageStatus = "current" | "done" | "waiting";

export interface WorkflowStage {
  id: string;
  label: string;
  description: string;
  status: WorkflowStageStatus;
}

const statusText: Record<WorkflowStageStatus, string> = {
  current: "当前",
  done: "完成",
  waiting: "待处理",
};

export function StageStrip({ stages }: { stages: WorkflowStage[] }) {
  return (
    <ol className="stage-strip" aria-label="首切片流程状态">
      {stages.map((stage) => (
        <li className={`stage-item stage-item-${stage.status}`} key={stage.id}>
          <div>
            <span className="stage-label">{stage.label}</span>
            <p>{stage.description}</p>
          </div>
          <span className="stage-status">{statusText[stage.status]}</span>
        </li>
      ))}
    </ol>
  );
}
