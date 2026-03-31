#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码文档增强工具
版本: v1.0

功能:
1. 自动检测缺少注释的代码
2. 生成标准化的文档字符串
3. 添加类型注解
4. 生成API文档
5. 代码质量检查
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import json
from datetime import datetime


class CodeDocumentationEnhancer:
    """代码文档增强器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_files = []
        self.documentation_stats = {
            'total_files': 0,
            'documented_functions': 0,
            'undocumented_functions': 0,
            'documented_classes': 0,
            'undocumented_classes': 0,
            'files_with_issues': []
        }
        
        # 文档模板
        self.docstring_templates = {
            'function': '''"""
    {description}
    
    Args:
        {args}
    
    Returns:
        {returns}
    
    Raises:
        {raises}
    """''',
            'class': '''"""
    {description}
    
    Attributes:
        {attributes}
    
    Methods:
        {methods}
    """''',
            'module': '''"""
{description}

模块功能:
{features}

作者: {author}
创建时间: {created}
最后修改: {modified}
版本: {version}
"""'''
        }
    
    def scan_project(self) -> Dict[str, Any]:
        """扫描项目中的Python文件"""
        print("🔍 扫描项目文件...")
        
        # 查找所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            # 跳过虚拟环境和缓存目录
            if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            self.python_files.append(py_file)
        
        self.documentation_stats['total_files'] = len(self.python_files)
        print(f"📁 找到 {len(self.python_files)} 个Python文件")
        
        return self.analyze_documentation_coverage()
    
    def analyze_documentation_coverage(self) -> Dict[str, Any]:
        """分析文档覆盖率"""
        print("📊 分析文档覆盖率...")
        
        analysis_results = {
            'files': [],
            'summary': self.documentation_stats.copy()
        }
        
        for py_file in self.python_files:
            try:
                file_analysis = self.analyze_file(py_file)
                analysis_results['files'].append(file_analysis)
                
                # 更新统计信息
                self.documentation_stats['documented_functions'] += file_analysis['documented_functions']
                self.documentation_stats['undocumented_functions'] += file_analysis['undocumented_functions']
                self.documentation_stats['documented_classes'] += file_analysis['documented_classes']
                self.documentation_stats['undocumented_classes'] += file_analysis['undocumented_classes']
                
                if file_analysis['issues']:
                    self.documentation_stats['files_with_issues'].append(str(py_file))
                    
            except Exception as e:
                print(f"⚠️ 分析文件失败 {py_file}: {e}")
        
        # 计算覆盖率
        total_functions = (self.documentation_stats['documented_functions'] + 
                          self.documentation_stats['undocumented_functions'])
        total_classes = (self.documentation_stats['documented_classes'] + 
                        self.documentation_stats['undocumented_classes'])
        
        if total_functions > 0:
            analysis_results['function_coverage'] = (
                self.documentation_stats['documented_functions'] / total_functions * 100
            )
        
        if total_classes > 0:
            analysis_results['class_coverage'] = (
                self.documentation_stats['documented_classes'] / total_classes * 100
            )
        
        analysis_results['summary'] = self.documentation_stats
        
        return analysis_results
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个文件的文档情况"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                'file_path': str(file_path),
                'error': f"语法错误: {e}",
                'documented_functions': 0,
                'undocumented_functions': 0,
                'documented_classes': 0,
                'undocumented_classes': 0,
                'issues': [f"语法错误: {e}"]
            }
        
        analyzer = DocumentationAnalyzer()
        analyzer.visit(tree)
        
        return {
            'file_path': str(file_path),
            'has_module_docstring': analyzer.has_module_docstring,
            'documented_functions': len(analyzer.documented_functions),
            'undocumented_functions': len(analyzer.undocumented_functions),
            'documented_classes': len(analyzer.documented_classes),
            'undocumented_classes': len(analyzer.undocumented_classes),
            'functions': analyzer.documented_functions + analyzer.undocumented_functions,
            'classes': analyzer.documented_classes + analyzer.undocumented_classes,
            'issues': analyzer.issues
        }
    
    def generate_enhanced_docstrings(self, file_path: Path) -> str:
        """为文件生成增强的文档字符串"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content  # 返回原内容
        
        enhancer = DocstringEnhancer(content)
        enhancer.visit(tree)
        
        return enhancer.get_enhanced_content()
    
    def enhance_project_documentation(self) -> Dict[str, str]:
        """增强整个项目的文档"""
        print("✨ 增强项目文档...")
        
        enhanced_files = {}
        
        for py_file in self.python_files:
            try:
                enhanced_content = self.generate_enhanced_docstrings(py_file)
                
                # 检查是否有改动
                with open(py_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                if enhanced_content != original_content:
                    enhanced_files[str(py_file)] = enhanced_content
                    print(f"📝 增强文档: {py_file.name}")
                
            except Exception as e:
                print(f"⚠️ 增强文档失败 {py_file}: {e}")
        
        return enhanced_files
    
    def save_enhanced_files(self, enhanced_files: Dict[str, str], backup: bool = True):
        """保存增强后的文件"""
        print("💾 保存增强后的文件...")
        
        if backup:
            backup_dir = self.project_root / "backup_docs"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for file_path, enhanced_content in enhanced_files.items():
            file_path_obj = Path(file_path)
            
            # 备份原文件
            if backup:
                backup_file = backup_dir / f"{file_path_obj.name}_{timestamp}.bak"
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    with open(backup_file, 'w', encoding='utf-8') as bf:
                        bf.write(f.read())
            
            # 保存增强后的文件
            with open(file_path_obj, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
        
        print(f"✅ 已保存 {len(enhanced_files)} 个增强文件")
    
    def generate_api_documentation(self) -> str:
        """生成API文档"""
        print("📚 生成API文档...")
        
        api_doc = "# API文档\n\n"
        api_doc += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for py_file in self.python_files:
            if 'api' in str(py_file) or 'app.py' in str(py_file):
                api_doc += self._extract_api_info(py_file)
        
        # 保存API文档
        api_doc_path = self.project_root / "docs" / "api_documentation.md"
        api_doc_path.parent.mkdir(exist_ok=True)
        
        with open(api_doc_path, 'w', encoding='utf-8') as f:
            f.write(api_doc)
        
        print(f"✅ API文档已生成: {api_doc_path}")
        return str(api_doc_path)
    
    def _extract_api_info(self, file_path: Path) -> str:
        """提取API信息"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        api_info = f"## {file_path.name}\n\n"
        
        # 提取路由信息
        route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"].*?\)\s*def\s+(\w+)"
        routes = re.findall(route_pattern, content)
        
        for route, function_name in routes:
            api_info += f"### {route}\n"
            api_info += f"**函数**: `{function_name}`\n\n"
            
            # 提取函数文档
            func_pattern = rf"def\s+{function_name}\s*\([^)]*\):\s*\"\"\"([^\"]*)\"\"\""
            func_doc = re.search(func_pattern, content, re.DOTALL)
            if func_doc:
                api_info += f"**描述**: {func_doc.group(1).strip()}\n\n"
            
            api_info += "---\n\n"
        
        return api_info
    
    def generate_documentation_report(self, analysis_results: Dict[str, Any]) -> str:
        """生成文档报告"""
        print("📄 生成文档报告...")
        
        report_path = self.project_root / "docs" / "documentation_report.md"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 代码文档分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 总体统计
            summary = analysis_results['summary']
            f.write("## 总体统计\n\n")
            f.write(f"- **总文件数**: {summary['total_files']}\n")
            f.write(f"- **已文档化函数**: {summary['documented_functions']}\n")
            f.write(f"- **未文档化函数**: {summary['undocumented_functions']}\n")
            f.write(f"- **已文档化类**: {summary['documented_classes']}\n")
            f.write(f"- **未文档化类**: {summary['undocumented_classes']}\n")
            f.write(f"- **有问题的文件**: {len(summary['files_with_issues'])}\n\n")
            
            # 覆盖率
            if 'function_coverage' in analysis_results:
                f.write(f"- **函数文档覆盖率**: {analysis_results['function_coverage']:.1f}%\n")
            if 'class_coverage' in analysis_results:
                f.write(f"- **类文档覆盖率**: {analysis_results['class_coverage']:.1f}%\n")
            f.write("\n")
            
            # 详细分析
            f.write("## 详细分析\n\n")
            for file_info in analysis_results['files']:
                if file_info.get('issues'):
                    f.write(f"### {Path(file_info['file_path']).name}\n")
                    f.write(f"**路径**: `{file_info['file_path']}`\n\n")
                    f.write("**问题**:\n")
                    for issue in file_info['issues']:
                        f.write(f"- {issue}\n")
                    f.write("\n")
            
            # 改进建议
            f.write("## 改进建议\n\n")
            f.write("1. 为所有公共函数和类添加文档字符串\n")
            f.write("2. 使用标准的文档字符串格式 (Google/NumPy风格)\n")
            f.write("3. 添加类型注解提高代码可读性\n")
            f.write("4. 定期运行文档检查工具\n")
            f.write("5. 在代码审查中检查文档质量\n")
        
        print(f"✅ 文档报告已生成: {report_path}")
        return str(report_path)


class DocumentationAnalyzer(ast.NodeVisitor):
    """文档分析器"""
    
    def __init__(self):
        self.has_module_docstring = False
        self.documented_functions = []
        self.undocumented_functions = []
        self.documented_classes = []
        self.undocumented_classes = []
        self.issues = []
    
    def visit_Module(self, node):
        # 检查模块文档字符串
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.has_module_docstring = True
        else:
            self.issues.append("缺少模块文档字符串")
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        # 跳过私有函数和特殊方法
        if node.name.startswith('_'):
            return
        
        # 检查函数文档字符串
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.documented_functions.append({
                'name': node.name,
                'line': node.lineno,
                'docstring': node.body[0].value.value
            })
        else:
            self.undocumented_functions.append({
                'name': node.name,
                'line': node.lineno
            })
            self.issues.append(f"函数 '{node.name}' (第{node.lineno}行) 缺少文档字符串")
    
    def visit_ClassDef(self, node):
        # 检查类文档字符串
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.documented_classes.append({
                'name': node.name,
                'line': node.lineno,
                'docstring': node.body[0].value.value
            })
        else:
            self.undocumented_classes.append({
                'name': node.name,
                'line': node.lineno
            })
            self.issues.append(f"类 '{node.name}' (第{node.lineno}行) 缺少文档字符串")
        
        self.generic_visit(node)


class DocstringEnhancer(ast.NodeVisitor):
    """文档字符串增强器"""
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
        self.enhancements = []
    
    def visit_FunctionDef(self, node):
        # 检查是否需要添加文档字符串
        if (not node.body or 
            not isinstance(node.body[0], ast.Expr) or 
            not isinstance(node.body[0].value, ast.Constant)):
            
            # 生成文档字符串
            docstring = self._generate_function_docstring(node)
            self.enhancements.append({
                'line': node.lineno,
                'type': 'add_docstring',
                'content': docstring
            })
    
    def _generate_function_docstring(self, node) -> str:
        """生成函数文档字符串"""
        args_info = []
        for arg in node.args.args:
            args_info.append(f"{arg.arg}: 参数描述")
        
        docstring = f'    """\n    {node.name}函数的描述\n    \n'
        if args_info:
            docstring += '    Args:\n'
            for arg_info in args_info:
                docstring += f'        {arg_info}\n'
            docstring += '    \n'
        
        docstring += '    Returns:\n        返回值描述\n    """'
        
        return docstring
    
    def get_enhanced_content(self) -> str:
        """获取增强后的内容"""
        enhanced_lines = self.lines.copy()
        
        # 按行号倒序处理，避免行号偏移
        for enhancement in sorted(self.enhancements, key=lambda x: x['line'], reverse=True):
            if enhancement['type'] == 'add_docstring':
                enhanced_lines.insert(enhancement['line'], enhancement['content'])
        
        return '\n'.join(enhanced_lines)


def main():
    """主函数"""
    print("📚 代码文档增强工具")
    print("=" * 40)
    
    # 项目根目录
    project_root = "."
    
    # 创建文档增强器
    enhancer = CodeDocumentationEnhancer(project_root)
    
    # 扫描项目
    analysis_results = enhancer.scan_project()
    
    # 生成文档报告
    report_path = enhancer.generate_documentation_report(analysis_results)
    
    # 生成API文档
    api_doc_path = enhancer.generate_api_documentation()
    
    # 增强项目文档 (可选)
    # enhanced_files = enhancer.enhance_project_documentation()
    # enhancer.save_enhanced_files(enhanced_files, backup=True)
    
    print(f"\n✅ 文档分析完成!")
    print(f"📄 分析报告: {report_path}")
    print(f"📚 API文档: {api_doc_path}")


if __name__ == "__main__":
    main()
