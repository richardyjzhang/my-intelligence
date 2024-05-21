import axios from "axios";
import { history } from "umi";
import { message } from "antd";

const request = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// 创建响应拦截
request.interceptors.response.use(
  (res) => {
    let data = res.data;
    return data;
  },
  (error) => {
    let msg = "";
    if (error && error.response) {
      switch (error.response.status) {
        case 401:
          history.push("/login");
          break;
        case 400:
          message.error("不允许的操作请求");
          break;
        default:
          message.error("服务端错误，请联系管理员");
          break;
      }
    }
    return Promise.reject(msg);
  }
);

export default request;
