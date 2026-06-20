"""
梅花易数卦象分析与爻辞解读系统
包含八卦基础数据、64卦卦辞爻辞、吉凶判断及解卦分析
先天八卦数：乾1、兑2、离3、震4、巽5、坎6、艮7、坤8
"""


BAGUA = {
    1: {'name': '乾', 'nature': '天', 'symbol': '☰', 'wuxing': '金', 'description': '天行健，君子以自强不息'},
    2: {'name': '兑', 'nature': '泽', 'symbol': '☱', 'wuxing': '金', 'description': '丽泽，兑。君子以朋友讲习'},
    3: {'name': '离', 'nature': '火', 'symbol': '☲', 'wuxing': '火', 'description': '明两作，离。大人以继明照于四方'},
    4: {'name': '震', 'nature': '雷', 'symbol': '☳', 'wuxing': '木', 'description': '洊雷，震。君子以恐惧修省'},
    5: {'name': '巽', 'nature': '风', 'symbol': '☴', 'wuxing': '木', 'description': '随风，巽。君子以申命行事'},
    6: {'name': '坎', 'nature': '水', 'symbol': '☵', 'wuxing': '水', 'description': '习坎，有孚维心亨，行有尚'},
    7: {'name': '艮', 'nature': '山', 'symbol': '☶', 'wuxing': '土', 'description': '兼山，艮。君子以思不出其位'},
    8: {'name': '坤', 'nature': '地', 'symbol': '☷', 'wuxing': '土', 'description': '地势坤，君子以厚德载物'},
}


