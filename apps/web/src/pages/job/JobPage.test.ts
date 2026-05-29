import {
  JOB_HEADER_CONTROL_ORDER,
  JOB_ROW_ACTION_KEYS,
  JOB_SEARCH_WIDTH,
} from "./JobPage";
import { JOB_API_PATHS } from "../../entities/job/api/jobApi";

type Equal<Actual, Expected> =
  (<Value>() => Value extends Actual ? 1 : 2) extends
  (<Value>() => Value extends Expected ? 1 : 2)
    ? true
    : false;

type Expect<Condition extends true> = Condition;

type JobHeaderPlacesActionsBeforeSearch = Expect<
  Equal<typeof JOB_HEADER_CONTROL_ORDER, readonly ["actions", "search"]>
>;
type JobSearchWidthMatchesInterviewPage = Expect<Equal<typeof JOB_SEARCH_WIDTH, 360>>;
type JobRowActionsExposeSoftDelete = Expect<
  Equal<typeof JOB_ROW_ACTION_KEYS, readonly ["view", "edit", "archive", "delete"]>
>;
type JobApiPathsExposeRealDelete = Expect<
  Equal<
    typeof JOB_API_PATHS,
    {
      readonly list: "/jobs";
      readonly detail: "/jobs/:job_id";
      readonly delete: "/jobs/:job_id";
    }
  >
>;
