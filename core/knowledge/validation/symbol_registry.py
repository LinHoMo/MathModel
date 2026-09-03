"""
L1: Symbol Registry - 符号注册表
确保符号一致性：一个符号只表示一个物理量，全文一致
"""
import re
from typing import Optional


class SymbolRegistry:
    """L1: 符号注册表 - 管理符号定义和一致性"""
    
    def __init__(self):
        self.symbols = {}  # symbol -> {meaning, unit, first_appearance}
        self.conflicts = []
    
    def register(self, symbol: str, meaning: str, unit: str, location: str = "") -> bool:
        """注册一个符号
        
        Returns:
            bool: True=注册成功, False=发现冲突
        """
        # 清理符号
        symbol = symbol.strip()
        
        if symbol in self.symbols:
            existing = self.symbols[symbol]
            # 检查是否冲突
            if existing["meaning"] != meaning or existing["unit"] != unit:
                self.conflicts.append({
                    "symbol": symbol,
                    "existing": existing,
                    "new": {"meaning": meaning, "unit": unit, "location": location}
                })
                return False
            # 相同定义，更新位置
            if location:
                existing["locations"].append(location)
            return True
        
        self.symbols[symbol] = {
            "meaning": meaning,
            "unit": unit,
            "first_appearance": location,
            "locations": [location] if location else []
        }
        return True
    
    def check_conflicts(self) -> list:
        """检查所有冲突"""
        return self.conflicts
    
    def check_consistency(self) -> dict:
        """检查符号一致性"""
        issues = []
        
        # 检查同义不同符
        meaning_map = {}
        for sym, info in self.symbols.items():
            key = (info["meaning"], info["unit"])
            if key not in meaning_map:
                meaning_map[key] = []
            meaning_map[key].append(sym)
        
        for key, syms in meaning_map.items():
            if len(syms) > 1:
                issues.append({
                    "type": "same_meaning_different_symbol",
                    "meaning": key[0],
                    "unit": key[1],
                    "symbols": syms
                })
        
        # 检查同符不同义
        # （已在register中检测）
        
        return {
            "consistent": len(issues) == 0 and len(self.conflicts) == 0,
            "issues": issues,
            "conflicts": self.conflicts,
            "total_symbols": len(self.symbols)
        }
    
    def validate_symbol(self, symbol: str, expected_meaning: str = None, expected_unit: str = None) -> dict:
        """验证单个符号"""
        if symbol not in self.symbols:
            return {"valid": False, "issue": f"符号 '{symbol}' 未注册"}
        
        info = self.symbols[symbol]
        issues = []
        
        if expected_meaning and info["meaning"] != expected_meaning:
            issues.append(f"含义不匹配: 期望'{expected_meaning}', 实际'{info['meaning']}'")
        if expected_unit and info["unit"] != expected_unit:
            issues.append(f"单位不匹配: 期望'{expected_unit}', 实际'{info['unit']}'")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def get_all_symbols(self) -> list:
        """获取所有已注册符号"""
        return [
            {"symbol": sym, **info}
            for sym, info in self.symbols.items()
        ]
    
    def generate_symbol_table(self) -> str:
        """生成符号表Markdown"""
        if not self.symbols:
            return "（无符号定义）"
        
        lines = ["| 符号 | 含义 | 单位 |", "|------|------|------|"]
        for sym, info in sorted(self.symbols.items()):
            lines.append(f"| ${sym}$ | {info['meaning']} | {info['unit']} |")
        
        return "\n".join(lines)
    
    def extract_from_text(self, text: str) -> dict:
        """从文本中提取符号定义"""
        # 匹配表格格式: | 符号 | 含义 | 单位 |
        table_pattern = r"\|\s*\$?([^$|]+)\$?\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
        matches = re.findall(table_pattern, text)
        
        extracted = []
        for match in matches:
            symbol = match[0].strip()
            meaning = match[1].strip()
            unit = match[2].strip()
            
            # 跳过表头
            if symbol in ["符号", "Symbol", "---", "----"]:
                continue
            
            self.register(symbol, meaning, unit, "text_extraction")
            extracted.append({"symbol": symbol, "meaning": meaning, "unit": unit})
        
        return {"extracted": len(extracted), "symbols": extracted}


def check_symbol_consistency(text: str) -> dict:
    """便捷函数：检查文本中的符号一致性"""
    registry = SymbolRegistry()
    registry.extract_from_text(text)
    return registry.check_consistency()
