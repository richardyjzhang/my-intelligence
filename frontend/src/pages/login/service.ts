import request from "@/utils/request";

export async function postLoginRequest(user: API.LoginUser) {
  const response = await request("/api/login", {
    method: "POST",
    data: user,
  });
  return response;
}
