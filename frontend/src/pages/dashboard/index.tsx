import React, { useState } from "react";
import { Card } from "antd";
import {} from "@ant-design/icons";
import { useRequest } from "ahooks";
import { fetchTagsRequest } from "../service";
import styles from "./index.css";

const DashboardPage: React.FC = () => {
  // 各种网络请求
  const { runAsync: fetchTags, data: tags } = useRequest(fetchTagsRequest);

  return <Card className={styles.mainCard} title="情报检索"></Card>;
};

export default DashboardPage;
