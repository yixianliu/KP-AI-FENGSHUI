"""
命理知识库 - 结构化存储八字命理和梅花易数的专业知识
支持术语查询、知识检索、分类浏览等功能
为AI分析提供结构化知识支撑
"""
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING
from core.hexagram_analyzer import BAGUA, HEXAGRAMS


WUXING_KNOWLEDGE = {
    '木': {
        'nature': '木曰曲直',
        'characteristics': ['生长', '生发', '条达', '舒畅', '仁慈'],
        'direction': '东方',
        'season': '春季',
        'color': '绿色、青色',
        'organ': ['肝', '胆'],
        'taste': '酸',
        'number': 3,
        'positive_traits': ['积极向上', '富有创造力', '善于创新', '有进取心', '正直善良', '乐观开朗'],
        'negative_traits': ['固执己见', '过于冲动', '缺乏耐心', '容易情绪化', '优柔寡断'],
        'career': ['创意设计', '艺术文化', '教育培训', '林业农业', '木材加工', '出版传媒'],
        'health_advice': '注意肝胆保养，少熬夜，多运动，保持心情舒畅',
        'description': '木主生发，代表生命力和成长力。木旺之人性格开朗、有创造力，但需注意避免过于冲动。'
    },
    '火': {
        'nature': '火曰炎上',
        'characteristics': ['温热', '上升', '光明', '热烈', '急躁'],
        'direction': '南方',
        'season': '夏季',
        'color': '红色、紫色',
        'organ': ['心', '小肠'],
        'taste': '苦',
        'number': 2,
        'positive_traits': ['热情洋溢', '乐观开朗', '富有感染力', '社交能力强', '充满活力', '敢作敢当'],
        'negative_traits': ['急躁冲动', '缺乏冷静', '过于张扬', '容易骄傲', '缺乏耐心'],
        'career': ['销售营销', '演艺娱乐', '公共关系', '能源电力', '餐饮酒店', '互联网'],
        'health_advice': '注意心脏和血压保养，避免过度劳累，保持心态平和',
        'description': '火主炎上，代表热情和活力。火旺之人性格开朗、善于交际，但需注意控制情绪，避免急躁。'
    },
    '土': {
        'nature': '土爰稼穑',
        'characteristics': ['生化', '承载', '受纳', '稳重', '包容'],
        'direction': '中央',
        'season': '长夏',
        'color': '黄色、棕色',
        'organ': ['脾', '胃'],
        'taste': '甘',
        'number': 5,
        'positive_traits': ['稳重可靠', '诚实守信', '有责任感', '踏实肯干', '包容大度', '务实节俭'],
        'negative_traits': ['过于保守', '缺乏变通', '固执僵化', '反应迟钝', '容易犹豫'],
        'career': ['金融银行', '房地产', '建筑工程', '企业管理', '农业生产', '仓储物流'],
        'health_advice': '注意脾胃保养，饮食规律，避免暴饮暴食，适当运动',
        'description': '土主稼穑，代表包容和承载。土旺之人性格稳重、值得信赖，但需注意避免过于保守，学会灵活变通。'
    },
    '金': {
        'nature': '金曰从革',
        'characteristics': ['清净', '肃杀', '收敛', '决断', '刚毅'],
        'direction': '西方',
        'season': '秋季',
        'color': '白色、金色',
        'organ': ['肺', '大肠'],
        'taste': '辛',
        'number': 4,
        'positive_traits': ['果断刚毅', '追求完美', '有决断力', '精明干练', '公正无私', '重情重义'],
        'negative_traits': ['刻薄寡恩', '刚愎自用', '过于挑剔', '缺乏变通', '容易悲伤'],
        'career': ['法律司法', '金融投资', '金属机械', '汽车制造', '珠宝首饰', '军警保安'],
        'health_advice': '注意肺部和呼吸道保养，多喝水，保持空气清新，避免悲伤过度',
        'description': '金主从革，代表决断和变革。金旺之人性格刚毅、做事果断，但需注意人际关系，避免过于苛刻。'
    },
    '水': {
        'nature': '水曰润下',
        'characteristics': ['寒凉', '向下', '滋润', '智慧', '灵活'],
        'direction': '北方',
        'season': '冬季',
        'color': '蓝色、黑色',
        'organ': ['肾', '膀胱'],
        'taste': '咸',
        'number': 1,
        'positive_traits': ['聪明灵活', '思维敏捷', '适应力强', '富有智慧', '善于变通', '足智多谋'],
        'negative_traits': ['散漫无章', '缺乏定力', '优柔寡断', '过于敏感', '容易多疑'],
        'career': ['商贸物流', '旅游服务', '科技研发', '水产养殖', '交通运输', '咨询策划'],
        'health_advice': '注意肾脏和泌尿系统保养，避免过度劳累，注意保暖',
        'description': '水主润下，代表智慧和灵活。水旺之人聪明机智、善于变通，但需注意保持专注，避免过于散漫。'
    }
}


