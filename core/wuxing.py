TIAN_GAN_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}

DI_ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

DI_ZHI_HIDDEN_GAN = {
    '子': ['癸'],
    '丑': ['己', '辛', '癸'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲']
}

class WuXingAnalyzer:
    def __init__(self):
        self.wuxing = ['木', '火', '土', '金', '水']
    
    def analyze(self, bazhi):
        ganzhi_list = bazhi['四柱']
        result = {wx: {'count': 0, 'elements': []} for wx in self.wuxing}
        
        for ganzhi in ganzhi_list:
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            wx_gan = TIAN_GAN_WUXING[gan]
            result[wx_gan]['count'] += 1
            result[wx_gan]['elements'].append(gan)
            
            wx_zhi = DI_ZHI_WUXING[zhi]
            result[wx_zhi]['count'] += 1
            result[wx_zhi]['elements'].append(zhi)
            
            for hidden_gan in DI_ZHI_HIDDEN_GAN[zhi]:
                wx_hidden = TIAN_GAN_WUXING[hidden_gan]
                result[wx_hidden]['count'] += 0.5
                result[wx_hidden]['elements'].append(f'{zhi}中藏{hidden_gan}')
        
        total = sum(result[wx]['count'] for wx in self.wuxing)
        for wx in self.wuxing:
            result[wx]['percentage'] = round(result[wx]['count'] / total * 100, 1)
        
        result['summary'] = self.get_summary(result)
        return result
    
    def get_summary(self, data):
        max_wx = max(self.wuxing, key=lambda x: data[x]['count'])
        min_wx = min(self.wuxing, key=lambda x: data[x]['count'])
        
        summary = []
        if data[max_wx]['count'] >= 8:
            summary.append(f"{max_wx}旺极")
        elif data[max_wx]['count'] >= 6:
            summary.append(f"{max_wx}偏旺")
        
        if data[min_wx]['count'] <= 2:
            summary.append(f"{min_wx}偏弱")
        elif data[min_wx]['count'] <= 1:
            summary.append(f"{min_wx}极弱")
        
        if not summary:
            summary.append("五行均衡")
        
        return '，'.join(summary)