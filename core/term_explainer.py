"""
专业术语解释系统
提供命理术语的查询、分类浏览、关联推荐等功能
"""
from core.knowledge_base import KnowledgeBase


# ==================== 神煞术语详解 ====================
SHENSHA_TERMS = {
    '天德贵人': {
        'category': '神煞-吉神',
        'type': 'positive',
        'brief': '四柱神煞之一，主福德、贵人相助',
        'description': '天德贵人，又称天德星，是八字命理中最重要的吉神之一。天德象征上天的恩德与庇佑，命带天德之人，一生多遇贵人，逢凶化吉，遇难呈祥。',
        'check_method': '正月生者见丁，二月生者见申，三月生者见壬，四月生者见辛，五月生者见亥，六月生者见甲，七月生者见癸，八月生者见寅，九月生者见丙，十月生者见乙，十一月生者见巳，十二月生者见庚。',
        'influence': ['一生贵人多助', '逢凶化吉', '品德高尚', '人缘好', '易获成功'],
        'related_terms': ['月德贵人', '天乙贵人', '福星贵人']
    },
    '月德贵人': {
        'category': '神煞-吉神',
        'type': 'positive',
        'brief': '四柱神煞之一，主吉祥、消灾解厄',
        'description': '月德贵人是与天德贵人齐名的吉神，象征月亮的德泽。月德入命，主其人仁慈善良，聪明智慧，一生少灾少难，平安顺遂。',
        'check_method': '寅午戌月生者见丙，申子辰月生者见壬，亥卯未月生者见甲，巳酉丑月生者见庚。',
        'influence': ['仁慈善良', '聪明智慧', '消灾解厄', '平安顺遂', '人缘佳'],
        'related_terms': ['天德贵人', '天乙贵人', '三奇贵人']
    },
    '天乙贵人': {
        'category': '神煞-吉神',
        'type': 'positive',
        'brief': '最高贵的神煞，主贵人提携、事业有成',
        'description': '天乙贵人是八字神煞中最尊贵的吉神，被誉为"贵人之王"。天乙入命，主其人聪明智慧，人缘极佳，一生多遇贵人提携，事业易成。',
        'check_method': '甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎，此是贵人方。',
        'influence': ['聪明智慧', '贵人提携', '事业易成', '人缘极佳', '遇难呈祥'],
        'related_terms': ['天德贵人', '月德贵人', '文昌贵人']
    },
    '文昌贵人': {
        'category': '神煞-吉神',
        'type': 'positive',
        'brief': '主学业、文才、智慧的吉神',
        'description': '文昌贵人是主管学业、文才、智慧的吉神。命带文昌之人，聪明好学，文采出众，考试运佳，适合从事文化教育、科研等工作。',
        'check_method': '甲乙巳午报君知，丙戊申宫丁己鸡，庚猪辛鼠壬逢虎，癸人见兔入云梯。',
        'influence': ['聪明好学', '文采出众', '考试运佳', '学业有成', '适合文职'],
        'related_terms': ['学堂', '词馆', '食神']
    },
    '桃花': {
        'category': '神煞-中性',
        'type': 'neutral',
        'brief': '又称咸池，主姻缘、人缘、艺术天赋',
        'description': '桃花，又称咸池，是八字命理中最广为人知的神煞之一。桃花主姻缘、人缘、魅力和艺术天赋。桃花有正桃花和桃花煞之分。',
        'check_method': '寅午戌兔从茅里出，申子辰鸡叫乱人伦，亥卯未鼠子当头忌，巳酉丑跃马南方走。即：寅午戌日见卯，申子辰日见酉，亥卯未日见子，巳酉丑日见午。',
        'influence': ['人缘好', '有魅力', '艺术天赋', '异性缘佳', '感情丰富'],
        'related_terms': ['红鸾', '天喜', '咸池']
    },
    '驿马': {
        'category': '神煞-中性',
        'type': 'neutral',
        'brief': '主走动、出行、变动的神煞',
        'description': '驿马是主走动、出行、变动的神煞。命带驿马之人，一生多走动，适合外出发展、出差、旅游等。驿马逢冲则动，逢合则止。',
        'check_method': '申子辰马在寅，寅午戌马在申，巳酉丑马在亥，亥卯未马在巳。',
        'influence': ['好动', '适合外出发展', '多变', '有冲劲', '适合物流旅游'],
        'related_terms': ['迁移', '禄马', '羊刃']
    },
    '羊刃': {
        'category': '神煞-凶煞',
        'type': 'negative',
        'brief': '主刚强、暴戾、刑伤的凶煞',
        'description': '羊刃是八字命理中的凶煞之一，主刚强、暴戾、刑伤。羊刃旺而无制者，性格刚愎自用，易招灾祸。但羊刃也有积极一面，主魄力和执行力。',
        'check_method': '甲羊刃在卯，乙羊刃在寅，丙戊羊刃在午，丁己羊刃在巳，庚羊刃在酉，辛羊刃在申，壬羊刃在子，癸羊刃在亥。',
        'influence': ['性格刚强', '有魄力', '易招刑伤', '刚愎自用', '需防灾祸'],
        'related_terms': ['七杀', '劫财', '伤官']
    },
    '劫煞': {
        'category': '神煞-凶煞',
        'type': 'negative',
        'brief': '主灾祸、破财、是非的凶煞',
        'description': '劫煞是主灾祸、破财、是非的凶煞。命带劫煞之人，需谨防意外灾祸、破财纠纷。但劫煞若与吉神并见，反主有威严和决断力。',
        'check_method': '申子辰劫在巳，寅午戌劫在亥，亥卯未劫在申，巳酉丑劫在寅。',
        'influence': ['易招灾祸', '谨防破财', '是非纠纷', '需谨慎行事'],
        'related_terms': ['灾煞', '天煞', '地煞']
    },
    '空亡': {
        'category': '神煞-中性',
        'type': 'neutral',
        'brief': '主虚无、落空、不得力的神煞',
        'description': '空亡，又称旬空，是十天干配十二地支中，每旬少两地支，这两个地支即为空亡。空亡主虚无、落空，吉落空则不吉，凶落空则不凶。',
        'check_method': '甲子旬中戌亥空，甲戌旬中申酉空，甲申旬中午未空，甲午旬中辰巳空，甲辰旬中寅卯空，甲寅旬中子丑空。',
        'influence': ['吉空则减吉', '凶空则减凶', '虚空不实', '需防落空'],
        'related_terms': ['六甲旬空', '截路空亡']
    },
    '华盖': {
        'category': '神煞-中性',
        'type': 'neutral',
        'brief': '主艺术、玄学、孤独的神煞',
        'description': '华盖是主艺术、玄学、宗教和孤独的神煞。命带华盖之人，聪明好学，悟性高，对玄学、艺术、宗教有兴趣，但性格偏孤独。',
        'check_method': '寅午戌见戌，亥卯未见未，申子辰见辰，巳酉丑见丑。',
        'influence': ['聪明好学', '悟性高', '有艺术天赋', '喜玄学宗教', '性格偏孤'],
        'related_terms': ['偏印', '太极贵人', '学堂']
    },
    '将星': {
        'category': '神煞-吉神',
        'type': 'positive',
        'brief': '主领导才能、权威的吉神',
        'description': '将星是主领导才能和权威的吉神。命带将星之人，有组织领导能力，适合从政或从事管理工作，能服众，有威望。',
        'check_method': '寅午戌见午，巳酉丑见酉，申子辰见子，亥卯未见卯。',
        'influence': ['领导才能', '有权威', '适合管理', '能服众', '事业有成'],
        'related_terms': ['天乙贵人', '正官', '七杀']
    },
}