WUXING_RELATIONS = {
    'sheng': {
        'name': '五行相生',
        'description': '木生火，火生土，土生金，金生水，水生木',
        'relations': [
            {'from': '木', 'to': '火', 'meaning': '木燃而生火，木为火之母，火为木之子'},
            {'from': '火', 'to': '土', 'meaning': '火焚万物而生土，火为土之母，土为火之子'},
            {'from': '土', 'to': '金', 'meaning': '土中藏金，土为金之母，金为土之子'},
            {'from': '金', 'to': '水', 'meaning': '金销熔生水，金为水之母，水为金之子'},
            {'from': '水', 'to': '木', 'meaning': '水滋润生木，水为木之母，木为水之子'},
        ]
    },
    'ke': {
        'name': '五行相克',
        'description': '木克土，土克水，水克火，火克金，金克木',
        'relations': [
            {'from': '木', 'to': '土', 'meaning': '木植根于土中，吸收土中养分，故土被木所克'},
            {'from': '土', 'to': '水', 'meaning': '土能阻挡水流，故土能克水'},
            {'from': '水', 'to': '火', 'meaning': '水能灭火，故水能克火'},
            {'from': '火', 'to': '金', 'meaning': '火能熔金，故火能克金'},
            {'from': '金', 'to': '木', 'meaning': '金属制成的刀具能砍伐树木，故金能克木'},
        ]
    },
    'multiplication': {
        'name': '五行相乘',
        'description': '乘，即乘虚侵袭之意。相乘即相克太过，超过正常制约程度',
        'relations': [
            {'from': '木', 'to': '土', 'meaning': '木气太过，乘土之虚而克之'},
            {'from': '土', 'to': '水', 'meaning': '土气太过，乘水之虚而克之'},
            {'from': '水', 'to': '火', 'meaning': '水气太过，乘火之虚而克之'},
            {'from': '火', 'to': '金', 'meaning': '火气太过，乘金之虚而克之'},
            {'from': '金', 'to': '木', 'meaning': '金气太过，乘木之虚而克之'},
        ]
    },
    'insult': {
        'name': '五行相侮',
        'description': '侮，即持强凌弱之意。相侮即反克，被克者反过来克制克者',
        'relations': [
            {'from': '木', 'to': '金', 'meaning': '木气太过，反侮金（木旺反侮金）'},
            {'from': '金', 'to': '火', 'meaning': '金气太过，反侮火（金旺反侮火）'},
            {'from': '火', 'to': '水', 'meaning': '火气太过，反侮水（火旺反侮水）'},
            {'from': '水', 'to': '土', 'meaning': '水气太过，反侮土（水旺反侮土）'},
            {'from': '土', 'to': '木', 'meaning': '土气太过，反侮木（土旺反侮木）'},
        ]
    }
}


