import request from "@/utils/request";

export async function postLogoutRequest() {
  const response = await request("/api/my-intelligence/logout", {
    method: "POST",
  });
  return response;
}
