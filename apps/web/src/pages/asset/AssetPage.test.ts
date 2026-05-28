import {
  ASSET_DETAIL_ACTIONS,
  ASSET_PAGE_SEARCH_PLACEHOLDER,
  ASSET_PAGE_TABLE_COLUMN_KEYS,
  ASSET_PAGE_TOOLBAR_CONTROL_ORDER,
  ASSET_PAGE_VIEW_STATES,
  ASSET_STATUS_ACTIONS,
  ASSET_TYPE_FILTER_KIND,
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
type AssetFilterUsesTypeAndSource = Expect<Equal<typeof ASSET_TYPE_FILTER_KIND, "asset_type_and_source">>;
type AssetToolbarOrderMatchesInterviewPage = Expect<
  Equal<typeof ASSET_PAGE_TOOLBAR_CONTROL_ORDER, readonly ["primary_action", "filters", "refresh", "search"]>
>;
type AssetSearchPlaceholderIsStable = Expect<Equal<typeof ASSET_PAGE_SEARCH_PLACEHOLDER, "搜索资产">>;
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
