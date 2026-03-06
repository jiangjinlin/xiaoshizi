"""操作题自动评分模块

将 Word、Excel、PPT 的评分逻辑拆分到独立文件，便于维护与扩展。
对外暴露统一入口 auto_score_operation(file_path)。

新增题型的建议方式：
- 新增一个 {type}.py，提供 score_{type}(file_path) 或 score(file_path) 函数；
- 在 EXT_TO_SCORER 中注册扩展名到评分函数的映射。
"""
from .word import score_word  # noqa: F401
from .excel import score_excel  # noqa: F401
from .ppt import score_ppt  # noqa: F401
import os

# 扩展名到评分函数的映射，可按需扩展
EXT_TO_SCORER = {
    '.docx': score_word,
    '.xlsx': score_excel,
    '.pptx': score_ppt,
}


def auto_score_operation(file_path: str):
    """根据文件扩展名分发到对应评分器。
    返回值规范：
    - 可返回 dict，如 { 'suggest_score': int, 'full_score': int, 'msg': str, ... }
    - 或返回 (score, total, msg) 三元组
    """
    ext = os.path.splitext(file_path)[1].lower()
    scorer = EXT_TO_SCORER.get(ext)
    if not scorer:
        return {'msg': f'不支持的文件类型: {ext}', 'suggest_score': 0, 'full_score': 0}
    try:
        return scorer(file_path)
    except Exception as e:
        return {'msg': f'评分失败: {e}', 'suggest_score': 0, 'full_score': 0}

