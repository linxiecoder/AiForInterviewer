import { request, buildSuccessData } from "../../../shared/api/client";
import type { AssetDetail, AssetSummary } from "../model/types";

export const ASSET_API_PATHS = {
  list: "/assets",
  detail: "/assets/:asset_id",
  archive: "/assets/:asset_id/archive",
  unarchive: "/assets/:asset_id/unarchive",
} as const;

export type FetchAssetsParams = {
  status?: string;
  asset_type?: string;
  q?: string;
};

export type CreateAssetRequest = {
  title: string;
  asset_type: string;
  content: string;
  summary?: string;
};

function replaceAssetId(path: string, assetId: string): string {
  return path.replace(":asset_id", encodeURIComponent(assetId));
}

function toQuery(params: FetchAssetsParams): string {
  const query = new URLSearchParams();
  if (params.status) {
    query.set("status", params.status);
  }
  if (params.asset_type) {
    query.set("asset_type", params.asset_type);
  }
  if (params.q?.trim()) {
    query.set("q", params.q.trim());
  }
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export async function fetchAssets(params: FetchAssetsParams = {}): Promise<AssetSummary[]> {
  const response = await request<AssetSummary[]>(`${ASSET_API_PATHS.list}${toQuery(params)}`);
  return buildSuccessData(response) ?? [];
}

export async function fetchAsset(assetId: string): Promise<AssetDetail> {
  const response = await request<AssetDetail>(replaceAssetId(ASSET_API_PATHS.detail, assetId));
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("资产详情返回为空");
  }
  return data;
}

export async function createAsset(payload: CreateAssetRequest): Promise<AssetDetail> {
  const response = await request<AssetDetail>(ASSET_API_PATHS.list, {
    method: "POST",
    body: payload,
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("资产创建返回为空");
  }
  return data;
}

export async function archiveAsset(assetId: string): Promise<AssetDetail> {
  const response = await request<AssetDetail>(replaceAssetId(ASSET_API_PATHS.archive, assetId), {
    method: "POST",
    body: {},
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("资产归档返回为空");
  }
  return data;
}

export async function unarchiveAsset(assetId: string): Promise<AssetDetail> {
  const response = await request<AssetDetail>(replaceAssetId(ASSET_API_PATHS.unarchive, assetId), {
    method: "POST",
    body: {},
  });
  const data = buildSuccessData(response);
  if (data === null) {
    throw new Error("取消归档返回为空");
  }
  return data;
}
