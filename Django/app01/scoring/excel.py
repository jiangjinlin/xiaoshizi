import zipfile
import xml.etree.ElementTree as ET
from typing import Tuple, Optional
import re


def _ln(tag) -> str:
    try:
        return tag.split('}')[-1]
    except Exception:
        return str(tag)


def _findall(root: ET.Element, name: str):
    if root is None:
        return []
    return [e for e in root.iter() if _ln(e.tag) == name]


def _find_first(root: ET.Element, name: str) -> Optional[ET.Element]:
    arr = _findall(root, name)
    return arr[0] if arr else None


def _get_xml(doc, path: str) -> Optional[ET.Element]:
    try:
        data = doc.read(path)
        return ET.fromstring(data)
    except Exception:
        return None


def _get_shared_strings(doc) -> list:
    sst = _get_xml(doc, 'xl/sharedStrings.xml')
    if sst is None:
        return []
    arr = []
    for si in _findall(sst, 'si'):
        # 拼接可能分片的 t
        text_parts = []
        for t in _findall(si, 't'):
            if t.text:
                text_parts.append(t.text)
        arr.append(''.join(text_parts))
    return arr


def _cell_text(c: ET.Element, shared_strings: list) -> str:
    if c is None:
        return ''
    t = c.attrib.get('t')
    # 共享字符串
    if t == 's':
        v = _find_first(c, 'v')
        try:
            idx = int(v.text) if v is not None and v.text is not None else -1
        except Exception:
            idx = -1
        return shared_strings[idx] if 0 <= idx < len(shared_strings) else ''
    # 内联字符串
    if t == 'inlineStr':
        is_el = _find_first(c, 'is')
        if is_el is not None:
            t_el = _find_first(is_el, 't')
            return t_el.text.strip() if (t_el is not None and t_el.text) else ''
    # 公式或数字当作字符串读取
    v = _find_first(c, 'v')
    return v.text if (v is not None and v.text) else ''


def _col_row_from_ref(ref: str):
    # 如 "C12" -> ("C", 12)
    col = ''.join([ch for ch in ref if ch.isalpha()])
    row = int(''.join([ch for ch in ref if ch.isdigit()]) or '0')
    return col, row


def _col_index(col_letters: str) -> int:
    # A->1, B->2 ... AA->27
    n = 0
    for ch in col_letters:
        n = n * 26 + (ord(ch.upper()) - ord('A') + 1)
    return n


def _find_cell(sheet: ET.Element, r: str) -> Optional[ET.Element]:
    # 在 sheetData 下查找具体单元格
    for row in _findall(sheet, 'row'):
        for c in _findall(row, 'c'):
            if c.attrib.get('r') == r:
                return c
    return None


def _xf_maps(styles: ET.Element):
    # 返回 (xf -> borderId, xf -> alignment dict)
    xf_to_border = {}
    xf_to_align = {}
    if styles is None:
        return xf_to_border, xf_to_align, {}
    borders = _find_first(styles, 'borders')
    border_list = _findall(borders, 'border') if borders is not None else []
    cellXfs = _find_first(styles, 'cellXfs')
    if cellXfs is not None:
        for i, xf in enumerate(_findall(cellXfs, 'xf')):
            b_id = xf.attrib.get('borderId')
            try:
                b_id = int(b_id) if b_id is not None else None
            except Exception:
                b_id = None
            xf_to_border[i] = b_id
            align = _find_first(xf, 'alignment')
            if align is not None:
                xf_to_align[i] = {
                    'horizontal': align.attrib.get('horizontal'),
                    'vertical': align.attrib.get('vertical')
                }
            else:
                xf_to_align[i] = {}
    # 构建 borderId -> 四边样式
    border_id_to_sides = {}
    for i, b in enumerate(border_list):
        def side_has_style(tag):
            el = _find_first(b, tag)
            return el is not None and ('style' in el.attrib)
        border_id_to_sides[i] = {
            'left': side_has_style('left'),
            'right': side_has_style('right'),
            'top': side_has_style('top'),
            'bottom': side_has_style('bottom'),
        }
    return xf_to_border, xf_to_align, border_id_to_sides


