declare namespace API {
  // 标签
  type Tag = {
    id?: number;
    name: string;
  };

  // 文档
  type Doc = {
    id?: number;
    name: string;
    ct?: string;
    description?: string;
    status?: number;
    tags?: number[];
  };
}
