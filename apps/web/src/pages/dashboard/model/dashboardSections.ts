export type DashboardFrameMode =
  | "default"
  | "loading"
  | "error"
  | "empty"
  | "insufficient"
  | "disabled";

export type DashboardSectionState = "default" | "loading" | "empty" | "error" | "insufficient" | "disabled";

export type DashboardSectionId = "above" | "todo" | "activity";

export type DashboardSectionStateMap = Record<DashboardSectionId, DashboardSectionState>;

export const DASHBOARD_FRAME_MODES: DashboardFrameMode[] = [
  "default",
  "loading",
  "error",
  "empty",
  "insufficient",
  "disabled",
];

export const DASHBOARD_FRAME_MODE_SET = new Set<DashboardFrameMode>(DASHBOARD_FRAME_MODES);

export const DASHBOARD_SECTION_STATE_BY_FRAME: Record<DashboardFrameMode, DashboardSectionStateMap> = {
  default: {
    above: "default",
    todo: "default",
    activity: "default",
  },
  loading: {
    above: "loading",
    todo: "loading",
    activity: "loading",
  },
  error: {
    above: "error",
    todo: "error",
    activity: "error",
  },
  empty: {
    above: "empty",
    todo: "empty",
    activity: "empty",
  },
  insufficient: {
    above: "default",
    todo: "insufficient",
    activity: "default",
  },
  disabled: {
    above: "disabled",
    todo: "disabled",
    activity: "disabled",
  },
};

export function readDashboardFrameMode(raw = ""): DashboardFrameMode {
  const query = raw || window.location.search;
  const fromSearch = new URLSearchParams(query).get("frame");
  if (fromSearch !== null && DASHBOARD_FRAME_MODE_SET.has(fromSearch as DashboardFrameMode)) {
    return fromSearch as DashboardFrameMode;
  }
  return "default";
}