SHISHEN_KNOWLEDGE = {
    '比肩': {
        'type': '同我',
        'yinyang': '同阴阳',
        'description': '与日主五行相同、阴阳相同的天干或地支藏干',
        'meaning': '代表兄弟、朋友、同事、竞争者、自我意识',
        'positive': ['独立自主', '意志坚定', '自尊自信', '行动力强', '善于合作'],
        'negative': ['固执己见', '争强好胜', '容易冲动', '缺乏耐心', '孤独自负'],
        'career': '适合独立创业、自由职业、合伙经营',
        'wealth': '能守财，但也容易因朋友兄弟而破财',
        'love': '感情中较为自我，容易与伴侣产生争执'
    },
    '劫财': {
        'type': '同我',
        'yinyang': '异阴阳',
        'description': '与日主五行相同、阴阳不同的天干或地支藏干',
        'meaning': '代表异性朋友、兄弟姐妹、竞争者、破财星',
        'positive': ['热情开朗', '善于交际', '行动力强', '敢于冒险', '仗义疏财'],
        'negative': ['冲动好斗', '花钱大手', '容易受骗', '嫉妒心强', '口舌是非'],
        'career': '适合销售、公关、娱乐等需要交际的行业',
        'wealth': '财运起伏大，容易大起大落',
        'love': '异性缘好，但感情容易有竞争'
    },
    '食神': {
        'type': '我生',
        'yinyang': '同阴阳',
        'description': '日主所生、与日主阴阳相同的天干或地支藏干',
        'meaning': '代表子女、才华、福气、口福、艺术天赋',
        'positive': ['聪明智慧', '才华横溢', '乐观开朗', '品味高雅', '福德深厚'],
        'negative': ['过于享乐', '懒散拖延', '清高孤傲', '不切实际', '容易发胖'],
        'career': '适合艺术、设计、美食、教育、文化等行业',
        'wealth': '财运稳定，衣食无忧',
        'love': '感情浪漫，追求精神层面的契合'
    },
    '伤官': {
        'type': '我生',
        'yinyang': '异阴阳',
        'description': '日主所生、与日主阴阳不同的天干或地支藏干',
        'meaning': '代表才华、创造力、口才、叛逆、伤官见官',
        'positive': ['才华出众', '思维敏捷', '口才极佳', '创造力强', '敢作敢当'],
        'negative': ['叛逆不羁', '心高气傲', '口舌是非', '容易得罪人', '感情波折'],
        'career': '适合创意、表演、销售、法律、传媒等行业',
        'wealth': '财运起伏大，靠才华赚钱',
        'love': '感情丰富，但容易有波折'
    },
    '偏财': {
        'type': '我克',
        'yinyang': '异阴阳',
        'description': '日主所克、与日主阴阳不同的天干或地支藏干',
        'meaning': '代表偏财运、意外之财、父亲、情妇、生意',
        'positive': ['财运亨通', '善于理财', '慷慨大方', '商业头脑', '人缘极好'],
        'negative': ['花钱大手', '投机心理', '感情不专', '容易被骗', '虚荣浮华'],
        'career': '适合经商、投资、金融、销售等行业',
        'wealth': '偏财旺，容易有意外收入',
        'love': '异性缘佳，感情经历丰富'
    },
    '正财': {
        'type': '我克',
        'yinyang': '同阴阳',
        'description': '日主所克、与日主阴阳相同的天干或地支藏干',
        'meaning': '代表正财运、稳定收入、妻子、财产、务实',
        'positive': ['踏实肯干', '勤俭节约', '财运稳定', '顾家负责', '诚实守信'],
        'negative': ['过于节俭', '固执保守', '缺乏浪漫', '容易斤斤计较', '劳碌命'],
        'career': '适合稳定工作、财务管理、实业经营',
        'wealth': '正财运好，收入稳定',
        'love': '感情稳定，重视家庭'
    },
    '正官': {
        'type': '克我',
        'yinyang': '异阴阳',
        'description': '克制日主、与日主阴阳不同的天干或地支藏干',
        'meaning': '代表官职、地位、丈夫、规矩、约束力',
        'positive': ['正直守信', '责任感强', '领导能力', '规矩自律', '名声好'],
        'negative': ['过于刻板', '压抑自我', '胆小怕事', '压力山大', '墨守成规'],
        'career': '适合公务员、管理层、法律、军警等职业',
        'wealth': '财运稳定，靠职位收入',
        'love': '女命正官为夫，感情稳定'
    },
    '七杀': {
        'type': '克我',
        'yinyang': '同阴阳',
        'description': '克制日主、与日主阴阳相同的天干或地支藏干',
        'meaning': '代表偏官、权力、小人、压力、冲劲',
        'positive': ['有魄力', '决断力强', '不服输', '执行力强', '敢闯敢拼'],
        'negative': ['脾气暴躁', '好勇斗狠', '压力过大', '容易招小人', '叛逆反抗'],
        'career': '适合军警、创业、竞争激烈的行业',
        'wealth': '财运起伏大，风险与机遇并存',
        'love': '感情有挑战，需要磨合'
    },
    '正印': {
        'type': '生我',
        'yinyang': '异阴阳',
        'description': '生助日主、与日主阴阳不同的天干或地支藏干',
        'meaning': '代表母亲、长辈、学问、名誉、贵人',
        'positive': ['学识渊博', '心地善良', '贵人相助', '名声好', '有福气'],
        'negative': ['依赖心强', '缺乏主见', '好逸恶劳', '空想多实干少', '过于清高'],
        'career': '适合教育、学术研究、文化、出版等行业',
        'wealth': '财运平稳，靠知识技能赚钱',
        'love': '感情温和，注重精神交流'
    },
    '偏印': {
        'type': '生我',
        'yinyang': '同阴阳',
        'description': '生助日主、与日主阴阳相同的天干或地支藏干',
        'meaning': '代表继母、偏门学问、玄学、孤独、枭神',
        'positive': ['思维独特', '悟性极高', '偏才多能', '直觉敏锐', '适合研究'],
        'negative': ['性格孤僻', '多疑善变', '容易钻牛角尖', '离群索居', '不利于子女'],
        'career': '适合玄学、心理学、科研、技术研发等',
        'wealth': '财运偏门，靠特殊技能赚钱',
        'love': '感情平淡，追求精神层面'
    }
}


