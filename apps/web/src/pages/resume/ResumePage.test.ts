import {
  RESUME_DETAIL_FIELD_KEYS,
  RESUME_EDIT_FIELD_KEYS,
  RESUME_LINK_JOB_FIELD_KEYS,
  RESUME_LINK_JOB_CLEAR_SELECTION_CONTROL,
  RESUME_LINK_JOB_EMPTY_SELECTION_ACTION,
  RESUME_LINK_JOB_MODAL_TITLE,
  RESUME_LINK_JOB_SAVE_BUTTON_LABEL,
  RESUME_LINK_JOB_SELECTION_KIND,
  RESUME_HEADER_CONTROL_ORDER,
  RESUME_ROW_ACTION_KEYS,
  RESUME_SEARCH_ENTER_BUTTON_KIND,
  RESUME_SEARCH_FIELD_KEYS,
  RESUME_SEARCH_PLACEHOLDER,
  RESUME_TABLE_COLUMN_KEYS,
  RESUME_TITLE_ACTION_KEY,
  filterResumesBySearch,
} from "./ResumePage";
import type { ResumeSummary } from "../../entities/resume/model/types";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type ResumeTableColumnKeys = typeof RESUME_TABLE_COLUMN_KEYS;

type ResumeTableIncludesAcceptanceColumns = Expect<
  Equal<
    ResumeTableColumnKeys,
    readonly [
      "title",
      "status",
      "score",
      "linked_job",
      "current_version_id",
      "updated_at",
      "actions",
    ]
  >
>;

type ResumeSearchFieldKeys = typeof RESUME_SEARCH_FIELD_KEYS;

type ResumeSearchCoversNameAndStatus = Expect<
  Equal<ResumeSearchFieldKeys, readonly ["title", "file_name", "resume_id", "status"]>
>;

type ResumeSearchPlaceholderIsExplicit = Expect<
  Equal<typeof RESUME_SEARCH_PLACEHOLDER, "搜索简历名称、状态">
>;

type ResumeSearchUsesIconSubmit = Expect<
  Equal<typeof RESUME_SEARCH_ENTER_BUTTON_KIND, "icon">
>;

type ResumeHeaderPlacesActionsBeforeSearch = Expect<
  Equal<typeof RESUME_HEADER_CONTROL_ORDER, readonly ["actions", "search"]>
>;

type ResumeRowActionKeys = typeof RESUME_ROW_ACTION_KEYS;

type ResumeRowActionsCoverAcceptanceButtons = Expect<
  Equal<ResumeRowActionKeys, readonly ["link_job", "edit_resume", "archive_resume"]>
>;

type ResumeTitleActionOpensDetail = Expect<
  Equal<typeof RESUME_TITLE_ACTION_KEY, "open_detail">
>;

type ResumeDetailFieldKeys = typeof RESUME_DETAIL_FIELD_KEYS;

type ResumeDetailDrawerShowsCoreFields = Expect<
  Equal<
    ResumeDetailFieldKeys,
    readonly [
      "title",
      "resume_id",
      "score",
      "linked_job",
      "status",
      "current_version_id",
      "updated_at",
      "markdown_text",
    ]
  >
>;

type ResumeEditFieldKeys = typeof RESUME_EDIT_FIELD_KEYS;

type ResumeEditDrawerEditsTitleAndBody = Expect<
  Equal<ResumeEditFieldKeys, readonly ["title", "markdown_text"]>
>;

type ResumeLinkJobFieldKeys = typeof RESUME_LINK_JOB_FIELD_KEYS;

type ResumeLinkJobModalSelectsJobAndSavesBinding = Expect<
  Equal<ResumeLinkJobFieldKeys, readonly ["resume_id", "job_ids", "resume_job_binding_ids"]>
>;

type ResumeLinkJobEmptySelectionUnbindsExistingBinding = Expect<
  Equal<typeof RESUME_LINK_JOB_EMPTY_SELECTION_ACTION, "unbind_existing_binding">
>;

type ResumeLinkJobSelectionUsesCheckboxes = Expect<
  Equal<typeof RESUME_LINK_JOB_SELECTION_KIND, "checkbox">
>;

type ResumeLinkJobHasNoClearSelectionButton = Expect<
  Equal<typeof RESUME_LINK_JOB_CLEAR_SELECTION_CONTROL, "none">
>;

type ResumeLinkJobModalTitleIsExplicit = Expect<
  Equal<typeof RESUME_LINK_JOB_MODAL_TITLE, "关联岗位">
>;

type ResumeLinkJobSaveButtonIsExplicit = Expect<
  Equal<typeof RESUME_LINK_JOB_SAVE_BUTTON_LABEL, "保存关联">
>;

const sampleResumes = [
  {
    resume_id: "res_alpha",
    title: "前端工程师简历",
    updated_at: "2026-05-18T10:00:00Z",
    status: "active",
    current_version_ref: {
      resource_type: "resume",
      resource_id: "res_alpha",
      version_id: "res_alpha_v1",
    },
    created_at: "2026-05-18T09:00:00Z",
  },
  {
    resume_id: "res_archived",
    title: "后端工程师简历",
    updated_at: "2026-05-18T11:00:00Z",
    status: "archived",
    current_version_ref: {
      resource_type: "resume",
      resource_id: "res_archived",
      version_id: "res_archived_v1",
    },
    created_at: "2026-05-18T09:30:00Z",
  },
] satisfies ResumeSummary[];

const filteredByTitle: ResumeSummary[] = filterResumesBySearch(sampleResumes, "前端");
const filteredByStatus: ResumeSummary[] = filterResumesBySearch(sampleResumes, "archived");

void filteredByTitle;
void filteredByStatus;