HEXAGRAMS = {
    (1, 1): {
        'name': '乾为天',
        'judgment': '吉',
        'gua_ci': '元亨，利贞。',
        'description': '纯阳之卦，主刚健、进取、成功。天行健，君子以自强不息。',
        'yao_ci': [
            {'yao': '初九', 'text': '潜龙勿用。', 'meaning': '时机未到，阳气潜藏，宜潜伏等待，不可轻举妄动。'},
            {'yao': '九二', 'text': '见龙在田，利见大人。', 'meaning': '龙出现在田野，阳气渐显，崭露头角，利于遇见贵人相助。'},
            {'yao': '九三', 'text': '君子终日乾乾，夕惕若厉，无咎。', 'meaning': '君子终日勤奋努力，夜晚也要警惕自省，如临危险，如此则无灾。'},
            {'yao': '九四', 'text': '或跃在渊，无咎。', 'meaning': '龙或腾跃上进，或退处在渊，审时度势，进退自如，无灾。'},
            {'yao': '九五', 'text': '飞龙在天，利见大人。', 'meaning': '龙飞腾于天空，阳气极盛，大展宏图，利于遇见贵人。'},
            {'yao': '上九', 'text': '亢龙有悔。', 'meaning': '龙飞得过高，过盛必衰，物极必反，应有悔恨。'},
        ]
    },
    (8, 8): {
        'name': '坤为地',
        'judgment': '吉',
        'gua_ci': '元亨，利牝马之贞。君子有攸往，先迷后得主。利西南得朋，东北丧朋。安贞吉。',
        'description': '纯阴之卦，主柔顺、包容、厚德。地势坤，君子以厚德载物。',
        'yao_ci': [
            {'yao': '初六', 'text': '履霜，坚冰至。', 'meaning': '脚踩霜花，坚冰即将到来，见微知著，防患未然。'},
            {'yao': '六二', 'text': '直方大，不习无不利。', 'meaning': '正直、方正、博大，不刻意学习也无所不利，顺其自然。'},
            {'yao': '六三', 'text': '含章可贞。或从王事，无成有终。', 'meaning': '内含文采，坚守正道。辅佐君王事务，不求有功但求有终。'},
            {'yao': '六四', 'text': '括囊，无咎无誉。', 'meaning': '扎紧口袋，收敛言行，无灾也无赞誉，明哲保身。'},
            {'yao': '六五', 'text': '黄裳，元吉。', 'meaning': '穿着黄色下裳，居位中正，大吉大利。'},
            {'yao': '上六', 'text': '龙战于野，其血玄黄。', 'meaning': '阴阳二龙在原野交战，流出青黄相杂的血，两败俱伤。'},
        ]
    },
    (6, 4): {
        'name': '水雷屯',
        'judgment': '平',
        'gua_ci': '元亨，利贞。勿用有攸往。利建侯。',
        'description': '初生之卦，主艰难、积累、萌芽。云雷屯，君子以经纶。',
        'yao_ci': [
            {'yao': '初九', 'text': '磐桓，利居贞，利建侯。', 'meaning': '徘徊不前，利于安居守正，利于建立功业。'},
            {'yao': '六二', 'text': '屯如邅如，乘马班如。匪寇婚媾，女子贞不字，十年乃字。', 'meaning': '进退维谷，骑马徘徊。不是盗寇而是求婚者，女子守正不嫁，十年后才成婚。'},
            {'yao': '六三', 'text': '即鹿无虞，惟入于林中。君子几不如舍，往吝。', 'meaning': '追逐野鹿却没有向导，徒入山林深处。君子不如舍弃，前往必有困难。'},
            {'yao': '六四', 'text': '乘马班如，求婚媾，往吉，无不利。', 'meaning': '骑马徘徊，寻求婚配，前往则吉，无所不利。'},
            {'yao': '九五', 'text': '屯其膏，小贞吉，大贞凶。', 'meaning': '囤积膏泽恩惠，小事守正则吉，大事守正则凶。'},
            {'yao': '上六', 'text': '乘马班如，泣血涟如。', 'meaning': '骑马徘徊不前，悲伤哭泣泪血涟涟。'},
        ]
    },
    (7, 6): {
        'name': '山水蒙',
        'judgment': '平',
        'gua_ci': '亨。匪我求童蒙，童蒙求我。初筮告，再三渎，渎则不告。利贞。',
        'description': '启蒙之卦，主学习、教育、启发。山下出泉，蒙。君子以果行育德。',
        'yao_ci': [
            {'yao': '初六', 'text': '发蒙，利用刑人，用说桎梏，以往吝。', 'meaning': '启发蒙昧，宜用刑罚惩戒，去除束缚，前往则有困难。'},
            {'yao': '九二', 'text': '包蒙，吉。纳妇吉，子克家。', 'meaning': '包容蒙昧，吉。娶妻吉，儿子能成家立业。'},
            {'yao': '六三', 'text': '勿用取女，见金夫，不有躬，无攸利。', 'meaning': '不宜娶此女，见金夫失身，无所利。'},
            {'yao': '六四', 'text': '困蒙，吝。', 'meaning': '困于蒙昧之中，有困难。'},
            {'yao': '六五', 'text': '童蒙，吉。', 'meaning': '童子蒙昧天真，吉。'},
            {'yao': '上九', 'text': '击蒙，不利为寇，利御寇。', 'meaning': '打击蒙昧，不宜主动为寇，利于防御寇盗。'},
        ]
    },
    (6, 1): {
        'name': '水天需',
        'judgment': '吉',
        'gua_ci': '有孚，光亨，贞吉。利涉大川。',
        'description': '等待之卦，主耐心、准备、时机。云上于天，需。君子以饮食宴乐。',
        'yao_ci': [
            {'yao': '初九', 'text': '需于郊，利用恒，无咎。', 'meaning': '在郊外等待，利于保持恒心，无灾。'},
            {'yao': '九二', 'text': '需于沙，小有言，终吉。', 'meaning': '在沙滩等待，小有言语冲突，最终吉祥。'},
            {'yao': '九三', 'text': '需于泥，致寇至。', 'meaning': '在泥沼中等待，招致寇盗到来。'},
            {'yao': '六四', 'text': '需于血，出自穴。', 'meaning': '在血泊中等待，从洞穴中逃出。'},
            {'yao': '九五', 'text': '需于酒食，贞吉。', 'meaning': '在酒食宴乐中等待，守正则吉。'},
            {'yao': '上六', 'text': '入于穴，有不速之客三人来，敬之终吉。', 'meaning': '进入洞穴，有三位不速之客到来，恭敬相待最终吉祥。'},
        ]
    },
    (1, 6): {
        'name': '天水讼',
        'judgment': '凶',
        'gua_ci': '有孚窒惕，中吉，终凶。利见大人，不利涉大川。',
        'description': '争讼之卦，主争端、诉讼、口舌。天与水违行，讼。君子以作事谋始。',
        'yao_ci': [
            {'yao': '初六', 'text': '不永所事，小有言，终吉。', 'meaning': '不长久争执，小有言语，最终吉祥。'},
            {'yao': '九二', 'text': '不克讼，归而逋，其邑人三百户，无眚。', 'meaning': '争讼不胜，逃归其邑，三百户人家无灾。'},
            {'yao': '六三', 'text': '食旧德，贞厉，终吉。或从王事，无成。', 'meaning': '安享旧有福德，守正有危，终吉。或辅佐王事，无所成就。'},
            {'yao': '九四', 'text': '不克讼，复即命，渝安贞，吉。', 'meaning': '争讼不胜，回复天命，改变而安守正道，吉。'},
            {'yao': '九五', 'text': '讼，元吉。', 'meaning': '争讼，大吉。'},
            {'yao': '上九', 'text': '或锡之鞶带，终朝三褫之。', 'meaning': '或许赐予官带，一日之内三次被剥夺。'},
        ]
    },
    (8, 6): {
        'name': '地水师',
        'judgment': '平',
        'gua_ci': '贞，丈人吉，无咎。',
        'description': '军队之卦，主战争、组织、领导。地中有水，师。君子以容民畜众。',
        'yao_ci': [
            {'yao': '初六', 'text': '师出以律，否臧凶。', 'meaning': '出师要有纪律，否则凶险。'},
            {'yao': '九二', 'text': '在师中，吉，无咎。王三锡命。', 'meaning': '在军队中，吉，无灾。君王三次赐命嘉奖。'},
            {'yao': '六三', 'text': '师或舆尸，凶。', 'meaning': '军队可能载尸而归，凶险。'},
            {'yao': '六四', 'text': '师左次，无咎。', 'meaning': '军队撤退驻扎，无灾。'},
            {'yao': '六五', 'text': '田有禽，利执言，无咎。长子帅师，弟子舆尸，贞凶。', 'meaning': '田中有禽兽，利于捕捉，无灾。长子率军，次子载尸，守正凶。'},
            {'yao': '上六', 'text': '大君有命，开国承家，小人勿用。', 'meaning': '君王有命，分封诸侯大夫，小人不可任用。'},
        ]
    },
    (6, 8): {
        'name': '水地比',
        'judgment': '吉',
        'gua_ci': '吉。原筮元永贞，无咎。不宁方来，后夫凶。',
        'description': '亲比之卦，主亲近、合作、团结。地上有水，比。先王以建万国，亲诸侯。',
        'yao_ci': [
            {'yao': '初六', 'text': '有孚比之，无咎。有孚盈缶，终来有它，吉。', 'meaning': '有诚信而亲近，无灾。诚信如满缸之水，终将有意外之吉。'},
            {'yao': '六二', 'text': '比之自内，贞吉。', 'meaning': '发自内心的亲近，守正则吉。'},
            {'yao': '六三', 'text': '比之匪人。', 'meaning': '亲近不当之人。'},
            {'yao': '六四', 'text': '外比之，贞吉。', 'meaning': '向外亲近贤人，守正则吉。'},
            {'yao': '九五', 'text': '显比，王用三驱，失前禽，邑人不诫，吉。', 'meaning': '光明正大的亲近，君王用三驱之礼，放走前面的禽兽，邑人不戒备，吉。'},
            {'yao': '上六', 'text': '比之无首，凶。', 'meaning': '亲近而无首领，凶险。'},
        ]
    },
    (5, 1): {
        'name': '风天小畜',
        'judgment': '平',
        'gua_ci': '亨，密云不雨，自我西郊。',
        'description': '小畜之卦，主积蓄、等待。风行天上，小畜。君子以懿文德。',
        'yao_ci': [
            {'yao': '初九', 'text': '复自道，何其咎，吉。', 'meaning': '从正道返回，有何灾祸，吉。'},
            {'yao': '九二', 'text': '牵复，吉。', 'meaning': '牵连返回，吉。'},
            {'yao': '九三', 'text': '舆说辐，夫妻反目。', 'meaning': '车子脱落辐条，夫妻反目成仇。'},
            {'yao': '六四', 'text': '有孚，血去惕出，无咎。', 'meaning': '有诚信，忧患消除，恐惧散去，无灾。'},
            {'yao': '九五', 'text': '有孚挛如，富以其邻。', 'meaning': '有诚信牵连，富有及于邻人。'},
            {'yao': '上九', 'text': '既雨既处，尚德载，妇贞厉，月几望，君子征凶。', 'meaning': '既下雨又停止，崇尚德行承载，妇人守正危险，月将圆，君子出征凶。'},
        ]
    },
    (1, 2): {
        'name': '天泽履',
        'judgment': '吉',
        'gua_ci': '履虎尾，不咥人，亨。',
        'description': '履行之卦，主实践、礼仪。上天下泽，履。君子以辨上下，定民志。',
        'yao_ci': [
            {'yao': '初九', 'text': '素履往，无咎。', 'meaning': '朴素地前行，无灾。'},
            {'yao': '九二', 'text': '履道坦坦，幽人贞吉。', 'meaning': '履行大道平坦，隐士守正则吉。'},
            {'yao': '六三', 'text': '眇能视，跛能履，履虎尾，咥人，凶。武人为于大君。', 'meaning': '独眼能视，跛脚能行，踩虎尾被虎咬，凶。武人成为大君。'},
            {'yao': '九四', 'text': '履虎尾，愬愬，终吉。', 'meaning': '踩虎尾，恐惧谨慎，最终吉祥。'},
            {'yao': '九五', 'text': '夬履，贞厉。', 'meaning': '果断地履行，守正有危险。'},
            {'yao': '上九', 'text': '视履考祥，其旋元吉。', 'meaning': '审视履迹考察吉凶，回归大吉。'},
        ]
    },
    (8, 1): {
        'name': '地天泰',
        'judgment': '吉',
        'gua_ci': '小往大来，吉亨。',
        'description': '通泰之卦，主亨通、顺利。天地交，泰。后以财成天地之道，辅相天地之宜，以左右民。',
        'yao_ci': [
            {'yao': '初九', 'text': '拔茅茹，以其汇，征吉。', 'meaning': '拔茅草连类而及，出征吉。'},
            {'yao': '九二', 'text': '包荒，用冯河，不遐遗，朋亡，得尚于中行。', 'meaning': '包容广大，徒步渡河，不遗弃远方，朋友丧失，在行中正道上得到崇尚。'},
            {'yao': '九三', 'text': '无平不陂，无往不复，艰贞无咎。勿恤其孚，于食有福。', 'meaning': '没有平地不变山坡，没有前往不返回，艰难守正无灾。不必忧虑诚信，在饮食方面有福。'},
            {'yao': '六四', 'text': '翩翩不富，以其邻，不戒以孚。', 'meaning': '翩翩然不富足，与邻人一起，不戒备而有诚信。'},
            {'yao': '六五', 'text': '帝乙归妹，以祉元吉。', 'meaning': '帝乙嫁女，因此得福大吉。'},
            {'yao': '上六', 'text': '城复于隍，勿用师，自邑告命，贞吝。', 'meaning': '城墙倒塌在城壕里，不可用兵，从邑中报告命令，守正困难。'},
        ]
    },
    (1, 8): {
        'name': '天地否',
        'judgment': '凶',
        'gua_ci': '否之匪人，不利君子贞，大往小来。',
        'description': '闭塞之卦，主阻隔、不通。天地不交，否。君子以俭德辟难，不可荣以禄。',
        'yao_ci': [
            {'yao': '初六', 'text': '拔茅茹，以其汇，贞吉，亨。', 'meaning': '拔茅草连类而及，守正吉，亨通。'},
            {'yao': '六二', 'text': '包承，小人吉，大人否，亨。', 'meaning': '包容承受，小人吉，大人不吉，亨通。'},
            {'yao': '六三', 'text': '包羞。', 'meaning': '包容羞辱。'},
            {'yao': '九四', 'text': '有命无咎，畴离祉。', 'meaning': '有天命无灾，同类相聚得福。'},
            {'yao': '九五', 'text': '休否，大人吉，其亡其亡，系于苞桑。', 'meaning': '休止否塞，大人吉，危而不忘危，如系于苞桑之坚。'},
            {'yao': '上九', 'text': '倾否，先否后喜。', 'meaning': '倾覆否塞，先否塞后喜悦。'},
        ]
    },
    (1, 3): {
        'name': '天火同人',
        'judgment': '吉',
        'gua_ci': '同人于野，亨。利涉大川，利君子贞。',
        'description': '同人之卦，主团结、合作。天与火，同人。君子以类族辨物。',
        'yao_ci': [
            {'yao': '初九', 'text': '同人于门，无咎。', 'meaning': '在门口与人和同，无灾。'},
            {'yao': '六二', 'text': '同人于宗，吝。', 'meaning': '只与宗族同和，有困难。'},
            {'yao': '九三', 'text': '伏戎于莽，升其高陵，三岁不兴。', 'meaning': '埋伏兵卒于草莽，登上高陵，三年不能兴兵。'},
            {'yao': '九四', 'text': '乘其墉，弗克攻，吉。', 'meaning': '登上城墙，不能攻克，吉。'},
            {'yao': '九五', 'text': '同人，先号咷而后笑，大师克相遇。', 'meaning': '与人和同，先号哭后欢笑，大军克敌相遇。'},
            {'yao': '上九', 'text': '同人于郊，无悔。', 'meaning': '在郊外与人和同，没有悔恨。'},
        ]
    },
    (3, 1): {
        'name': '火天大有',
        'judgment': '吉',
        'gua_ci': '元亨。',
        'description': '丰盛之卦，主富足、收获。火在天上，大有。君子以遏恶扬善，顺天休命。',
        'yao_ci': [
            {'yao': '初九', 'text': '无交害，匪咎，艰则无咎。', 'meaning': '没有交相侵害，不是灾祸，艰难则无灾。'},
            {'yao': '九二', 'text': '大车以载，有攸往，无咎。', 'meaning': '用大车装载，有所前往，无灾。'},
            {'yao': '九三', 'text': '公用亨于天子，小人弗克。', 'meaning': '公侯向天子朝贡，小人不能胜任。'},
            {'yao': '九四', 'text': '匪其彭，无咎。', 'meaning': '不自大骄横，无灾。'},
            {'yao': '六五', 'text': '厥孚交如，威如，吉。', 'meaning': '诚信相交，有威严，吉。'},
            {'yao': '上九', 'text': '自天佑之，吉无不利。', 'meaning': '自上天保佑，吉祥无所不利。'},
        ]
    },
    (7, 8): {
        'name': '地山谦',
        'judgment': '吉',
        'gua_ci': '亨，君子有终。',
        'description': '谦逊之卦，主谦虚、退让。地中有山，谦。君子以裒多益寡，称物平施。',
        'yao_ci': [
            {'yao': '初六', 'text': '谦谦君子，用涉大川，吉。', 'meaning': '谦而又谦的君子，用以渡大川，吉。'},
            {'yao': '六二', 'text': '鸣谦，贞吉。', 'meaning': '名声外扬而谦逊，守正则吉。'},
            {'yao': '九三', 'text': '劳谦君子，有终吉。', 'meaning': '勤劳而谦逊的君子，有好结果吉。'},
            {'yao': '六四', 'text': '无不利，撝谦。', 'meaning': '无所不利，发挥谦逊。'},
            {'yao': '六五', 'text': '不富以其邻，利用侵伐，无不利。', 'meaning': '不富足因为邻人，利于征讨，无所不利。'},
            {'yao': '上六', 'text': '鸣谦，利用行师，征邑国。', 'meaning': '名声外扬而谦逊，利于用兵征伐邑国。'},
        ]
    },
    (8, 7): {
        'name': '雷地豫',
        'judgment': '吉',
        'gua_ci': '利建侯行师。',
        'description': '欢乐之卦，主喜悦、安逸。雷出地奋，豫。先王以作乐崇德，殷荐之上帝，以配祖考。',
        'yao_ci': [
            {'yao': '初六', 'text': '鸣豫，凶。', 'meaning': '自鸣得意享乐，凶。'},
            {'yao': '六二', 'text': '介于石，不终日，贞吉。', 'meaning': '坚如磐石，不终日沉迷，守正则吉。'},
            {'yao': '六三', 'text': '盱豫，悔。迟有悔。', 'meaning': '媚上求乐，有悔恨。迟缓也有悔恨。'},
            {'yao': '九四', 'text': '由豫，大有得，勿疑，朋盍簪。', 'meaning': '因他人而享乐，大有收获，不疑，朋友相聚如簪聚发。'},
            {'yao': '六五', 'text': '贞疾，恒不死。', 'meaning': '守正有病，长久不死。'},
            {'yao': '上六', 'text': '冥豫，成有渝，无咎。', 'meaning': '昏沉迷于享乐，成功后有变化，无灾。'},
        ]
    },
    (4, 7): {
        'name': '雷山小过',
        'judgment': '平',
        'gua_ci': '亨，利贞，可小事，不可大事。飞鸟遗之音，不宜上宜下，大吉。',
        'description': '小过之卦，主小有过越、谦卑行事。山上有雷，小过。君子以行过乎恭，丧过乎哀，用过乎俭。',
        'yao_ci': [
            {'yao': '初六', 'text': '飞鸟以凶。', 'meaning': '飞鸟向上飞有凶险。'},
            {'yao': '六二', 'text': '过其祖，遇其妣，不及其君，遇其臣，无咎。', 'meaning': '越过祖父，遇到祖母，不及于君王，遇到臣子，无灾。'},
            {'yao': '九三', 'text': '弗过防之，从或戕之，凶。', 'meaning': '不过分防备，放纵或许被杀害，凶。'},
            {'yao': '九四', 'text': '无咎，弗过遇之，往厉必戒，勿用永贞。', 'meaning': '无灾，不过分而相遇，前往危险必须戒备，不可永久守正。'},
            {'yao': '六五', 'text': '密云不雨，自我西郊，公弋取彼在穴。', 'meaning': '密云不下雨，从我西郊而来，公侯射鸟取之于穴中。'},
            {'yao': '上六', 'text': '弗遇过之，飞鸟离之，凶，是谓灾眚。', 'meaning': '不相遇而越过，飞鸟被网罗，凶，这叫灾祸。'},
        ]
    },
    (7, 4): {
        'name': '山雷颐',
        'judgment': '吉',
        'gua_ci': '贞吉，观颐，自求口实。',
        'description': '颐养之卦，主养生、调养。山下有雷，颐。君子以慎言语，节饮食。',
        'yao_ci': [
            {'yao': '初九', 'text': '舍尔灵龟，观我朵颐，凶。', 'meaning': '舍弃你灵验的龟甲，观看我鼓起的腮帮子，凶。'},
            {'yao': '六二', 'text': '颠颐，拂经于丘，颐征凶。', 'meaning': '颠倒颐养，违背常理于山丘，颐养出征凶。'},
            {'yao': '六三', 'text': '拂颐，贞凶，十年勿用，无攸利。', 'meaning': '违背颐养之道，守正凶，十年不可用，无所利。'},
            {'yao': '六四', 'text': '颠颐，吉，虎视眈眈，其欲逐逐，无咎。', 'meaning': '颠倒颐养，吉，虎视眈眈，欲望迫切，无灾。'},
            {'yao': '六五', 'text': '拂经，居贞吉，不可涉大川。', 'meaning': '违背常理，居守正则吉，不可渡大川。'},
            {'yao': '上九', 'text': '由颐，厉吉，利涉大川。', 'meaning': '从于颐养，危险而吉，利于渡大川。'},
        ]
    },
}


