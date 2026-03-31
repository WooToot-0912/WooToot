#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强OCR识别模块
实现多策略OCR识别、图像预处理、结果验证等功能
"""

import cv2
import numpy as np
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
import time

# 安全导入pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

class ImagePreprocessor:
    """图像预处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def enhance_for_ocr(self, image: np.ndarray, method: str = "auto") -> np.ndarray:
        """为OCR增强图像"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            if method == "auto":
                # 自动选择最佳预处理方法
                return self._auto_enhance(gray)
            elif method == "contrast":
                return self._enhance_contrast(gray)
            elif method == "denoise":
                return self._denoise(gray)
            elif method == "binary":
                return self._binarize(gray)
            elif method == "scale":
                return self._scale_up(gray)
            else:
                return gray
                
        except Exception as e:
            self.logger.error(f"图像预处理失败: {e}")
            return image
    
    def _auto_enhance(self, gray: np.ndarray) -> np.ndarray:
        """自动增强"""
        # 计算图像质量指标
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        mean_brightness = np.mean(gray)
        
        enhanced = gray.copy()
        
        # 如果图像模糊，进行锐化
        if variance < 100:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # 如果亮度不足，进行对比度增强
        if mean_brightness < 100:
            enhanced = self._enhance_contrast(enhanced)
        
        # 放大图像
        enhanced = self._scale_up(enhanced)
        
        # 去噪
        enhanced = self._denoise(enhanced)
        
        return enhanced
    
    def _enhance_contrast(self, gray: np.ndarray) -> np.ndarray:
        """增强对比度"""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        return clahe.apply(gray)
    
    def _denoise(self, gray: np.ndarray) -> np.ndarray:
        """去噪"""
        return cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    def _binarize(self, gray: np.ndarray) -> np.ndarray:
        """二值化"""
        # 自适应阈值
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    def _scale_up(self, gray: np.ndarray) -> np.ndarray:
        """放大图像"""
        return cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

class ResultValidator:
    """结果验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 数字模式
        self.number_patterns = [
            r'^[+-]?\d+\.?\d*$',  # 基本数字
            r'^[+-]?\d{1,3}(?:,\d{3})*\.?\d*$',  # 带千分位
            r'^[+-]?\d+\.?\d*[%％]?$',  # 带百分号
        ]
        
        # 价格模式
        self.price_patterns = [
            r'^\d{3,5}\.?\d*$',  # 价格范围
            r'^\d{1,3}(?:,\d{3})*\.?\d*$',  # 带千分位的价格
        ]
    
    def validate_number(self, text: str, min_val: float = -1000, 
                       max_val: float = 1000) -> Tuple[bool, float]:
        """验证数字"""
        try:
            # 清理文本
            cleaned = self._clean_text(text)
            
            # 检查模式
            for pattern in self.number_patterns:
                if re.match(pattern, cleaned):
                    # 提取数字
                    number = self._extract_number(cleaned)
                    if number is not None and min_val <= number <= max_val:
                        return True, number
            
            return False, 0.0
            
        except Exception as e:
            self.logger.error(f"数字验证失败: {e}")
            return False, 0.0
    
    def validate_price(self, text: str, min_price: float = 1000, 
                      max_price: float = 2000) -> Tuple[bool, float]:
        """验证价格"""
        try:
            cleaned = self._clean_text(text)
            
            for pattern in self.price_patterns:
                if re.match(pattern, cleaned):
                    price = self._extract_number(cleaned)
                    if price is not None and min_price <= price <= max_price:
                        return True, price
            
            return False, 0.0
            
        except Exception as e:
            self.logger.error(f"价格验证失败: {e}")
            return False, 0.0
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除空白字符
        cleaned = text.strip()
        
        # 替换中文符号
        cleaned = cleaned.replace('，', ',')
        cleaned = cleaned.replace('。', '.')
        cleaned = cleaned.replace('％', '%')
        
        # 移除非数字字符（保留+-.,）
        cleaned = re.sub(r'[^\d+\-.,]', '', cleaned)
        
        return cleaned
    
    def _extract_number(self, text: str) -> Optional[float]:
        """提取数字"""
        try:
            # 移除千分位逗号
            text = text.replace(',', '')
            
            # 移除百分号
            text = text.replace('%', '').replace('％', '')
            
            return float(text)
            
        except:
            return None