# ==================== 干支作用关系术语 ====================
GANZHI_RELATION_TERMS = {
    '天干五合': {
        'category': '干支关系-合',
        'type': 'neutral',
        'brief': '天干之间的五种合化关系',
        'description': '天干五合是指甲己合土、乙庚合金、丙辛合水、丁壬合木、戊癸合火。天干相合主和谐、合作、吸引，但合化为吉为凶需看具体情况。',
        'details': [
            '甲己合土：中正之合，主诚信稳重',
            '乙庚合金：仁义之合，主刚柔并济',
            '丙辛合水：威制之合，主威严果决',
            '丁壬合木：淫昵之合，主感情丰富',
            '戊癸合火：无情之合，主老少相配'
        ],
        'influence': ['主和谐合作', '人际关系好', '有吸引力', '需看化神吉凶'],
        'related_terms': ['地支六合', '地支三合', '地支三会']
    },
    '地支六合': {
        'category': '干支关系-合',
        'type': 'neutral',
        'brief': '地支之间的六种两两相合关系',
        'description': '地支六合是指子丑合土、寅亥合木、卯戌合火、辰酉合金、巳申合水、午未合土（或日月合）。地支六合主亲密、合作、姻缘。',
        'details': [
            '子丑合土：泥合，主纠结',
            '寅亥合木：仁合，主善良',
            '卯戌合火：合火，主热情',
            '辰酉合金：合金，主刚毅',
            '巳申合水：合水，主智慧',
            '午未合土：合土，主包容'
        ],
        'influence': ['主亲密合作', '姻缘标志', '人缘好', '需看喜忌'],
        'related_terms': ['天干五合', '地支三合', '地支六冲']
    },
    '地支三合': {
        'category': '干支关系-合',
        'type': 'neutral',
        'brief': '三个地支合成局，力量强大',
        'description': '地支三合局是指申子辰合水局、亥卯未合木局、寅午戌合火局、巳酉丑合金局。三合局力量强大，主团结、合力、成局。',
        'details': [
            '申子辰合水局：水局，主智慧流动',
            '亥卯未合木局：木局，主仁慈生发',
            '寅午戌合火局：火局，主热情炎上',
            '巳酉丑合金局：金局，主刚毅收敛'
        ],
        'influence': ['力量强大', '主团结合力', '易成大事', '需看喜忌'],
        'related_terms': ['地支六合', '地支三会', '地支半合']
    },
    '地支六冲': {
        'category': '干支关系-冲',
        'type': 'negative',
        'brief': '地支之间的六种相冲关系',
        'description': '地支六冲是指子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲。相冲主冲突、变动、分离，是一种强烈的对立关系。',
        'details': [
            '子午冲：水火相冲，主心脑血管',
            '丑未冲：土土相冲，主脾胃',
            '寅申冲：金木相冲，主道路',
            '卯酉冲：金木相冲，主门户',
            '辰戌冲：土土相冲，主墓库',
            '巳亥冲：水火相冲，主驿马'
        ],
        'influence': ['主冲突变动', '易有分离', '奔波劳碌', '冲吉则凶冲凶则吉'],
        'related_terms': ['地支六害', '地支三刑', '地支六合']
    },
    '地支六害': {
        'category': '干支关系-害',
        'type': 'negative',
        'brief': '地支之间的六种相害关系',
        'description': '地支六害是指子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害。相害主损害、不和、暗伤，其力次于冲。',
        'details': [
            '子未害：彼此损害',
            '丑午害：官鬼相害',
            '寅巳害：无辜受害',
            '卯辰害：口舌是非',
            '申亥害：竞争伤害',
            '酉戌害：口舌争斗'
        ],
        'influence': ['主损害不和', '暗箭难防', '口舌是非', '需防小人'],
        'related_terms': ['地支六冲', '地支三刑', '地支六合']
    },
    '地支三刑': {
        'category': '干支关系-刑',
        'type': 'negative',
        'brief': '地支之间的刑克关系，主刑伤、灾祸',
        'description': '地支三刑包括：寅巳申三刑（无恩之刑）、丑戌未三刑（恃势之刑）、子卯相刑（无礼之刑）、辰辰、午午、酉酉、亥亥自刑。刑主刑伤、灾祸、官非。',
        'details': [
            '寅巳申三刑：无恩之刑，忘恩负义',
            '丑戌未三刑：恃势之刑，仗势欺人',
            '子卯相刑：无礼之刑，以下犯上',
            '自刑：辰午酉亥，自寻烦恼'
        ],
        'influence': ['主刑伤病灾', '官非口舌', '需防意外', '行善可解'],
        'related_terms': ['地支六冲', '地支六害', '羊刃']
    },
    '五行相生': {
        'category': '五行关系-生',
        'type': 'positive',
        'brief': '木生火、火生土、土生金、金生水、水生木',
        'description': '五行相生是指木生火、火生土、土生金、金生水、水生木。相生主生助、滋养、有益。我生者为泄，生我者为益。',
        'details': [
            '木生火：木燃而生火',
            '火生土：火焚而生土',
            '土生金：土中藏金',
            '金生水：金销生水',
            '水生木：水滋润木'
        ],
        'influence': ['主生助滋养', '有贵人助', '生生不息', '需适度不宜过'],
        'related_terms': ['五行相克', '五行相乘', '五行相侮']
    },
    '五行相克': {
        'category': '五行关系-克',
        'type': 'negative',
        'brief': '木克土、土克水、水克火、火克金、金克木',
        'description': '五行相克是指木克土、土克水、水克火、火克金、金克木。相克主制约、克制、对立。克我者为官杀，我克者为财星。',
        'details': [
            '木克土：木扎根于土',
            '土克水：土能挡水',
            '水克火：水能灭火',
            '火克金：火能熔金',
            '金克木：金能伐木'
        ],
        'influence': ['主制约克制', '有压力管束', '对立竞争', '克为喜用反为吉'],
        'related_terms': ['五行相生', '五行相乘', '五行相侮']
    },
}


