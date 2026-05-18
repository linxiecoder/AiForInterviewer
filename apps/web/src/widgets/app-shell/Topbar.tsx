import { Input } from "antd";
import { useCallback } from "react";
import { TOPBAR_SEARCH_PLACEHOLDER } from "./model/navigation";
import styles from "./Topbar.module.css";

const { Search } = Input;

export function Topbar() {
  const onSearch = useCallback((_value: string) => {
    return undefined;
  }, []);

  return (
    <div className={styles.topbar}>
      <Search
        placeholder={TOPBAR_SEARCH_PLACEHOLDER}
        className={styles.searchInput}
        onSearch={onSearch}
        allowClear
      />
    </div>
  );
}
