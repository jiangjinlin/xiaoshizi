import os
import xml.etree.ElementTree as ET
import zipfile


def score_word(file_path: str):
    """
    Word 操作题评分。
    返回 (score, total, msg) 三元组。
    规则与原有实现保持一致：
    - 标题为“追逐梦想，不负韶华”，并加粗、居中、仿宋、字号14（28 half-points）各+5分；
    - 正文首段首行缩进约 480 twips +5分；
    - 文档设置双栏 +5分；
    总分 total=30。
    """
    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'ns2': 'http://schemas.microsoft.com/office/word/2010/wordml'
    }
    score = 0
    total = 30
    details = []  # 收集逐项说明

    # 读取 document.xml
    try:
        with zipfile.ZipFile(file_path, 'r') as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
    except Exception as e:
        # 兜底：尝试当作纯 XML 解析
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
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
            # 字体（仿宋/东亚字体）
            rFonts = p.find('.//w:rFonts', ns)
            if rFonts is not None and rFonts.attrib.get('{%s}eastAsia' % ns['w']) == '仿宋':
                font_ok = True
                score += 5
            # 字号（14号=28 half-points）
            sz = p.find('.//w:sz', ns)
            if sz is not None and sz.attrib.get('{%s}val' % ns['w']) == '28':
                size_ok = True
                score += 5
            break

    if not title_found:
        details.append(f"未通过：未找到标题“{title_text}”（0分）")
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
            details.append('通过：标题字体为仿宋（+5分）')
        else:
            miss.append('字体非仿宋')
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
                    details.append('未通过：无法解析首行缩进数值（0分）')
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
