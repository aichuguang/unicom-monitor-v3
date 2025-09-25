#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from app.models import db
from sqlalchemy import text

def migrate_database():
    """执行数据库迁移"""
    app = create_app()
    with app.app_context():
        # 执行SQL迁移
        migration_sqls = [
            'ALTER TABLE flow_records ADD COLUMN used_general VARCHAR(50) COMMENT "已用通用流量"',
            'ALTER TABLE flow_records ADD COLUMN used_special VARCHAR(50) COMMENT "已用专属流量"',
            'ALTER TABLE flow_records ADD COLUMN used_other VARCHAR(50) COMMENT "已用其他流量"',
            'ALTER TABLE flow_records ADD COLUMN remain_general VARCHAR(50) COMMENT "剩余通用流量"',
            'ALTER TABLE flow_records ADD COLUMN remain_special VARCHAR(50) COMMENT "剩余专属流量"',
            'ALTER TABLE flow_records ADD COLUMN remain_other VARCHAR(50) COMMENT "剩余其他流量"'
        ]
        
        success_count = 0
        for sql in migration_sqls:
            try:
                db.session.execute(text(sql))
                db.session.commit()
                success_count += 1
                print(f'✅ 执行成功: {sql[:50]}...')
            except Exception as e:
                print(f'⚠️ 执行失败或字段已存在: {sql[:50]}... - {e}')
                db.session.rollback()
        
        print(f'\n数据库迁移完成，成功执行 {success_count}/{len(migration_sqls)} 条SQL')

if __name__ == '__main__':
    migrate_database()
