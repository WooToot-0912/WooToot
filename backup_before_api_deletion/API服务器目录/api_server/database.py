#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据库管理模块
"""

import sqlite3
import hashlib
import time
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class UserDatabase:
    """用户数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    api_key TEXT UNIQUE,
                    permissions TEXT DEFAULT 'user'
                )
            ''')
            
            # 用户会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    trading_session TEXT,
                    firm_id TEXT,
                    user_id_jtyg TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def create_user(self, username: str, phone: str, password: str, 
                    email: str = None, permissions: str = "user") -> bool:
        """创建新用户"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            api_key = hashlib.md5(f"{username}{time.time()}".encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, phone, password_hash, email, api_key, permissions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, phone, password_hash, email, api_key, permissions))
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户 {username} 创建成功")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"用户 {username} 或手机号 {phone} 已存在")
            return False
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return False
    
    def authenticate_user(self, phone: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, phone, email, api_key, permissions, status
                FROM users 
                WHERE phone = ? AND password_hash = ? AND status = 'active'
            ''', (phone, password_hash))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "phone": user[2],
                    "email": user[3],
                    "api_key": user[4],
                    "permissions": user[5],
                    "status": user[6]
                }
            return None
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    def create_session(self, user_id: int, trading_session: str = None,
                      firm_id: str = None, user_id_jtyg: str = None) -> Optional[str]:
        """创建用户会话"""
        try:
            session_token = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()
            expires_at = time.time() + 3600  # 1小时后过期
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (user_id, session_token, trading_session, firm_id, user_id_jtyg, expires_at)
                VALUES (?, ?, ?, ?, ?, datetime(?, 'unixepoch'))
            ''', (user_id, session_token, trading_session, firm_id, user_id_jtyg, expires_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户 {user_id} 会话创建成功")
            return session_token
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """验证会话有效性"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT us.id, us.user_id, us.trading_session, us.firm_id, us.user_id_jtyg,
                       u.username, u.phone, u.permissions
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ? AND us.expires_at > datetime('now')
            ''', (session_token,))
            
            session = cursor.fetchone()
            conn.close()
            
            if session:
                return {
                    "session_id": session[0],
                    "user_id": session[1],
                    "trading_session": session[2],
                    "firm_id": session[3],
                    "user_id_jtyg": session[4],
                    "username": session[5],
                    "phone": session[6],
                    "permissions": session[7]
                }
            return None
            
        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return None 