TIANGAN_DIZHI_KNOWLEDGE = {
    'tiangan': {
        '甲': {'wuxing': '阳木', 'direction': '东方', 'season': '春季', 'meaning': '万物破土而出，开始生长', 'organ': '胆', 'body': '头、头发'},
        '乙': {'wuxing': '阴木', 'direction': '东方', 'season': '春季', 'meaning': '万物初生，枝叶柔软', 'organ': '肝', 'body': '肩、颈'},
        '丙': {'wuxing': '阳火', 'direction': '南方', 'season': '夏季', 'meaning': '万物光明茂盛，气势恢宏', 'organ': '小肠', 'body': '额、肩'},
        '丁': {'wuxing': '阴火', 'direction': '南方', 'season': '夏季', 'meaning': '万物成长，欣欣向荣', 'organ': '心', 'body': '胸、舌'},
        '戊': {'wuxing': '阳土', 'direction': '中央', 'season': '长夏', 'meaning': '万物茂盛，阳土厚重', 'organ': '胃', 'body': '胁、鼻'},
        '己': {'wuxing': '阴土', 'direction': '中央', 'season': '长夏', 'meaning': '万物蕴藏，阴土柔和', 'organ': '脾', 'body': '腹、口'},
        '庚': {'wuxing': '阳金', 'direction': '西方', 'season': '秋季', 'meaning': '万物收敛，阳金刚健', 'organ': '大肠', 'body': '筋、爪'},
        '辛': {'wuxing': '阴金', 'direction': '西方', 'season': '秋季', 'meaning': '万物成熟，阴金温润', 'organ': '肺', 'body': '胸、肺'},
        '壬': {'wuxing': '阳水', 'direction': '北方', 'season': '冬季', 'meaning': '万物潜藏，阳水奔腾', 'organ': '膀胱', 'body': '胫、足'},
        '癸': {'wuxing': '阴水', 'direction': '北方', 'season': '冬季', 'meaning': '万物闭藏，阴水滋润', 'organ': '肾', 'body': '足、发'},
    },
    'dizhi': {
        '子': {'wuxing': '阳水', 'direction': '北方', 'season': '冬季', 'month': '十一月', 'hour': '23:00-01:00', 'meaning': '万物种子，阳气始生', 'organ': '膀胱、耳', 'hidden_stems': ['癸']},
        '丑': {'wuxing': '阴土', 'direction': '东北方', 'season': '冬季', 'month': '十二月', 'hour': '01:00-03:00', 'meaning': '万物纽芽，阴寒凝结', 'organ': '脾、肚', 'hidden_stems': ['己', '辛', '癸']},
        '寅': {'wuxing': '阳木', 'direction': '东北方', 'season': '春季', 'month': '正月', 'hour': '03:00-05:00', 'meaning': '万物始生，阳气初发', 'organ': '胆、手', 'hidden_stems': ['甲', '丙', '戊']},
        '卯': {'wuxing': '阴木', 'direction': '东方', 'season': '春季', 'month': '二月', 'hour': '05:00-07:00', 'meaning': '万物茂盛，阳气盛大', 'organ': '肝、指', 'hidden_stems': ['乙']},
        '辰': {'wuxing': '阳土', 'direction': '东南方', 'season': '春季', 'month': '三月', 'hour': '07:00-09:00', 'meaning': '万物振奋，阳气渐盛', 'organ': '胃、肩', 'hidden_stems': ['戊', '乙', '癸']},
        '巳': {'wuxing': '阴火', 'direction': '东南方', 'season': '夏季', 'month': '四月', 'hour': '09:00-11:00', 'meaning': '万物已成，阳气正盛', 'organ': '心、面', 'hidden_stems': ['丙', '戊', '庚']},
        '午': {'wuxing': '阳火', 'direction': '南方', 'season': '夏季', 'month': '五月', 'hour': '11:00-13:00', 'meaning': '万物丰满，阳气极盛', 'organ': '小肠、眼', 'hidden_stems': ['丁', '己']},
        '未': {'wuxing': '阴土', 'direction': '西南方', 'season': '夏季', 'month': '六月', 'hour': '13:00-15:00', 'meaning': '万物滋味，阴气始生', 'organ': '脾、脊', 'hidden_stems': ['己', '丁', '乙']},
        '申': {'wuxing': '阳金', 'direction': '西南方', 'season': '秋季', 'month': '七月', 'hour': '15:00-17:00', 'meaning': '万物身体，阴气渐长', 'organ': '大肠、经络', 'hidden_stems': ['庚', '壬', '戊']},
        '酉': {'wuxing': '阴金', 'direction': '西方', 'season': '秋季', 'month': '八月', 'hour': '17:00-19:00', 'meaning': '万物成熟，阴气正盛', 'organ': '肺、皮毛', 'hidden_stems': ['辛']},
        '戌': {'wuxing': '阳土', 'direction': '西北方', 'season': '秋季', 'month': '九月', 'hour': '19:00-21:00', 'meaning': '万物尽灭，阳气渐衰', 'organ': '胃、命门', 'hidden_stems': ['戊', '辛', '丁']},
        '亥': {'wuxing': '阴水', 'direction': '西北方', 'season': '冬季', 'month': '十月', 'hour': '21:00-23:00', 'meaning': '万物收藏，阳气微弱', 'organ': '肾、头', 'hidden_stems': ['壬', '甲']},
    }
}


