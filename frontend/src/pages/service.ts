import request from "@/utils/request";

// 登录请求
export async function postLoginRequest(user: API.LoginUser) {
  const response = await request("/api/my-intelligence/login", {
    method: "POST",
    data: user,
  });
  return response;
}

// 获取标签列表
export async function fetchTagsRequest() {
  const response = await request("/api/my-intelligence/tags");
  return response;
}

// 新增一个标签
export async function addOneTagRequest(tag: API.Tag) {
  await request("/api/my-intelligence/tags", {
    method: "POST",
    data: tag,
  });
}

// 更新一个标签
export async function updateOneTagRequest(tag: API.Tag) {
  await request(`/api/my-intelligence/tags/${tag.id}`, {
    method: "PUT",
    data: tag,
  });
}

// 删除某个标签
export async function deleteOneTagRequest(id: number) {
  await request(`/api/my-intelligence/tags/${id}`, {
    method: "DELETE",
  });
}

// 获取文档列表
export async function fetchDocsRequest() {
  const response = await request("/api/my-intelligence/docs");
  return response;
}

// 删除某个文档
export async function deleteOneDocRequest(id: number) {
  await request(`/api/my-intelligence/docs/${id}`, {
    method: "DELETE",
  });
}

// 新增一个文档
export async function addOneDocRequest(doc: API.Doc, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", doc.name);
  formData.append("description", doc.description || "");
  return await request.postForm("/api/my-intelligence/docs", formData);
}

// 更新一个文档
export async function updateOneDocRequest(doc: API.Doc) {
  await request(`/api/my-intelligence/docs/${doc.id}`, {
    method: "PUT",
    data: doc,
  });
}

// 设置文档的标签
export async function updateOneDocTagRequest(docId: number, tagIds: number[]) {
  await request(`/api/my-intelligence/docs/tags/${docId}`, {
    method: "POST",
    data: tagIds,
  });
}
