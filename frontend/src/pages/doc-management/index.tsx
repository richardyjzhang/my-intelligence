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
  Select,
  ConfigProvider,
  Modal,
  Upload,
  Tag,
} from "antd";
import {
  EditOutlined,
  DeleteOutlined,
  InboxOutlined,
  PlusOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";
import { useRequest } from "ahooks";
import {
  fetchTagsRequest,
  fetchDocsRequest,
  addOneDocRequest,
  updateOneDocRequest,
  deleteOneDocRequest,
  updateOneDocTagRequest,
} from "../service";
import styles from "./index.css";

const DocManagementPage: React.FC = () => {
  // 弹窗展示
  const [modalOpen, setModalOpen] = useState(false);
  const [curDoc, setCurDoc] = useState<API.Doc | null>(null);

  // 各种网络请求
  const { data: tags } = useRequest(fetchTagsRequest);
  const { runAsync: fetchDocs, data: docs } = useRequest(fetchDocsRequest);
  const { runAsync: addOneDoc } = useRequest(addOneDocRequest, {
    manual: true,
  });
  const { runAsync: updateOneDoc } = useRequest(updateOneDocRequest, {
    manual: true,
  });
  const { runAsync: deleteOneDoc } = useRequest(deleteOneDocRequest, {
    manual: true,
  });
  const { runAsync: updateOneDocTag } = useRequest(updateOneDocTagRequest, {
    manual: true,
  });

  // 添加一个文档
  const onCreate = async (value: {
    name: string;
    description?: string;
    tags?: number[];
    file?: {
      file: File;
    };
  }) => {
    const newDoc = {
      name: value.name,
      description: value.description,
    };
    const file = value.file?.file;

    if (file) {
      const thisDoc: API.Doc = await addOneDoc(newDoc, file);
      if (thisDoc.id && value.tags) {
        await updateOneDocTag(thisDoc.id, value.tags);
      }
      fetchDocs();
    }
  };

  // 删除一个文档
  const onDelete = async (id: number) => {
    const _ = await deleteOneDoc(id);
    await fetchDocs();
  };

  // 主体表格配置
  const columns: TableProps<API.Doc>["columns"] = [
    {
      title: "文档名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "创建时间",
      dataIndex: "ct",
      key: "ct",
    },
    {
      title: "文档说明",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "文档标签",
      key: "tags",
      render: (_, doc) => {
        return (
          <div className={styles.tagWrapper}>
            {doc.tags?.map((tagId) => {
              const tag = tags.find((t: API.Tag) => t.id === tagId);
              return <Tag>{tag.name}</Tag>;
            })}
          </div>
        );
      },
    },
    {
      title: "文档处理状态",
      key: "status",
      render: (_, doc) => {
        return doc.status === 0 ? "处理中" : "已完成";
      },
    },
    {
      title: "操作",
      key: "operation",
      render: (_, doc) => {
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
                  setCurDoc(doc);
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
                title="删除文档"
                description="此操作无法恢复。是否确认删除？"
                okText="确认"
                cancelText="取消"
                icon={
                  <ExclamationCircleOutlined style={{ color: "#2D3047BB" }} />
                }
                onConfirm={() => {
                  if (doc.id) {
                    onDelete(doc.id);
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
    const onFormFinished = async (value: {
      id?: number;
      name: string;
      description?: string;
      tags?: number[];
      file?: {
        file: File;
      };
    }) => {
      setModalOpen(false);
      if (!curDoc) {
        await onCreate(value);
      } else {
        await updateOneDoc({
          id: curDoc.id,
          name: value.name,
          description: value.description,
        });
        if (curDoc.id) {
          await updateOneDocTag(curDoc.id, value.tags || []);
        }
        fetchDocs();
      }
      setCurDoc(null);
    };

    const [form] = Form.useForm();

    return (
      <Modal
        className={styles.addEditModal}
        open={modalOpen}
        title={`${!!curDoc ? "编辑文档" : "新增文档"}`}
        footer={null}
        destroyOnClose
        onCancel={() => {
          setModalOpen(false);
          setCurDoc(null);
        }}
      >
        <div className={styles.addEditForm}>
          <Divider />
          <Form form={form} layout="vertical" onFinish={onFormFinished}>
            {!curDoc ? (
              <Form.Item
                name="file"
                label="文档文件"
                rules={[{ required: true }]}
              >
                <Upload.Dragger
                  name="file"
                  multiple={false}
                  maxCount={1}
                  beforeUpload={(file) => {
                    form.setFieldValue("name", file.name);
                    return false;
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">点击或拖拽上传文档附件</p>
                </Upload.Dragger>
              </Form.Item>
            ) : null}
            <Form.Item
              name="name"
              label="文档名称"
              rules={[{ required: true }]}
              initialValue={curDoc?.name}
            >
              <Input placeholder="文档名称" />
            </Form.Item>
            <Form.Item
              name="description"
              label="文档说明"
              initialValue={curDoc?.description}
            >
              <Input.TextArea rows={4} placeholder="文档说明" />
            </Form.Item>
            <Form.Item name="tags" label="文档标签" initialValue={curDoc?.tags}>
              <Select
                options={tags?.map((t: API.Tag) => {
                  return { label: t.name, value: t.id };
                })}
                mode="multiple"
                allowClear
                style={{ width: "100%" }}
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
    <Card className={styles.mainCard} title="文档管理">
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
            fetchDocs();
          }}
        >
          刷新
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={docs} />
      <AddEditModal />
    </Card>
  );
};

export default DocManagementPage;