SHIER_CHANGSHENG_KNOWLEDGE = {
    '长生': {
        'stage': 1,
        'meaning': '万物出生、生长的阶段，象征新生、希望、起点',
        'characteristics': ['生机勃勃', '充满希望', '新的开始', '发展潜力大'],
        'influence': '运势上升，有利于学习、创业、恋爱等新事物的开始'
    },
    '沐浴': {
        'stage': 2,
        'meaning': '万物初生后沐浴清洁，象征洗礼、净化、诱惑',
        'characteristics': ['清洗净化', '桃花旺盛', '易受诱惑', '需要谨慎'],
        'influence': '桃花运旺，但需警惕感情波折，注意洁身自好'
    },
    '冠带': {
        'stage': 3,
        'meaning': '万物渐长，穿衣戴冠，象征成长、礼仪、成年',
        'characteristics': ['逐渐成熟', '注重形象', '社交活跃', '事业起步'],
        'influence': '运势稳步上升，适合发展事业、建立人际关系'
    },
    '临官': {
        'stage': 4,
        'meaning': '万物长成，可以出仕做官，象征事业、官位、成就',
        'characteristics': ['事业有成', '官位亨通', '财运亨通', '地位提升'],
        'influence': '事业运势最好的阶段，利于升职加薪、创业发展'
    },
    '帝旺': {
        'stage': 5,
        'meaning': '万物极盛，如帝王般强盛，象征巅峰、鼎盛、极盛',
        'characteristics': ['鼎盛时期', '如日中天', '功成名就', '物极必反'],
        'influence': '运势达到顶峰，但需注意盛极而衰，保持谦虚谨慎'
    },
    '衰': {
        'stage': 6,
        'meaning': '万物由盛转衰，象征衰退、减弱、走下坡',
        'characteristics': ['运势渐衰', '精力减退', '保守为宜', '不宜冒进'],
        'influence': '运势开始下降，宜守不宜攻，注意养生保健'
    },
    '病': {
        'stage': 7,
        'meaning': '万物生病，象征疾病、困苦、不顺',
        'characteristics': ['身体欠安', '诸事不顺', '困难重重', '需要休养'],
        'influence': '运势不佳，容易生病或遇到困难，宜静养修身'
    },
    '死': {
        'stage': 8,
        'meaning': '万物死亡，象征终结、消亡、低谷',
        'characteristics': ['运势低谷', '诸事不成', '死气沉沉', '需要转变'],
        'influence': '运势最差的阶段，但物极必反，黑暗中孕育希望'
    },
    '墓': {
        'stage': 9,
        'meaning': '万物入墓收藏，象征收藏、入库、结束',
        'characteristics': ['收藏入库', '尘埃落定', '安定平稳', '适合总结'],
        'influence': '运势趋于平稳，适合总结经验、积蓄力量'
    },
    '绝': {
        'stage': 10,
        'meaning': '万物气绝，象征断绝、灭绝、最低点',
        'characteristics': ['运势低谷', '孤立无援', '断绝关系', '重新开始'],
        'influence': '运势极低，但绝处逢生，是新循环的开始'
    },
    '胎': {
        'stage': 11,
        'meaning': '万物受胎孕育，象征孕育、萌芽、计划',
        'characteristics': ['孕育新生命', '计划酝酿', '充满期待', '打基础'],
        'influence': '运势开始回升，适合规划未来、打基础、学习充电'
    },
    '养': {
        'stage': 12,
        'meaning': '万物养育成长，象征养育、培养、准备',
        'characteristics': ['蓄势待发', '养精蓄锐', '稳步成长', '准备充分'],
        'influence': '运势继续上升，适合学习成长、积蓄力量，等待时机'
    }
}