class EnhancedOCR:
    """增强OCR识别器"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.preprocessor = ImagePreprocessor()
        self.validator = ResultValidator()
        
        # OCR配置
        self.load_ocr_config()
        
        # 统计信息
        self.stats = {
            'total_attempts': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_confidence': 0.0
        }
        
        self.logger.info(f"增强OCR初始化完成，Tesseract可用: {TESSERACT_AVAILABLE}")
    
    def load_ocr_config(self):
        """加载OCR配置"""
        if self.config_manager:
            ocr_config = self.config_manager.get('detection.profit_loss', {})
            self.ocr_configs = ocr_config.get('ocr_configs', [
                "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789.-+",
                "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.-+",
                "--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789.-+"
            ])
            
            validation_config = ocr_config.get('validation', {})
            self.min_value = validation_config.get('min_value', -100)
            self.max_value = validation_config.get('max_value', 100)
            self.confidence_threshold = validation_config.get('confidence_threshold', 0.7)
        else:
            # 默认配置
            self.ocr_configs = [
                "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789.-+",
                "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.-+",
                "--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789.-+"
            ]
            self.min_value = -100
            self.max_value = 100
            self.confidence_threshold = 0.7
    
    def recognize_profit_loss(self, image: np.ndarray) -> Dict[str, Any]:
        """识别盈亏数值"""
        if not TESSERACT_AVAILABLE:
            return {
                'success': False,
                'value': 0.0,
                'confidence': 0.0,
                'method': 'none',
                'error': 'Tesseract不可用'
            }
        
        self.stats['total_attempts'] += 1
        start_time = time.time()
        
        # 多策略识别
        strategies = [
            ('auto', 'auto'),
            ('contrast', 'contrast'),
            ('scale', 'scale'),
            ('denoise', 'denoise'),
            ('binary', 'binary')
        ]
        
        best_result = None
        best_confidence = 0.0
        
        for strategy_name, preprocess_method in strategies:
            try:
                # 预处理图像
                processed_image = self.preprocessor.enhance_for_ocr(image, preprocess_method)
                
                # 尝试多种OCR配置
                for config in self.ocr_configs:
                    result = self._try_ocr_recognition(processed_image, config, strategy_name)
                    
                    if result['success'] and result['confidence'] > best_confidence:
                        best_result = result
                        best_confidence = result['confidence']
                        
                        # 如果置信度足够高，直接返回
                        if best_confidence >= 0.9:
                            break
                
                if best_confidence >= 0.9:
                    break
                    
            except Exception as e:
                self.logger.error(f"OCR策略 {strategy_name} 失败: {e}")
                continue
        
        # 处理结果
        processing_time = time.time() - start_time
        
        if best_result and best_result['success']:
            self.stats['successful_recognitions'] += 1
            self.stats['average_confidence'] = (
                (self.stats['average_confidence'] * (self.stats['successful_recognitions'] - 1) + 
                 best_result['confidence']) / self.stats['successful_recognitions']
            )
            
            self.logger.info(f"OCR识别成功: {best_result['value']} "
                           f"(置信度: {best_result['confidence']:.2f}, "
                           f"方法: {best_result['method']}, "
                           f"耗时: {processing_time:.3f}s)")
            
            return best_result
        else:
            self.stats['failed_recognitions'] += 1
            self.logger.warning(f"OCR识别失败，耗时: {processing_time:.3f}s")
            
            return {
                'success': False,
                'value': 0.0,
                'confidence': 0.0,
                'method': 'none',
                'error': '无法识别数值'
            }
    
    def _try_ocr_recognition(self, image: np.ndarray, config: str, 
                           method: str) -> Dict[str, Any]:
        """尝试OCR识别"""
        try:
            # OCR识别
            text = pytesseract.image_to_string(image, config=config, lang='eng')
            
            # 获取详细信息
            data = pytesseract.image_to_data(image, config=config, lang='eng', 
                                           output_type=pytesseract.Output.DICT)
            
            # 计算平均置信度
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # 验证结果
            is_valid, value = self.validator.validate_number(
                text.strip(), self.min_value, self.max_value
            )
            
            if is_valid and avg_confidence >= self.confidence_threshold * 100:
                return {
                    'success': True,
                    'value': value,
                    'confidence': avg_confidence / 100,
                    'method': method,
                    'raw_text': text.strip(),
                    'config': config
                }
            else:
                return {
                    'success': False,
                    'value': 0.0,
                    'confidence': avg_confidence / 100,
                    'method': method,
                    'raw_text': text.strip(),
                    'error': f'验证失败或置信度不足: {avg_confidence}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'value': 0.0,
                'confidence': 0.0,
                'method': method,
                'error': str(e)
            }
    
    def recognize_price(self, image: np.ndarray, min_price: float = 1000, 
                       max_price: float = 2000) -> Dict[str, Any]:
        """识别价格"""
        if not TESSERACT_AVAILABLE:
            return {
                'success': False,
                'price': 0.0,
                'confidence': 0.0,
                'error': 'Tesseract不可用'
            }
        
        try:
            # 预处理图像
            processed_image = self.preprocessor.enhance_for_ocr(image, 'auto')
            
            # 使用数字识别配置
            config = "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789.,"
            text = pytesseract.image_to_string(processed_image, config=config, lang='eng')
            
            # 验证价格
            is_valid, price = self.validator.validate_price(text.strip(), min_price, max_price)
            
            if is_valid:
                return {
                    'success': True,
                    'price': price,
                    'confidence': 0.8,  # 简化的置信度
                    'raw_text': text.strip()
                }
            else:
                return {
                    'success': False,
                    'price': 0.0,
                    'confidence': 0.0,
                    'error': f'价格验证失败: {text.strip()}'
                }
                
        except Exception as e:
            self.logger.error(f"价格识别失败: {e}")
            return {
                'success': False,
                'price': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.stats['total_attempts'] > 0:
            success_rate = self.stats['successful_recognitions'] / self.stats['total_attempts']
        
        return {
            'total_attempts': self.stats['total_attempts'],
            'successful_recognitions': self.stats['successful_recognitions'],
            'failed_recognitions': self.stats['failed_recognitions'],
            'success_rate': success_rate,
            'average_confidence': self.stats['average_confidence'],
            'tesseract_available': TESSERACT_AVAILABLE
        }

# 全局增强OCR实例
enhanced_ocr = EnhancedOCR()
