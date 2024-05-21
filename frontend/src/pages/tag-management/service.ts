import request from "@/utils/request";

// 获取标签列表
export async function fetchTagsRequest() {
  const response = await request("/api/tags");
  return response;
}

// 新增一个标签
export async function addOneTagRequest(tag: API.Tag) {
  await request("/api/tags", {
    method: "POST",
    data: tag,
  });
}

// 更新一个标签
export async function updateOneTagRequest(tag: API.Tag) {
  await request(`/api/tags/${tag.id}`, {
    method: "PUT",
    data: tag,
  });
}

// 删除某个标签
export async function deleteOneTagRequest(id: number) {
  await request(`/api/tags/${id}`, {
    method: "DELETE",
  });
}
