from core.baazi import TIAN_GAN, DI_ZHI
from core.wuxing import TIAN_GAN_WUXING, DI_ZHI_WUXING, DI_ZHI_HIDDEN_GAN

NAYIN_MAP = {
    '甲子': ('海中金', '金'), '乙丑': ('海中金', '金'),
    '丙寅': ('炉中火', '火'), '丁卯': ('炉中火', '火'),
    '戊辰': ('大林木', '木'), '己巳': ('大林木', '木'),
    '庚午': ('路旁土', '土'), '辛未': ('路旁土', '土'),
    '壬申': ('剑锋金', '金'), '癸酉': ('剑锋金', '金'),
    '甲戌': ('山头火', '火'), '乙亥': ('山头火', '火'),
    '丙子': ('涧下水', '水'), '丁丑': ('涧下水', '水'),
    '戊寅': ('城头土', '土'), '己卯': ('城头土', '土'),
    '庚辰': ('白蜡金', '金'), '辛巳': ('白蜡金', '金'),
    '壬午': ('杨柳木', '木'), '癸未': ('杨柳木', '木'),
    '甲申': ('泉中水', '水'), '乙酉': ('泉中水', '水'),
    '丙戌': ('屋上土', '土'), '丁亥': ('屋上土', '土'),
    '戊子': ('霹雳火', '火'), '己丑': ('霹雳火', '火'),
    '庚寅': ('松柏木', '木'), '辛卯': ('松柏木', '木'),
    '壬辰': ('长流水', '水'), '癸巳': ('长流水', '水'),
    '甲午': ('沙中金', '金'), '乙未': ('沙中金', '金'),
    '丙申': ('山下火', '火'), '丁酉': ('山下火', '火'),
    '戊戌': ('平地木', '木'), '己亥': ('平地木', '木'),
    '庚子': ('壁上土', '土'), '辛丑': ('壁上土', '土'),
    '壬寅': ('金箔金', '金'), '癸卯': ('金箔金', '金'),
    '甲辰': ('覆灯火', '火'), '乙巳': ('覆灯火', '火'),
    '丙午': ('天河水', '水'), '丁未': ('天河水', '水'),
    '戊申': ('大驿土', '土'), '己酉': ('大驿土', '土'),
    '庚戌': ('钗钏金', '金'), '辛亥': ('钗钏金', '金'),
    '壬子': ('桑柘木', '木'), '癸丑': ('桑柘木', '木'),
    '甲寅': ('大溪水', '水'), '乙卯': ('大溪水', '水'),
    '丙辰': ('沙中土', '土'), '丁巳': ('沙中土', '土'),
    '戊午': ('天上火', '火'), '己未': ('天上火', '火'),
    '庚申': ('石榴木', '木'), '辛酉': ('石榴木', '木'),
    '壬戌': ('大海水', '水'), '癸亥': ('大海水', '水')
}

