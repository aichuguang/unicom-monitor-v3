-- 为FlowRecord表添加分类流量字段
-- 执行时间：2025-09-25

ALTER TABLE flow_records ADD COLUMN used_general VARCHAR(50) COMMENT '已用通用流量';
ALTER TABLE flow_records ADD COLUMN used_special VARCHAR(50) COMMENT '已用专属流量';
ALTER TABLE flow_records ADD COLUMN used_other VARCHAR(50) COMMENT '已用其他流量';
ALTER TABLE flow_records ADD COLUMN remain_general VARCHAR(50) COMMENT '剩余通用流量';
ALTER TABLE flow_records ADD COLUMN remain_special VARCHAR(50) COMMENT '剩余专属流量';
ALTER TABLE flow_records ADD COLUMN remain_other VARCHAR(50) COMMENT '剩余其他流量';