def _build_full_hexagram_map():
    """构建完整的64卦映射表，补全剩余卦象的基础信息"""
    base_names = {
        (2, 2): '兑为泽', (3, 3): '离为火', (4, 4): '震为雷',
        (5, 5): '巽为风', (6, 6): '坎为水', (7, 7): '艮为山',
        (2, 6): '泽水困', (2, 8): '泽地萃', (2, 7): '泽山咸',
        (6, 7): '水山蹇', (4, 6): '雷水解', (4, 5): '雷风恒',
        (8, 5): '地风升', (2, 5): '泽风大过', (2, 4): '泽雷随',
        (5, 3): '风火家人', (5, 4): '风雷益', (1, 4): '天雷无妄',
        (3, 4): '火雷噬嗑', (7, 5): '山风蛊', (3, 7): '火山旅',
        (3, 5): '火风鼎', (3, 6): '火水未济', (5, 6): '风水涣',
        (8, 4): '地雷复', (8, 2): '地泽临', (4, 1): '雷天大壮',
        (2, 1): '泽天夬', (6, 3): '水火既济', (6, 2): '水泽节',
        (6, 5): '水风井', (4, 3): '雷火丰', (8, 3): '地火明夷',
        (5, 2): '风泽中孚', (5, 7): '风山渐', (7, 3): '山火贲',
        (7, 1): '山天大畜', (7, 2): '山泽损', (3, 2): '火泽睽',
        (1, 7): '天山遁', (1, 5): '天风姤', (5, 8): '风地观',
        (7, 6): '山水蒙', (3, 8): '火地晋', (6, 2): '水泽节',
        (4, 8): '雷地豫', (2, 3): '泽火革', (4, 2): '雷泽归妹',
    }
    
    for key, name in base_names.items():
        if key not in HEXAGRAMS:
            upper_wuxing = BAGUA[key[0]]['wuxing']
            lower_wuxing = BAGUA[key[1]]['wuxing']
            HEXAGRAMS[key] = {
                'name': name,
                'judgment': '平',
                'gua_ci': '',
                'description': f'{name}卦，{BAGUA[key[0]]["nature"]}上{BAGUA[key[1]]["nature"]}下。',
                'yao_ci': [
                    {'yao': ('初九' if key[1] in [1,2,3,4,5] else '初六'), 'text': '', 'meaning': ''},
                    {'yao': ('九二' if key[1] in [1,2,3,4,5] else '六二'), 'text': '', 'meaning': ''},
                    {'yao': ('九三' if key[1] in [1,2,3,4,5] else '六三'), 'text': '', 'meaning': ''},
                    {'yao': ('九四' if key[0] in [1,2,3,4,5] else '六四'), 'text': '', 'meaning': ''},
                    {'yao': ('九五' if key[0] in [1,2,3,4,5] else '六五'), 'text': '', 'meaning': ''},
                    {'yao': ('上九' if key[0] in [1,2,3,4,5] else '上六'), 'text': '', 'meaning': ''},
                ]
            }
    
    return HEXAGRAMS