MEIHUA_KNOWLEDGE = {
    'introduction': {
        'name': '梅花易数',
        'origin': '相传为宋代邵雍所创，是一种以八卦为基础的占卜方法',
        'principle': '以数起卦，以卦断事，灵活多变，简便易行',
        'characteristics': ['起卦方式灵活', '解卦直接明了', '随时随地可用', '准确率较高']
    },
    'divination_methods': {
        'time': {
            'name': '时间起卦',
            'description': '以年、月、日、时的数字计算卦象',
            'method': '上卦 = (年数 + 月数 + 日数) % 8；下卦 = (年数 + 月数 + 日数 + 时数) % 8；动爻 = (年数 + 月数 + 日数 + 时数) % 6',
            'use_case': '适合询问任何事情，以问事时间起卦'
        },
        'number': {
            'name': '数字起卦',
            'description': '以数字起卦，可报1-3个数字',
            'method': '1个数：上卦=数%8，下卦=(数//10)%8，动爻=数%6；2个数：上卦=第一个%8，下卦=第二个%8，动爻=两数和%6；3个数：上卦=第一个%8，下卦=第二个%8，动爻=第三个%6',
            'use_case': '方便快捷，让求测者随意报数即可'
        },
        'direction': {
            'name': '方位起卦',
            'description': '以方位和时辰起卦',
            'method': '上卦=方位对应数，下卦=时辰对应数，动爻=两数和%6',
            'use_case': '适合来人不问事情，以来人方位起卦'
        },
        'text': {
            'name': '文字起卦',
            'description': '以文字笔画起卦',
            'method': '上卦=笔画总数%8，下卦=(笔画总数+字数)%8，动爻=笔画总数*字数%6',
            'use_case': '适合写个字或说句话起卦'
        }
    },
    'hexagram_types': {
        'ben': {'name': '本卦', 'description': '起卦得到的原始卦象，代表当前状态'},
        'hu': {'name': '互卦', 'description': '取本卦2、3、4爻为下卦，3、4、5爻为上卦，代表发展过程'},
        'bian': {'name': '变卦', 'description': '动爻阴阳改变后的卦象，代表最终结果'},
        'cuo': {'name': '错卦', 'description': '本卦各爻阴阳全变，代表对立面'},
        'zong': {'name': '综卦', 'description': '本卦颠倒过来，代表不同角度的看法'}
    },
    'interpretation': {
        'basic_rules': [
            '本卦代表现状和起点',
            '互卦代表发展过程和中间状态',
            '变卦代表最终结果和趋势',
            '动爻是判断吉凶的关键',
            '结合卦辞和爻辞综合判断'
        ],
        'judgment_levels': {
            '吉': '运势向好，事情顺利，利于进取',
            '平': '运势平稳，不好不坏，宜稳扎稳打',
            '凶': '运势不佳，诸事不顺，宜守不宜攻'
        }
    }
}


