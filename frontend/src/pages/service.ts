import request from "@/utils/request";

// 登录请求
export async function postLoginRequest(user: API.LoginUser) {
  const response = await request("/api/login", {
    method: "POST",
    data: user,
  });
  return response;
}

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

// 获取文档列表
export async function fetchDocsRequest() {
  const response = await request("/api/docs");
  return response;
}

// 删除某个文档
export async function deleteOneDocRequest(id: number) {
  await request(`/api/docs/${id}`, {
    method: "DELETE",
  });
}

// 新增一个文档
export async function addOneDocRequest(doc: API.Doc, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", doc.name);
  formData.append("description", doc.description || "");
  return await request.postForm("/api/docs", formData);
}

// 更新一个文档
export async function updateOneDocRequest(doc: API.Doc) {
  await request(`/api/docs/${doc.id}`, {
    method: "PUT",
    data: doc,
  });
}

// 设置文档的标签
export async function updateOneDocTagRequest(docId: number, tagIds: number[]) {
  await request(`/api/docs/tags/${docId}`, {
    method: "POST",
    data: tagIds,
  });
}