# ==================== 命理基础术语 ====================
FOUNDATION_TERMS = {
    '四柱八字': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '年柱、月柱、日柱、时柱组成的八个字',
        'description': '四柱八字，简称八字，是根据人出生的年、月、日、时，配以天干地支，共八个字来推算命运的方法。年柱代表祖辈，月柱代表父母兄弟，日柱代表自己和配偶，时柱代表子女。',
        'details': [
            '年柱：代表祖辈、少年运（1-16岁）',
            '月柱：代表父母兄弟、青年运（17-32岁）',
            '日柱：代表自己和配偶、中年运（33-48岁）',
            '时柱：代表子女、晚年运（49岁以后）'
        ],
        'influence': ['人生命运的整体格局', '各柱各有所主', '需综合分析'],
        'related_terms': ['天干地支', '六十甲子', '日主']
    },
    '日主': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '日柱天干，代表命主本人',
        'description': '日主，又称日元、命主，是指日柱的天干。日主是八字的核心，代表命主本人。整个八字命局的分析都是围绕日主的强弱、喜忌来展开的。',
        'details': [
            '甲木日主：正直仁慈，有领导才能',
            '乙木日主：温柔善良，善于变通',
            '丙火日主：热情开朗，积极向上',
            '丁火日主：温和有礼，心思细腻',
            '戊土日主：稳重可靠，诚实守信',
            '己土日主：包容善良，踏实肯干',
            '庚金日主：刚健果断，重情重义',
            '辛金日主：温润秀气，追求完美',
            '壬水日主：聪明灵活，足智多谋',
            '癸水日主：温柔智慧，直觉敏锐'
        ],
        'influence': ['代表命主本人', '八字分析的核心', '判断旺衰喜忌的基准'],
        'related_terms': ['日柱', '身强身弱', '用神']
    },
    '十神': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '以日主为中心的十种五行关系',
        'description': '十神是八字命理中以日主为中心，根据五行生克关系和阴阳异同而划分的十种关系，分别是：比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印。',
        'details': [
            '比肩：同我同阴阳，代表兄弟朋友',
            '劫财：同我异阴阳，代表竞争破财',
            '食神：我生同阴阳，代表才华福气',
            '伤官：我生异阴阳，代表才华叛逆',
            '偏财：我克异阴阳，代表偏财运',
            '正财：我克同阴阳，代表正财运',
            '七杀：克我同阴阳，代表压力权力',
            '正官：克我异阴阳，代表官职地位',
            '偏印：生我同阴阳，代表偏学玄学',
            '正印：生我异阴阳，代表学问贵人'
        ],
        'influence': ['八字分析的核心工具', '各有吉凶两面', '需配合全局分析'],
        'related_terms': ['比肩', '劫财', '食神', '伤官', '正财', '偏财', '正官', '七杀', '正印', '偏印']
    },
    '用神': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '对命局最有利的五行或十神',
        'description': '用神是指对命局最有利、最需要的五行或十神。找准用神是八字分析的关键。用神有力则命好，用神受伤则命差。',
        'details': [
            '扶抑用神：强者抑之，弱者扶之',
            '调候用神：寒者暖之，热者寒之',
            '通关用神：两相斗者，从中调和',
            '病药用神：有病方为贵，无伤不是奇'
        ],
        'influence': ['命局的关键', '行运吉凶的标准', '补救改运的依据'],
        'related_terms': ['忌神', '喜神', '身强身弱']
    },
    '忌神': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '对命局最不利的五行或十神',
        'description': '忌神是指对命局最不利、最忌讳的五行或十神。忌神旺相则运势不佳，忌神受克制则运势好转。',
        'details': [
            '身强忌比劫印星',
            '身弱忌财官杀星',
            '忌神宜制不宜助',
            '忌神也可为用（从格）'
        ],
        'influence': ['命局的不利因素', '需警惕规避', '受克制则吉'],
        'related_terms': ['用神', '喜神', '身强身弱']
    },
    '身强身弱': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '日主五行力量的强弱程度',
        'description': '身强身弱是指日主（日干）在整个八字命局中的力量强弱。身强者喜克泄耗，身弱者喜生扶。判断身强身弱是八字分析的第一步。',
        'details': [
            '得令：生于当旺之月',
            '得地：地支有根气',
            '得势：天干有比劫印星相助',
            '中和：不强不弱最为贵'
        ],
        'influence': ['判断用神的基础', '决定喜忌方向', '强抑弱扶为原则'],
        'related_terms': ['日主', '用神', '月令']
    },
    '大运': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '十年一步的人生大运走势',
        'description': '大运是指人生中每十年一步的运势阶段。大运根据月柱排出，阳男阴女顺行，阴男阳女逆行。大运的吉凶直接影响人生各阶段的运势。',
        'details': [
            '起运年龄：根据出生日与节气计算',
            '顺行逆行：阳男阴女顺，阴男阳女逆',
            '十年一步：每步大运管十年',
            '大运与命局：运为动，命为静'
        ],
        'influence': ['人生各阶段的运势', '命好不如运好', '需结合流年看'],
        'related_terms': ['流年', '小运', '命局']
    },
    '流年': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '每一年的运势，即当年的干支',
        'description': '流年是指每一年的运势，以当年的干支为标志。流年与命局、大运相互作用，决定当年的吉凶祸福。',
        'details': [
            '太岁：当年的地支',
            '犯太岁：刑冲克害太岁',
            '本命年：地支与流年相同',
            '流年吉凶：需结合大运命局'
        ],
        'influence': ['当年的运势', '吉年宜进取', '凶年宜守成'],
        'related_terms': ['大运', '太岁', '本命年']
    },
    '纳音五行': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '六十甲子的纳音五行属性',
        'description': '纳音五行是古人为六十甲子搭配的五行属性，每两组干支对应一个纳音五行。如甲子乙丑海中金、丙寅丁卯炉中火等。纳音多用于合婚、年命等。',
        'details': [
            '甲子乙丑海中金',
            '丙寅丁卯炉中火',
            '戊辰己巳大林木',
            '庚午辛未路旁土',
            '壬申癸酉剑锋金',
            '...共三十种纳音'
        ],
        'influence': ['年命的五行属性', '合婚参考', '补充正五行'],
        'related_terms': ['六十甲子', '天干地支', '五行']
    },
    '十二长生': {
        'category': '命理基础',
        'type': 'neutral',
        'brief': '天干在十二地支的旺衰状态',
        'description': '十二长生是描述天干在十二地支中从生到死的十二个阶段，分别是：长生、沐浴、冠带、临官、帝旺、衰、病、死、墓、绝、胎、养。',
        'details': [
            '长生：万物出生，生机勃勃',
            '沐浴：初长沐浴，桃花旺盛',
            '冠带：渐长穿衣，事业起步',
            '临官：事业有成，官位亨通',
            '帝旺：鼎盛时期，如日中天',
            '衰：由盛转衰，精力减退',
            '病：生病困苦，诸事不顺',
            '死：运势低谷，诸事不成',
            '墓：收藏入库，安定平稳',
            '绝：断绝灭绝，重新开始',
            '胎：受胎孕育，计划酝酿',
            '养：养育成长，蓄势待发'
        ],
        'influence': ['五行旺衰的精细描述', '各有所主', '需结合全局'],
        'related_terms': ['长生', '帝旺', '墓库']
    },
}


