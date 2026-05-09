import sys
import traceback

sys.path.insert(0, '.')

def test_baazi():
    try:
        from core.baazi import BaZiCalculator
        print("测试八字排盘模块...")
        calculator = BaZiCalculator()
        
        result = calculator.calculate(1990, 1, 1, 12, is_lunar=False)
        print(f"排盘结果: {result}")
        print("八字排盘模块测试通过!")
        return result
    except Exception as e:
        print(f"八字排盘模块测试失败: {e}")
        traceback.print_exc()
        return None

def test_wuxing(bazi_result):
    try:
        from core.wuxing import WuXingAnalyzer
        print("\n测试五行分析模块...")
        analyzer = WuXingAnalyzer()
        result = analyzer.analyze(bazi_result)
        print(f"五行分析结果: {result}")
        print("五行分析模块测试通过!")
        return result
    except Exception as e:
        print(f"五行分析模块测试失败: {e}")
        traceback.print_exc()
        return None

def test_shishen(bazi_result):
    try:
        from core.shishen import ShiShenAnalyzer
        print("\n测试十神分析模块...")
        analyzer = ShiShenAnalyzer()
        result = analyzer.analyze(bazi_result)
        print(f"十神分析结果: {result}")
        print("十神分析模块测试通过!")
        return result
    except Exception as e:
        print(f"十神分析模块测试失败: {e}")
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("="*50)
    print("八字排盘程序测试套件 - 核心算法")
    print("="*50)
    
    bazi_result = test_baazi()
    
    if bazi_result:
        wuxing_result = test_wuxing(bazi_result)
        shishen_result = test_shishen(bazi_result)
    
    print("\n" + "="*50)
    print("核心算法测试完成")
    print("="*50)