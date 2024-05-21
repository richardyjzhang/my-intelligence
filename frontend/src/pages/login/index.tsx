import {
  Button,
  ConfigProvider,
  Divider,
  Form,
  Input,
  message,
  Row,
} from "antd";
import { SHA256 } from "crypto-js";
import React from "react";
import { useRequest } from "ahooks";
import styles from "./index.css";
import { postLoginRequest } from "../service";
import { history } from "umi";

const LoginPage: React.FC = () => {
  const { run: login } = useRequest(postLoginRequest, {
    manual: true,
    onSuccess: (data) => {
      const result = data as API.LoginResult;
      if (result.success) {
        message.success("登录成功");
        history.push("/");
      } else {
        message.error(result.message);
      }
    },
  });

  // 密码加密
  const onFormFinished = (values: API.LoginUser) => {
    if (!values.username || !values.password) {
      message.error("请输入用户名或密码");
      return;
    }
    login({
      ...values,
      password: SHA256(`${values.password}MYINTELLIGENCE`)
        .toString()
        .toUpperCase(),
    });
  };

  return (
    <div className={styles.root}>
      <div className={styles.loginWrapper}>
        <div className={styles.loginCard}>
          <div className={styles.loginTitle}>
            <img className={styles.loginIcon} src="icon.png" />
            <div className={styles.loginTitleText}>智能情报管理系统</div>
          </div>
          <ConfigProvider
            theme={{
              token: {
                colorPrimary: "#2D3047BB",
              },
            }}
          >
            <Divider className={styles.loginDivider} />
            <Form onFinish={onFormFinished}>
              <Form.Item name="username">
                <Input placeholder="请输入用户名" />
              </Form.Item>
              <Form.Item name="password">
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                className={styles.loginBtn}
              >
                登录
              </Button>
            </Form>
          </ConfigProvider>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