# ==================== 梅花易数术语 ====================
MEIHUA_TERMS = {
    '本卦': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '起卦得到的原始卦象，代表当前状态',
        'description': '本卦，又称正卦、主卦，是起卦时直接得到的卦象。本卦代表事物当前的状态、现状和起点，是判断吉凶的基础。',
        'details': [
            '代表当前状态和现状',
            '是事物发展的起点',
            '卦辞爻辞是主要参考',
            '体卦和用卦都在本卦中'
        ],
        'influence': ['判断现状的依据', '起卦的直接结果', '事物发展的起点'],
        'related_terms': ['互卦', '变卦', '动爻']
    },
    '互卦': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '本卦二三四爻为下，三四五爻为上，代表发展过程',
        'description': '互卦是由本卦的二、三、四爻组成下卦，三、四、五爻组成上卦而得到的新卦。互卦代表事物发展的中间过程、内在因素和隐藏的信息。',
        'details': [
            '取本卦二三四爻为下卦',
            '取本卦三四五爻为上卦',
            '代表发展过程和中间状态',
            '反映内在因素和隐藏信息'
        ],
        'influence': ['事物发展的过程', '中间阶段的状态', '隐藏的信息'],
        'related_terms': ['本卦', '变卦', '综卦']
    },
    '变卦': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '动爻阴阳改变后的卦象，代表最终结果',
        'description': '变卦，又称之卦，是本卦的动爻阴阳性质改变后得到的新卦。变卦代表事物发展的最终结果、趋势和归宿。',
        'details': [
            '动爻阳变阴、阴变阳',
            '代表最终结果和趋势',
            '是判断吉凶的重要依据',
            '本卦为因，变卦为果'
        ],
        'influence': ['事物发展的结果', '最终的趋势归宿', '吉凶判断的关键'],
        'related_terms': ['本卦', '动爻', '互卦']
    },
    '错卦': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '本卦各爻阴阳全变，代表对立面',
        'description': '错卦，又称旁通卦，是本卦六个爻的阴阳全部相反得到的卦。错卦代表事物的对立面、反面和潜在的可能性。',
        'details': [
            '六爻阴阳全变',
            '代表事物的对立面',
            '反映事物的反面',
            '从对面看问题'
        ],
        'influence': ['事物的对立面', '反面的可能性', '换角度思考'],
        'related_terms': ['综卦', '本卦', '互卦']
    },
    '综卦': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '本卦颠倒过来，代表不同角度的看法',
        'description': '综卦，又称覆卦，是将本卦颠倒过来（旋转180度）得到的新卦。综卦代表从不同角度、不同立场所看到的情况。',
        'details': [
            '本卦旋转180度',
            '代表不同角度的看法',
            '换位思考的体现',
            '全面看问题'
        ],
        'influence': ['不同角度的观点', '换位思考', '全面看问题'],
        'related_terms': ['错卦', '本卦', '互卦']
    },
    '动爻': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '卦中要变化的爻，是吉凶判断的关键',
        'description': '动爻是卦中要发生变化的爻（阳变阴、阴变阳）。动爻是梅花易数中判断吉凶的关键，动爻的爻辞是解卦的重要依据。',
        'details': [
            '动爻是卦中变化的爻',
            '是吉凶判断的关键',
            '动爻爻辞是解卦重点',
            '动爻代表事物的变动'
        ],
        'influence': ['解卦的关键', '代表事物的变动', '爻辞是重要参考'],
        'related_terms': ['变卦', '爻辞', '本卦']
    },
    '体用': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '体卦代表自己，用卦代表所问之事',
        'description': '体用是梅花易数中的重要概念。体卦代表自己、本体、内在；用卦代表对方、所问之事、外在。体用的五行生克关系是判断吉凶的重要依据。',
        'details': [
            '体卦：代表自己、不动的一方',
            '用卦：代表对方、所问之事',
            '有动爻的卦为用卦',
            '无动爻的卦为体卦'
        ],
        'influence': ['判断吉凶的重要方法', '体克用吉，用克体凶', '体用比和为吉'],
        'related_terms': ['本卦', '动爻', '五行生克']
    },
    '先天八卦数': {
        'category': '梅花易数',
        'type': 'neutral',
        'brief': '乾1兑2离3震4巽5坎6艮7坤8',
        'description': '先天八卦数是邵雍根据先天八卦图排列的数字：乾一、兑二、离三、震四、巽五、坎六、艮七、坤八。梅花易数起卦主要使用先天八卦数。',
        'details': [
            '乾1：天，金',
            '兑2：泽，金',
            '离3：火，火',
            '震4：雷，木',
            '巽5：风，木',
            '坎6：水，水',
            '艮7：山，土',
            '坤8：地，土'
        ],
        'influence': ['梅花易数起卦的基础', '数字与卦的对应', '计算卦象的依据'],
        'related_terms': ['后天八卦', '八卦', '起卦方法']
    },
}


