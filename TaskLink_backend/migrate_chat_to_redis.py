#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天消息数据迁移脚本
将 MySQL 中的聊天历史一次性导入 Redis 缓存

使用方法:
    python migrate_chat_to_redis.py
"""

import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, ChatMessage, redis_client, get_chat_cache_key, CHAT_CACHE_TTL
import json


def migrate_all_messages():
    """
    将所有聊天消息按分页批量导入 Redis
    """
    print("🚀 开始数据迁移: MySQL -> Redis")
    print("=" * 50)
    
    with app.app_context():
        # 获取总消息数
        total_count = ChatMessage.query.count()
        print(f"📊 MySQL 中共有 {total_count} 条消息")
        
        if total_count == 0:
            print("❌ 没有消息需要迁移")
            return
        
        # 分页大小
        page_size = 50
        total_pages = (total_count + page_size - 1) // page_size
        
        print(f"📦 将分为 {total_pages} 批导入...\n")
        
        migrated_count = 0
        
        for page in range(total_pages):
            offset = page * page_size
            
            # 按时间正序查询（旧消息在前）
            messages = ChatMessage.query \
                .order_by(ChatMessage.created_at.asc()) \
                .offset(offset) \
                .limit(page_size) \
                .all()
            
            if not messages:
                break
            
            # 转换为字典列表
            messages_list = [m.to_dict() for m in messages]
            
            # 写入 Redis 缓存
            cache_key = get_chat_cache_key(offset, page_size)
            
            try:
                if redis_client:
                    redis_client.setex(
                        cache_key,
                        CHAT_CACHE_TTL,
                        json.dumps(messages_list, ensure_ascii=False)
                    )
                    migrated_count += len(messages_list)
                    print(f"✅ 第 {page + 1}/{total_pages} 批: offset={offset}, count={len(messages_list)}")
                else:
                    print(f"⚠️ Redis 未连接，跳过 offset={offset}")
            except Exception as e:
                print(f"❌ 写入失败 offset={offset}: {e}")
        
        print("\n" + "=" * 50)
        print(f"🎉 迁移完成! 共导入 {migrated_count} 条消息")
        
        # 验证缓存
        if redis_client:
            try:
                keys = redis_client.keys("chat:messages:*")
                print(f"📋 Redis 中共有 {len(keys)} 个缓存键")
            except Exception as e:
                print(f"⚠️ 验证缓存失败: {e}")


def migrate_latest_messages(count=50):
    """
    只迁移最新的 N 条消息
    """
    print(f"🚀 开始迁移最新 {count} 条消息...")
    
    with app.app_context():
        messages = ChatMessage.query \
            .order_by(ChatMessage.created_at.desc()) \
            .limit(count) \
            .all()
        
        # 翻转顺序（旧消息在前）
        messages_list = [m.to_dict() for m in messages][::-1]
        
        cache_key = get_chat_cache_key(0, count)
        
        try:
            if redis_client:
                redis_client.setex(
                    cache_key,
                    CHAT_CACHE_TTL,
                    json.dumps(messages_list, ensure_ascii=False)
                )
                print(f"✅ 已将最新 {count} 条消息写入缓存")
            else:
                print("❌ Redis 未连接")
        except Exception as e:
            print(f"❌ 写入失败: {e}")


def clear_redis_cache():
    """
    清除 Redis 中所有聊天缓存
    """
    print("🗑️  清除 Redis 缓存...")
    
    try:
        if redis_client:
            keys = redis_client.keys("chat:messages:*")
            if keys:
                redis_client.delete(*keys)
                print(f"✅ 已清除 {len(keys)} 个缓存键")
            else:
                print("ℹ️  没有缓存需要清除")
        else:
            print("❌ Redis 未连接")
    except Exception as e:
        print(f"❌ 清除失败: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="聊天消息 Redis 迁移工具")
    parser.add_argument("--mode", choices=["migrate", "latest", "clear"], default="migrate",
                        help="模式: migrate=迁移全部, latest=迁移最新, clear=清除缓存")
    parser.add_argument("--count", type=int, default=50,
                        help="latest 模式下的消息数量")
    
    args = parser.parse_args()
    
    if args.mode == "migrate":
        migrate_all_messages()
    elif args.mode == "latest":
        migrate_latest_messages(args.count)
    elif args.mode == "clear":
        clear_redis_cache()
