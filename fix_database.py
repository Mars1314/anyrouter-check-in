#!/usr/bin/env python3
"""
快速修复数据库脚本 - 删除旧数据库，重新初始化
"""

import os
from pathlib import Path

db_path = Path('data/checkin.db')
key_path = Path('data/secret.key')

print('🔧 数据库修复工具')
print('=' * 50)

if db_path.exists():
    print(f'✅ 找到旧数据库: {db_path}')
    choice = input('是否删除并重建？这将清空所有数据 (y/N): ')

    if choice.lower() == 'y':
        # 备份
        import shutil
        backup_path = db_path.with_suffix('.db.backup')
        shutil.copy(db_path, backup_path)
        print(f'📦 已备份到: {backup_path}')

        # 删除
        db_path.unlink()
        print(f'🗑️  已删除旧数据库')

        # 如果需要，也删除加密密钥（会生成新的）
        reset_key = input('是否也重置加密密钥？(y/N): ')
        if reset_key.lower() == 'y' and key_path.exists():
            key_backup = key_path.with_suffix('.key.backup')
            shutil.copy(key_path, key_backup)
            key_path.unlink()
            print(f'🔑 已重置加密密钥（备份到 {key_backup}）')

        # 重新初始化
        from web.database import db
        print('✅ 数据库已重新初始化')
        print(f'📁 新数据库: {db.db_path}')

        # 测试
        print('\n🧪 测试数据库...')
        stats = db.get_statistics()
        print(f'✅ 数据库工作正常: {stats}')

        print('\n✅ 完成！现在可以重新启动服务了')
    else:
        print('❌ 已取消')
else:
    print('ℹ️  数据库不存在，将自动创建新的')
    from web.database import db
    print('✅ 数据库已创建')