# 合并所有术语
ALL_TERMS = {}
ALL_TERMS.update(SHENSHA_TERMS)
ALL_TERMS.update(GANZHI_RELATION_TERMS)
ALL_TERMS.update(FOUNDATION_TERMS)
ALL_TERMS.update(MEIHUA_TERMS)


# 术语分类
TERM_CATEGORIES = [
    {'key': 'all', 'name': '全部术语', 'description': '所有专业术语'},
    {'key': '命理基础', 'name': '命理基础', 'description': '八字命理基础概念'},
    {'key': '神煞-吉神', 'name': '吉神', 'description': '吉祥的神煞'},
    {'key': '神煞-凶煞', 'name': '凶煞', 'description': '不吉的神煞'},
    {'key': '神煞-中性', 'name': '中性神煞', 'description': '吉凶两面的神煞'},
    {'key': '干支关系-合', 'name': '干支合化', 'description': '天干地支的合化关系'},
    {'key': '干支关系-冲', 'name': '干支相冲', 'description': '天干地支的相冲关系'},
    {'key': '干支关系-害', 'name': '干支相害', 'description': '天干地支的相害关系'},
    {'key': '干支关系-刑', 'name': '干支相刑', 'description': '天干地支的相刑关系'},
    {'key': '五行关系-生', 'name': '五行相生', 'description': '五行相生关系'},
    {'key': '五行关系-克', 'name': '五行相克', 'description': '五行相克关系'},
    {'key': '梅花易数', 'name': '梅花易数', 'description': '梅花易数相关术语'},
]


