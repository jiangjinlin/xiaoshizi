import io
import os
import xml.etree.ElementTree as ET
import zipfile

# 已知 OOXML 标准 URI → 规范前缀映射
_OOXML_URI_TO_PREFIX = {
    'http://schemas.openxmlformats.org/wordprocessingml/2006/main': 'w',
    'http://schemas.microsoft.com/office/word/2010/wordml': 'w14',
    'http://schemas.openxmlformats.org/officeDocument/2006/relationships': 'r',
    'http://schemas.openxmlformats.org/drawingml/2006/main': 'a',
    'http://schemas.openxmlformats.org/presentationml/2006/main': 'p',
    'http://schemas.openxmlformats.org/spreadsheetml/2006/main': 'x',
    'http://schemas.openxmlformats.org/package/2006/relationships': 'rel',
}

# 默认命名空间（底底，确保 XPath 查询始终可用）
_NS_DEFAULTS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
}


def get_namespace_map(xml_bytes: bytes) -> dict:
    """动态提取并映射 OOXML 文档的有效命名空间，返回可用于 ElementTree XPath 查询的字典。

    通过 iterparse 的 start-ns 事件预扫描文档全部 xmlns 声明，将已知 OOXML 标准 URI
    规范化到固定前缀（如 ``w``、``a``、``r`` 等），同时保留文档中声明的非标准扩展
    命名空间（如 WPS 自定义扩展），确保跨版本（WPS / Office 2016 / Office 365 等）
    的 XPath 寻址路径不受命名空间前缀差异影响，精准命中目标结构标签。

    Args:
        xml_bytes: 待解析的 XML 文件原始字节。

    Returns:
        ``{'prefix': 'uri', ...}`` 形式的命名空间字典，可直接传给
        ``Element.find()`` / ``Element.findall()`` 的 ``namespaces`` 参数。
    """
    ns_map: dict = dict(_NS_DEFAULTS)
    try:
        for _, (prefix, uri) in ET.iterparse(io.BytesIO(xml_bytes), events=['start-ns']):
            if not uri:
                continue
            # 按 URI 映射到标准前缀，保证 XPath 表达式与版本无关
            std_prefix = _OOXML_URI_TO_PREFIX.get(uri)
            if std_prefix:
                ns_map[std_prefix] = uri
            # 保留文档原始声明的非标准/扩展命名空间前缀
            if prefix and prefix not in ns_map:
                ns_map[prefix] = uri
    except Exception:
        pass
    return ns_map



def score_word(file_path: str):
    """Word 操作题评分。

    基于 OOXML 国际标准，利用 Python 内置 zipfile 库对 .docx 文档进行流式解压，
    定位 ``word/document.xml`` 核心内容文件，并通过 :func:`get_namespace_map`
    动态提取文档命名空间（兼容 WPS、Office 2016 等不同版本产生的命名空间差异），
    随后深入解析底层 XML 属性特征进行细粒度评分。

    返回 (score, total, msg) 三元组：
    - 标题为“追逐梦想，不负韶华”，并加粗、居中、俳宋、字号14（28 half-points）呅4×5分；
    - 正文首段首行缩进约 480 twips +5分；
    - 文档设置双栏 +5分；
    总分 total=30。
    """
    score = 0
    total = 30
    details = []  # 收集逐项说明

    # 流式读取 document.xml（zipfile 内存解压，全程无需额外落盘）
    try:
        with zipfile.ZipFile(file_path, 'r') as docx:
            xml_content = docx.read('word/document.xml')
            # 动态提取文档命名空间，兼容 WPS / Office 多版本
            ns = get_namespace_map(xml_content)
            root = ET.fromstring(xml_content)
    except Exception as e:
        # 底底：尝试当作纯 XML 解析
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            ns = _NS_DEFAULTS.copy()
        except Exception:
            return 0, total, f"文件格式无法解析：{e}"

    title_text = "追逐梦想，不负韶华"
    title_found = False
    bold_ok = False
    center_ok = False
    font_ok = False
    size_ok = False

    # 标题定位与样式检查
    for p in root.findall('.//w:p', ns):
        t = p.find('.//w:t', ns)
        if t is not None and t.text and t.text.strip() == title_text:
            title_found = True
            # 加粗
            if p.find('.//w:b', ns) is not None:
                bold_ok = True
                score += 5
            # 居中（段落对齐）
            jc = p.find('.//w:jc', ns)
            if jc is not None and jc.attrib.get('{%s}val' % ns['w']) == 'center':
                center_ok = True
                score += 5
            # 字体（俳宋/东亚字体）
            rFonts = p.find('.//w:rFonts', ns)
            if rFonts is not None and rFonts.attrib.get('{%s}eastAsia' % ns['w']) == '俳宋':
                font_ok = True
                score += 5
            # 字号（14号=28 half-points）
            sz = p.find('.//w:sz', ns)
            if sz is not None and sz.attrib.get('{%s}val' % ns['w']) == '28':
                size_ok = True
                score += 5
            break

    if not title_found:
        details.append(f'未通过：未找到标题“{title_text}”（0分）')
    else:
        miss = []
        if bold_ok:
            details.append('通过：标题加粗（+5分）')
        else:
            miss.append('未加粗')
        if center_ok:
            details.append('通过：标题居中（+5分）')
        else:
            miss.append('未居中')
        if font_ok:
            details.append('通过：标题字体为俳宋（+5分）')
        else:
            miss.append('字体非俳宋')
        if size_ok:
            details.append('通过：标题字号为14号（+5分）')
        else:
            miss.append('字号非14号(应为28 half-points)')
        if miss:
            details.append('未通过：标题样式不完全符合要求：' + '；'.join(miss) + '（上述未通过项不计分）')

    # 正文首段首行缩进（排除标题段）
    if title_found:
        for p in root.findall('.//w:p', ns):
            t = p.find('.//w:t', ns)
            text_val = (t.text or '').strip() if t is not None and t.text else ''
            if not text_val or text_val == title_text:
                # 跳过空行与标题行
                continue
            ind = p.find('.//w:ind', ns)
            if ind is not None and ind.attrib.get('{%s}firstLine' % ns['w']):
                try:
                    indent_val = float(ind.attrib.get('{%s}firstLine' % ns['w']))
                    if abs(indent_val - 480) <= 10:
                        score += 5
                        details.append('通过：正文首段首行缩进约 480 twips（+5分）')
                    else:
                        details.append(f'未通过：正文首段首行缩进应约 480 twips，实际 {indent_val}（0分）')
                except Exception:
                    details.append('未通过：无法解析首行缩进数値（0分）')
            else:
                details.append('未通过：未检测到正文首段首行缩进设置（0分）')
            break

    # 分栏设置检查（双栏）
    two_cols = False
    for cols in root.findall('.//w:cols', ns):
        num = cols.attrib.get('{%s}num' % ns['w'])
        try:
            if num and int(num) == 2:
                two_cols = True
                break
        except Exception:
            pass
    if two_cols:
        score += 5
        details.append('通过：文档设置为双栏（+5分）')
    else:
        details.append('未通过：未检测到文档设置为双栏（0分）')

    msg = '\n'.join(details) if details else '评分完成'
    return score, total, msg
