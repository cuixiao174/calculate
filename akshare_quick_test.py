"""
AKSHARE接口快速测试脚本
用于日常快速检查AKSHARE主要接口的状态
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time

def quick_test_interface(func, *args, **kwargs):
    """快速测试单个接口"""
    test_name = kwargs.pop('test_name', func.__name__)
    
    try:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        if result is None:
            return test_name, "❌ 失败", "返回None", end_time - start_time
        
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return test_name, "❌ 失败", "空DataFrame", end_time - start_time
            else:
                return test_name, "✅ 通过", f"数据形状: {result.shape}", end_time - start_time
        else:
            return test_name, "✅ 通过", f"类型: {type(result).__name__}", end_time - start_time
            
    except Exception as e:
        return test_name, "❌ 失败", str(e), 0

def run_quick_test():
    """运行快速测试"""
    print("🚀 AKSHARE接口快速测试")
    print("=" * 50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    test_cases = [
        # 股票接口
        (ak.stock_info_a_code_name, {}, "股票列表"),
        (ak.stock_individual_info_em, {"symbol": "000001"}, "股票基本信息"),
        (ak.stock_zh_a_spot_em, {}, "实时行情"),
        
        # 基金接口 - 使用正确的接口名称
        (ak.fund_open_fund_daily_em, {}, "开放式基金"),
        
        # 期货接口
        (ak.futures_main_sina, {}, "期货主力合约"),
        
        # 宏观接口
        (ak.macro_china_cpi, {}, "CPI数据"),
        
        # 债券接口
        (ak.bond_zh_us_rate, {}, "国债收益率"),
        
        # 新闻接口 - 使用可用的新闻接口
        (ak.stock_news_em, {"symbol": "000001"}, "股票新闻"),
        
        # 指数接口
        (ak.index_stock_info, {}, "指数列表"),
    ]
    
    results = []
    total_time = 0
    
    print("\n📊 测试进度:")
    print("-" * 60)
    
    for i, (func, args, name) in enumerate(test_cases, 1):
        test_name, status, message, exec_time = quick_test_interface(func, **args, test_name=name)
        results.append((test_name, status, message, exec_time))
        total_time += exec_time
        
        print(f"{i:2d}. {test_name:15} {status:8} {message:20} {exec_time:.3f}s")
    
    # 统计结果
    passed = sum(1 for r in results if "✅" in r[1])
    failed = len(results) - passed
    
    print("\n" + "=" * 60)
    print("📈 测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {len(results)}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {failed}")
    print(f"成功率: {passed/len(results):.1%}")
    print(f"总耗时: {total_time:.3f} 秒")
    print(f"平均响应时间: {total_time/len(results):.3f} 秒")
    
    # 显示失败详情
    if failed > 0:
        print(f"\n❌ 失败详情:")
        for test_name, status, message, _ in results:
            if "❌" in status:
                print(f"  - {test_name}: {message}")
    
    return results

def test_specific_stock(stock_code="000001"):
    """测试特定股票的数据完整性"""
    print(f"\n🔍 测试股票 {stock_code} 数据完整性")
    print("-" * 40)
    
    tests = [
        ("基本信息", ak.stock_individual_info_em, {"symbol": stock_code}),
        ("实时行情", lambda: ak.stock_zh_a_spot_em().query(f"代码 == '{stock_code}'"), {}),
        ("财务指标", ak.stock_financial_analysis_indicator, {"symbol": stock_code}),
    ]
    
    for name, func, args in tests:
        try:
            result = func(**args) if args else func()
            if result is not None and (not isinstance(result, pd.DataFrame) or not result.empty):
                print(f"✅ {name}: 数据可用")
                if isinstance(result, pd.DataFrame):
                    print(f"   数据形状: {result.shape}")
            else:
                print(f"❌ {name}: 数据不可用")
        except Exception as e:
            print(f"❌ {name}: 错误 - {e}")

def check_akshare_version():
    """检查AKSHARE版本信息"""
    print("\n🔧 AKSHARE版本信息")
    print("-" * 30)
    try:
        # AKSHARE没有直接的版本查询函数，但我们可以检查一些基本功能
        print("✅ AKSHARE导入成功")
        print("📚 可用模块:")
        modules = [name for name in dir(ak) if not name.startswith('_')]
        print(f"   共 {len(modules)} 个模块")
        
        # 显示主要模块分类
        module_categories = {
            '股票': [m for m in modules if 'stock' in m.lower()],
            '基金': [m for m in modules if 'fund' in m.lower()],
            '期货': [m for m in modules if 'future' in m.lower()],
            '债券': [m for m in modules if 'bond' in m.lower()],
            '宏观': [m for m in modules if 'macro' in m.lower()],
        }
        
        for category, mods in module_categories.items():
            if mods:
                print(f"   {category}: {len(mods)} 个接口")
        
    except Exception as e:
        print(f"❌ 检查版本信息失败: {e}")

def main():
    """主函数"""
    print("🚀 AKSHARE快速测试工具")
    print("=" * 50)
    
    # 检查版本信息
    check_akshare_version()
    
    # 运行快速测试
    results = run_quick_test()
    
    # 测试特定股票
    test_specific_stock("000001")  # 平安银行
    test_specific_stock("600036")  # 招商银行
    
    print("\n🎉 快速测试完成！")
    print("💡 提示: 使用完整测试脚本进行更详细的测试")

if __name__ == "__main__":
    main()