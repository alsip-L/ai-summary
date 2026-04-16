from typing import List
from pathlib import Path
from dataclasses import dataclass
from core.config_manager import ConfigManager


@dataclass
class PathConfig:
    """路径配置数据类
    
    Attributes:
        input_path: txt文件输入路径
        output_path: md文件输出路径（如果未设置，默认与输入路径相同）
    """
    input_path: str
    output_path: str
    
    def __post_init__(self):
        if not self.output_path:
            self.output_path = self.input_path


class FileManager:
    """文件路径管理器
    
    职责：管理txt输入路径和md输出路径，扫描输入文件，生成输出路径
    
    使用示例：
        manager = FileManager()
        
        # 设置路径
        manager.set_paths("/data/txt_files", "/output/md_files")
        
        # 获取当前路径配置
        paths = manager.get_paths()
        
        # 扫描txt文件
        txt_files = manager.scan_input_files()
        
        # 获取对应的输出路径
        md_path = manager.get_output_path("/data/txt_files/article.txt")
    """
    
    def __init__(self):
        self.config = ConfigManager()
    
    def get_paths(self) -> PathConfig:
        """获取当前路径配置
        
        Returns:
            PathConfig对象，包含输入和输出路径
        """
        paths = self.config.get("file_paths", {})
        return PathConfig(
            input_path=paths.get("input", ""),
            output_path=paths.get("output", "")
        )
    
    def set_paths(self, input_path: str, output_path: str = None) -> bool:
        """设置输入和输出路径
        
        Args:
            input_path: txt文件输入路径
            output_path: md文件输出路径（可选，默认与输入路径相同）
            
        Returns:
            是否设置成功
        """
        return self.config.set("file_paths", {
            "input": input_path,
            "output": output_path or input_path
        })
    
    def scan_input_files(self) -> List[Path]:
        """扫描输入路径中的所有txt文件
        
        Returns:
            txt文件路径列表（Path对象）
        """
        paths = self.get_paths()
        input_dir = Path(paths.input_path)
        
        if not input_dir.exists():
            return []
        
        return list(input_dir.rglob("*.txt"))
    
    def get_output_path(self, input_file_path: str) -> Path:
        """根据输入文件路径生成输出文件路径
        
        例如：
            输入: /data/txt_files/folder/article.txt
            输出: /output/md_files/folder/article.md
        
        Args:
            input_file_path: 输入txt文件的完整路径
            
        Returns:
            输出md文件的Path对象
        """
        paths = self.get_paths()
        input_path = Path(input_file_path)
        
        # 计算相对路径
        try:
            relative = input_path.relative_to(paths.input_path)
        except ValueError:
            # 如果不在输入路径下，直接使用文件名
            relative = input_path.name
        
        # 生成输出路径
        output_dir = Path(paths.output_path)
        output_file = output_dir / relative.with_suffix(".md")
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        return output_file
    
    def validate_paths(self) -> tuple[bool, str]:
        """验证路径配置是否有效
        
        Returns:
            (是否有效, 错误信息) 的元组
        """
        paths = self.get_paths()
        
        if not paths.input_path:
            return False, "输入路径未设置"
        
        input_dir = Path(paths.input_path)
        if not input_dir.exists():
            return False, f"输入路径不存在: {paths.input_path}"
        
        if not input_dir.is_dir():
            return False, f"输入路径不是目录: {paths.input_path}"
        
        # 检查输出路径（如果不存在会尝试创建）
        if paths.output_path:
            output_dir = Path(paths.output_path)
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"无法创建输出目录: {e}"
        
        return True, "路径有效"
    
    def get_relative_path(self, file_path: str) -> str:
        """获取文件相对于输入路径的相对路径
        
        Args:
            file_path: 文件的完整路径
            
        Returns:
            相对路径字符串
        """
        paths = self.get_paths()
        path = Path(file_path)
        
        try:
            return str(path.relative_to(paths.input_path))
        except ValueError:
            return path.name
