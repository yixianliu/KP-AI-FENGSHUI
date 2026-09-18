"""
service/bazi_service.py — 八字业务编排层

对应执行计划任务 3.1-3.2：
- 封装 BaziCalculator 为可复用的业务服务
- 提供历史记录模糊搜索
- 综合建议落库（save_pan_record）
- 事件总线参数变更 -> 计算 -> 视图刷新

设计原则：
1. core 层只负责确定性计算，service 层负责业务编排
2. 参数校验委托 core/data_validator_v2
3. 历史记录存 SQLite（通过 core/database_manager 的 analysis_records 表）
4. 事件机制用简单回调列表，避免引入重量级依赖
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

from core.bazi.bazi_calculator import BaziCalculator
from core.knowledge.data_validator_v2 import validate_bazi_input
from core import database_manager as dbm_module

# ---------------------------------------------------------------- 事件总线

class EventBus:
    """极简事件总线：参数变更 -> 计算 -> 视图刷新。

    支持：
    - subscribe(event, callback)：订阅事件
    - emit(event, payload)：发布事件

    事件名约定：
    - 'params_changed'：参数变更
    - 'result_ready'：计算完成
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, callback: Callable) -> Callable[[], None]:
        """订阅事件，返回取消订阅函数。"""
        self._listeners.setdefault(event, []).append(callback)

        def unsubscribe():
            if event in self._listeners:
                try:
                    self._listeners[event].remove(callback)
                except ValueError:
                    pass

        return unsubscribe

    def emit(self, event: str, payload: Dict[str, Any] = None) -> None:
        """发布事件，触发所有订阅者。"""
        for cb in list(self._listeners.get(event, [])):
            try:
                cb(payload or {})
            except Exception:
                pass  # 订阅者异常不影响其他订阅者


# ---------------------------------------------------------------- 业务服务

