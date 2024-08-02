import React, { useState } from "react";
import {
  Button,
  Card,
  Divider,
  Form,
  Input,
  List,
  Select,
  Space,
  Tag,
} from "antd";
import { CloudDownloadOutlined } from "@ant-design/icons";
import { useRequest } from "ahooks";
import { fetchTagsRequest, fetchDocsAllinSearchRequest } from "../service";
import styles from "./index.css";

const DashboardPage: React.FC = () => {
  // 各种网络请求
  const { data: tags } = useRequest(fetchTagsRequest);
  const { runAsync: fetchDocsAllinSearch } = useRequest(
    fetchDocsAllinSearchRequest,
    {
      onSuccess: (data: API.SearchResult[]) => {
        if (data) {
          setResults([...data]);
        }
      },
    }
  );

  // 搜索结果
  const [results, setResults] = useState<API.SearchResult[]>([]);

  const onSearch = (values: { type: string; keyword: string }) => {
    if (values.type === "allin") {
      fetchDocsAllinSearch(values.keyword, []);
    }
  };

  return (
    <Card className={styles.mainCard} title="情报检索">
      <div className={styles.searchArea}>
        <Form
          initialValues={{
            type: "allin",
          }}
          onFinish={onSearch}
        >
          <Space.Compact className={styles.searchBar}>
            <Form.Item name="type" noStyle>
              <Select
                className={styles.searchMethodSelect}
                options={[
                  { value: "allin", label: "智能检索" },
                  {
                    value: "filename",
                    label: "文件名检索",
                  },
                  {
                    value: "content",
                    label: "内容检索",
                  },
                ]}
              />
            </Form.Item>
            <Form.Item name="keyword" className={styles.searchContent}>
              <Input allowClear className={styles.searchContentInput} />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className={styles.searchSubmitButton}
            >
              搜索
            </Button>
          </Space.Compact>
        </Form>
      </div>
      <div className={styles.searchResultsArea}>
        <List
          dataSource={results}
          pagination={{
            onChange: (page) => {
              console.log(page);
            },
            pageSize: 5,
          }}
          renderItem={(r) => (
            <>
              <Divider />
              <div key={r.id} className={styles.resultArea}>
                <div className={styles.resultInfo}>
                  <div className={styles.resultTitle}>{r.name}</div>
                  <div className={styles.resultTagBar}>
                    {r.tagIds?.map((tagId) => {
                      const tag: API.Tag = tags?.find(
                        (t: API.Tag) => t.id === tagId
                      );
                      if (!tag) {
                        return null;
                      }
                      return <Tag color={tag.color}>{tag.name}</Tag>;
                    })}
                    <Divider type="vertical" />
                    <div className={styles.resultDescription}>
                      {r.description || "暂无描述"}
                    </div>
                  </div>
                </div>
                <div className={styles.resultDownload}>
                  <Button
                    type="link"
                    icon={<CloudDownloadOutlined />}
                    target="blank"
                    href={`/api/my-intelligence/docs/download/${r.id}`}
                  >
                    下载
                  </Button>
                </div>
              </div>
            </>
          )}
        />
      </div>
    </Card>
  );
};

export default DashboardPage;
