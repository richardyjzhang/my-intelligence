import React, { useState } from "react";
import { Button, Card, Divider, Form, Input, Select, Space, Tag } from "antd";
import { CloudDownloadOutlined } from "@ant-design/icons";
import { useRequest } from "ahooks";
import { fetchTagsRequest } from "../service";
import styles from "./index.css";

const DashboardPage: React.FC = () => {
  // 各种网络请求
  const { runAsync: fetchTags, data: tags } = useRequest(fetchTagsRequest);

  // 搜索结果
  const [results, setResults] = useState<API.SearchResult[]>([
    {
      id: 589561819922432,
      name: "宁靖盐公司桥梁养护辅助决策技术体系研究响应文件(东衢).doc",
      description:
        "宁靖盐公司养护决策投标文件，主要根据病害和病害发展趋势进行单桥综合评估以及桥梁群优先级排序",
      tags: [589557650784256, 589558007300096, 589558288318464],
    },
    {
      id: 589561819922433,
      name: "宁靖盐公司桥梁养护辅助决策技术体系研究响应文件(东衢).doc",
      description:
        "宁靖盐公司养护决策投标文件，主要根据病害和病害发展趋势进行单桥综合评估以及桥梁群优先级排序",
      tags: [589557650784256, 589558007300096, 589558288318464],
    },
  ]);

  const onSearch = (values: { type: string; keywords: string }) => {
    console.log(values);
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
            <Form.Item name="keywords" className={styles.searchContent}>
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
        {results.map((r) => (
          <>
            <Divider />
            <div key={r.id} className={styles.resultArea}>
              <div className={styles.resultInfo}>
                <div className={styles.resultTitle}>{r.name}</div>
                <div className={styles.resultTagBar}>
                  {r.tags?.map((tagId) => {
                    const tag: API.Tag = tags?.find(
                      (t: API.Tag) => t.id === tagId
                    );
                    if (!tag) {
                      return null;
                    }
                    return <Tag color={tag.color}>{tag.name}</Tag>;
                  })}
                </div>
                <div className={styles.resultDescription}>{r.description}</div>
              </div>
              <div className={styles.resultDownload}>
                <Button type="link" icon={<CloudDownloadOutlined />}>
                  下载
                </Button>
              </div>
            </div>
          </>
        ))}
      </div>
    </Card>
  );
};

export default DashboardPage;