SHEN_SHA = {
    '天德': {
        'type': 'positive',
        'description': '天德贵人，主吉祥、逢凶化吉，一生少病灾',
        'detailed': '天德贵人是四柱神煞中最吉祥的神煞之一。天德者，谓合天德之正气，主人慈祥和蔼，聪明正直，一生少病灾，遇难呈祥，逢凶化吉。命中有天德贵人者，多为善良之人，容易得到他人帮助，一生平安顺遂。',
        'locations': ['月柱'],
        'conditions': {'丙': ['寅'], '丁': ['亥'], '戊': ['寅'], '己': ['申'], '庚': ['亥'], '辛': ['巳'], '壬': ['寅'], '癸': ['申']}
    },
    '月德': {
        'type': 'positive',
        'description': '月德贵人，主仁慈、聪明、福寿，一生平安',
        'detailed': '月德贵人与天德贵人并称"二德"，同为吉祥神煞。月德者，谓合月德之正气，主人仁慈敦厚，聪明好学，福寿双全，一生平安。命中有月德贵人者，性情温和，乐于助人，容易得到长辈和上级的提携。',
        'locations': ['月柱'],
        'conditions': {'丙': ['甲'], '丁': ['壬'], '戊': ['丙'], '己': ['甲'], '庚': ['戊'], '辛': ['丙'], '壬': ['庚'], '癸': ['戊']}
    },
    '文昌': {
        'type': 'positive',
        'description': '文昌星，主学业、才华、聪明过人',
        'detailed': '文昌星主学业、文章、才华。命中有文昌星者，聪明伶俐，记忆力强，学习能力出众，容易在学业上取得优异成绩，适合从事学术研究、教育、文化艺术等工作。文昌星入命，主其人多才多艺，富有创造力。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['巳'], '乙': ['午'], '丙': ['申'], '丁': ['酉'], '戊': ['申'], '己': ['酉'], '庚': ['亥'], '辛': ['子'], '壬': ['寅'], '癸': ['卯']}
    },
    '桃花': {
        'type': 'neutral',
        'description': '桃花星，主人缘、异性缘、社交能力强',
        'detailed': '桃花星主异性缘、人际关系、社交能力。命中有桃花星者，相貌俊秀，气质高雅，善于交际，异性缘旺盛。桃花星也主艺术才华，适合从事演艺、娱乐、公关等行业。但桃花过旺也可能带来感情困扰，需注意把握分寸。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'子': ['卯'], '午': ['酉'], '卯': ['子'], '酉': ['午']}
    },
    '驿马': {
        'type': 'neutral',
        'description': '驿马星，主变动、旅行、迁移',
        'detailed': '驿马星主变动、旅行、迁移、外出。命中有驿马星者，一生多动少静，喜欢旅行和探索，适合从事需要经常出差或外出的工作，如销售、物流、旅游等行业。驿马星也主机遇，往往在变动中获得发展机会。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'申': ['寅'], '寅': ['申'], '巳': ['亥'], '亥': ['巳']}
    },
    '华盖': {
        'type': 'neutral',
        'description': '华盖星，主艺术、才华、孤独',
        'detailed': '华盖星主艺术、才华、宗教、哲学。命中有华盖星者，富有艺术天赋，对传统文化、宗教哲学有浓厚兴趣，容易在这些领域取得成就。但华盖星也主孤独，其人往往性格内向，喜欢独处，有时会显得孤僻不合群。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'寅': ['戌'], '戌': ['寅'], '辰': ['丑'], '丑': ['辰']}
    },
    '将星': {
        'type': 'positive',
        'description': '将星，主权威、领导力、事业有成',
        'detailed': '将星主权威、领导力、组织能力。命中有将星者，具有领导才能，善于组织和指挥他人，容易成为团队中的核心人物或领导者。将星入命，主其人在事业上容易取得成就，适合从事管理、军事、政治等工作。',
        'locations': ['月柱', '时柱'],
        'conditions': {'子': ['午'], '午': ['子'], '卯': ['酉'], '酉': ['卯']}
    },
    '天乙': {
        'type': 'positive',
        'description': '天乙贵人，主贵人相助、逢凶化吉',
        'detailed': '天乙贵人是四柱神煞中最重要的贵人星。天乙者，乃天上之神，在紫微垣、阊阖门外，与太乙并列，事天皇大帝，下游三辰，家在己丑斗牛之次，出乎己未井鬼之舍，执玉衡较量天人之事，名曰天乙也。命中有天乙贵人者，一生多得贵人相助，逢凶化吉，遇难呈祥。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'], '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'], '庚': ['寅', '午'], '辛': ['寅', '午'], '壬': ['巳', '卯'], '癸': ['巳', '卯']}
    },
    '劫煞': {
        'type': 'negative',
        'description': '劫煞，主是非、争斗、意外之灾',
        'detailed': '劫煞主是非、争斗、抢劫、意外之灾。命中有劫煞者，性格刚烈，容易冲动，好勇斗狠，容易与人发生争执和冲突。劫煞也主财物损失，需注意防范盗窃、抢劫等意外事件。但劫煞也主勇敢果断，若能善用其力，也可在竞争中取得优势。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'申': ['巳'], '巳': ['申'], '寅': ['亥'], '亥': ['寅']}
    },
    '亡神': {
        'type': 'negative',
        'description': '亡神，主官非、病灾、精神困扰',
        'detailed': '亡神主官非、病灾、精神困扰。命中有亡神者，容易遇到官司诉讼，身体方面容易有慢性疾病，精神上容易焦虑不安。亡神也主阴谋、暗害，需注意防范小人陷害。但亡神也主聪明才智，若能修身养性，也可将其转化为智慧之力。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'寅': ['巳'], '巳': ['申'], '申': ['亥'], '亥': ['寅']}
    },
    '孤辰': {
        'type': 'negative',
        'description': '孤辰，主孤独、寡合、婚姻不顺',
        'detailed': '孤辰主孤独、寡合、婚姻不顺。命中有孤辰者，性格孤僻，不善于与人交往，朋友稀少，婚姻方面容易晚婚或婚姻不顺。孤辰也主内心空虚，容易感到孤独寂寞。但孤辰也主独立自强，其人往往能够独自完成事业，不需要依赖他人。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'寅': ['巳'], '巳': ['申'], '申': ['亥'], '亥': ['寅']}
    },
    '寡宿': {
        'type': 'negative',
        'description': '寡宿，主孤独、守寡、人际关系淡薄',
        'detailed': '寡宿主孤独、守寡、人际关系淡薄。命中有寡宿者，女性容易守寡或婚姻不幸，男性则容易孤独终老。寡宿也主人际关系淡薄，朋友不多，社交圈子狭窄。但寡宿也主清净无为，其人往往能够专注于自己的事业，不受外界干扰。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'辰': ['丑'], '丑': ['辰'], '戌': ['未'], '未': ['戌']}
    },
    '福星': {
        'type': 'positive',
        'description': '福星贵人，主福禄、长寿、吉祥',
        'detailed': '福星贵人主福禄、长寿、吉祥。命中有福星贵人者，一生福气深厚，衣食无忧，寿命较长。福星贵人也主善良仁慈，乐于助人，容易得到他人的尊敬和爱戴。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['子'], '乙': ['丑'], '丙': ['寅'], '丁': ['卯'], '戊': ['辰'], '己': ['巳'], '庚': ['午'], '辛': ['未'], '壬': ['申'], '癸': ['酉']}
    },
    '金舆': {
        'type': 'positive',
        'description': '金舆贵人，主财富、地位、车房',
        'detailed': '金舆贵人主财富、地位、车房。命中有金舆贵人者，容易拥有车辆、房产等资产，财运较好，社会地位较高。金舆贵人也主出行便利，一生出行多有车辆代步。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['辰'], '乙': ['巳'], '丙': ['午'], '丁': ['未'], '戊': ['申'], '己': ['酉'], '庚': ['戌'], '辛': ['亥'], '壬': ['子'], '癸': ['丑']}
    },
    '学堂': {
        'type': 'positive',
        'description': '学堂星，主学业、教育、知识',
        'detailed': '学堂星主学业、教育、知识。命中有学堂星者，学习能力强，学业成绩优异，适合从事教育、学术研究等工作。学堂星也主智慧，其人往往聪明好学，知识渊博。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['亥'], '乙': ['戌'], '丙': ['寅'], '丁': ['卯'], '戊': ['巳'], '己': ['午'], '庚': ['申'], '辛': ['酉'], '壬': ['子'], '癸': ['丑']}
    },
    '词馆': {
        'type': 'positive',
        'description': '词馆星，主文辞、才华、写作',
        'detailed': '词馆星主文辞、才华、写作。命中有词馆星者，善于文辞表达，写作能力强，适合从事文学创作、新闻媒体、文案策划等工作。词馆星也主口才，其人往往能言善辩，表达能力出众。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['寅'], '乙': ['卯'], '丙': ['巳'], '丁': ['午'], '戊': ['申'], '己': ['酉'], '庚': ['亥'], '辛': ['子'], '壬': ['辰'], '癸': ['丑']}
    },
    '太极贵人': {
        'type': 'positive',
        'description': '太极贵人，主智慧、神秘、悟性',
        'detailed': '太极贵人主智慧、神秘、悟性。命中有太极贵人者，对哲学、宗教、神秘学等有浓厚兴趣，悟性较高，容易理解深奥的道理。太极贵人也主创造力，其人往往能够提出独特的见解和想法。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['子'], '乙': ['午'], '丙': ['卯'], '丁': ['酉'], '戊': ['辰'], '己': ['戌'], '庚': ['巳'], '辛': ['亥'], '壬': ['寅'], '癸': ['申']}
    },
    '天医': {
        'type': 'positive',
        'description': '天医星，主健康、医药、治愈',
        'detailed': '天医星主健康、医药、治愈。命中有天医星者，对医学、养生等有浓厚兴趣，适合从事医疗、养生、保健等行业。天医星也主身体健康，其人往往较少生病，即使生病也容易痊愈。',
        'locations': ['月柱', '时柱'],
        'conditions': {'甲': ['卯'], '乙': ['寅'], '丙': ['子'], '丁': ['亥'], '戊': ['丑'], '己': ['子'], '庚': ['酉'], '辛': ['申'], '壬': ['午'], '癸': ['巳']}
    },
    '红艳': {
        'type': 'neutral',
        'description': '红艳煞，主桃花、感情、魅力',
        'detailed': '红艳煞主桃花、感情、魅力。命中有红艳煞者，相貌出众，气质迷人，异性缘非常旺盛。红艳煞也主感情丰富，其人往往容易陷入感情纠葛，需注意把握感情分寸。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'甲': ['午'], '乙': ['巳'], '丙': ['寅'], '丁': ['卯'], '戊': ['辰'], '己': ['丑'], '庚': ['子'], '辛': ['亥'], '壬': ['戌'], '癸': ['酉']}
    },
    '勾绞': {
        'type': 'negative',
        'description': '勾绞煞，主是非、纠缠、牵连',
        'detailed': '勾绞煞主是非、纠缠、牵连。命中有勾绞煞者，容易卷入他人的是非纠纷中，即使与自己无关也可能被牵连。勾绞煞也主人际关系复杂，容易与人发生矛盾和冲突。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'子': ['卯'], '卯': ['子'], '丑': ['辰'], '辰': ['丑'], '寅': ['巳'], '巳': ['寅'], '卯': ['午'], '午': ['卯'], '辰': ['未'], '未': ['辰'], '巳': ['申'], '申': ['巳'], '午': ['酉'], '酉': ['午'], '未': ['戌'], '戌': ['未'], '申': ['亥'], '亥': ['申'], '酉': ['子'], '子': ['酉'], '戌': ['丑'], '丑': ['戌'], '亥': ['寅'], '寅': ['亥']}
    },
    '绞煞': {
        'type': 'negative',
        'description': '绞煞，主纠缠、束缚、困扰',
        'detailed': '绞煞主纠缠、束缚、困扰。命中有绞煞者，容易被事情或人际关系所束缚，难以摆脱困扰。绞煞也主精神压力，其人往往感到身心疲惫，难以放松。',
        'locations': ['年柱', '月柱', '日柱', '时柱'],
        'conditions': {'子': ['酉'], '酉': ['子'], '丑': ['戌'], '戌': ['丑'], '寅': ['亥'], '亥': ['寅'], '卯': ['子'], '子': ['卯'], '辰': ['丑'], '丑': ['辰'], '巳': ['寅'], '寅': ['巳'], '午': ['卯'], '卯': ['午'], '未': ['辰'], '辰': ['未'], '申': ['巳'], '巳': ['申'], '酉': ['午'], '午': ['酉'], '戌': ['未'], '未': ['戌'], '亥': ['申'], '申': ['亥']}
    }
}

