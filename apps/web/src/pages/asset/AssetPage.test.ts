import {
  ASSET_DETAIL_ACTIONS,
  ASSET_LIST_ACTION_KEYS,
  ASSET_PAGE_SEARCH_PLACEHOLDER,
  ASSET_PAGE_SEARCH_WIDTH,
  ASSET_PAGE_TABLE_COLUMN_KEYS,
  ASSET_PAGE_LEFT_CONTROL_KEYS,
  ASSET_PAGE_SECONDARY_CONTROL_KEYS,
  ASSET_PAGE_TOOLBAR_CONTROL_ORDER,
  ASSET_PAGE_VIEW_STATES,
  ASSET_STATUS_ACTIONS,
} from "./AssetPage";
import { ASSET_API_PATHS, type CreateAssetRequest, type FetchAssetsParams } from "../../entities/asset/api/assetApi";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type AssetApiPathsAreStable = Expect<
  Equal<
    typeof ASSET_API_PATHS,
    {
      readonly list: "/assets";
      readonly detail: "/assets/:asset_id";
      readonly archive: "/assets/:asset_id/archive";
      readonly unarchive: "/assets/:asset_id/unarchive";
      readonly delete: "/assets/:asset_id";
    }
  >
>;
type AssetTableColumnsAreStable = Expect<
  Equal<
    typeof ASSET_PAGE_TABLE_COLUMN_KEYS,
    readonly ["title", "asset_type", "source", "status", "updated_at", "actions"]
  >
>;
type AssetPageStatesAreVisible = Expect<
  Equal<typeof ASSET_PAGE_VIEW_STATES, readonly ["loading", "empty", "error", "loaded"]>
>;
type AssetActionsAreExplicit = Expect<
  Equal<typeof ASSET_STATUS_ACTIONS, readonly ["archive", "unarchive"]>
>;
type AssetDetailHasNoCopyAction = Expect<Equal<typeof ASSET_DETAIL_ACTIONS, readonly ["view_source", "archive", "unarchive"]>>;
type AssetListActionsExposeSoftDelete = Expect<Equal<typeof ASSET_LIST_ACTION_KEYS, readonly ["view", "archive", "delete"]>>;
type AssetLeftControlsKeepPrimaryAndRefresh = Expect<Equal<typeof ASSET_PAGE_LEFT_CONTROL_KEYS, readonly ["primary_action", "refresh"]>>;
type AssetSecondaryControlsStayOnRight = Expect<
  Equal<typeof ASSET_PAGE_SECONDARY_CONTROL_KEYS, readonly ["search"]>
>;
type AssetToolbarOrderDropsMockFilters = Expect<
  Equal<typeof ASSET_PAGE_TOOLBAR_CONTROL_ORDER, readonly ["primary_action", "refresh", "search"]>
>;
type AssetSearchPlaceholderIsStable = Expect<Equal<typeof ASSET_PAGE_SEARCH_PLACEHOLDER, "搜索资产">>;
type AssetSearchWidthMatchesInterviewPage = Expect<Equal<typeof ASSET_PAGE_SEARCH_WIDTH, 360>>;
type AssetSearchParamUsesQ = Expect<Equal<FetchAssetsParams["q"], string | undefined>>;
type AssetCreateRequestShapeIsStable = Expect<
  Equal<
    CreateAssetRequest,
    {
      title: string;
      asset_type: string;
      content: string;
      summary?: string;
    }
  >
>;
