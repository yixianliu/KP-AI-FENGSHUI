import json
import requests
import traceback
import time
import warnings
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING, DI_ZHI_HIDDEN_GAN

# 禁用未验证HTTPS请求警告（仅用于开发测试环境，生产环境应启用证书验证）
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# API配置
API_KEY = "Bearer FNAbWpKiIOGUuBkvwhSK:hFQKWgODImKpIssPyIqs"
API_URL = "https://spark-api-open.xf-yun.com/v2/chat/completions"

# 重试配置
MAX_RETRIES = 2
RETRY_DELAY = 2  # 重试间隔（秒）
REQUEST_TIMEOUT = 60  # 请求超时时间（秒）

# 本地分析数据（作为降级方案）
PERSONALITY_TRAITS = {
    '木': {
        'positive': ['积极向上', '富有创造力', '善于创新', '有进取心', '正直善良'],
        'negative': ['固执己见', '过于冲动', '缺乏耐心', '容易情绪化']
    },
    '火': {
        'positive': ['热情洋溢', '乐观开朗', '富有感染力', '社交能力强', '充满活力'],
        'negative': ['急躁冲动', '缺乏冷静', '过于张扬', '容易骄傲']
    },
    '土': {
        'positive': ['稳重可靠', '诚实守信', '有责任感', '踏实肯干', '包容大度'],
        'negative': ['过于保守', '缺乏变通', '固执僵化', '反应迟钝']
    },
    '金': {
        'positive': ['果断刚毅', '追求完美', '有决断力', '精明干练', '公正无私'],
        'negative': ['刻薄寡恩', '刚愎自用', '过于挑剔', '缺乏变通']
    },
    '水': {
        'positive': ['聪明灵活', '思维敏捷', '适应力强', '富有智慧', '善于变通'],
        'negative': ['散漫无章', '缺乏定力', '优柔寡断', '过于敏感']
    }
}

ELEMENT_RECOMMENDATIONS = {
    '木': {
        'career': '适合从事创意、艺术、教育、农林等行业',
        'color': '绿色、青色系',
        'direction': '东方',
        'advice': '保持创新精神，注意人际关系'
    },
    '火': {
        'career': '适合从事销售、演艺、公关、能源等行业',
        'color': '红色、紫色系',
        'direction': '南方',
        'advice': '发挥热情优势，保持冷静思考'
    },
    '土': {
        'career': '适合从事金融、房地产、建筑、管理等行业',
        'color': '黄色、棕色系',
        'direction': '中央',
        'advice': '发挥稳重优势，学会灵活变通'
    },
    '金': {
        'career': '适合从事法律、金融、金属、机械等行业',
        'color': '白色、金色系',
        'direction': '西方',
        'advice': '发挥果断优势，注意人际关系'
    },
    '水': {
        'career': '适合从事商贸、物流、旅游、科技等行业',
        'color': '蓝色、黑色系',
        'direction': '北方',
        'advice': '发挥智慧优势，保持专注定力'
    }
}


