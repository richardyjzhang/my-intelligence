declare namespace API {
  // 标签
  type Tag = {
    id?: number;
    name: string;
    color: string;
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

  // 搜索结果
  type SearchResult = {
    id: number;
    name: string;
    description?: string;
    tagIds?: number[];
    match?: string;
  };
}
