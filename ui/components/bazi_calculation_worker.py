"""
八字排盘计算工作线程：将耗时的八字计算移至后台线程，避免GUI卡死。
"""
from PySide6.QtCore import QThread, Signal
from core.bazi.bazi_calculator import BaziCalculator
from core.lunar_converter import LunarConverter
from core.calendar_utils import SolarTimeCalculator
from core.location_db import LocationDB
from core.bazi.yunshi import YunShiCalculator
from core.bazi.yuncheng import YunChengAnalyzer
from core.bazi.geju_analyzer import GeJuAnalyzer
import traceback
from datetime import datetime


class BaziCalculationWorker(QThread):
    """后台计算八字排盘结果的工作线程。"""

    # 信号
    finished = Signal(dict)          # 计算成功，传递结果字典
    failed = Signal(str, str)        # 计算失败，传递错误类型和错误消息
    progress = Signal(str, str)      # 进度更新，传递阶段和消息

    def __init__(self, input_data: dict):
        """
        Args:
            input_data: 输入面板数据（年/月/日/时/经纬度/农历标志/性别等）
        """
        super().__init__()
        self.input_data = input_data
        self._is_cancelled = False

    def cancel(self):
        """请求取消计算。"""
        self._is_cancelled = True

    def run(self):
        """执行八字排盘计算流程。"""
        try:
            self.progress.emit('validating', '正在验证输入数据…')
            y, m, d, hh, mm = self.input_data['year'], self.input_data['month'], self.input_data['day'], self.input_data['hour'], self.input_data['minute']
            longitude = self.input_data['longitude']
            latitude = self.input_data.get('latitude', 30.0)
            is_lunar = self.input_data['is_lunar']
            gender = self.input_data.get('gender', '男')

            # 出生地解析
            loc_text = (self.input_data.get('location') or '').strip()
            if loc_text:
                longitude, latitude = self._resolve_location(loc_text, longitude, latitude)
                self.input_data['longitude'] = longitude
                self.input_data['latitude'] = latitude
                self.input_data['location'] = loc_text

            if is_lunar:
                self.progress.emit('converting', '正在转换农历日期…')
                lunar_conv = LunarConverter()
                sol = lunar_conv.lunar_to_solar(y, m, d)
                if not sol:
                    self.failed.emit('validation_error', '农历转换失败：日期无效')
                    return
                y, m, d = sol

            self.progress.emit('calculating', '正在计算八字命理…')
            dt = datetime(y, m, d, hh, mm)
            solar_time_calc = SolarTimeCalculator()
            sdt = solar_time_calc.get_true_solar_time(dt, longitude)

            bazi_calc = BaziCalculator()
            bazi = bazi_calc.calculate(y, m, d, hh, mm, longitude, is_lunar=False)
            lunar_conv = LunarConverter()
            li = lunar_conv.solar_to_lunar(y, m, d)

            wx = bazi_calc.get_wuxing(bazi)
            ss = bazi_calc.get_shishen(bazi)
            ml = bazi_calc.get_mingli(bazi)

            # 计算大运流年
            self.progress.emit('calculating_fortune', '正在计算大运流年…')
            if self._is_cancelled:
                return
            try:
                yunshi_calc = YunShiCalculator()
                dayun = yunshi_calc.calculate_major_fortune(bazi, gender, y, birth_dt=sdt)
                if self._is_cancelled:
                    return
                liunian = yunshi_calc.calculate_annual_fortune(bazi, start_year=datetime.now().year, years_count=10)
                if self._is_cancelled:
                    return
            except Exception:
                traceback.print_exc()
                dayun = {'periods': [], 'direction': '顺行'}
                liunian = {'years': []}

            # 计算十二长生
            if self._is_cancelled:
                return
            try:
                shier_shen_raw = bazi_calc.get_shier_shen(bazi)
                if self._is_cancelled:
                    return
                shier_shen = {}
                for item in shier_shen_raw.get('shier_shen', []):
                    shier_shen[item['pillar']] = {
                        'name': item.get('shier_shen', ''),
                        'description': item.get('description', ''),
                        'ganzhi': item.get('ganzhi', ''),
                    }
                if self._is_cancelled:
                    return
            except Exception:
                traceback.print_exc()
                shier_shen = {}

            # 计算命局类型
            self.progress.emit('calculating_types', '正在分析命局类型…')
            if self._is_cancelled:
                return
            bazi_types = self._compute_bazi_types(bazi, wx)
            if self._is_cancelled:
                return

            # 计算运程总结
            self.progress.emit('calculating_fortune_summary', '正在生成运程总结…')
            if self._is_cancelled:
                return
            try:
                yuncheng = YunChengAnalyzer().analyze(bazi, wx, ss, bazi_types)
                if self._is_cancelled:
                    return
            except Exception:
                traceback.print_exc()
                yuncheng = {}

            # 五行汇总
            if self._is_cancelled:
                return
            wuxing_summary = {}
            for k in ('木', '火', '土', '金', '水'):
                v = wx.get(k, {})
                if isinstance(v, int):
                    wuxing_summary[k] = v
                else:
                    wuxing_summary[k] = round(v.get('score', 0), 2)
                if self._is_cancelled:
                    return

            result = {
                'basic_info': {
                    'pan_type': bazi_types.get('pan_type', '八字四柱'),
                    'solar_date': f'{y}年{m}月{d}日',
                    'lunar_date': f'{li[0]}年{li[1]}月{li[2]}日' if li else bazi.get('lunar_date', '-'),
                    'hour': f'{sdt.hour:02d}:{sdt.minute:02d}',
                    'location': self.input_data.get('location') or '-',
                    'gender': gender,
                    'solar_time': bazi.get('solar_time', ''),
                    'original_time': bazi.get('original_time', ''),
                    'longitude': longitude,
                    'latitude': latitude,
                },
                'bazi': {
                    'year_pillar': bazi['year_pillar'],
                    'month_pillar': bazi['month_pillar'],
                    'day_pillar': bazi['day_pillar'],
                    'hour_pillar': bazi['hour_pillar'],
                    'rizhu': bazi.get('rizhu', ''),
                    'month_zhi': bazi.get('month_zhi', ''),
                },
                'wuxing': wuxing_summary,
                'wuxing_detail': wx,
                'shishen': ss,
                'mingli': ml,
                'dayun': dayun,
                'liunian': liunian,
                'shier_shen': shier_shen,
                'analysis': self._analysis(ml, ss),
                'bazi_types': bazi_types,
                'yuncheng': yuncheng,
            }

            if self._is_cancelled:
                return

            self.finished.emit(result)

        except Exception as e:
            traceback.print_exc()
            self.failed.emit('calculation_error', str(e))

    def _resolve_location(self, text, fallback_lon=120.0, fallback_lat=30.0):
        """将出生地文本解析为（经度, 纬度）。"""
        # 1) 本地城市库优先
        try:
            db = LocationDB()
            hits = db.search_city(text)
            if not hits:
                short = text.rstrip('省市县区自治州盟')
                hits = db.search_city(short)
            if not hits:
                for c in db.get_all_cities():
                    if c and c in text:
                        hits = [c]
                        break
            if hits:
                lon, lat = db.get_coords(hits[0])
                return float(lon), float(lat)
        except Exception:
            pass

        # 2) AI 地理解析（加超时保护）
        try:
            from api.agnes_client import get_agnes_client, AgnesClient
            client = get_agnes_client()
            prompt = (
                f"请解析出生地「{text}」的地理坐标，"
                f"仅返回一个 JSON 对象，不要任何解释："
                f'{{"longitude": 数值, "latitude": 数值, "timezone": "Asia/Shanghai"}}'
            )
            resp = client.chat_completion(
                [{'role': 'user', 'content': prompt}],
                temperature=0.0, max_tokens=256,
            )
            content = (resp or {}).get('content', '')
            cleaned = AgnesClient._clean_json_response(content)
            import json
            obj = json.loads(cleaned)
            lon = float(obj['longitude'])
            lat = float(obj['latitude'])
            return lon, lat
        except Exception:
            pass

        # 3) 兜底
        return float(fallback_lon), float(fallback_lat)

    def _compute_bazi_types(self, bazi, wx):
        """计算八字命局类型：日主强弱 / 格局类型 / 五行旺衰类别"""
        from core.bazi.bazi_types import get_bazi_types_payload
        strength = ''
        geju_type = ''
        geju_name = ''
        geju_desc = ''
        rizhu_wx = wx.get('rizhu_wx', '') if isinstance(wx, dict) else ''

        try:
            analyzer = GeJuAnalyzer()
            geju = analyzer.analyze(bazi, wx, bazi.get('month_zhi'))
            wangshuai = geju.get('wangshuai', {}) or {}
            strength = wangshuai.get('level', '')
            geju_type = geju.get('geju_type', '')
            geju_name = geju.get('main_geju', '')
            geju_desc = geju.get('description', '')
        except Exception:
            pass

        wuxing_summary = wx.get('summary', '') if isinstance(wx, dict) else ''

        from core.bazi.bazi_types import get_yongshen
        yongshen = get_yongshen(rizhu_wx, strength) if rizhu_wx else {}

        return get_bazi_types_payload(
            pan_type_code='bazi',
            strength=strength,
            geju_type=geju_type,
            geju_name=geju_name,
            geju_desc=geju_desc,
            wuxing_summary=wuxing_summary,
            rizhu_wx=rizhu_wx,
            yongshen=yongshen,
        )

    def _analysis(self, ml, ss):
        """根据十神汇总与命理神煞生成吉凶批注列表（规则引擎，离线可跑）。"""
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
                for category, label in [('印星', '生扶'), ('食伤', '泄秀'), ('官杀', '克制'), ('财星', '耗身'), ('比劫', '帮身')]:
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
            a = [{'type': '吉', 'text': '日主得令，宜积极进取'}, {'type': '中', 'text': '财星透干，理财宜谨慎'}, {'type': '凶', 'text': '官杀混杂，注意身心'}]
        return a