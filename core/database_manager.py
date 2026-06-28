"""
数据库管理模块 - 封装所有数据库操作
支持MySQL配置读取、用户管理、排盘记录管理
"""
import configparser
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import pymysql


class DatabaseManager:
    """数据库管理器 - 封装所有数据库操作"""

    def __init__(self, config_path: str = None):
        """
        初始化数据库管理器

        Args:
            config_path: 配置文件路径，默认使用项目根目录的config.ini
        """
        if config_path is None:
            project_root = Path(__file__).resolve().parent.parent
            config_path = project_root / 'config.ini'
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.db_config = self._load_db_config()
        self._init_database()

    def _load_db_config(self) -> Dict[str, str]:
        """从config.ini读取MySQL配置"""
        parser = configparser.ConfigParser()
        if not self.config_path.exists():
            raise FileNotFoundError(f"未找到数据库配置文件: {self.config_path}")

        parser.read(self.config_path, encoding='utf-8')
        if 'database' not in parser:
            raise ValueError("config.ini 缺少 [database] 配置段")

        section = parser['database']
        return {
            'host': section.get('host', '127.0.0.1'),
            'user': section.get('user', 'root'),
            'password': section.get('password', ''),
            'database': section.get('database', 'ai_fengshui'),
            'charset': section.get('charset', 'utf8mb4')
        }

    def _connect(self, include_database: bool = True, autocommit: bool = False):
        """建立数据库连接"""
        connect_args = {
            'host': self.db_config['host'],
            'user': self.db_config['user'],
            'password': self.db_config['password'],
            'charset': self.db_config['charset'],
            'autocommit': autocommit
        }
        if include_database:
            connect_args['database'] = self.db_config['database']
        return pymysql.connect(**connect_args)

    def _init_database(self):
        """初始化数据库和表结构"""
        # 创建数据库（如果不存在）
        with self._connect(include_database=False, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.db_config['database']}` "
                    f"CHARACTER SET {self.db_config['charset']}"
                )

        # 创建用户表
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        password_hash VARCHAR(64) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_username (username)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

            # 创建排盘记录表
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pan_records (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        user_id INT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        gender VARCHAR(10),
                        birth_date VARCHAR(20),
                        birth_time VARCHAR(20),
                        city VARCHAR(100),
                        pan_type VARCHAR(50),
                        result_json LONGTEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
            connection.commit()

    # ==================== 文本数据表初始化 ====================
    # 数据表已通过 init_db.py 脚本初始化完成，数据已存入数据库
    # init_data_tables() 方法已废弃

    # ==================== 文本数据查询接口 ====================

    def _query_all(self, sql: str, params=None) -> list:
        """执行查询并返回所有结果"""
        with self._connect() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()

    def _query_one(self, sql: str, params=None) -> dict:
        """执行查询并返回单条结果"""
        with self._connect() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()

    # -- 天干 --
    def get_tian_gan_all(self) -> list:
        """获取所有天干数据"""
        return self._query_all("SELECT * FROM tian_gan ORDER BY idx")

    def get_tian_gan_list(self) -> list:
        """获取天干列表 ['甲','乙',...]"""
        rows = self._query_all("SELECT gan FROM tian_gan ORDER BY idx")
        return [r['gan'] for r in rows]

    def get_tian_gan_map(self) -> dict:
        """获取天干到索引的映射 {gan: idx}"""
        rows = self._query_all("SELECT gan, idx FROM tian_gan")
        return {r['gan']: r['idx'] for r in rows}

    def get_tian_gan_wuxing(self) -> dict:
        """获取天干五行映射 {gan: wuxing}"""
        rows = self._query_all("SELECT gan, wuxing FROM tian_gan")
        return {r['gan']: r['wuxing'] for r in rows}

    def get_tian_gan_detail(self, gan: str) -> dict:
        """获取单个天干详细信息"""
        return self._query_one("SELECT * FROM tian_gan WHERE gan = %s", (gan,))

    # -- 地支 --
    def get_di_zhi_all(self) -> list:
        """获取所有地支数据"""
        return self._query_all("SELECT * FROM di_zhi ORDER BY idx")

    def get_di_zhi_list(self) -> list:
        """获取地支列表"""
        rows = self._query_all("SELECT zhi FROM di_zhi ORDER BY idx")
        return [r['zhi'] for r in rows]

    def get_di_zhi_map(self) -> dict:
        """获取地支到索引的映射"""
        rows = self._query_all("SELECT zhi, idx FROM di_zhi")
        return {r['zhi']: r['idx'] for r in rows}

    def get_di_zhi_wuxing(self) -> dict:
        """获取地支五行映射"""
        rows = self._query_all("SELECT zhi, wuxing FROM di_zhi")
        return {r['zhi']: r['wuxing'] for r in rows}

    # -- 地支藏干 --
    def get_di_zhi_hidden_gan(self) -> dict:
        """获取地支藏干数据 {zhi: [(gan, qi_type, score), ...]}"""
        rows = self._query_all(
            "SELECT zhi, hidden_gan, qi_type, qi_score FROM di_zhi_hidden_gan ORDER BY zhi, sort_order"
        )
        result = {}
        for r in rows:
            zhi = r['zhi']
            if zhi not in result:
                result[zhi] = []
            result[zhi].append((r['hidden_gan'], r['qi_type'], float(r['qi_score'])))
        return result

    def get_di_zhi_hidden_gan_simple(self) -> dict:
        """获取地支藏干简化版 {zhi: [gan, ...]}"""
        rows = self._query_all(
            "SELECT zhi, hidden_gan FROM di_zhi_hidden_gan ORDER BY zhi, sort_order"
        )
        result = {}
        for r in rows:
            if r['zhi'] not in result:
                result[r['zhi']] = []
            result[r['zhi']].append(r['hidden_gan'])
        return result

    # -- 六十甲子 --
    def get_sixty_jiazi(self) -> list:
        """获取六十甲子列表 ['甲子','乙丑',...]"""
        rows = self._query_all("SELECT ganzhi FROM sixty_jiazi ORDER BY idx")
        return [r['ganzhi'] for r in rows]

    def get_sixty_jiazi_map(self) -> dict:
        """获取六十甲子索引映射 {ganzhi: idx}"""
        rows = self._query_all("SELECT ganzhi, idx FROM sixty_jiazi")
        return {r['ganzhi']: r['idx'] for r in rows}

    # -- 月干规则 --
    def get_month_gan_rules(self) -> dict:
        """获取月干规则(五虎遁) {year_gan_group: [gan1, gan2, ...]}"""
        rows = self._query_all(
            "SELECT year_gan_group, month_order, month_gan FROM month_gan_rules ORDER BY year_gan_group, month_order"
        )
        result = {}
        for r in rows:
            group = r['year_gan_group']
            if group not in result:
                result[group] = [None] * 12
            result[group][r['month_order']] = r['month_gan']
        return result

    # -- 节气 --
    def get_jie_qi_list(self) -> list:
        """获取节气名称列表"""
        rows = self._query_all("SELECT name FROM jie_qi ORDER BY idx")
        return [r['name'] for r in rows]

    def get_jie_qi_angles(self) -> list:
        """获取节气黄经角度列表"""
        rows = self._query_all("SELECT angle FROM jie_qi ORDER BY idx")
        return [r['angle'] for r in rows]

    def get_jie_qi_base_days(self) -> list:
        """获取节气基准日偏移"""
        rows = self._query_all("SELECT base_days FROM jie_qi ORDER BY idx")
        return [float(r['base_days']) for r in rows]

    def get_jie_qi_month_map(self) -> dict:
        """获取节气-月建映射 {jieqi_idx: month_zhi}"""
        rows = self._query_all("SELECT jie_qi_idx, month_zhi FROM jie_qi_month_map")
        return {r['jie_qi_idx']: r['month_zhi'] for r in rows}

    # -- 月令权重 --
    def get_yue_ling_weight(self) -> dict:
        """获取月令权重 {zhi: {wuxing: weight}}"""
        rows = self._query_all("SELECT zhi, wuxing, weight FROM yue_ling_weight")
        result = {}
        for r in rows:
            if r['zhi'] not in result:
                result[r['zhi']] = {}
            result[r['zhi']][r['wuxing']] = float(r['weight'])
        return result

    # -- 八卦 --
    def get_ba_gua(self) -> dict:
        """获取八卦数据 {num: info_dict}"""
        rows = self._query_all("SELECT * FROM ba_gua")
        return {r['num']: r for r in rows}

    def get_ba_gua_by_num(self, num: int) -> dict:
        """按先天数获取八卦信息"""
        return self._query_one("SELECT * FROM ba_gua WHERE num = %s", (num,))

    # -- 64卦 --
    def get_hexagram_64(self) -> dict:
        """获取64卦数据 {(upper, lower): info_dict}"""
        rows = self._query_all("SELECT * FROM hexagram_64")
        return {(r['upper_num'], r['lower_num']): r for r in rows}

    def get_hexagram_by_id(self, hexagram_id: int) -> dict:
        """按卦序获取卦信息"""
        return self._query_one(
            "SELECT * FROM hexagram_64 WHERE hexagram_id = %s", (hexagram_id,)
        )

    def get_hexagram_by_upper_lower(self, upper: int, lower: int) -> dict:
        """按上下卦数获取卦信息"""
        return self._query_one(
            "SELECT * FROM hexagram_64 WHERE upper_num = %s AND lower_num = %s",
            (upper, lower)
        )

    # -- 64卦爻辞 --
    def get_hexagram_yao_ci(self, hexagram_id: int) -> list:
        """获取某卦的所有爻辞"""
        return self._query_all(
            "SELECT * FROM hexagram_yao_ci WHERE hexagram_id = %s ORDER BY yao_order",
            (hexagram_id,)
        )

    # -- 十神 --
    def get_shishen_knowledge(self) -> dict:
        """获取十神知识 {name: info}"""
        rows = self._query_all("SELECT * FROM shishen_knowledge")
        return {r['name']: r for r in rows}

    def get_shishen_map(self) -> dict:
        """获取十神映射 {shishen_type: {category, yang_name, yin_name}}"""
        rows = self._query_all("SELECT * FROM shishen_map")
        return {r['shishen_type']: r for r in rows}

    def get_shishen_wuxing_map(self) -> dict:
        """获取十神到五行关系的映射 {shishen_name: relation_type}"""
        rows = self._query_all("SELECT name, shishen_type FROM shishen_knowledge")
        return {r['name']: r['shishen_type'] for r in rows}

    # -- 五行知识 --
    def get_wuxing_knowledge(self) -> dict:
        """获取五行知识 {wuxing_name: info}"""
        rows = self._query_all("SELECT * FROM wuxing_knowledge")
        return {r['wuxing_name']: r for r in rows}

    # -- 五行关系 --
    def get_wuxing_relations(self) -> dict:
        """获取五行关系 {relation_type: {name, description, relations: [...]}}"""
        rows = self._query_all(
            "SELECT * FROM wuxing_relations ORDER BY relation_type, id"
        )
        result = {}
        for r in rows:
            rt = r['relation_type']
            if rt not in result:
                result[rt] = {
                    'name': r['relation_name'],
                    'description': r['description'],
                    'relations': []
                }
            result[rt]['relations'].append({
                'from': r['from_wuxing'],
                'to': r['to_wuxing'],
                'meaning': r['meaning']
            })
        return result

    # -- 天干合化 --
    def get_tian_gan_he(self) -> dict:
        """获取天干合化 {gan_pair: info}"""
        rows = self._query_all("SELECT * FROM tian_gan_he")
        return {r['gan_pair']: r for r in rows}

    # -- 地支合冲害刑 --
    def get_di_zhi_he(self) -> dict:
        """获取地支六合 {zhi_pair: info}"""
        rows = self._query_all("SELECT * FROM di_zhi_he")
        return {r['zhi_pair']: r for r in rows}

    def get_di_zhi_chong(self) -> dict:
        """获取地支六冲 {zhi_pair: info}"""
        rows = self._query_all("SELECT * FROM di_zhi_chong")
        return {r['zhi_pair']: r for r in rows}

    def get_di_zhi_hai(self) -> dict:
        """获取地支六害"""
        rows = self._query_all("SELECT * FROM di_zhi_hai")
        return {r['zhi_pair']: r for r in rows}

    def get_di_zhi_xing(self) -> dict:
        """获取地支三刑"""
        rows = self._query_all("SELECT * FROM di_zhi_xing")
        return {r['zhi_group']: r for r in rows}

    def get_di_zhi_san_he(self) -> dict:
        """获取地支三合"""
        rows = self._query_all("SELECT * FROM di_zhi_san_he")
        return {r['zhi_group']: r for r in rows}

    # -- 十二长生 --
    def get_shier_changsheng(self) -> dict:
        """获取十二长生知识 {name: info}"""
        rows = self._query_all("SELECT * FROM shier_changsheng")
        return {r['name']: r for r in rows}

    # -- 十二长生查找表 --
    def init_changsheng_lookup(self):
        """初始化十二长生查找表（天干->地支->阶段）"""
        # 十二长生阶段名称
        stages = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
        # 天干在地支上的十二长生起始地支（阳干顺排，阴干逆排）
        changsheng_start = {
            '甲': '亥', '乙': '午', '丙': '寅', '丁': '酉',
            '戊': '寅', '己': '酉', '庚': '巳', '辛': '子',
            '壬': '申', '癸': '卯'
        }
        di_zhi_order = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        di_zhi_map = {z: i for i, z in enumerate(di_zhi_order)}
        
        data = []
        for gan, start_zhi in changsheng_start.items():
            gan_idx = {'甲':0, '乙':1, '丙':2, '丁':3, '戊':4, '己':5, '庚':6, '辛':7, '壬':8, '癸':9}[gan]
            is_yang = gan_idx % 2 == 0
            start_pos = di_zhi_map[start_zhi]
            for i, stage in enumerate(stages):
                if is_yang:
                    zhi_pos = (start_pos + i) % 12
                else:
                    zhi_pos = (start_pos - i) % 12
                zhi = di_zhi_order[zhi_pos]
                data.append((gan, zhi, stage))
        
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT IGNORE INTO changsheng_lookup (gan, zhi, stage_name) VALUES (%s, %s, %s)",
                    data
                )
            conn.commit()

    def get_changsheng_lookup(self) -> dict:
        """获取十二长生查找表 {gan: {zhi: stage_name}}"""
        rows = self._query_all("SELECT gan, zhi, stage_name FROM changsheng_lookup")
        result = {}
        for r in rows:
            if r['gan'] not in result:
                result[r['gan']] = {}
            result[r['gan']][r['zhi']] = r['stage_name']
        return result

    def get_changsheng_lookup_list(self) -> dict:
        """获取十二长生查找表 {gan: [zhi_list]} 按阶段顺序"""
        stages = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']
        rows = self._query_all("SELECT gan, zhi, stage_name FROM changsheng_lookup")
        result = {}
        for r in rows:
            if r['gan'] not in result:
                result[r['gan']] = [None] * 12
            stage_idx = stages.index(r['stage_name']) if r['stage_name'] in stages else 0
            result[r['gan']][stage_idx] = r['zhi']
        return result

    # -- 纳音五行 --
    def init_nayin_wuxing(self):
        """初始化纳音五行数据"""
        nayin_data = [
            ('甲子', '海中金', '金'), ('乙丑', '海中金', '金'),
            ('丙寅', '炉中火', '火'), ('丁卯', '炉中火', '火'),
            ('戊辰', '大林木', '木'), ('己巳', '大林木', '木'),
            ('庚午', '路旁土', '土'), ('辛未', '路旁土', '土'),
            ('壬申', '剑锋金', '金'), ('癸酉', '剑锋金', '金'),
            ('甲戌', '山头火', '火'), ('乙亥', '山头火', '火'),
            ('丙子', '涧下水', '水'), ('丁丑', '涧下水', '水'),
            ('戊寅', '城头土', '土'), ('己卯', '城头土', '土'),
            ('庚辰', '白蜡金', '金'), ('辛巳', '白蜡金', '金'),
            ('壬午', '杨柳木', '木'), ('癸未', '杨柳木', '木'),
            ('甲申', '泉中水', '水'), ('乙酉', '泉中水', '水'),
            ('丙戌', '屋上土', '土'), ('丁亥', '屋上土', '土'),
            ('戊子', '霹雳火', '火'), ('己丑', '霹雳火', '火'),
            ('庚寅', '松柏木', '木'), ('辛卯', '松柏木', '木'),
            ('壬辰', '长流水', '水'), ('癸巳', '长流水', '水'),
            ('甲午', '沙中金', '金'), ('乙未', '沙中金', '金'),
            ('丙申', '山下火', '火'), ('丁酉', '山下火', '火'),
            ('戊戌', '平地木', '木'), ('己亥', '平地木', '木'),
            ('庚子', '壁上土', '土'), ('辛丑', '壁上土', '土'),
            ('壬寅', '金箔金', '金'), ('癸卯', '金箔金', '金'),
            ('甲辰', '覆灯火', '火'), ('乙巳', '覆灯火', '火'),
            ('丙午', '天河水', '水'), ('丁未', '天河水', '水'),
            ('戊申', '大驿土', '土'), ('己酉', '大驿土', '土'),
            ('庚戌', '钗钏金', '金'), ('辛亥', '钗钏金', '金'),
            ('壬子', '桑柘木', '木'), ('癸丑', '桑柘木', '木'),
            ('甲寅', '大溪水', '水'), ('乙卯', '大溪水', '水'),
            ('丙辰', '沙中土', '土'), ('丁巳', '沙中土', '土'),
            ('戊午', '天上火', '火'), ('己未', '天上火', '火'),
            ('庚申', '石榴木', '木'), ('辛酉', '石榴木', '木'),
            ('壬戌', '大海水', '水'), ('癸亥', '大海水', '水')
        ]
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT IGNORE INTO nayin_wuxing (ganzhi_pair, nayin_name, wuxing) VALUES (%s, %s, %s)",
                    nayin_data
                )
            conn.commit()

    def get_nayin_wuxing(self) -> dict:
        """获取纳音五行 {ganzhi: (nayin_name, wuxing)}"""
        rows = self._query_all("SELECT ganzhi_pair, nayin_name, wuxing FROM nayin_wuxing")
        return {r['ganzhi_pair']: (r['nayin_name'], r['wuxing']) for r in rows}

    # -- 神煞数据（含计算条件） --
    def init_shensha_terms(self):
        """初始化神煞术语数据（含计算条件）"""
        # shensha_terms 表字段: name, category, term_type, brief, description, check_method, influences, related_terms
        shensha_data = [
            ('天德', '神煞', 'positive', '天德贵人，主吉祥、逢凶化吉',
             '天德贵人是四柱神煞中最吉祥的神煞之一。天德者，谓合天德之正气，主人慈祥和蔼，聪明正直，一生少病灾，遇难呈祥，逢凶化吉。命中有天德贵人者，多为善良之人，容易得到他人帮助，一生平安顺遂。',
             '{"type": "gan", "conditions": {"丙": ["寅"], "丁": ["亥"], "戊": ["寅"], "己": ["申"], "庚": ["亥"], "辛": ["巳"], "壬": ["寅"], "癸": ["申"]}, "locations": ["月柱"]}',
             '["健康", "贵人运", "平安"]', '["月德", "天乙贵人"]'),
            ('月德', '神煞', 'positive', '月德贵人，主仁慈、聪明、福寿',
             '月德贵人与天德贵人并称"二德"，同为吉祥神煞。月德者，谓合月德之正气，主人仁慈敦厚，聪明好学，福寿双全，一生平安。命中有月德贵人者，性情温和，乐于助人，容易得到长辈和上级的提携。',
             '{"type": "gan", "conditions": {"丙": ["甲"], "丁": ["壬"], "戊": ["丙"], "己": ["甲"], "庚": ["戊"], "辛": ["丙"], "壬": ["庚"], "癸": ["戊"]}, "locations": ["月柱"]}',
             '["贵人运", "健康", "福寿"]', '["天德"]'),
            ('文昌', '神煞', 'positive', '文昌星，主学业、才华、聪明过人',
             '文昌星主学业、文章、才华。命中有文昌星者，聪明伶俐，记忆力强，学习能力出众，容易在学业上取得优异成绩，适合从事学术研究、教育、文化艺术等工作。文昌星入命，主其人多才多艺，富有创造力。',
             '{"type": "gan", "conditions": {"甲": ["巳"], "乙": ["午"], "丙": ["申"], "丁": ["酉"], "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"], "壬": ["寅"], "癸": ["卯"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["学业", "才华", "聪明"]', '["学堂", "词馆"]'),
            ('桃花', '神煞', 'neutral', '桃花星，主人缘、异性缘、社交能力强',
             '桃花星主异性缘、人际关系、社交能力。命中有桃花星者，相貌俊秀，气质高雅，善于交际，异性缘旺盛。桃花星也主艺术才华，适合从事演艺、娱乐、公关等行业。但桃花过旺也可能带来感情困扰，需注意把握分寸。',
             '{"type": "zhi", "conditions": {"子": ["卯"], "午": ["酉"], "卯": ["子"], "酉": ["午"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["桃花", "人缘", "社交"]', '["红艳"]'),
            ('驿马', '神煞', 'neutral', '驿马星，主变动、旅行、迁移',
             '驿马星主变动、旅行、迁移、外出。命中有驿马星者，一生多动少静，喜欢旅行和探索，适合从事需要经常出差或外出的工作，如销售、物流、旅游等行业。驿马星也主机遇，往往在变动中获得发展机会。',
             '{"type": "zhi", "conditions": {"申": ["寅"], "寅": ["申"], "巳": ["亥"], "亥": ["巳"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["变动", "旅行", "迁移"]', '["华盖"]'),
            ('华盖', '神煞', 'neutral', '华盖星，主艺术、才华、孤独',
             '华盖星主艺术、才华、宗教、哲学。命中有华盖星者，富有艺术天赋，对传统文化、宗教哲学有浓厚兴趣，容易在这些领域取得成就。但华盖星也主孤独，其人往往性格内向，喜欢独处，有时会显得孤僻不合群。',
             '{"type": "zhi", "conditions": {"寅": ["戌"], "戌": ["寅"], "辰": ["丑"], "丑": ["辰"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["艺术", "才华", "孤独"]', '["驿马"]'),
            ('将星', '神煞', 'positive', '将星，主权威、领导力、事业有成',
             '将星主权威、领导力、组织能力。命中有将星者，具有领导才能，善于组织和指挥他人，容易成为团队中的核心人物或领导者。将星入命，主其人在事业上容易取得成就，适合从事管理、军事、政治等工作。',
             '{"type": "zhi", "conditions": {"子": ["午"], "午": ["子"], "卯": ["酉"], "酉": ["卯"]}, "locations": ["月柱", "时柱"]}',
             '["权威", "领导力", "事业"]', '["紫微"]'),
            ('天乙', '神煞', 'positive', '天乙贵人，主贵人相助、逢凶化吉',
             '天乙贵人是四柱神煞中最重要的贵人星。天乙者，乃天上之神，在紫微垣、阊阖门外，与太乙并列，事天皇大帝，下游三辰，家在己丑斗牛之次，出乎己未井鬼之舍，执玉衡较量天人之事，名曰天乙也。命中有天乙贵人者，一生多得贵人相助，逢凶化吉，遇难呈祥。',
             '{"type": "gan", "conditions": {"甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"], "丁": ["亥", "酉"], "戊": ["丑", "未"], "己": ["子", "申"], "庚": ["寅", "午"], "辛": ["寅", "午"], "壬": ["巳", "卯"], "癸": ["巳", "卯"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["贵人运", "吉祥", "帮助"]', '["天德", "月德"]'),
            ('劫煞', '神煞', 'negative', '劫煞，主是非、争斗、意外之灾',
             '劫煞主是非、争斗、抢劫、意外之灾。命中有劫煞者，性格刚烈，容易冲动，好勇斗狠，容易与人发生争执和冲突。劫煞也主财物损失，需注意防范盗窃、抢劫等意外事件。但劫煞也主勇敢果断，若能善用其力，也可在竞争中取得优势。',
             '{"type": "zhi", "conditions": {"申": ["巳"], "巳": ["申"], "寅": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["是非", "争斗", "意外"]', '["亡神"]'),
            ('亡神', '神煞', 'negative', '亡神，主官非、病灾、精神困扰',
             '亡神主官非、病灾、精神困扰。命中有亡神者，容易遇到官司诉讼，身体方面容易有慢性疾病，精神上容易焦虑不安。亡神也主阴谋、暗害，需注意防范小人陷害。但亡神也主聪明才智，若能修身养性，也可将其转化为智慧之力。',
             '{"type": "zhi", "conditions": {"寅": ["巳"], "巳": ["申"], "申": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["官非", "病灾", "精神困扰"]', '["劫煞"]'),
            ('孤辰', '神煞', 'negative', '孤辰，主孤独、寡合、婚姻不顺',
             '孤辰主孤独、寡合、婚姻不顺。命中有孤辰者，性格孤僻，不善于与人交往，朋友稀少，婚姻方面容易晚婚或婚姻不顺。孤辰也主内心空虚，容易感到孤独寂寞。但孤辰也主独立自强，其人往往能够独自完成事业，不需要依赖他人。',
             '{"type": "zhi", "conditions": {"寅": ["巳"], "巳": ["申"], "申": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["孤独", "寡合", "婚姻不顺"]', '["寡宿"]'),
            ('寡宿', '神煞', 'negative', '寡宿，主孤独、守寡、人际关系淡薄',
             '寡宿主孤独、守寡、人际关系淡薄。命中有寡宿者，女性容易守寡或婚姻不幸，男性则容易孤独终老。寡宿也主人际关系淡薄，朋友不多，社交圈子狭窄。但寡宿也主清净无为，其人往往能够专注于自己的事业，不受外界干扰。',
             '{"type": "zhi", "conditions": {"辰": ["丑"], "丑": ["辰"], "戌": ["未"], "未": ["戌"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["孤独", "守寡", "人际关系淡薄"]', '["孤辰"]'),
            ('福星', '神煞', 'positive', '福星贵人，主福禄、长寿、吉祥',
             '福星贵人主福禄、长寿、吉祥。命中有福星贵人者，一生福气深厚，衣食无忧，寿命较长。福星贵人也主善良仁慈，乐于助人，容易得到他人的尊敬和爱戴。',
             '{"type": "gan", "conditions": {"甲": ["子"], "乙": ["丑"], "丙": ["寅"], "丁": ["卯"], "戊": ["辰"], "己": ["巳"], "庚": ["午"], "辛": ["未"], "壬": ["申"], "癸": ["酉"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["福禄", "长寿", "吉祥"]', '["金舆"]'),
            ('金舆', '神煞', 'positive', '金舆贵人，主财富、地位、车房',
             '金舆贵人主财富、地位、车房。命中有金舆贵人者，容易拥有车辆、房产等资产，财运较好，社会地位较高。金舆贵人也主出行便利，一生出行多有车辆代步。',
             '{"type": "gan", "conditions": {"甲": ["辰"], "乙": ["巳"], "丙": ["午"], "丁": ["未"], "戊": ["申"], "己": ["酉"], "庚": ["戌"], "辛": ["亥"], "壬": ["子"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["财富", "地位", "车房"]', '["福星"]'),
            ('学堂', '神煞', 'positive', '学堂星，主学业、教育、知识',
             '学堂星主学业、教育、知识。命中有学堂星者，学习能力强，学业成绩优异，适合从事教育、学术研究等工作。学堂星也主智慧，其人往往聪明好学，知识渊博。',
             '{"type": "gan", "conditions": {"甲": ["亥"], "乙": ["戌"], "丙": ["寅"], "丁": ["卯"], "戊": ["巳"], "己": ["午"], "庚": ["申"], "辛": ["酉"], "壬": ["子"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["学业", "教育", "知识"]', '["文昌", "词馆"]'),
            ('词馆', '神煞', 'positive', '词馆星，主文辞、才华、写作',
             '词馆星主文辞、才华、写作。命中有词馆星者，善于文辞表达，写作能力强，适合从事文学创作、新闻媒体、文案策划等工作。词馆星也主口才，其人往往能言善辩，表达能力出众。',
             '{"type": "gan", "conditions": {"甲": ["寅"], "乙": ["卯"], "丙": ["巳"], "丁": ["午"], "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"], "壬": ["辰"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["文辞", "才华", "写作"]', '["文昌", "学堂"]'),
            ('太极贵人', '神煞', 'positive', '太极贵人，主智慧、神秘、悟性',
             '太极贵人主智慧、神秘、悟性。命中有太极贵人者，对哲学、宗教、神秘学等有浓厚兴趣，悟性较高，容易理解深奥的道理。太极贵人也主创造力，其人往往能够提出独特的见解和想法。',
             '{"type": "gan", "conditions": {"甲": ["子"], "乙": ["午"], "丙": ["卯"], "丁": ["酉"], "戊": ["辰"], "己": ["戌"], "庚": ["巳"], "辛": ["亥"], "壬": ["寅"], "癸": ["申"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["智慧", "神秘", "悟性"]', '["华盖"]'),
            ('天医', '神煞', 'positive', '天医星，主健康、医药、治愈',
             '天医星主健康、医药、治愈。命中有天医星者，对医学、养生等有浓厚兴趣，适合从事医疗、养生、保健等行业。天医星也主身体健康，其人往往较少生病，即使生病也容易痊愈。',
             '{"type": "gan", "conditions": {"甲": ["卯"], "乙": ["寅"], "丙": ["子"], "丁": ["亥"], "戊": ["丑"], "己": ["子"], "庚": ["酉"], "辛": ["申"], "壬": ["午"], "癸": ["巳"]}, "locations": ["月柱", "时柱"]}',
             '["健康", "医药", "治愈"]', '["华盖"]'),
            ('红艳', '神煞', 'neutral', '红艳煞，主桃花、感情、魅力',
             '红艳煞主桃花、感情、魅力。命中有红艳煞者，相貌出众，气质迷人，异性缘非常旺盛。红艳煞也主感情丰富，其人往往容易陷入感情纠葛，需注意把握感情分寸。',
             '{"type": "gan", "conditions": {"甲": ["午"], "乙": ["巳"], "丙": ["寅"], "丁": ["卯"], "戊": ["辰"], "己": ["丑"], "庚": ["子"], "辛": ["亥"], "壬": ["戌"], "癸": ["酉"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["桃花", "感情", "魅力"]', '["桃花"]'),
            ('勾绞', '神煞', 'negative', '勾绞煞，主是非、纠缠、牵连',
             '勾绞煞主是非、纠缠、牵连。命中有勾绞煞者，容易卷入他人的是非纠纷中，即使与自己无关也可能被牵连。勾绞煞也主人际关系复杂，容易与人发生矛盾和冲突。',
             '{"type": "zhi", "conditions": {"子": ["卯"], "卯": ["子"], "丑": ["辰"], "辰": ["丑"], "寅": ["巳"], "巳": ["寅"], "卯": ["午"], "午": ["卯"], "辰": ["未"], "未": ["辰"], "巳": ["申"], "申": ["巳"], "午": ["酉"], "酉": ["午"], "未": ["戌"], "戌": ["未"], "申": ["亥"], "亥": ["申"], "酉": ["子"], "子": ["酉"], "戌": ["丑"], "丑": ["戌"], "亥": ["寅"], "寅": ["亥"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["是非", "纠缠", "牵连"]', '["绞煞"]'),
            ('绞煞', '神煞', 'negative', '绞煞，主纠缠、束缚、困扰',
             '绞煞主纠缠、束缚、困扰。命中有绞煞者，容易被事情或人际关系所束缚，难以摆脱困扰。绞煞也主精神压力，其人往往感到身心疲惫，难以放松。',
             '{"type": "zhi", "conditions": {"子": ["酉"], "酉": ["子"], "丑": ["戌"], "戌": ["丑"], "寅": ["亥"], "亥": ["寅"], "卯": ["子"], "子": ["卯"], "辰": ["丑"], "丑": ["辰"], "巳": ["寅"], "寅": ["巳"], "午": ["卯"], "卯": ["午"], "未": ["辰"], "辰": ["未"], "申": ["巳"], "巳": ["申"], "酉": ["午"], "午": ["酉"], "戌": ["未"], "未": ["戌"], "亥": ["申"], "申": ["亥"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}',
             '["纠缠", "束缚", "困扰"]', '["勾绞"]')
        ]
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """INSERT IGNORE INTO shensha_terms 
                    (name, category, term_type, brief, description, check_method, influences, related_terms) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    shensha_data
                )
            conn.commit()

    def get_shensha_terms(self) -> dict:
        """获取神煞术语（用于术语解释）"""
        rows = self._query_all("SELECT * FROM shensha_terms")
        return {r['name']: r for r in rows}

    def get_shensha_for_calculation(self) -> dict:
        """获取神煞计算数据 {name: {type, description, detailed, locations, conditions}}"""
        rows = self._query_all("SELECT name, term_type, brief, description, check_method FROM shensha_terms")
        result = {}
        for r in rows:
            check = json.loads(r['check_method']) if r['check_method'] else {}
            result[r['name']] = {
                'type': r['term_type'] or 'neutral',
                'description': r['brief'] or r['name'],
                'detailed': r['description'] or '',
                'locations': check.get('locations', ['年柱', '月柱', '日柱', '时柱']),
                'conditions': check.get('conditions', {})
            }
        return result

    def get_ganzhi_relation_terms(self) -> dict:
        """获取干支关系术语"""
        rows = self._query_all("SELECT * FROM ganzhi_relation_terms")
        return {r['name']: r for r in rows}

    def get_foundation_terms(self) -> dict:
        """获取命理基础术语"""
        rows = self._query_all("SELECT * FROM foundation_terms")
        return {r['name']: r for r in rows}

    def get_meihua_terms(self) -> dict:
        """获取梅花易数术语"""
        rows = self._query_all("SELECT * FROM meihua_terms")
        return {r['name']: r for r in rows}

    def get_all_terms(self) -> dict:
        """获取所有术语合并"""
        result = {}
        for rows_func in [self.get_shensha_terms, self.get_ganzhi_relation_terms,
                         self.get_foundation_terms, self.get_meihua_terms]:
            result.update(rows_func())
        return result

    # -- 梅花易数知识 --
    def get_meihua_knowledge(self) -> dict:
        """获取梅花易数知识 {section: {content_key: content_value}}"""
        rows = self._query_all("SELECT * FROM meihua_knowledge")
        result = {}
        for r in rows:
            section = r['section']
            if section not in result:
                result[section] = {}
            result[section][r['content_key']] = json.loads(r['content_value']) if isinstance(r['content_value'], str) else r['content_value']
        return result

    # -- 城市坐标 --
    def get_city_coords(self) -> dict:
        """获取城市坐标 {city: (lon, lat)}"""
        rows = self._query_all("SELECT city_name, longitude, latitude FROM city_coords")
        return {r['city_name']: (float(r['longitude']), float(r['latitude'])) for r in rows}

    def get_city_list(self) -> list:
        """获取城市列表"""
        rows = self._query_all("SELECT city_name FROM city_coords")
        return [r['city_name'] for r in rows]

    # -- 运势天干分析 --
    def get_yunshi_gan_analysis(self) -> dict:
        """获取运势天干分析"""
        rows = self._query_all("SELECT * FROM yunshi_gan_analysis")
        return {r['gan']: r for r in rows}

    # -- 运势地支分析 --
    def get_yunshi_zhi_analysis(self) -> dict:
        """获取运势地支分析"""
        rows = self._query_all("SELECT * FROM yunshi_zhi_analysis")
        return {r['zhi']: r for r in rows}

    # -- 地支冲刑适配方法 (返回 geju_analyzer 兼容格式) --
    def get_di_zhi_chong_map(self) -> dict:
        """获取地支六冲映射 {zhi1: zhi2, zhi2: zhi1}"""
        rows = self._query_all("SELECT zhi_pair FROM di_zhi_chong")
        result = {}
        for r in rows:
            pair = r['zhi_pair']
            if len(pair) == 2:
                result[pair[0]] = pair[1]
                result[pair[1]] = pair[0]
        return result

    def get_di_zhi_xing_map(self) -> dict:
        """获取地支相刑映射 {zhi: [zhi_list]}"""
        rows = self._query_all("SELECT zhi_group FROM di_zhi_xing")
        result = {}
        for r in rows:
            group = r['zhi_group']
            for zhi in group:
                if zhi not in result:
                    result[zhi] = []
                for other in group:
                    if other != zhi:
                        result[zhi].append(other)
        return result

    # ==================== 用户管理 ====================

    import hashlib
    def create_user(self, username: str, password: str) -> Optional[int]:
        """
        创建新用户

        Args:
            username: 用户名
            password: 用户密码（明文）

        Returns:
            新用户ID，失败返回None
        """
        if not username or not password:
            return None
        
        if len(password) < 6:
            raise ValueError("密码长度不能少于6位")
        
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                        (username, password_hash)
                    )
                    user_id = cursor.lastrowid
                connection.commit()
                return user_id
        except pymysql.IntegrityError:
            return None
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户登录

        Args:
            username: 用户名
            password: 用户密码（明文）

        Returns:
            用户信息字典，验证失败返回None
        """
        if not username or not password:
            return None
        
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT id, username, created_at FROM users WHERE username = %s AND password_hash = %s",
                        (username, password_hash)
                    )
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"验证用户失败: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名查询用户

        Args:
            username: 用户名

        Returns:
            用户信息字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT id, username, created_at FROM users WHERE username = %s",
                        (username,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"查询用户失败: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID查询用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT id, username, created_at FROM users WHERE id = %s",
                        (user_id,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            print(f"查询用户失败: {e}")
            return None

    # ==================== 排盘记录管理 ====================

    def save_pan_record(self, user_id: int, name: str, gender: str,
                        birth_date: str, birth_time: str, city: str,
                        pan_type: str, result: Dict[str, Any]) -> Optional[int]:
        """
        保存排盘记录

        Args:
            user_id: 用户ID
            name: 姓名
            gender: 性别
            birth_date: 出生日期
            birth_time: 出生时间
            city: 城市
            pan_type: 排盘类型
            result: 排盘结果字典

        Returns:
            记录ID，失败返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO pan_records
                        (user_id, name, gender, birth_date, birth_time, city, pan_type, result_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id, name, gender, birth_date, birth_time,
                            city, pan_type, json.dumps(result, ensure_ascii=False)
                        )
                    )
                    record_id = cursor.lastrowid
                connection.commit()
                return record_id
        except Exception as e:
            print(f"保存排盘记录失败: {e}")
            return None

    def get_user_records(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的排盘记录列表

        Args:
            user_id: 用户ID
            limit: 返回记录数量上限

        Returns:
            排盘记录列表
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT id, name, gender, birth_date, birth_time,
                               city, pan_type, result_json, created_at
                        FROM pan_records
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (user_id, limit)
                    )
                    records = cursor.fetchall()
                    # 解析JSON字段
                    for record in records:
                        try:
                            record['result'] = json.loads(record['result_json'])
                        except (json.JSONDecodeError, KeyError):
                            record['result'] = {}
                        del record['result_json']
                    return records
        except Exception as e:
            print(f"获取排盘记录失败: {e}")
            return []

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单条排盘记录

        Args:
            record_id: 记录ID

        Returns:
            排盘记录字典，不存在返回None
        """
        try:
            with self._connect() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT id, user_id, name, gender, birth_date, birth_time,
                               city, pan_type, result_json, created_at
                        FROM pan_records
                        WHERE id = %s
                        """,
                        (record_id,)
                    )
                    record = cursor.fetchone()
                    if record:
                        try:
                            record['result'] = json.loads(record['result_json'])
                        except (json.JSONDecodeError, KeyError):
                            record['result'] = {}
                        del record['result_json']
                    return record
        except Exception as e:
            print(f"获取排盘记录失败: {e}")
            return None

    def delete_record(self, record_id: int, user_id: int) -> bool:
        """
        删除排盘记录

        Args:
            record_id: 记录ID
            user_id: 用户ID（用于权限验证）

        Returns:
            是否删除成功
        """
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM pan_records WHERE id = %s AND user_id = %s",
                        (record_id, user_id)
                    )
                    affected = cursor.rowcount
                connection.commit()
                return affected > 0
        except Exception as e:
            print(f"删除排盘记录失败: {e}")
            return False

    def init_database(self):
        """
        重新初始化数据库（公开接口）
        用于外部调用确保数据库和表已创建
        """
        self._init_database()
