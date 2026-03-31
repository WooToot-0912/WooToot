"""
图像预处理增强模块
用于提高检测准确性，减少背景、阴影等干扰因素

优化说明:
  - segment_leaf_by_background(): 基于背景颜色(黑/灰)反向识别叶片前景
  - enhance_for_detection_full(): 集成完整预处理流程(分割+增强+滤波)
  - enhance_for_detection_light(): 轻量级增强(保留，向后兼容)
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict
import logging

class ImageEnhancer:
    """图像增强器，专门用于烟草叶片病害检测的预处理"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ---------------------------------------------------------------
    # 新增: 基于背景颜色的叶片前景分割（用户指定方案）
    # ---------------------------------------------------------------
    def segment_leaf_by_background(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        通过识别背景颜色（黑色/灰色/暗色）来反向提取叶片前景。
        
        比传统的"找绿色"更稳健：即使叶片出现严重病害（棕褐色/暗色），
        仍能正确识别叶片区域。
        
        Args:
            image: 输入图像 (BGR格式)
        
        Returns:
            leaf_mask:  叶片区域掩码 (0=背景, 255=叶片)
            leaf_image: 叶片区域的原图(背景填黑)
            info:       分析信息字典
        """
        info = {'method': 'background_subtraction', 'background_type': 'unknown'}
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        
        # ---- 1. 识别黑色背景 (低亮度，低饱和度) ----
        black_bg_mask = (v < 50).astype(np.uint8) * 255
        
        # ---- 2. 识别深灰色背景 (低饱和度, 中低亮度) ----
        dark_gray_bg_mask = ((s < 35) & (v < 120)).astype(np.uint8) * 255
        
        # ---- 3. 识别浅灰/白色背景 (低饱和度, 高亮度) ----
        light_gray_bg_mask = ((s < 25) & (v >= 180)).astype(np.uint8) * 255
        
        # ---- 4. 识别紫色/蓝紫色背景 (紫色色调范围, 中低饱和度) ----
        purple_bg_mask = (
            ((h >= 120) & (h <= 160)) &  # 紫色色调
            (s >= 20) & (s < 120) &
            (v > 40) & (v < 180)
        ).astype(np.uint8) * 255
        
        # ---- 合并所有背景掩码 ----
        background_mask = cv2.bitwise_or(black_bg_mask, dark_gray_bg_mask)
        background_mask = cv2.bitwise_or(background_mask, light_gray_bg_mask)
        background_mask = cv2.bitwise_or(background_mask, purple_bg_mask)
        
        # ---- 形态学处理，连接背景碎片 ----
        kernel_bg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_CLOSE, kernel_bg)
        background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_DILATE, kernel_bg, iterations=1)
        
        # ---- 叶片掩码 = 非背景 ----
        leaf_mask = cv2.bitwise_not(background_mask)
        
        # ---- 形态学清理叶片区域（填充内部空洞，去除噪点）----
        kernel_leaf = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel_leaf, iterations=2)
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel_leaf, iterations=1)
        
        # ---- 保留最大连通区域（叶片主体）----
        contours, _ = cv2.findContours(leaf_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # 按面积排序，保留前3个最大连通区域（防止复杂叶片被拆分）
            contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)
            clean_mask = np.zeros_like(leaf_mask)
            max_area = cv2.contourArea(contours_sorted[0])
            for cnt in contours_sorted:
                if cv2.contourArea(cnt) >= max_area * 0.1:  # 保留面积≥最大区域10%的部分
                    cv2.fillPoly(clean_mask, [cnt], 255)
            leaf_mask = clean_mask
        
        # ---- 统计信息 ----
        total_pixels = image.shape[0] * image.shape[1]
        leaf_ratio = np.sum(leaf_mask > 0) / total_pixels
        bg_black_ratio = np.sum(black_bg_mask > 0) / total_pixels
        bg_gray_ratio = np.sum(dark_gray_bg_mask > 0) / total_pixels
        bg_purple_ratio = np.sum(purple_bg_mask > 0) / total_pixels
        
        if bg_black_ratio > 0.1:
            info['background_type'] = 'black'
        elif bg_purple_ratio > 0.1:
            info['background_type'] = 'purple'
        elif bg_gray_ratio > 0.1:
            info['background_type'] = 'gray'
        else:
            info['background_type'] = 'mixed_or_unknown'
        
        info.update({
            'leaf_ratio': float(leaf_ratio),
            'bg_black_ratio': float(bg_black_ratio),
            'bg_gray_ratio': float(bg_gray_ratio),
            'bg_purple_ratio': float(bg_purple_ratio),
        })
        
        # ---- 如果叶片面积过小（提取失败），回退到宽松模式 ----
        if leaf_ratio < 0.05:
            self.logger.warning(f"叶片提取面积过小({leaf_ratio:.2%})，回退到宽松模式")
            info['method'] = 'fallback_loose'
            # 宽松模式：去除纯黑区域，保留其余所有区域
            leaf_mask = (v > 30).astype(np.uint8) * 255
        
        # ---- 应用掩码得到叶片图像 ----
        leaf_image = cv2.bitwise_and(image, image, mask=leaf_mask)
        
        return leaf_mask, leaf_image, info

    def enhance_for_detection_full(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        完整叶片预处理流程（用户指定方案）：
        1. 基于背景颜色分割叶片（HSV/RGB颜色通道）
        2. 光照均匀化（CLAHE）
        3. 对比度增强
        4. 双边滤波去噪（保留边缘）
        5. 病害特征增强（饱和度提升）

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            enhanced_image: 增强后的图像
            enhancement_info: 处理信息
        """
        enhancement_info = {
            'original_shape': image.shape,
            'applied_enhancements': []
        }

        # Step 1: 基于背景颜色分割叶片
        try:
            leaf_mask, leaf_image, seg_info = self.segment_leaf_by_background(image)
            enhancement_info['leaf_segmentation'] = seg_info
            enhancement_info['applied_enhancements'].append('background_subtraction')
            current_img = leaf_image  # 使用叶片区域图像
        except Exception as e:
            self.logger.warning(f"叶片分割失败，使用原图: {e}")
            leaf_mask = None
            current_img = image.copy()

        # Step 2: 光照均匀化
        current_img = self.correct_illumination(current_img)
        enhancement_info['applied_enhancements'].append('illumination_correction')

        # Step 3: 对比度增强（CLAHE）
        current_img = self.enhance_contrast(current_img)
        enhancement_info['applied_enhancements'].append('contrast_enhancement')

        # Step 4: 双边滤波去噪
        current_img = self.reduce_noise(current_img)
        enhancement_info['applied_enhancements'].append('noise_reduction')

        # Step 5: 病害特征增强（颜色饱和度提升，突出病害颜色）
        current_img = self.enhance_disease_features(current_img)
        enhancement_info['applied_enhancements'].append('disease_feature_enhancement')

        # 保存叶片掩码以便后续使用
        enhancement_info['leaf_mask_available'] = leaf_mask is not None

        return current_img, enhancement_info
        
    def enhance_for_detection_light(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        轻量级图像增强，不进行背景去除，避免误删病害区域

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            enhanced_image: 增强后的图像
            enhancement_info: 增强处理信息
        """
        enhancement_info = {
            'original_shape': image.shape,
            'applied_enhancements': []
        }

        # 直接使用原始图像，不进行背景去除
        current_img = image.copy()

        # 1. 光照均匀化（轻度）
        illumination_corrected = self.correct_illumination(current_img)
        enhancement_info['applied_enhancements'].append('illumination_correction')

        # 2. 对比度增强（轻度）
        contrast_enhanced = self.enhance_contrast(illumination_corrected)
        enhancement_info['applied_enhancements'].append('contrast_enhancement')

        # 3. 降噪处理
        denoised = self.reduce_noise(contrast_enhanced)
        enhancement_info['applied_enhancements'].append('noise_reduction')

        return denoised, enhancement_info

    def enhance_for_detection(self, image: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        综合图像增强，提高病害检测准确性
        ⚠️ 注意：此方法包含背景去除，可能会误删病害区域，建议使用 enhance_for_detection_light

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            enhanced_image: 增强后的图像
            enhancement_info: 增强处理信息
        """
        enhancement_info = {
            'original_shape': image.shape,
            'applied_enhancements': []
        }

        # 1. 背景分离和叶片提取
        leaf_mask, background_removed = self.remove_background(image)
        enhancement_info['applied_enhancements'].append('background_removal')

        # 2. 阴影消除
        shadow_corrected = self.remove_shadows(background_removed, leaf_mask)
        enhancement_info['applied_enhancements'].append('shadow_correction')

        # 3. 光照均匀化
        illumination_corrected = self.correct_illumination(shadow_corrected)
        enhancement_info['applied_enhancements'].append('illumination_correction')

        # 4. 对比度和清晰度增强
        contrast_enhanced = self.enhance_contrast(illumination_corrected)
        enhancement_info['applied_enhancements'].append('contrast_enhancement')
        
        # 5. 噪声减少
        denoised = self.reduce_noise(contrast_enhanced)
        enhancement_info['applied_enhancements'].append('noise_reduction')
        
        # 6. 病害特征增强
        disease_enhanced = self.enhance_disease_features(denoised)
        enhancement_info['applied_enhancements'].append('disease_feature_enhancement')
        
        return disease_enhanced, enhancement_info
    
    def remove_background(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        移除背景，保留叶片区域
        """
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 定义绿色范围（叶片颜色）
        lower_green1 = np.array([35, 40, 40])
        upper_green1 = np.array([85, 255, 255])
        
        # 创建绿色掩码
        green_mask = cv2.inRange(hsv, lower_green1, upper_green1)
        
        # 形态学操作，去除噪声
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
        
        # 找到最大连通区域（主要叶片）
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            leaf_mask = np.zeros_like(green_mask)
            cv2.fillPoly(leaf_mask, [largest_contour], 255)
        else:
            leaf_mask = green_mask
        
        # 应用掩码
        background_removed = cv2.bitwise_and(image, image, mask=leaf_mask)
        
        return leaf_mask, background_removed
    
    def remove_shadows(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        消除阴影影响
        """
        # 转换到LAB色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # 在叶片区域内计算亮度统计
        masked_l = cv2.bitwise_and(l_channel, l_channel, mask=mask)
        non_zero_pixels = masked_l[masked_l > 0]
        
        if len(non_zero_pixels) > 0:
            # 计算目标亮度
            target_brightness = np.percentile(non_zero_pixels, 75)
            
            # 创建亮度调整映射
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)
            
            # 重新组合LAB通道
            lab[:, :, 0] = l_channel
            shadow_corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            shadow_corrected = image
        
        return shadow_corrected
    
    def correct_illumination(self, image: np.ndarray) -> np.ndarray:
        """
        光照均匀化
        """
        # 转换到YUV色彩空间
        yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        
        # 对Y通道进行直方图均衡化
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        
        # 转换回BGR
        illumination_corrected = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        
        return illumination_corrected
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        增强对比度和清晰度
        """
        # 转换到LAB色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # 对L通道应用CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # 转换回BGR
        contrast_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 锐化滤波器
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
        
        # 混合原图和锐化图
        alpha = 0.7
        contrast_enhanced = cv2.addWeighted(contrast_enhanced, alpha, sharpened, 1-alpha, 0)
        
        return contrast_enhanced
    
    def reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        减少噪声
        """
        # 使用双边滤波保持边缘的同时减少噪声
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        return denoised
    
    def enhance_disease_features(self, image: np.ndarray) -> np.ndarray:
        """
        增强病害特征
        """
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 增强饱和度以突出病害颜色
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.2)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # 转换回BGR
        disease_enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return disease_enhanced
    
    def create_focus_mask(self, image: np.ndarray, leaf_mask: np.ndarray) -> np.ndarray:
        """
        创建焦点掩码，突出叶片区域，模糊背景
        """
        # 创建高斯模糊的背景
        blurred_bg = cv2.GaussianBlur(image, (21, 21), 0)
        
        # 创建渐变掩码
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
        dilated_mask = cv2.dilate(leaf_mask, kernel, iterations=1)
        
        # 高斯模糊掩码边缘
        smooth_mask = cv2.GaussianBlur(dilated_mask, (15, 15), 0)
        smooth_mask = smooth_mask.astype(np.float32) / 255.0
        
        # 混合清晰叶片和模糊背景
        focused_image = image.astype(np.float32) * smooth_mask[:, :, np.newaxis] + \
                       blurred_bg.astype(np.float32) * (1 - smooth_mask[:, :, np.newaxis])
        
        return focused_image.astype(np.uint8)
