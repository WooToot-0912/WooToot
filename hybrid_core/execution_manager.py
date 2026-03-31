#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
执行管理器 - 智能交易执行的统一管理
负责协调API执行和图像执行，提供故障切换和性能优化
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError

class ExecutionMethod(Enum):
    """执行方法"""
    API = "api"
    IMAGE = "image"
    HYBRID = "hybrid"

class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class ExecutionTask:
    """执行任务"""
    task_id: str
    signal: Dict
    commodity_id: str
    method: ExecutionMethod
    timestamp: float
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    execution_time: float = 0.0

class ExecutionManager:
    """执行管理器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化执行管理器

        Args:
            config: 执行配置
        """
        self.logger = logging.getLogger(__name__)

        # 默认配置
        default_config = {
            "max_workers": 3,               # 最大并发执行数
            "api_timeout": 15,              # API执行超时时间(秒)
            "image_timeout": 20,            # 图像执行超时时间(秒)
            "retry_attempts": 2,            # 重试次数
            "retry_delay": 5,               # 重试延迟(秒)
            "fallback_enabled": True,       # 是否启用故障切换
            "performance_tracking": True     # 是否跟踪性能
        }

        self.config = {**default_config, **(config or {})}

        # 执行器
        self.executor = ThreadPoolExecutor(max_workers=self.config["max_workers"])

        # 任务管理
        self.active_tasks: Dict[str, ExecutionTask] = {}
        self.task_history: List[ExecutionTask] = []
        self.task_counter = 0

        # 性能统计
        self.performance_stats = {
            ExecutionMethod.API: {"success": 0, "failed": 0, "total_time": 0.0},
            ExecutionMethod.IMAGE: {"success": 0, "failed": 0, "total_time": 0.0},
            ExecutionMethod.HYBRID: {"success": 0, "failed": 0, "total_time": 0.0}
        }

        # 组件引用（由外部设置）
        self.api_executor: Optional[Callable] = None
        self.image_executor: Optional[Callable] = None

        # 回调函数
        self.on_execution_start: Optional[Callable] = None
        self.on_execution_complete: Optional[Callable] = None
        self.on_execution_failed: Optional[Callable] = None

        self.logger.info("✅ 执行管理器初始化完成")

    def set_executors(self, api_executor: Callable, image_executor: Callable):
        """设置执行器"""
        self.api_executor = api_executor
        self.image_executor = image_executor
        self.logger.info("✅ 执行器已设置")

    def execute_trade(self, signal: Dict, commodity_id: str,
                     method: ExecutionMethod = ExecutionMethod.HYBRID) -> str:
        """
        执行交易（异步）

        Args:
            signal: 交易信号
            commodity_id: 商品ID
            method: 执行方法

        Returns:
            str: 任务ID
        """
        try:
            # 生成任务ID
            self.task_counter += 1
            task_id = f"task_{self.task_counter}_{int(time.time())}"

            # 创建执行任务
            task = ExecutionTask(
                task_id=task_id,
                signal=signal,
                commodity_id=commodity_id,
                method=method,
                timestamp=time.time()
            )

            # 添加到活动任务
            self.active_tasks[task_id] = task

            # 提交执行
            future = self.executor.submit(self._execute_task, task)

            self.logger.info(f"🎯 提交交易任务: {task_id} ({method.value})")

            # 触发开始回调
            if self.on_execution_start:
                self.on_execution_start(task)

            return task_id

        except Exception as e:
            self.logger.error(f"提交交易任务失败: {e}")
            return ""

    def _execute_task(self, task: ExecutionTask):
        """执行任务"""
        start_time = time.time()
        task.status = ExecutionStatus.RUNNING

        try:
            self.logger.info(f"🚀 开始执行任务: {task.task_id}")

            # 根据方法执行
            if task.method == ExecutionMethod.API:
                success = self._execute_via_api(task)
            elif task.method == ExecutionMethod.IMAGE:
                success = self._execute_via_image(task)
            elif task.method == ExecutionMethod.HYBRID:
                success = self._execute_hybrid(task)
            else:
                raise ValueError(f"未知执行方法: {task.method}")

            # 更新任务状态
            task.execution_time = time.time() - start_time

            if success:
                task.status = ExecutionStatus.SUCCESS
                self.logger.info(f"✅ 任务执行成功: {task.task_id} ({task.execution_time:.2f}s)")

                # 更新性能统计
                self._update_performance_stats(task.method, True, task.execution_time)

                # 触发成功回调
                if self.on_execution_complete:
                    self.on_execution_complete(task, True)
            else:
                task.status = ExecutionStatus.FAILED
                self.logger.error(f"❌ 任务执行失败: {task.task_id}")

                # 更新性能统计
                self._update_performance_stats(task.method, False, task.execution_time)

                # 触发失败回调
                if self.on_execution_failed:
                    self.on_execution_failed(task, "执行失败")

        except TimeoutError:
            task.status = ExecutionStatus.TIMEOUT
            task.error = "执行超时"
            self.logger.error(f"⏰ 任务执行超时: {task.task_id}")

        except Exception as e:
            task.status = ExecutionStatus.FAILED
            task.error = str(e)
            task.execution_time = time.time() - start_time
            self.logger.error(f"❌ 任务执行异常: {task.task_id} - {e}")

        finally:
            # 移动到历史记录
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

            self.task_history.append(task)

            # 限制历史记录大小
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]

    def _execute_via_api(self, task: ExecutionTask) -> bool:
        """通过API执行"""
        try:
            if not self.api_executor:
                raise ValueError("API执行器未设置")

            # 设置超时
            timeout = self.config["api_timeout"]

            # 执行API交易
            future = self.executor.submit(
                self.api_executor,
                task.signal,
                task.commodity_id
            )

            result = future.result(timeout=timeout)
            task.result = {"method": "api", "success": result}

            return result

        except TimeoutError:
            self.logger.error(f"API执行超时: {task.task_id}")
            return False
        except Exception as e:
            self.logger.error(f"API执行失败: {e}")
            task.error = str(e)
            return False

    def _execute_via_image(self, task: ExecutionTask) -> bool:
        """通过图像执行"""
        try:
            if not self.image_executor:
                raise ValueError("图像执行器未设置")

            # 设置超时
            timeout = self.config["image_timeout"]

            # 执行图像交易
            future = self.executor.submit(
                self.image_executor,
                task.signal
            )

            result = future.result(timeout=timeout)
            task.result = {"method": "image", "success": result}

            return result

        except TimeoutError:
            self.logger.error(f"图像执行超时: {task.task_id}")
            return False
        except Exception as e:
            self.logger.error(f"图像执行失败: {e}")
            task.error = str(e)
            return False

    def _execute_hybrid(self, task: ExecutionTask) -> bool:
        """混合执行 - 智能故障切换"""
        try:
            # 优先尝试API执行
            if self.api_executor:
                self.logger.info(f"🔄 混合模式: 尝试API执行 {task.task_id}")
                api_success = self._execute_via_api(task)

                if api_success:
                    self.logger.info(f"✅ 混合模式: API执行成功 {task.task_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ 混合模式: API执行失败，尝试图像执行 {task.task_id}")

            # API失败或不可用，尝试图像执行
            if self.image_executor and self.config["fallback_enabled"]:
                self.logger.info(f"🔄 混合模式: 尝试图像执行 {task.task_id}")
                image_success = self._execute_via_image(task)

                if image_success:
                    self.logger.info(f"✅ 混合模式: 图像执行成功 {task.task_id}")
                    return True
                else:
                    self.logger.error(f"❌ 混合模式: 图像执行也失败 {task.task_id}")

            return False

        except Exception as e:
            self.logger.error(f"混合执行异常: {e}")
            task.error = str(e)
            return False

    def _update_performance_stats(self, method: ExecutionMethod, success: bool, execution_time: float):
        """更新性能统计"""
        try:
            if method in self.performance_stats:
                stats = self.performance_stats[method]

                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

                stats["total_time"] += execution_time

        except Exception as e:
            self.logger.error(f"更新性能统计失败: {e}")

    def get_task_status(self, task_id: str) -> Optional[ExecutionTask]:
        """获取任务状态"""
        # 先检查活动任务
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]

        # 再检查历史任务
        for task in reversed(self.task_history):
            if task.task_id == task_id:
                return task

        return None

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        try:
            report = {
                "active_tasks": len(self.active_tasks),
                "total_tasks": len(self.task_history),
                "method_performance": {}
            }

            # 计算各方法的性能指标
            for method, stats in self.performance_stats.items():
                total_executions = stats["success"] + stats["failed"]

                if total_executions > 0:
                    success_rate = stats["success"] / total_executions
                    avg_time = stats["total_time"] / total_executions
                else:
                    success_rate = 0.0
                    avg_time = 0.0

                report["method_performance"][method.value] = {
                    "success_rate": success_rate,
                    "avg_execution_time": avg_time,
                    "total_executions": total_executions,
                    "success_count": stats["success"],
                    "failed_count": stats["failed"]
                }

            # 最近任务统计
            recent_tasks = self.task_history[-20:] if len(self.task_history) >= 20 else self.task_history
            if recent_tasks:
                recent_success = sum(1 for task in recent_tasks if task.status == ExecutionStatus.SUCCESS)
                recent_success_rate = recent_success / len(recent_tasks)
                report["recent_success_rate"] = recent_success_rate
            else:
                report["recent_success_rate"] = 0.0

            return report

        except Exception as e:
            self.logger.error(f"生成性能报告失败: {e}")
            return {"error": str(e)}

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = ExecutionStatus.CANCELLED

                self.logger.info(f"🚫 任务已取消: {task_id}")
                return True
            else:
                self.logger.warning(f"⚠️ 任务不存在或已完成: {task_id}")
                return False

        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return False

    def cleanup_completed_tasks(self):
        """清理已完成的任务"""
        try:
            # 移除已完成的活动任务
            completed_tasks = [
                task_id for task_id, task in self.active_tasks.items()
                if task.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED,
                                 ExecutionStatus.TIMEOUT, ExecutionStatus.CANCELLED]
            ]

            for task_id in completed_tasks:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]

            if completed_tasks:
                self.logger.info(f"🧹 清理了 {len(completed_tasks)} 个已完成任务")

        except Exception as e:
            self.logger.error(f"清理任务失败: {e}")

    def get_execution_recommendation(self, signal: Dict, api_available: bool,
                                   image_available: bool) -> ExecutionMethod:
        """获取执行建议"""
        try:
            # 检查可用性
            if not api_available and not image_available:
                raise ValueError("所有执行方法都不可用")

            if not api_available:
                return ExecutionMethod.IMAGE

            if not image_available:
                return ExecutionMethod.API

            # 基于性能选择
            api_perf = self.performance_stats[ExecutionMethod.API]
            image_perf = self.performance_stats[ExecutionMethod.IMAGE]

            # 计算成功率
            api_total = api_perf["success"] + api_perf["failed"]
            image_total = image_perf["success"] + image_perf["failed"]

            if api_total > 0 and image_total > 0:
                api_success_rate = api_perf["success"] / api_total
                image_success_rate = image_perf["success"] / image_total

                # 考虑信号置信度
                signal_confidence = signal.get('confidence', 0.5)

                if signal_confidence > 0.8:
                    # 高置信度信号，选择成功率更高的方法
                    if api_success_rate > image_success_rate:
                        return ExecutionMethod.API
                    else:
                        return ExecutionMethod.IMAGE
                else:
                    # 低置信度信号，使用混合模式增加成功率
                    return ExecutionMethod.HYBRID
            else:
                # 无足够历史数据，默认使用API
                return ExecutionMethod.API

        except Exception as e:
            self.logger.error(f"获取执行建议失败: {e}")
            return ExecutionMethod.API

    def shutdown(self):
        """关闭执行管理器"""
        try:
            # 等待所有任务完成
            self.executor.shutdown(wait=True)

            # 清理资源
            self.active_tasks.clear()

            self.logger.info("✅ 执行管理器已关闭")

        except Exception as e:
            self.logger.error(f"关闭执行管理器失败: {e}")

    def get_active_tasks_summary(self) -> Dict[str, Any]:
        """获取活动任务摘要"""
        try:
            summary = {
                "total_active": len(self.active_tasks),
                "by_status": {},
                "by_method": {},
                "oldest_task_age": 0.0
            }

            current_time = time.time()
            oldest_age = 0.0

            for task in self.active_tasks.values():
                # 按状态统计
                status = task.status.value
                summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

                # 按方法统计
                method = task.method.value
                summary["by_method"][method] = summary["by_method"].get(method, 0) + 1

                # 计算最老任务年龄
                task_age = current_time - task.timestamp
                oldest_age = max(oldest_age, task_age)

            summary["oldest_task_age"] = oldest_age

            return summary

        except Exception as e:
            self.logger.error(f"获取任务摘要失败: {e}")
            return {"error": str(e)}