HEXAGRAMS = _build_full_hexagram_map()


class HexagramAnalyzer:
    """卦象分析器 - 解读卦象、爻辞及吉凶判断"""

    def __init__(self):
        self.bagua = BAGUA
        self.hexagrams = HEXAGRAMS

    def get_bagua_info(self, num):
        """获取八卦单卦信息"""
        return self.bagua.get(num, {'name': '未知', 'nature': '', 'symbol': '', 'wuxing': '', 'description': ''})

    def get_hexagram_info(self, upper_num, lower_num):
        """获取64卦完整信息"""
        key = (upper_num, lower_num)
        return self.hexagrams.get(key, {
            'name': '未知卦',
            'judgment': '平',
            'gua_ci': '',
            'description': '',
            'yao_ci': []
        })

    def analyze_divination(self, divination_result, all_hexagrams):
        """
        分析完整的起卦结果
        返回本卦、互卦、变卦、错卦、综卦的详细分析及综合判断
        """
        base_upper = divination_result['upper_num']
        base_lower = divination_result['lower_num']
        changing_yao = divination_result['changing_yao']
        question = divination_result.get('question', '')

        base_info = self.get_hexagram_info(base_upper, base_lower)

        bi_upper = self._extract_hex_num(all_hexagrams['bian']['upper_yangs'])
        bi_lower = self._extract_hex_num(all_hexagrams['bian']['lower_yangs'])
        bi_info = self.get_hexagram_info(bi_upper, bi_lower)

        hu_upper = self._extract_hex_num(all_hexagrams['hu']['upper_yangs'])
        hu_lower = self._extract_hex_num(all_hexagrams['hu']['lower_yangs'])
        hu_info = self.get_hexagram_info(hu_upper, hu_lower)

        cuo_upper = self._extract_hex_num(all_hexagrams['cuo']['upper_yangs'])
        cuo_lower = self._extract_hex_num(all_hexagrams['cuo']['lower_yangs'])
        cuo_info = self.get_hexagram_info(cuo_upper, cuo_lower)

        zong_upper = self._extract_hex_num(all_hexagrams['zong']['upper_yangs'])
        zong_lower = self._extract_hex_num(all_hexagrams['zong']['lower_yangs'])
        zong_info = self.get_hexagram_info(zong_upper, zong_lower)

        yao_text = ''
        yao_meaning = ''
        yao_name = ''
        yao_ci_list = base_info.get('yao_ci', [])
        if yao_ci_list and changing_yao <= len(yao_ci_list):
            yao_data = yao_ci_list[changing_yao - 1]
            yao_name = yao_data.get('yao', '')
            yao_text = yao_data.get('text', '')
            yao_meaning = yao_data.get('meaning', '')

        judgment = self._make_judgment(base_info, bi_info, changing_yao)
        suggestions = self._generate_suggestions(base_info, bi_info, judgment, question)

        return {
            'question': question,
            'base': {
                'name': base_info.get('name', ''),
                'upper_num': base_upper,
                'lower_num': base_lower,
                'upper_name': self.get_bagua_info(base_upper)['name'],
                'lower_name': self.get_bagua_info(base_lower)['name'],
                'upper_nature': self.get_bagua_info(base_upper)['nature'],
                'lower_nature': self.get_bagua_info(base_lower)['nature'],
                'upper_symbol': self.get_bagua_info(base_upper)['symbol'],
                'lower_symbol': self.get_bagua_info(base_lower)['symbol'],
                'description': base_info.get('description', ''),
                'judgment': base_info.get('judgment', ''),
                'gua_ci': base_info.get('gua_ci', ''),
                'yao_ci': yao_ci_list,
                'changing_yao': changing_yao,
                'changing_yao_name': yao_name,
                'changing_yao_text': yao_text,
                'changing_yao_meaning': yao_meaning
            },
            'hu': {
                'name': hu_info.get('name', ''),
                'upper_num': hu_upper,
                'lower_num': hu_lower,
                'description': hu_info.get('description', '')
            },
            'bian': {
                'name': bi_info.get('name', ''),
                'upper_num': bi_upper,
                'lower_num': bi_lower,
                'description': bi_info.get('description', ''),
                'judgment': bi_info.get('judgment', '')
            },
            'cuo': {
                'name': cuo_info.get('name', ''),
                'upper_num': cuo_upper,
                'lower_num': cuo_lower,
                'description': cuo_info.get('description', '')
            },
            'zong': {
                'name': zong_info.get('name', ''),
                'upper_num': zong_upper,
                'lower_num': zong_lower,
                'description': zong_info.get('description', '')
            },
            'overall_judgment': judgment,
            'suggestions': suggestions,
            'wuxing_analysis': self._analyze_wuxing(base_upper, base_lower, bi_upper, bi_lower)
        }

    def _extract_hex_num(self, yangs):
        """从爻信息提取卦的先天数（二进制转十进制+1）"""
        num = 0
        for yao in yangs:
            num = num * 2 + (1 if yao['symbol_short'] == '阳' else 0)
        num = num + 1
        if num < 1:
            num = 1
        elif num > 8:
            num = num % 8
            if num == 0:
                num = 8
        return num

    def _make_judgment(self, base_info, bi_info, changing_yao):
        """综合判断吉凶"""
        base_judgment = base_info.get('judgment', '平')
        bi_judgment = bi_info.get('judgment', '平')

        judgments = {'吉': 2, '平': 1, '凶': 0}
        base_score = judgments.get(base_judgment, 1)
        bi_score = judgments.get(bi_judgment, 1)

        total_score = base_score + bi_score

        if total_score >= 3:
            return '吉'
        elif total_score >= 2:
            return '平'
        else:
            return '凶'

    def _generate_suggestions(self, base_info, bi_info, judgment, question=''):
        """生成趋吉避凶建议"""
        suggestions = []

        if judgment == '吉':
            suggestions.append('运势吉利，宜积极进取，把握良机。')
            suggestions.append('保持谦虚谨慎，善始善终，不可骄傲自满。')
        elif judgment == '平':
            suggestions.append('运势平稳，宜稳扎稳打，不宜冒进。')
            suggestions.append('耐心等待时机，做好准备工作，厚积薄发。')
        else:
            suggestions.append('运势不佳，宜守静不动，避免冒险。')
            suggestions.append('反思自身问题，寻求贵人相助，积德行善。')

        base_name = base_info.get('name', '')
        base_desc = base_info.get('description', '')

        if '乾' in base_name or '刚健' in base_desc:
            suggestions.append('宜发挥刚健进取精神，但需避免过刚易折。')
        if '坤' in base_name or '柔顺' in base_desc:
            suggestions.append('宜以柔克刚，厚德载物，包容忍让。')
        if '屯' in base_name or '艰难' in base_desc:
            suggestions.append('当前处于困难阶段，需坚定信念，逐步积累，厚积薄发。')
        if '蒙' in base_name or '启蒙' in base_desc:
            suggestions.append('宜虚心学习，请教明师，勿自以为是。')
        if '需' in base_name or '等待' in base_desc:
            suggestions.append('宜耐心等待时机，不可急于求成。')
        if '讼' in base_name or '争讼' in base_desc:
            suggestions.append('宜避免口舌争端，退一步海阔天空。')
        if '师' in base_name or '军队' in base_desc:
            suggestions.append('宜有组织有纪律，谋定而后动。')
        if '比' in base_name or '亲比' in base_desc:
            suggestions.append('宜广结善缘，与人为善，得道多助。')

        bi_name = bi_info.get('name', '')
        bi_desc = bi_info.get('description', '')
        bi_judgment_val = bi_info.get('judgment', '')

        if bi_judgment_val == '吉' or '吉' in bi_desc:
            suggestions.append('未来趋势向好，坚持努力终将成功。')
        elif bi_judgment_val == '凶':
            suggestions.append('未来需谨慎行事，提前做好防范措施。')

        if question:
            suggestions.append(f'针对所问「{question}」，需结合实际情况灵活应对。')

        return suggestions

    def _analyze_wuxing(self, base_upper, base_lower, bi_upper, bi_lower):
        """五行生克分析"""
        wuxing_sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        wuxing_ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

        base_upper_wx = self.get_bagua_info(base_upper)['wuxing']
        base_lower_wx = self.get_bagua_info(base_lower)['wuxing']
        bi_upper_wx = self.get_bagua_info(bi_upper)['wuxing']
        bi_lower_wx = self.get_bagua_info(bi_lower)['wuxing']

        def get_relation(a, b):
            if a == b:
                return '比和'
            elif wuxing_sheng.get(a) == b:
                return '我生'
            elif wuxing_sheng.get(b) == a:
                return '生我'
            elif wuxing_ke.get(a) == b:
                return '我克'
            elif wuxing_ke.get(b) == a:
                return '克我'
            return '未知'

        return {
            'base_upper_wuxing': base_upper_wx,
            'base_lower_wuxing': base_lower_wx,
            'base_relation': get_relation(base_upper_wx, base_lower_wx),
            'bian_upper_wuxing': bi_upper_wx,
            'bian_lower_wuxing': bi_lower_wx,
            'bian_relation': get_relation(bi_upper_wx, bi_lower_wx)
        }