TERM_INDEX = {}


def _build_term_index():
    """构建术语索引，支持快速查询"""
    terms = {}
    
    for wx, info in WUXING_KNOWLEDGE.items():
        terms[wx] = {
            'category': '五行',
            'name': wx,
            'description': info['description'],
            'details': info
        }
    
    for shishen, info in SHISHEN_KNOWLEDGE.items():
        terms[shishen] = {
            'category': '十神',
            'name': shishen,
            'description': info['description'],
            'details': info
        }
    
    for tiangan, info in TIANGAN_DIZHI_KNOWLEDGE['tiangan'].items():
        terms[tiangan] = {
            'category': '天干',
            'name': tiangan,
            'description': info['meaning'],
            'details': info
        }
    
    for dizhi, info in TIANGAN_DIZHI_KNOWLEDGE['dizhi'].items():
        terms[dizhi] = {
            'category': '地支',
            'name': dizhi,
            'description': info['meaning'],
            'details': info
        }
    
    for shen, info in SHIER_CHANGSHENG_KNOWLEDGE.items():
        terms[shen] = {
            'category': '十二长生',
            'name': shen,
            'description': info['meaning'],
            'details': info
        }
    
    for bagua_num, info in BAGUA.items():
        terms[info['name']] = {
            'category': '八卦',
            'name': info['name'],
            'description': info['description'],
            'details': info
        }
    
    return terms


TERM_INDEX = _build_term_index()


