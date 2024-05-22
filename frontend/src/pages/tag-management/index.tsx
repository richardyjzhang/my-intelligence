import React, { useState } from "react";
import {
  Button,
  Card,
  Divider,
  Form,
  Input,
  Popconfirm,
  Table,
  TableProps,
  ConfigProvider,
  Modal,
  Tag,
  Select,
} from "antd";
import {
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";
import { useRequest } from "ahooks";
import {
  fetchTagsRequest,
  addOneTagRequest,
  deleteOneTagRequest,
  updateOneTagRequest,
} from "../service";
import { tagColors } from "./color";
import styles from "./index.css";

const TagManagementPage: React.FC = () => {
  // 弹窗展示
  const [modalOpen, setModalOpen] = useState(false);
  const [curTag, setCurTag] = useState<API.Tag | null>(null);

  // 各种网络请求
  const { runAsync: fetchTags, data: tags } = useRequest(fetchTagsRequest);
  const { runAsync: addOneTag } = useRequest(addOneTagRequest, {
    manual: true,
  });
  const { runAsync: updateOneTag } = useRequest(updateOneTagRequest, {
    manual: true,
  });
  const { runAsync: deleteOneTag } = useRequest(deleteOneTagRequest, {
    manual: true,
  });

  // 删除一个标签
  const onDelete = async (id: number) => {
    const _ = await deleteOneTag(id);
    await fetchTags();
  };

  // 主体表格配置
  const columns: TableProps<API.Tag>["columns"] = [
    {
      title: "标签ID",
      dataIndex: "id",
      key: "id",
    },
    {
      title: "标签名称",
      key: "name",
      render: (_, tag) => <Tag color={tag.color}>{tag.name}</Tag>,
    },
    {
      title: "操作",
      key: "operation",
      render: (_, tag) => {
        return (
          <div className={styles.operations}>
            <ConfigProvider
              theme={{
                token: {
                  colorLink: "#2D3047",
                },
              }}
            >
              <Button
                className={styles.operationButton}
                icon={<EditOutlined />}
                type="link"
                onClick={() => {
                  setCurTag(tag);
                  setModalOpen(true);
                }}
              >
                编辑
              </Button>
            </ConfigProvider>
            <ConfigProvider
              theme={{
                token: {
                  colorLink: "#B22222",
                },
              }}
            >
              <Popconfirm
                title="删除标签"
                description="此操作无法恢复。是否确认删除？"
                okText="确认"
                cancelText="取消"
                icon={
                  <ExclamationCircleOutlined style={{ color: "#2D3047BB" }} />
                }
                onConfirm={() => {
                  if (tag.id) {
                    onDelete(tag.id);
                  }
                }}
              >
                <Button
                  className={styles.operationButton}
                  icon={<DeleteOutlined />}
                  type="link"
                >
                  删除
                </Button>
              </Popconfirm>
            </ConfigProvider>
          </div>
        );
      },
    },
  ];

  // 新增编辑弹窗
  const AddEditModal = () => {
    const onFormFinished = async (value: { name: string; color: string }) => {
      const newTag: API.Tag = {
        name: value.name,
        color: value.color,
      };
      setModalOpen(false);
      if (!curTag?.id) {
        await addOneTag(newTag);
      } else if (curTag.name !== newTag.name || curTag.color !== newTag.color) {
        newTag.id = curTag.id;
        await updateOneTag(newTag);
      }
      setCurTag(null);
      fetchTags();
    };

    return (
      <Modal
        className={styles.addEditModal}
        open={modalOpen}
        title={`${!!curTag ? "编辑标签" : "新增标签"}`}
        footer={null}
        destroyOnClose
        onCancel={() => {
          setModalOpen(false);
          setCurTag(null);
        }}
      >
        <div className={styles.addEditForm}>
          <Divider />
          <Form onFinish={onFormFinished}>
            <Form.Item
              name="name"
              label="标签名称"
              rules={[{ required: true }]}
              initialValue={curTag?.name}
            >
              <Input placeholder="标签名称" />
            </Form.Item>
            <Form.Item
              name="color"
              label="标签颜色"
              rules={[{ required: true }]}
              initialValue={curTag?.color}
            >
              <Select
                options={tagColors.map((t) => ({
                  value: t.name,
                  label: <Tag color={t.name}>{t.desc}</Tag>,
                }))}
              />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className={styles.addEditButton}
            >
              确认
            </Button>
          </Form>
        </div>
      </Modal>
    );
  };

  return (
    <Card className={styles.mainCard} title="标签管理">
      <div className={styles.search}>
        <Button
          icon={<PlusOutlined />}
          type="primary"
          onClick={() => {
            setModalOpen(true);
          }}
        >
          新增
        </Button>
        <div className={styles.space} />
        <Button
          icon={<ReloadOutlined />}
          type="primary"
          onClick={() => {
            fetchTags();
          }}
        >
          刷新
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={tags} />
      <AddEditModal />
    </Card>
  );
};

export default TagManagementPage;