MAIN_STARS = {
    '紫微': {
        'characteristics': '紫微为帝星，主尊贵、权威、领导力',
        'influence': '具有领导才能，容易成为领袖人物，一生运势较强',
        'element': '土'
    },
    '天府': {
        'characteristics': '天府为财库，主财富、稳重、保守',
        'influence': '财运较好，善于理财，但有时过于保守',
        'element': '土'
    },
    '太阳': {
        'characteristics': '太阳主光明、热情、正直',
        'influence': '性格开朗，乐于助人，事业上容易得到他人帮助',
        'element': '火'
    },
    '太阴': {
        'characteristics': '太阴主温柔、细腻、智慧',
        'influence': '心思细腻，富有艺术才华，适合从事文艺工作',
        'element': '水'
    },
    '贪狼': {
        'characteristics': '贪狼主欲望、才华、交际',
        'influence': '多才多艺，社交能力强，但需注意节制欲望',
        'element': '木'
    },
    '巨门': {
        'characteristics': '巨门主口才、是非、谋略',
        'influence': '善于言辞，适合从事律师、教师等职业',
        'element': '水'
    },
    '天相': {
        'characteristics': '天相主相貌、辅佐、正直',
        'influence': '相貌端正，善于辅佐他人，适合做幕僚',
        'element': '水'
    },
    '天梁': {
        'characteristics': '天梁主荫庇、延寿、清高',
        'influence': '一生多福气，容易得到长辈相助',
        'element': '土'
    },
    '七杀': {
        'characteristics': '七杀主刚强、果断、权威',
        'influence': '性格刚强，做事果断，但需注意脾气',
        'element': '金'
    },
    '破军': {
        'characteristics': '破军主变革、开创、破坏',
        'influence': '具有开创精神，但有时过于冲动',
        'element': '水'
    },
    '廉贞': {
        'characteristics': '廉贞主清廉、固执、桃花',
        'influence': '为人正直，但有时过于固执',
        'element': '火'
    },
    '武曲': {
        'characteristics': '武曲主财富、武勇、果断',
        'influence': '财运旺盛，适合经商或从军',
        'element': '金'
    }
}