class TermExplainer:
    """
    专业术语解释器
    提供术语查询、分类浏览、关联推荐等功能
    """

    def __init__(self):
        self.kb = KnowledgeBase()
        self.terms = ALL_TERMS
        self.categories = TERM_CATEGORIES
        self._build_search_index()

    def _build_search_index(self):
        """构建搜索索引，包含知识库术语"""
        self.search_index = {}
        
        # 加入扩展术语
        for term_name, info in self.terms.items():
            self.search_index[term_name] = {
                'name': term_name,
                'category': info.get('category', ''),
                'brief': info.get('brief', ''),
                'description': info.get('description', ''),
                'source': 'extended',
                'details': info
            }
        
        # 加入知识库术语
        kb_terms = self.kb.term_index
        for term_name, info in kb_terms.items():
            if term_name not in self.search_index:
                self.search_index[term_name] = {
                    'name': term_name,
                    'category': info.get('category', ''),
                    'brief': info.get('description', ''),
                    'description': info.get('description', ''),
                    'source': 'knowledge_base',
                    'details': info.get('details', {})
                }

    def search(self, keyword, category=None, limit=20):
        """
        搜索术语，支持模糊匹配
        
        Args:
            keyword: 搜索关键词
            category: 分类筛选（可选）
            limit: 返回结果数量限制
            
        Returns:
            匹配的术语列表
        """
        results = []
        keyword = keyword.strip()
        
        if not keyword:
            return results
        
        # 精确匹配优先
        if keyword in self.search_index:
            term = self.search_index[keyword]
            if not category or term['category'] == category:
                results.append(term)
        
        # 名称包含匹配
        for term_name, info in self.search_index.items():
            if term_name == keyword:
                continue
            if category and info['category'] != category:
                continue
            if keyword in term_name:
                results.append(info)
                if len(results) >= limit:
                    break
        
        # 描述包含匹配
        if len(results) < limit:
            for term_name, info in self.search_index.items():
                if category and info['category'] != category:
                    continue
                if keyword in info.get('brief', '') or keyword in info.get('description', ''):
                    if info not in results:
                        results.append(info)
                        if len(results) >= limit:
                            break
        
        return results[:limit]

    def get_term_detail(self, term_name):
        """
        获取术语详细信息
        
        Args:
            term_name: 术语名称
            
        Returns:
            术语详细信息字典
        """
        if term_name in self.search_index:
            term = self.search_index[term_name].copy()
            # 添加关联术语详情
            related = term.get('details', {}).get('related_terms', [])
            if related:
                related_details = []
                for rt in related:
                    if rt in self.search_index:
                        related_details.append({
                            'name': rt,
                            'category': self.search_index[rt]['category'],
                            'brief': self.search_index[rt]['brief']
                        })
                term['related_details'] = related_details
            return term
        return None

    def get_terms_by_category(self, category_key, limit=50):
        """
        按分类获取术语列表
        
        Args:
            category_key: 分类键名
            limit: 返回数量限制
            
        Returns:
            该分类下的术语列表
        """
        results = []
        
        if category_key == 'all':
            for term_name, info in self.search_index.items():
                results.append({
                    'name': term_name,
                    'category': info['category'],
                    'brief': info['brief']
                })
                if len(results) >= limit:
                    break
        else:
            for term_name, info in self.search_index.items():
                if info['category'] == category_key:
                    results.append({
                        'name': term_name,
                        'category': info['category'],
                        'brief': info['brief']
                    })
                    if len(results) >= limit:
                        break
        
        return results

    def get_all_categories(self):
        """获取所有术语分类"""
        return self.categories

    def get_hot_terms(self, limit=10):
        """
        获取热门/常用术语
        
        Args:
            limit: 返回数量限制
            
        Returns:
            热门术语列表
        """
        hot_names = [
            '四柱八字', '日主', '十神', '用神', '身强身弱',
            '大运', '流年', '桃花', '驿马', '十二长生',
            '五行相生', '五行相克', '本卦', '变卦', '动爻'
        ]
        
        results = []
        for name in hot_names:
            if name in self.search_index:
                results.append({
                    'name': name,
                    'category': self.search_index[name]['category'],
                    'brief': self.search_index[name]['brief']
                })
                if len(results) >= limit:
                    break
        
        return results

    def get_related_terms(self, term_name, limit=5):
        """
        获取相关术语
        
        Args:
            term_name: 术语名称
            limit: 返回数量限制
            
        Returns:
            相关术语列表
        """
        term = self.get_term_detail(term_name)
        if not term:
            return []
        
        related = term.get('details', {}).get('related_terms', [])
        results = []
        
        for rt in related:
            if rt in self.search_index:
                results.append({
                    'name': rt,
                    'category': self.search_index[rt]['category'],
                    'brief': self.search_index[rt]['brief']
                })
                if len(results) >= limit:
                    break
        
        return results

    def get_term_count(self):
        """获取术语总数统计"""
        category_counts = {}
        for info in self.search_index.values():
            cat = info['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            'total': len(self.search_index),
            'by_category': category_counts
        }