class BaziService:
    """八字业务编排服务。

    职责：
    1. 校验输入
    2. 调用 BaziCalculator 完成排盘
    3. 生成综合建议
    4. 落库历史记录
    5. 发布事件通知视图刷新
    """

    def __init__(self):
        self._calculator = BaziCalculator()
        self._bus = EventBus()

    # ===== 事件 =====

    def subscribe(self, event: str, callback: Callable) -> Callable[[], None]:
        """订阅业务事件。"""
        return self._bus.subscribe(event, callback)

    # ===== 核心方法 =====

    def calculate(self, year: int, month: int, day: int, hour: int,
                  minute: int = 0, longitude: float = 120.0,
                  gender: str = '男', save: bool = True,
                  name: str = '') -> Dict[str, Any]:
        """执行完整八字排盘（含校验、计算、落库、事件）。

        Args:
            year, month, day, hour: 出生时间
            minute: 分钟
            longitude: 经度（真太阳时修正）
            gender: 性别（男/女）
            save: 是否落库历史记录
            name: 命主姓名（可选，用于历史记录）

        Returns:
            dict: 排盘结果（含 basic_info、bazi、wuxing、shishen、
                  dayun、liunian、yuncheng、zonghe、shier_shen 等字段）
        """
        # 1. 校验输入
        input_data = {
            'year': year, 'month': month, 'day': day,
            'hour': hour, 'minute': minute,
            'longitude': longitude, 'gender': gender,
            'is_lunar': False,
        }
        v_result = validate_bazi_input(input_data)
        if not v_result.success:
            raise ValueError(f'输入校验失败：{"; ".join(v_result.errors)}')

        # 2. 计算（BaziCalculator.calculate 签名含 is_lunar）
        t0 = time.time()
        result = self._calculator.calculate(
            year, month, day, hour, minute, longitude, False)
        result['calc_ms'] = int((time.time() - t0) * 1000)

        # 2.1 补充五行/十神/大运/流年/命理/分析，供综合建议使用
        try:
            result['wuxing_detail'] = self._calculator.get_wuxing(result)
            result['shishen'] = self._calculator.get_shishen(result)
        except Exception:
            result.setdefault('wuxing_detail', {})
            result.setdefault('shishen', {})
        try:
            result['dayun'] = self._calculator.get_dayun(result, gender, year)
            result['liunian'] = self._calculator.get_liunian(result)
        except Exception:
            result.setdefault('dayun', {})
            result.setdefault('liunian', {})
        try:
            result['mingli'] = self._calculator.get_mingli(result)
        except Exception:
            result['mingli'] = {}
        try:
            result['analysis'] = self._build_analysis(
                result.get('mingli', {}), result.get('shishen', {}))
        except Exception:
            result['analysis'] = []

        # 3. 生成综合建议
        zonghe = self._build_zonghe(result)
        result['zonghe'] = zonghe

        # 4. 落库
        record_id = None
        if save:
            record_id = self.save_pan_record(result, input_data, name or '匿名')
            result['record_id'] = record_id

        # 5. 发布事件
        self._bus.emit('result_ready', {'result': result, 'record_id': record_id})
        return result

    def save_pan_record(self, result: Dict[str, Any],
                        input_data: Dict[str, Any],
                        name: str = '') -> Optional[int]:
        """把排盘结果落库到 analysis_records 表。

        适配 database_manager.py 中 analysis_records 表的实际 schema：
        - name, gender, birth_date, birth_time, city,
          professional_chart_json, ai_analysis_json, input_json

        Args:
            result: 排盘结果字典
            input_data: 输入参数字典
            name: 命主姓名

        Returns:
            int: 记录 ID，失败返回 None
        """
        try:
            manager = dbm_module.get_db_manager()
            birth_date = f"{input_data.get('year', '')}-{input_data.get('month', 0):02d}-{input_data.get('day', 0):02d}"
            birth_time = f"{input_data.get('hour', 0):02d}:{input_data.get('minute', 0):02d}"
            input_json = json.dumps(input_data, ensure_ascii=False)
            chart_json = json.dumps(result, ensure_ascii=False, default=str)
            # 综合建议作为 ai_analysis_json 的一部分（当前无 AI，占位）
            ai_json = json.dumps(
                {'zonghe': result.get('zonghe', {}), 'note': '确定性建议，非AI解读'},
                ensure_ascii=False)

            record_id = manager.execute_insert(
                "INSERT INTO analysis_records "
                "(name, gender, birth_date, birth_time, city, "
                " professional_chart_json, ai_analysis_json, input_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (name, input_data.get('gender', ''),
                 birth_date, birth_time,
                 str(input_data.get('longitude', '')),
                 chart_json, ai_json, input_json))
            return record_id
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'落库失败：{e}')
            return None

    def _build_analysis(self, ml: Dict, ss: Dict) -> List[Dict]:
        """根据十神汇总与命理神煞生成吉凶批注列表（规则引擎，离线可跑）。

        与 ui/main_window.py 的 _analysis 方法保持同源逻辑，
        使 service 层可独立产出 analysis 供综合建议消费。

        Args:
            ml: 命理数据（含 shensha）
            ss: 十神数据（含 summary 与 total_weights）

        Returns:
            批注条目列表，每条形如 {'type': '吉'/'中'/'凶', 'text': '...'}
        """
        a = []
        sh_summary = ss.get('summary', {})
        sh_total_weights = ss.get('total_weights', {})

        if sh_summary:
            if sh_summary.get('正官', 0) > 0 or sh_summary.get('七杀', 0) > 0:
                a.append({'type': '中', 'text': '官杀透干，事业心强，注意工作压力'})
            if sh_summary.get('正财', 0) > 0 or sh_summary.get('偏财', 0) > 0:
                a.append({'type': '吉', 'text': '财星显现，财运较好'})
            if sh_summary.get('正印', 0) > 0 or sh_summary.get('偏印', 0) > 0:
                a.append({'type': '吉', 'text': '印星护身，贵人相助'})
            if sh_summary.get('食神', 0) > 0 or sh_summary.get('伤官', 0) > 0:
                a.append({'type': '中', 'text': '食伤泄秀，才华出众'})

        if sh_total_weights:
            total = sh_total_weights.get('total', 0)
            if total > 0:
                for category, label in [('印星', '生扶'), ('食伤', '泄秀'),
                                        ('官杀', '克制'), ('财星', '耗身'),
                                        ('比劫', '帮身')]:
                    weight = sh_total_weights.get(category, 0)
                    if weight / total >= 0.3:
                        a.append({'type': '吉', 'text': f'{category}偏旺，{label}有力'})

        sn = ml.get('shensha', {}) if isinstance(ml, dict) else {}
        for k, key in [('positive', '吉'), ('negative', '凶')]:
            items = sn.get(k, [])
            if items:
                ns = '、'.join(s['name'] for s in items[:3])
                a.append({'type': key, 'text': f'命带{ns}'})

        if not a:
            a = [{'type': '吉', 'text': '日主得令，宜积极进取'},
                 {'type': '中', 'text': '财星透干，理财宜谨慎'},
                 {'type': '凶', 'text': '官杀混杂，注意身心'}]
        return a

    def _build_zonghe(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """基于排盘结果生成综合建议（确定性，非 AI）。

        依据《子平真诠》《滴天髓》的格局判断原则。

        Returns:
            dict: 综合建议，含总评/分项分析/建议三部分
        """
        analysis = result.get('analysis', [])
        wx_detail = result.get('wuxing_detail', {})

        # 提取吉凶条目（type 为 吉/中/凶）
        xiong_items = [a.get('text', '') for a in analysis
                       if a.get('type') == '凶']
        ji_items = [a.get('text', '') for a in analysis
                    if a.get('type') == '吉']

        # 五行旺衰（wuxing_detail 结构：{wx: {'count', 'score', ...}}）
        wx_summary = []
        for wx in ('木', '火', '土', '金', '水'):
            info = wx_detail.get(wx)
            if isinstance(info, dict):
                wx_summary.append(
                    f'{wx}{round(info.get("score", 0), 1)}')

        # 大运 / 流年摘要
        dayun = result.get('dayun') or {}
        dayun_cur = dayun.get('current_period', '')
        if not dayun_cur:
            for p in dayun.get('periods', []):
                if isinstance(p, dict) and p.get('active'):
                    dayun_cur = p.get('name', '') or p.get('ganzhi', '')
                    break

        liunian = result.get('liunian') or {}
        liunian_info = ''
        years = liunian.get('years', [])
        if years and isinstance(years, list):
            liunian_info = str(years[0].get('ganzhi', ''))

        total = len(analysis)
        return {
            'summary': f'共 {total} 条批注，吉 {len(ji_items)} 条 / '
                       f'凶 {len(xiong_items)} 条',
            'total_count': total,
            'ji_count': len(ji_items),
            'xiong_count': len(xiong_items),
            'wuxing_summary': wx_summary,
            'dayun': dayun_cur,
            'liunian': liunian_info,
            'note': '综合建议为确定性规则生成，非 AI 解读。',
            'ji_items': ji_items[:5],
            'xiong_items': xiong_items[:5],
        }

    # ===== 历史记录 =====

    def search_history(self, keyword: str, limit: int = 20) -> List[Dict]:
        """模糊搜索历史记录。

        Args:
            keyword: 搜索关键词（姓名/干支/日期等）
            limit: 最大返回条数

        Returns:
            list[dict]: 历史记录
        """
        try:
            manager = dbm_module.get_db_manager()
            return manager.query_all(
                "SELECT id, name, gender, birth_date, birth_time, city, "
                "       created_at "
                "FROM analysis_records "
                "WHERE name LIKE ? OR input_json LIKE ? "
                "ORDER BY id DESC LIMIT ?",
                (f'%{keyword}%', f'%{keyword}%', limit))
        except Exception:
            return []

    def get_history(self, limit: int = 50) -> List[Dict]:
        """获取最近 N 条历史记录。"""
        try:
            manager = dbm_module.get_db_manager()
            return manager.query_all(
                "SELECT id, name, gender, birth_date, birth_time, city, "
                "       created_at "
                "FROM analysis_records "
                "ORDER BY id DESC LIMIT ?",
                (limit,))
        except Exception:
            return []