TIAN_GAN_RELATION = {
    '甲': {'生': '丙', '克': '戊', '被生': '壬', '被克': '庚'},
    '乙': {'生': '丁', '克': '己', '被生': '癸', '被克': '辛'},
    '丙': {'生': '戊', '克': '庚', '被生': '甲', '被克': '壬'},
    '丁': {'生': '己', '克': '辛', '被生': '乙', '被克': '癸'},
    '戊': {'生': '庚', '克': '壬', '被生': '丙', '被克': '甲'},
    '己': {'生': '辛', '克': '癸', '被生': '丁', '被克': '乙'},
    '庚': {'生': '壬', '克': '甲', '被生': '戊', '被克': '丙'},
    '辛': {'生': '癸', '克': '乙', '被生': '己', '被克': '丁'},
    '壬': {'生': '甲', '克': '丙', '被生': '庚', '被克': '戊'},
    '癸': {'生': '乙', '克': '丁', '被生': '辛', '被克': '己'}
}

RELATION_DETAIL = {
    '生': {
        'description': '相生关系，主帮助、支持、生扶',
        'influence': '相生为吉，主得到他人帮助，事情顺利发展'
    },
    '克': {
        'description': '相克关系，主制约、管制、压制',
        'influence': '相克为凶，主压力、阻碍、冲突'
    },
    '被生': {
        'description': '被生关系，主受生扶、得滋养',
        'influence': '被生为吉，主得到贵人相助，受益于他人'
    },
    '被克': {
        'description': '被克关系，主受制约、受压制',
        'influence': '被克为凶，主遭遇压制，诸事不顺'
    },
    '冲': {
        'description': '相冲关系，主对立、冲突、变动',
        'influence': '相冲为凶，主变动大、冲突多、人际关系紧张'
    },
    '合': {
        'description': '相合关系，主和谐、合作、吸引',
        'influence': '相合为吉，主人际关系好、合作顺利、感情融洽'
    },
    '害': {
        'description': '相害关系，主伤害、陷害、暗中破坏',
        'influence': '相害为凶，主小人陷害、暗中伤害、是非纠纷'
    },
    '刑': {
        'description': '相刑关系，主刑罚、伤害、疾病',
        'influence': '相刑为凶，主官司诉讼、疾病缠身、意外伤害'
    }
}

