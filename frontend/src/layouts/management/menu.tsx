import React from "react";
import { Menu } from "antd";
import { useLocation, history } from "umi";
import styles from "./index.css";

const MyMenu: React.FC = () => {
  const location = useLocation();

  return (
    <Menu
      className={styles.menu}
      mode="inline"
      style={{
        marginTop: "1rem",
      }}
      selectedKeys={[location.pathname]}
      onClick={({ key }) => {
        history.push(key);
      }}
      items={[
        {
          key: "/dashboard",
          label: "情报检索",
        },
        {
          key: "/doc-management",
          label: "文档管理",
        },
        {
          key: "/system-management",
          label: "系统管理",
          children: [
            {
              key: "/tag-management",
              label: "标签管理",
            },
          ],
        },
      ]}
    />
  );
};

export default MyMenu;