def score_excel(file_path: str) -> Tuple[int, int, str]:
    """
    Excel 操作题评分。
    要求（共30分）：
    1) A1:J1 合并且写入“CDNU附属高中学生期末成绩表”，并居中（10分）
    2) 工作表名称为“学生成绩表”（5分）
    3) “学号”列自 A001 起为文本格式，序号自增（5分）
    4) “总分”列使用函数计算（5分）
    5) 数据区域添加“所有框线”边框（5分）
    返回 (score, total, msg)
    """
    total = 30
    score = 0
    details = []  # 收集逐项反馈
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            # 基础 XML
            workbook = _get_xml(z, 'xl/workbook.xml')
            sheet = _get_xml(z, 'xl/worksheets/sheet1.xml')
            styles = _get_xml(z, 'xl/styles.xml')
            sst = _get_shared_strings(z)
            if sheet is None or workbook is None:
                return 0, total, '无法读取工作表'

            # 样式映射
            xf_to_border, xf_to_align, border_id_to_sides = _xf_maps(styles)

            # 1) 标题与合并、居中
            ok_title_text = False
            ok_merge = False
            ok_center = False
            title_expected = 'CDNU附属高中学生期末成绩表'
            # 文本
            cA1 = _find_cell(sheet, 'A1')
            txt = _cell_text(cA1, sst)
            if txt.strip() == title_expected:
                ok_title_text = True
            # 合并区域
            merges = _find_first(sheet, 'mergeCells')
            if merges is not None:
                for mc in _findall(merges, 'mergeCell'):
                    if mc.attrib.get('ref', '').upper() == 'A1:J1':
                        ok_merge = True
                        break
            # 居中（查 A1 的对齐样式）
            try:
                s_idx = int(cA1.attrib.get('s')) if cA1 is not None and cA1.attrib.get('s') is not None else None
            except Exception:
                s_idx = None
            if s_idx is not None and s_idx in xf_to_align:
                horiz = xf_to_align[s_idx].get('horizontal')
                if (horiz or '').lower() == 'center':
                    ok_center = True
            # 10 分规则：标题文字 + 合并 + 居中全部满足
            if ok_title_text and ok_merge and ok_center:
                score += 10
                details.append('通过：标题文本、A1:J1 合并、水平居中均符合要求（10分）')
            else:
                miss = []
                if not ok_title_text:
                    miss.append(f"标题文本不匹配（检测到：{txt or '空'}）")
                if not ok_merge:
                    miss.append('未检测到 A1:J1 合并单元格')
                if not ok_center:
                    miss.append('A1 未设置水平居中')
                details.append('未通过：' + '；'.join(miss) + '（0分）')

            # 2) 工作表名称
            ok_sheet_name = False
            actual_sheet_name = None
            for sh in _findall(workbook, 'sheet'):
                # 默认第一张表
                name = sh.attrib.get('name', '')
                sheetId = sh.attrib.get('sheetId')
                if sheetId == '1':
                    actual_sheet_name = name
                    ok_sheet_name = (name == '学生成绩表')
                    break
            if ok_sheet_name:
                score += 5
                details.append('通过：工作表1 名称为“学生成绩表”（5分）')
            else:
                details.append(f"未通过：工作表1 名称应为“学生成绩表”，实际为“{actual_sheet_name or '未知'}”（0分）")

            # 扫描表头：找到“学号”“总分”
            header_row_idx = None
            col_map = {}
            # 遍历前10行寻找表头
            for row in _findall(sheet, 'row'):
                try:
                    r_idx = int(row.attrib.get('r') or '0')
                except Exception:
                    r_idx = 0
                if r_idx == 0 or r_idx > 20:
                    continue
                names = {}
                for c in _findall(row, 'c'):
                    ref = c.attrib.get('r') or ''
                    col, _ = _col_row_from_ref(ref)
                    text = _cell_text(c, sst).strip()
                    if text:
                        names[text] = col
                if ('学号' in names) and ('总分' in names):
                    header_row_idx = r_idx
                    col_map = names
                    break
            if not header_row_idx:
                details.append('未通过：未找到同时包含“学号”“总分”的表头行，后续相关检查跳过')

            data_start = (header_row_idx + 1) if header_row_idx else None

            # 3) 学号列检查
            sid_pass = False
            if header_row_idx and '学号' in col_map:
                sid_col = col_map['学号']  # 列字母
                sid_ok = False
                seq_ok = True
                text_ok = True
                found_count = 0
                expected_num = 1
                first_text_err = None
                first_seq_err = None
                for row in _findall(sheet, 'row'):
                    try:
                        r_idx = int(row.attrib.get('r') or '0')
                    except Exception:
                        r_idx = 0
                    if r_idx < data_start:
                        continue
                    c_ref = f'{sid_col}{r_idx}'
                    c = None
                    for cc in _findall(row, 'c'):
                        if cc.attrib.get('r') == c_ref:
                            c = cc
                            break
                    val = _cell_text(c, sst).strip() if c is not None else ''
                    if not val:
                        # 视为数据区域结束
                        if found_count >= 1:
                            break
                        else:
                            continue
                    # 文本格式：t 为 s/inlineStr/str 任一
                    t_attr = c.attrib.get('t') if c is not None else None
                    if t_attr not in ('s', 'inlineStr', 'str') and first_text_err is None:
                        first_text_err = f'第{r_idx}行学号单元格非文本格式(t={t_attr or "无"})'
                    # 序列 A001, A002 ...
                    if expected_num == 1:
                        # 第一条必须是 A001
                        sid_ok = (val == 'A001')
                        if not sid_ok and first_seq_err is None:
                            first_seq_err = f'第{r_idx}行应为 A001，实际为 {val}'
                    else:
                        expect = f'A{expected_num:03d}'
                        if val != expect and first_seq_err is None:
                            first_seq_err = f'第{r_idx}行应为 {expect}，实际为 {val}'
                        if val != expect:
                            seq_ok = False
                    expected_num += 1
                    found_count += 1
                sid_pass = (sid_ok and seq_ok and (first_text_err is None) and found_count >= 3)
                if sid_pass:
                    score += 5
                    details.append('通过：“学号”列为文本格式，且从 A001 起连续递增（5分）')
                else:
                    reasons = []
                    if not sid_ok:
                        reasons.append(first_seq_err or '首个学号不是 A001')
                    if not seq_ok and first_seq_err:
                        reasons.append(first_seq_err)
                    if first_text_err:
                        reasons.append(first_text_err)
                    if found_count < 3:
                        reasons.append('有效数据行少于 3 行')
                    details.append('未通过：“学号”列不符合要求：' + '；'.join(sorted(set(reasons or ['原因未知']))) + '（0分）')
            elif header_row_idx:
                details.append('未通过：表头未找到“学号”列（0分）')

            # 4) 总分列使用函数
            func_ok = False
            if header_row_idx and '总分' in col_map:
                total_col = col_map['总分']
                row = None
                for r in _findall(sheet, 'row'):
                    if r.attrib.get('r') == str(data_start):
                        row = r
                        break
                if row is not None:
                    c_ref = f'{total_col}{data_start}'
                    c = None
                    for cc in _findall(row, 'c'):
                        if cc.attrib.get('r') == c_ref:
                            c = cc
                            break
                    if c is not None:
                        f_el = _find_first(c, 'f')
                        if f_el is not None and (f_el.text or '').strip():
                            ftxt_raw = (f_el.text or '')
                            ftxt = re.sub(r'\s+', '', ftxt_raw.upper()).replace('$', '')
                            # 仅认可两种：SUM(Dn:In) 或 Dn+En+...+In
                            add_expr = '+'.join([f'{col}{data_start}' for col in ['D','E','F','G','H','I']])
                            sum_expr = f'SUM(D{data_start}:I{data_start})'
                            if ftxt == sum_expr or ftxt == add_expr:
                                func_ok = True
                                score += 5
                                details.append('通过：“总分”列使用正确公式（SUM 或逐项相加）（5分）')
                            else:
                                details.append(f'未通过：“总分”公式不符合要求，应为 {sum_expr} 或 {add_expr}，实际为 {ftxt_raw}（0分）')
                        else:
                            v = _cell_text(c, sst).strip()
                            details.append(f'未通过：“总分”列首个数据单元格未检测到公式（当前值={v or "空"}）（0分）')
                else:
                    details.append('未通过：无法定位“总分”列的数据起始行（0分）')
            elif header_row_idx:
                details.append('未通过：表头未找到“总分”列（0分）')

            # 5) 数据区域所有框线（抽样校验）
            border_ok = False
            if header_row_idx:
                used_cols = [col_map.get(k) for k in col_map.keys()]
                used_cols = [c for c in used_cols if c]
                if used_cols:
                    min_c = min(_col_index(c) for c in used_cols)
                    max_c = max(_col_index(c) for c in used_cols)
                    last_row = header_row_idx
                    for row in _findall(sheet, 'row'):
                        try:
                            r_idx = int(row.attrib.get('r') or '0')
                        except Exception:
                            r_idx = 0
                        if r_idx >= data_start:
                            # 如果这一行在任一已用列有值，就扩展 last_row
                            for c in _findall(row, 'c'):
                                col_letters, rr = _col_row_from_ref(c.attrib.get('r', ''))
                                if rr != r_idx:
                                    continue
                                ci = _col_index(col_letters)
                                if min_c <= ci <= max_c:
                                    v = _cell_text(c, sst).strip()
                                    if v:
                                        if r_idx > last_row:
                                            last_row = r_idx
                                        break
                    # 从表头行和首尾两行抽样若干单元格，检查四边样式
                    def cell_has_all_borders(c_el: ET.Element) -> bool:
                        if c_el is None:
                            return False
                        try:
                            s_idx = int(c_el.attrib.get('s'))
                        except Exception:
                            return False
                        b_id = xf_to_border.get(s_idx)
                        sides = border_id_to_sides.get(b_id)
                        if not sides:
                            return False
                        return all(bool(sides.get(k)) for k in ['left', 'right', 'top', 'bottom'])

                    samples = []
                    for r_idx in (header_row_idx, data_start, last_row):
                        if not r_idx:
                            continue
                        # 取三列位置：min、中间、max
                        mid_c = (min_c + max_c) // 2
                        for ci in (min_c, mid_c, max_c):
                            # 构造单元格引用
                            # 反推列字母
                            def to_col(n: int) -> str:
                                s = ''
                                while n:
                                    n, rem = divmod(n - 1, 26)
                                    s = chr(ord('A') + rem) + s
                                return s
                            ref = f'{to_col(ci)}{r_idx}'
                            samples.append(_find_cell(sheet, ref))
                    if samples:
                        ok_count = sum(1 for c in samples if cell_has_all_borders(c))
                        ratio = ok_count / len(samples)
                        if ratio >= 0.7:
                            border_ok = True
                            score += 5
                            details.append(f'通过：数据区域“所有框线”抽样通过（{ok_count}/{len(samples)}）（5分）')
                        else:
                            details.append(f'未通过：数据区域边框抽样仅 {ok_count}/{len(samples)} 个单元格具备四边框，疑似未设置“所有框线”（0分）')
                else:
                    details.append('未通过：无法推断数据区域列范围（0分）')

            msg = '\n'.join(details) if details else '评分完成'
            return score, total, msg
    except Exception as e:
        return 0, total, f'文件解析失败：{e}'