class KnowledgeBase:
    """命理知识库 - 提供结构化的命理知识查询和检索"""
    
    def __init__(self):
        self.wuxing = WUXING_KNOWLEDGE
        self.shishen = SHISHEN_KNOWLEDGE
        self.tiangan_dizhi = TIANGAN_DIZHI_KNOWLEDGE
        self.shier_changsheng = SHIER_CHANGSHENG_KNOWLEDGE
        self.wuxing_relations = WUXING_RELATIONS
        self.meihua = MEIHUA_KNOWLEDGE
        self.bagua = BAGUA
        self.hexagrams = HEXAGRAMS
        self.term_index = TERM_INDEX
    
    def search_term(self, keyword):
        """
        搜索术语，支持模糊匹配
        返回匹配的术语列表
        """
        results = []
        keyword = keyword.strip()
        
        if not keyword:
            return results
        
        if keyword in self.term_index:
            results.append(self.term_index[keyword])
            return results
        
        for term, info in self.term_index.items():
            if keyword in term or keyword in info['description']:
                results.append(info)
        
        return results
    
    def get_category_terms(self, category):
        """
        获取指定分类的所有术语
        分类：五行、十神、天干、地支、十二长生、八卦
        """
        results = []
        for term, info in self.term_index.items():
            if info['category'] == category:
                results.append(info)
        return results
    
    def get_wuxing_info(self, wuxing_name):
        """获取五行详细信息"""
        return self.wuxing.get(wuxing_name, {})
    
    def get_shishen_info(self, shishen_name):
        """获取十神详细信息"""
        return self.shishen.get(shishen_name, {})
    
    def get_shier_changsheng_info(self, shen_name):
        """获取十二长生详细信息"""
        return self.shier_changsheng.get(shen_name, {})
    
    def get_bagua_info(self, num_or_name):
        """获取八卦信息，支持按数字或名称查询"""
        if isinstance(num_or_name, int):
            return self.bagua.get(num_or_name, {})
        else:
            for num, info in self.bagua.items():
                if info['name'] == num_or_name:
                    info_copy = info.copy()
                    info_copy['num'] = num
                    return info_copy
            return {}
    
    def get_hexagram_info(self, upper_num, lower_num):
        """获取64卦信息"""
        key = (upper_num, lower_num)
        return self.hexagrams.get(key, {})
    
    def get_meihua_knowledge(self, section=None):
        """获取梅花易数相关知识"""
        if section:
            return self.meihua.get(section, {})
        return self.meihua
    
    def build_bazi_knowledge_context(self, bazi_data):
        """
        构建八字分析的知识上下文
        为AI分析提供结构化的命理知识背景
        """
        context_parts = []
        context_parts.append("=== 命理知识库 ===")
        
        rizhu = bazi_data.get('rizhu', '')
        if rizhu:
            rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
            wx_info = self.get_wuxing_info(rizhu_wx)
            if wx_info:
                context_parts.append(f"\n【日主五行：{rizhu_wx}】")
                context_parts.append(f"特性：{wx_info.get('description', '')}")
                context_parts.append(f"正面特质：{', '.join(wx_info.get('positive_traits', []))}")
                context_parts.append(f"负面特质：{', '.join(wx_info.get('negative_traits', []))}")
                context_parts.append(f"适合职业：{wx_info.get('career', '')}")
                context_parts.append(f"健康建议：{wx_info.get('health_advice', '')}")
        
        wuxing_result = bazi_data.get('wuxing', {})
        if wuxing_result:
            context_parts.append(f"\n【五行生克关系】")
            context_parts.append(f"相生：{WUXING_RELATIONS['sheng']['description']}")
            context_parts.append(f"相克：{WUXING_RELATIONS['ke']['description']}")
        
        return '\n'.join(context_parts)
    
    def build_meihua_knowledge_context(self, hexagram_data):
        """
        构建梅花易数分析的知识上下文
        为AI分析提供结构化的卦象知识背景
        """
        context_parts = []
        context_parts.append("=== 梅花易数知识库 ===")
        
        base_info = hexagram_data.get('base', {})
        base_name = base_info.get('name', '')
        if base_name:
            context_parts.append(f"\n【本卦：{base_name}】")
            context_parts.append(f"卦辞：{base_info.get('gua_ci', '')}")
            context_parts.append(f"释义：{base_info.get('description', '')}")
            
            changing_yao = base_info.get('changing_yao', 0)
            if changing_yao:
                context_parts.append(f"动爻：第{changing_yao}爻 - {base_info.get('changing_yao_name', '')}")
                context_parts.append(f"爻辞：{base_info.get('changing_yao_text', '')}")
                context_parts.append(f"释义：{base_info.get('changing_yao_meaning', '')}")
        
        bian_info = hexagram_data.get('bian', {})
        bian_name = bian_info.get('name', '')
        if bian_name:
            context_parts.append(f"\n【变卦：{bian_name}】")
            context_parts.append(f"释义：{bian_info.get('description', '')}")
        
        context_parts.append(f"\n【解卦原则】")
        for rule in MEIHUA_KNOWLEDGE['interpretation']['basic_rules']:
            context_parts.append(f"- {rule}")
        
        return '\n'.join(context_parts)
    
    def get_all_categories(self):
        """获取所有术语分类"""
        categories = set()
        for info in self.term_index.values():
            categories.add(info['category'])
        return sorted(list(categories))
