import {
  WEAKNESS_DETAIL_SECTIONS,
  WEAKNESS_LIST_ACTION_KEYS,
  WEAKNESS_PAGE_LEFT_CONTROL_KEYS,
  WEAKNESS_PAGE_SEARCH_PLACEHOLDER,
  WEAKNESS_PAGE_SEARCH_WIDTH,
  WEAKNESS_PAGE_SECONDARY_CONTROL_KEYS,
  WEAKNESS_PAGE_TABLE_COLUMN_KEYS,
  WEAKNESS_PAGE_TOOLBAR_CONTROL_ORDER,
  WEAKNESS_PAGE_VIEW_STATES,
  WEAKNESS_SELECTED_ACTION_TARGET,
  WEAKNESS_STATUS_ACTIONS,
} from "./WeaknessPage";
import { WEAKNESS_API_PATHS, type FetchWeaknessesParams } from "../../entities/weakness/api/weaknessApi";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type WeaknessApiPathsAreStable = Expect<
  Equal<
    typeof WEAKNESS_API_PATHS,
    {
      readonly list: "/weaknesses";
      readonly detail: "/weaknesses/:weakness_id";
      readonly updateStatus: "/weaknesses/:weakness_id/status";
      readonly delete: "/weaknesses/:weakness_id";
    }
  >
>;
type WeaknessTableColumnsAreStable = Expect<
  Equal<
    typeof WEAKNESS_PAGE_TABLE_COLUMN_KEYS,
    readonly ["selection", "title", "source", "severity", "status", "updated_at", "actions"]
  >
>;
type WeaknessPageStatesAreVisible = Expect<
  Equal<typeof WEAKNESS_PAGE_VIEW_STATES, readonly ["loading", "empty", "error", "loaded"]>
>;
type WeaknessStatusActionsAreStable = Expect<
  Equal<typeof WEAKNESS_STATUS_ACTIONS, readonly ["mark_low_priority", "mark_ignored", "mark_resolved", "reopen"]>
>;
type WeaknessListActionsExposeSoftDelete = Expect<
  Equal<typeof WEAKNESS_LIST_ACTION_KEYS, readonly ["view", "mark_resolved", "delete"]>
>;
type WeaknessDetailSectionsAreStable = Expect<
  Equal<
    typeof WEAKNESS_DETAIL_SECTIONS,
    readonly ["evidence", "training_actions", "related_records", "status_history_hint"]
  >
>;
type WeaknessSelectedActionTargetsPolish = Expect<
  Equal<typeof WEAKNESS_SELECTED_ACTION_TARGET, "interview_route">
>;
type WeaknessLeftControlsKeepPrimaryAndRefresh = Expect<Equal<typeof WEAKNESS_PAGE_LEFT_CONTROL_KEYS, readonly ["primary_action", "refresh"]>>;
type WeaknessSecondaryControlsStayOnRight = Expect<
  Equal<typeof WEAKNESS_PAGE_SECONDARY_CONTROL_KEYS, readonly ["search"]>
>;
type WeaknessToolbarOrderDropsMockFilters = Expect<
  Equal<typeof WEAKNESS_PAGE_TOOLBAR_CONTROL_ORDER, readonly ["primary_action", "refresh", "search"]>
>;
type WeaknessSearchPlaceholderIsStable = Expect<Equal<typeof WEAKNESS_PAGE_SEARCH_PLACEHOLDER, "搜索薄弱项">>;
type WeaknessSearchWidthMatchesInterviewPage = Expect<Equal<typeof WEAKNESS_PAGE_SEARCH_WIDTH, 360>>;
type WeaknessSearchParamUsesQ = Expect<Equal<FetchWeaknessesParams["q"], string | undefined>>;