class AIAnalyzer:
    def __init__(self):
        self.use_api = True

    def analyze(self, bazhi, wuxing_result, shishen_result,
                mingli_result=None, major_fortune=None, input_data=None):
        """
        主分析方法，优先使用API分析，失败时降级到本地分析
        """
        print(f"[AI分析器] 开始分析八字: {bazhi.get('四柱', '未知')}")
        
        if self.use_api:
            try:
                result = self._analyze_via_api(
                    bazhi, wuxing_result, shishen_result,
                    mingli_result, major_fortune, input_data
                )
                print(f"[AI分析器] API分析成功，返回字段: {list(result.keys())}")
                return result
            except Exception as e:
                print(f"[AI分析器] API分析失败，降级到本地分析: {str(e)}")
                result = self._analyze_locally(
                    bazhi, wuxing_result, shishen_result, mingli_result
                )
                print(f"[AI分析器] 本地分析完成，返回字段: {list(result.keys())}")
                return result
        else:
            result = self._analyze_locally(bazhi, wuxing_result, shishen_result, mingli_result)
            print(f"[AI分析器] 本地分析完成，返回字段: {list(result.keys())}")
            return result

    def _analyze_via_api(self, bazhi, wuxing_result, shishen_result,
                         mingli_result=None, major_fortune=None, input_data=None):
        """
        通过API进行AI分析，支持流式响应和重试机制
        参考 spark_api_reference.py 的实现方式
        """
        prompt = self._build_prompt(
            bazhi, wuxing_result, shishen_result,
            mingli_result, major_fortune, input_data
        )
        
        headers = {
            'Authorization': API_KEY,
            'Content-Type': 'application/json'
        }
        
        body = {
            "model": "x1",
            "user": "fs_shi",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的命理大师，精通传统八字命理、阴阳五行、十神等知识。请基于用户提供的八字信息进行专业分析，输出格式要求：用JSON格式输出，包含以下字段：personality（性格特质，数组）、career（事业财运，数组）、marriage（婚姻感情，数组）、health（健康注意，数组）、suggestions（综合建议，数组）。每个字段都是字符串数组，每个字符串是一个要点。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": True,
            "tools": [
                {
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_mode": "deep"
                    }
                }
            ]
        }
        
        last_exception = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                full_response = ""
                response = requests.post(
                    url=API_URL,
                    json=body,
                    headers=headers,
                    stream=True,
                    timeout=REQUEST_TIMEOUT,
                    verify=False
                )
                response.raise_for_status()
                
                print(f"[AI分析器] 开始接收流式响应...")
                
                for chunks in response.iter_lines():
                    if chunks and '[DONE]' not in str(chunks):
                        print(f"[AI分析器] 接收到数据块: {str(chunks)[:200]}")
                        
                        # 移除数据头（"data: "）
                        chunk_str = str(chunks)
                        if chunk_str.startswith("b'data: "):
                            data_org = chunks[6:]
                        elif chunk_str.startswith("b\"data: "):
                            data_org = chunks[6:]
                        elif chunk_str.startswith("data: "):
                            data_org = chunks[5:]
                        else:
                            data_org = chunks
                            
                        try:
                            chunk = json.loads(data_org)
                            text = chunk['choices'][0]['delta']
                            
                            if 'content' in text and '' != text['content']:
                                content = text["content"]
                                full_response += content
                                print(f"[AI分析器] 追加内容: {content[:50]}...")
                        except json.JSONDecodeError as e:
                            print(f"[AI分析器] JSON解析失败: {str(e)}")
                            continue
                
                print(f"[AI分析器] 完整响应: {full_response[:500]}")
                
                if full_response:
                    # 移除Markdown代码块标记
                    full_response = full_response.strip()
                    if full_response.startswith('```json'):
                        full_response = full_response[7:]  # 移除 ```json
                    elif full_response.startswith('```'):
                        full_response = full_response[3:]   # 移除 ```
                    
                    if full_response.endswith('```'):
                        full_response = full_response[:-3]  # 移除结尾的 ```
                    
                    full_response = full_response.strip()
                    
                    print(f"[AI分析器] 处理后响应: {full_response[:300]}")
                    
                    try:
                        result = json.loads(full_response)
                        print(f"[AI分析器] JSON解析成功")
                        return self._validate_and_format_result(result)
                    except json.JSONDecodeError as e:
                        print(f"[AI分析器] JSON解析失败: {str(e)}")
                        print(f"[AI分析器] 尝试文本解析")
                        return self._parse_text_response(full_response)
                
                print(f"[AI分析器] 响应为空，使用降级结果")
                return self._create_fallback_result()
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < MAX_RETRIES:
                    print(f"API请求失败(第{attempt+1}次)，{RETRY_DELAY}秒后重试: {str(e)}")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"API请求失败(第{attempt+1}次，已达最大重试次数): {str(e)}")
        
        raise Exception(f"API请求失败: {str(last_exception)}")

    def _build_prompt(self, bazhi, wuxing_result, shishen_result,
                      mingli_result=None, major_fortune=None, input_data=None):
        """
        构建API请求的提示词
        """
        parts = []

        if input_data:
            parts.append(
                f"命主信息：姓名{input_data.get('name', '')}，性别{input_data.get('gender', '')}，"
                f"出生{input_data.get('year', '')}-{input_data.get('month', 0):02d}-{input_data.get('day', 0):02d} "
                f"{input_data.get('hour', 0):02d}:{input_data.get('minute', 0):02d}，"
                f"{'农历' if input_data.get('is_lunar') else '公历'}，出生地{input_data.get('city', '')}"
            )
        
        parts.append(f"八字信息：年柱{bazhi['year']} 月柱{bazhi['month']} 日柱{bazhi['day']} 时柱{bazhi['hour']}")
        parts.append(f"日主：{bazhi['rizhu']}")
        parts.append(f"排盘日期：公历{bazhi.get('solar_date', '')}；农历{bazhi.get('lunar_date', '')}")
        
        if wuxing_result.get('summary'):
            parts.append(f"五行分析：{wuxing_result['summary']}")
            for wx in ['木', '火', '土', '金', '水']:
                count = wuxing_result.get(wx, {}).get('count', 0)
                percentage = wuxing_result.get(wx, {}).get('percentage', 0)
                parts.append(f"  {wx}：{count:.1f} ({percentage}%)")
        
        if shishen_result.get('summary'):
            shishen_list = [f"{shishen}{count}个" for shishen, count in shishen_result['summary'].items()]
            parts.append(f"十神分布：{'、'.join(shishen_list)}")
        if shishen_result.get('details'):
            detail_parts = []
            for detail in shishen_result['details']:
                detail_parts.append(
                    f"{detail.get('pillar', '')}{detail.get('ganzhi', '')}"
                    f" 天干十神{detail.get('gan_shishen', '')}"
                    f" 地支藏干十神{'、'.join(detail.get('zhi_shishens', []))}"
                )
            parts.append(f"十神详情：{'；'.join(detail_parts)}")
        
        if mingli_result:
            if mingli_result.get('shensha', {}).get('positive'):
                positive_shensha = [s['name'] for s in mingli_result['shensha']['positive']]
                parts.append(f"吉神：{'、'.join(positive_shensha)}")
            if mingli_result.get('shensha', {}).get('negative'):
                negative_shensha = [s['name'] for s in mingli_result['shensha']['negative']]
                parts.append(f"凶煞：{'、'.join(negative_shensha)}")
            if mingli_result.get('self_seat', {}).get('description'):
                parts.append(f"日主自坐：{mingli_result['self_seat']['description']}")
            if mingli_result.get('ganzhi_relations'):
                gan_relations = '、'.join(mingli_result['ganzhi_relations'].get('gan_relations', []))
                zhi_relations = '、'.join(mingli_result['ganzhi_relations'].get('zhi_relations', []))
                if gan_relations:
                    parts.append(f"天干关系：{gan_relations}")
                if zhi_relations:
                    parts.append(f"地支关系：{zhi_relations}")
            if mingli_result.get('kongwang', {}).get('description'):
                parts.append(f"空亡信息：{mingli_result['kongwang']['description']}")

        if major_fortune and major_fortune.get('periods'):
            fortune_lines = []
            for period in major_fortune['periods'][:6]:
                fortune_lines.append(
                    f"{period.get('start_age', '')}-{period.get('end_age', '')}岁"
                    f"{period.get('ganzhi', '')}：{period.get('description') or period.get('analysis', '')}"
                )
            parts.append(
                f"大运走势（{major_fortune.get('direction', '')}）："
                + '；'.join(fortune_lines)
            )
        
        return '\n'.join(parts)

    def _validate_and_format_result(self, result):
        """
        验证并格式化API返回结果
        """
        required_fields = ['personality', 'career', 'marriage', 'health', 'suggestions']
        formatted = {}
        
        for field in required_fields:
            value = result.get(field, [])
            if isinstance(value, list):
                formatted[field] = [str(item) for item in value if item]
            elif isinstance(value, str):
                formatted[field] = [value]
            else:
                formatted[field] = []
        
        return formatted

    def _parse_text_response(self, content):
        """
        解析非JSON格式的文本响应
        """
        sections = {
            '性格': 'personality',
            '事业': 'career',
            '财运': 'career',
            '婚姻': 'marriage',
            '感情': 'marriage',
            '健康': 'health',
            '建议': 'suggestions'
        }
        
        result = {
            'personality': [],
            'career': [],
            'marriage': [],
            'health': [],
            'suggestions': []
        }
        
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            for keyword, field in sections.items():
                if keyword in line:
                    current_section = field
                    continue
            
            if current_section and line:
                if line[0] in ['•', '·', '-', '●', '★', '1.', '2.', '3.', '（', '(']:
                    result[current_section].append(line.lstrip('•·-●★1234567890.（() '))
        
        return result

    def _create_fallback_result(self):
        """
        创建降级结果
        """
        return {
            'personality': ['API暂时不可用，请稍后重试'],
            'career': ['API暂时不可用，请稍后重试'],
            'marriage': ['API暂时不可用，请稍后重试'],
            'health': ['API暂时不可用，请稍后重试'],
            'suggestions': ['API暂时不可用，请稍后重试']
        }

    def _analyze_locally(self, bazhi, wuxing_result, shishen_result, mingli_result=None):
        """
        本地分析（降级方案）
        """
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        return {
            'personality': self._generate_personality(rizhu_wx, wuxing_result),
            'career': self._generate_career(rizhu_wx, wuxing_result, shishen_result),
            'marriage': self._generate_marriage(shishen_result),
            'health': self._generate_health(rizhu_wx, wuxing_result),
            'suggestions': self._generate_recommendations(rizhu_wx, wuxing_result)
        }

    def _generate_personality(self, rizhu_wx, wuxing_result):
        traits = PERSONALITY_TRAITS.get(rizhu_wx, {'positive': [], 'negative': []})
        positive_traits = traits['positive'][:3]
        
        dominant_elements = []
        for wx in ['木', '火', '土', '金', '水']:
            if wuxing_result.get(wx, {}).get('count', 0) >= 4:
                dominant_elements.append(wx)
        
        for wx in dominant_elements:
            if wx != rizhu_wx:
                wx_traits = PERSONALITY_TRAITS.get(wx, {'positive': [], 'negative': []})
                positive_traits.extend(wx_traits['positive'][:2])
        
        return list(set(positive_traits))[:5]

    def _generate_career(self, rizhu_wx, wuxing_result, shishen_result):
        result = []
        
        rec = ELEMENT_RECOMMENDATIONS.get(rizhu_wx, {})
        if 'career' in rec:
            result.append(rec['career'])
        
        shishen_summary = shishen_result.get('summary', {})
        if '正官' in shishen_summary or '七杀' in shishen_summary:
            result.append('适合从事管理、领导类工作')
        if '正财' in shishen_summary or '偏财' in shishen_summary:
            result.append('有较好的财运，适合经商或投资理财')
        if '正印' in shishen_summary or '偏印' in shishen_summary:
            result.append('适合从事教育、学术研究或技术工作')
        if '食神' in shishen_summary or '伤官' in shishen_summary:
            result.append('适合从事创意、艺术或设计类工作')
        
        return result[:5]

    def _generate_marriage(self, shishen_result):
        result = []
        
        shishen_summary = shishen_result.get('summary', {})
        if '正财' in shishen_summary:
            result.append('感情较为稳定，注重实际')
        elif '偏财' in shishen_summary:
            result.append('异性缘较好，感情生活丰富')
        if '七杀' in shishen_summary:
            result.append('感情上可能会有一些挑战和考验')
        if '正官' in shishen_summary:
            result.append('配偶能力较强，婚姻较为稳定')
        
        if not result:
            result.append('感情运势需要结合具体八字分析')
        
        return result

    def _generate_health(self, rizhu_wx, wuxing_result):
        result = []
        
        weak_elements = []
        for wx in ['木', '火', '土', '金', '水']:
            if wuxing_result.get(wx, {}).get('count', 0) <= 2:
                weak_elements.append(wx)
        
        health_map = {
            '木': '注意肝胆、神经系统健康',
            '火': '注意心脏、血液循环系统健康',
            '土': '注意脾胃、消化系统健康',
            '金': '注意肺部、呼吸系统健康',
            '水': '注意肾脏、泌尿系统健康'
        }
        
        for wx in weak_elements:
            result.append(health_map.get(wx, f'注意与{wx}相关的健康问题'))
        
        if not result:
            result.append('整体健康状况较好，注意保持规律生活')
        
        return result

    def _generate_recommendations(self, rizhu_wx, wuxing_result):
        result = []
        
        rec = ELEMENT_RECOMMENDATIONS.get(rizhu_wx, {})
        if 'color' in rec:
            result.append(f"幸运颜色：{rec['color']}")
        if 'direction' in rec:
            result.append(f"有利方向：{rec['direction']}")
        if 'advice' in rec:
            result.append(f"生活建议：{rec['advice']}")
        
        min_wx = None
        min_count = float('inf')
        for wx in ['木', '火', '土', '金', '水']:
            count = wuxing_result.get(wx, {}).get('count', 0)
            if count < min_count:
                min_count = count
                min_wx = wx
        
        if min_wx and min_count <= 2:
            wx_rec = ELEMENT_RECOMMENDATIONS.get(min_wx, {})
            result.append(f"建议适当补充{min_wx}元素，如：{wx_rec.get('color', '')}色系")
        
        return result