DI_ZHI_RELATION = {
    '子': {'冲': '午', '合': '丑', '害': '未', '刑': '卯'},
    '丑': {'冲': '未', '合': '子', '害': '午', '刑': '戌'},
    '寅': {'冲': '申', '合': '亥', '害': '巳', '刑': '巳'},
    '卯': {'冲': '酉', '合': '戌', '害': '辰', '刑': '子'},
    '辰': {'冲': '戌', '合': '酉', '害': '卯', '刑': '辰'},
    '巳': {'冲': '亥', '合': '申', '害': '寅', '刑': '寅'},
    '午': {'冲': '子', '合': '未', '害': '丑', '刑': '午'},
    '未': {'冲': '丑', '合': '午', '害': '子', '刑': '丑'},
    '申': {'冲': '寅', '合': '巳', '害': '亥', '刑': '申'},
    '酉': {'冲': '卯', '合': '辰', '害': '戌', '刑': '酉'},
    '戌': {'冲': '辰', '合': '卯', '害': '酉', '刑': '未'},
    '亥': {'冲': '巳', '合': '寅', '害': '申', '刑': '亥'}
}

KONG_WANG_TABLE = {
    '甲子': ['戌', '亥'], '乙丑': ['戌', '亥'], '丙寅': ['申', '酉'], '丁卯': ['申', '酉'],
    '戊辰': ['午', '未'], '己巳': ['午', '未'], '庚午': ['辰', '巳'], '辛未': ['辰', '巳'],
    '壬申': ['寅', '卯'], '癸酉': ['寅', '卯'], '甲戌': ['子', '丑'], '乙亥': ['子', '丑'],
    '丙子': ['戌', '亥'], '丁丑': ['戌', '亥'], '戊寅': ['申', '酉'], '己卯': ['申', '酉'],
    '庚辰': ['午', '未'], '辛巳': ['午', '未'], '壬午': ['辰', '巳'], '癸未': ['辰', '巳'],
    '甲申': ['寅', '卯'], '乙酉': ['寅', '卯'], '丙戌': ['子', '丑'], '丁亥': ['子', '丑'],
    '戊子': ['戌', '亥'], '己丑': ['戌', '亥'], '庚寅': ['申', '酉'], '辛卯': ['申', '酉'],
    '壬辰': ['午', '未'], '癸巳': ['午', '未'], '甲午': ['辰', '巳'], '乙未': ['辰', '巳'],
    '丙申': ['寅', '卯'], '丁酉': ['寅', '卯'], '戊戌': ['子', '丑'], '己亥': ['子', '丑'],
    '庚子': ['戌', '亥'], '辛丑': ['戌', '亥'], '壬寅': ['申', '酉'], '癸卯': ['申', '酉'],
    '甲辰': ['午', '未'], '乙巳': ['午', '未'], '丙午': ['辰', '巳'], '丁未': ['辰', '巳'],
    '戊申': ['寅', '卯'], '己酉': ['寅', '卯'], '庚戌': ['子', '丑'], '辛亥': ['子', '丑'],
    '壬子': ['戌', '亥'], '癸丑': ['戌', '亥'], '甲寅': ['申', '酉'], '乙卯': ['申', '酉'],
    '丙辰': ['午', '未'], '丁巳': ['午', '未'], '戊午': ['辰', '巳'], '己未': ['辰', '巳'],
    '庚申': ['寅', '卯'], '辛酉': ['寅', '卯'], '壬戌': ['子', '丑'], '癸亥': ['子', '丑']
}

