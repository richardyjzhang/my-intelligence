import { Outlet, history } from "umi";
import { ConfigProvider, Dropdown } from "antd";
import MyMenu from "./menu";
import { postLogoutRequest } from "./service";
import styles from "./index.css";

export default function Layout() {
  // 右上角用户名的下拉菜单选项
  const userMenuItems = [
    {
      key: "editPassword",
      label: "修改密码",
      onClick: () => {
        console.log("TODO: 修改密码");
      },
    },
    {
      key: "logout",
      label: "退出登录",
      onClick: () => {
        history.push("/login");
        postLogoutRequest();
      },
    },
  ];

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#2D3047BB",
        },
      }}
    >
      <div className={styles.root}>
        <nav className={styles.nav}>
          <img className={styles.icon} src="icon.png" />
          <div className={styles.title}>智能情报管理系统</div>
          <div className={styles.space} />
          <div>
            <Dropdown menu={{ items: userMenuItems }}>
              <div className={styles.userName}>管理员</div>
            </Dropdown>
          </div>
        </nav>
        <div className={styles.body}>
          <MyMenu />
          <main className={styles.main}>
            <Outlet />
          </main>
        </div>
      </div>
    </ConfigProvider>
  );
}
