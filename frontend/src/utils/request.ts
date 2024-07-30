import axios from "axios";
import { history } from "umi";
import { message } from "antd";

const request = axios.create({
  baseURL: `${document.location.origin}`,
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

    return error.response.message;
  }
);

export default request;