class MingLiAnalyzer:
    def __init__(self):
        self.tian_gan_map = {tg: i for i, tg in enumerate(TIAN_GAN)}
        self.di_zhi_map = {dz: i for i, dz in enumerate(DI_ZHI)}

    def analyze_hidden_stems(self, bazhi):
        result = []
        pillars = ['年柱', '月柱', '日柱', '时柱']
        
        for i, pillar in enumerate(pillars):
            ganzhi = bazhi['四柱'][i]
            zhi = ganzhi[1]
            hidden_gans = DI_ZHI_HIDDEN_GAN.get(zhi, [])
            
            if hidden_gans:
                hidden_info = []
                for hg in hidden_gans:
                    wx = TIAN_GAN_WUXING.get(hg, '')
                    hidden_info.append(f"{hg}({wx})")
                
                result.append({
                    'pillar': pillar,
                    'ganzhi': ganzhi,
                    'hidden_stems': hidden_gans,
                    'description': f'{pillar}地支{zhi}藏干：{"、".join(hidden_info)}'
                })
        
        return {'hidden_stems': result}

    def analyze_nayin(self, bazhi):
        result = {}
        pillars = ['year', 'month', 'day', 'hour']
        pillar_names = ['年柱', '月柱', '日柱', '时柱']
        
        for i, pillar in enumerate(pillars):
            ganzhi = bazhi[pillar]
            nayin_info = NAYIN_MAP.get(ganzhi, ('', ''))
            
            result[pillar] = {
                'pillar': pillar_names[i],
                'ganzhi': ganzhi,
                'nayin': nayin_info[0],
                'element': nayin_info[1],
                'description': f'{pillar_names[i]}{ganzhi}，纳音{nayin_info[0]}，五行属{nayin_info[1]}'
            }
        
        return result

    def analyze_shensha(self, bazhi):
        positive = []
        negative = []
        neutral = []
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for sha_name, sha_info in SHEN_SHA.items():
            conditions = sha_info['conditions']
            sha_type = sha_info.get('type', 'neutral')
            
            for i, ganzhi in enumerate(ganzhi_list):
                gan = ganzhi[0]
                zhi = ganzhi[1]
                
                if gan in conditions:
                    if zhi in conditions[gan]:
                        entry = {
                            'name': sha_name,
                            'type': sha_type,
                            'location': pillars[i],
                            'ganzhi': ganzhi,
                            'description': sha_info['description'],
                            'detailed': sha_info.get('detailed', '')
                        }
                        
                        if sha_type == 'positive':
                            positive.append(entry)
                        elif sha_type == 'negative':
                            negative.append(entry)
                        else:
                            neutral.append(entry)
        
        return {'positive': positive, 'negative': negative, 'neutral': neutral}

    def analyze_main_stars(self, bazhi):
        rizhu = bazhi['rizhu']
        rizhu_wx = TIAN_GAN_WUXING.get(rizhu, '')
        
        stars = []
        for star_name, star_info in MAIN_STARS.items():
            if star_info['element'] == rizhu_wx:
                stars.append({
                    'name': star_name,
                    'element': star_info['element'],
                    'characteristics': star_info['characteristics'],
                    'influence': star_info['influence']
                })
        
        if not stars:
            star_list = list(MAIN_STARS.keys())[:3]
            for star_name in star_list:
                stars.append({
                    'name': star_name,
                    'element': MAIN_STARS[star_name]['element'],
                    'characteristics': MAIN_STARS[star_name]['characteristics'],
                    'influence': MAIN_STARS[star_name]['influence']
                })
        
        return {'stars': stars}

    def analyze_ganzhi_relations(self, bazhi):
        gan_relations = []
        zhi_relations = []
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for i, ganzhi1 in enumerate(ganzhi_list):
            for j, ganzhi2 in enumerate(ganzhi_list):
                if i >= j:
                    continue
                
                gan1, zhi1 = ganzhi1[0], ganzhi1[1]
                gan2, zhi2 = ganzhi2[0], ganzhi2[1]
                
                if gan1 in TIAN_GAN_RELATION:
                    rel = TIAN_GAN_RELATION[gan1]
                    if gan2 == rel['生']:
                        detail = RELATION_DETAIL.get('生', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '生',
                            'description': f'{gan1}生{gan2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif gan2 == rel['克']:
                        detail = RELATION_DETAIL.get('克', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '克',
                            'description': f'{gan1}克{gan2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif gan2 == rel['被生']:
                        detail = RELATION_DETAIL.get('被生', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '被生',
                            'description': f'{gan1}被{gan2}生',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif gan2 == rel['被克']:
                        detail = RELATION_DETAIL.get('被克', {})
                        gan_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'gan1': gan1,
                            'gan2': gan2,
                            'relation': '被克',
                            'description': f'{gan1}被{gan2}克',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                
                if zhi1 in DI_ZHI_RELATION:
                    rel = DI_ZHI_RELATION[zhi1]
                    if zhi2 == rel['冲']:
                        detail = RELATION_DETAIL.get('冲', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '冲',
                            'description': f'{zhi1}冲{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif zhi2 == rel['合']:
                        detail = RELATION_DETAIL.get('合', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '合',
                            'description': f'{zhi1}合{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif zhi2 == rel['害']:
                        detail = RELATION_DETAIL.get('害', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '害',
                            'description': f'{zhi1}害{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
                    elif zhi2 == rel['刑']:
                        detail = RELATION_DETAIL.get('刑', {})
                        zhi_relations.append({
                            'pillar1': pillars[i],
                            'pillar2': pillars[j],
                            'zhi1': zhi1,
                            'zhi2': zhi2,
                            'relation': '刑',
                            'description': f'{zhi1}刑{zhi2}',
                            'detail_description': detail.get('description', ''),
                            'influence': detail.get('influence', '')
                        })
        
        return {
            'gan_relations': gan_relations,
            'zhi_relations': zhi_relations
        }

    def analyze_self_seat(self, bazhi):
        day_ganzhi = bazhi['day']
        day_gan = day_ganzhi[0]
        day_zhi = day_ganzhi[1]
        
        day_gan_wx = TIAN_GAN_WUXING.get(day_gan, '')
        day_zhi_wx = DI_ZHI_WUXING.get(day_zhi, '')
        
        relationship = ''
        if day_gan_wx == day_zhi_wx:
            relationship = '比和'
        elif self._is_wuxing_relationship(day_gan_wx, day_zhi_wx, '生'):
            relationship = '生日'
        elif self._is_wuxing_relationship(day_zhi_wx, day_gan_wx, '生'):
            relationship = '日生'
        elif self._is_wuxing_relationship(day_gan_wx, day_zhi_wx, '克'):
            relationship = '日克'
        elif self._is_wuxing_relationship(day_zhi_wx, day_gan_wx, '克'):
            relationship = '克日'
        
        hidden_gans = DI_ZHI_HIDDEN_GAN.get(day_zhi, [])
        
        descriptions = []
        descriptions.append(f'日主{day_gan}({day_gan_wx})，自坐{day_zhi}({day_zhi_wx})')
        descriptions.append(f'日支与日主关系：{relationship}')
        
        if hidden_gans:
            hidden_desc = []
            for hg in hidden_gans:
                hg_wx = TIAN_GAN_WUXING.get(hg, '')
                hidden_desc.append(f'{hg}({hg_wx})')
            descriptions.append(f'日支藏干：{"、".join(hidden_desc)}')
        
        return {
            'day_gan': day_gan,
            'day_zhi': day_zhi,
            'relationship': relationship,
            'hidden_stems': hidden_gans,
            'description': '；'.join(descriptions)
        }

    def _is_wuxing_relationship(self, wx1, wx2, rel_type):
        wuxing_order = ['木', '火', '土', '金', '水']
        if wx1 not in wuxing_order or wx2 not in wuxing_order:
            return False
        
        idx1 = wuxing_order.index(wx1)
        idx2 = wuxing_order.index(wx2)
        
        if rel_type == '生':
            return (idx1 + 1) % 5 == idx2
        elif rel_type == '克':
            return (idx1 + 2) % 5 == idx2
        return False

    def analyze_kongwang(self, bazhi):
        year_ganzhi = bazhi['year']
        day_ganzhi = bazhi['day']
        
        year_kongwang = KONG_WANG_TABLE.get(year_ganzhi, [])
        day_kongwang = KONG_WANG_TABLE.get(day_ganzhi, [])
        
        affected_pillars = []
        pillars = ['年柱', '月柱', '日柱', '时柱']
        ganzhi_list = bazhi['四柱']
        
        for i, ganzhi in enumerate(ganzhi_list):
            zhi = ganzhi[1]
            if zhi in year_kongwang or zhi in day_kongwang:
                affected_pillars.append({
                    'pillar': pillars[i],
                    'ganzhi': ganzhi,
                    'kongwang_type': '年空' if zhi in year_kongwang else '日空'
                })
        
        return {
            'year_kongwang': year_kongwang,
            'day_kongwang': day_kongwang,
            'affected_pillars': affected_pillars,
            'description': f'年空：{year_kongwang}；日空：{day_kongwang}'
        }

    def analyze_all(self, bazhi):
        return {
            'hidden_stems': self.analyze_hidden_stems(bazhi),
            'nayin': self.analyze_nayin(bazhi),
            'shensha': self.analyze_shensha(bazhi),
            'main_stars': self.analyze_main_stars(bazhi),
            'ganzhi_relations': self.analyze_ganzhi_relations(bazhi),
            'self_seat': self.analyze_self_seat(bazhi),
            'kongwang': self.analyze_kongwang(bazhi)
        }