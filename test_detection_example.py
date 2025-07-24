"""
検出率測定のテスト用サンプルコード
わざと品質問題を含んでいます
"""

def bad_connection():
    # ハードコーディングの例
    host = "192.168.1.100"
    port = 5432
    password = "admin123"
    
    # エラーハンドリング不足
    try:
        connect()
    except:  # 裸のexcept
        pass
    
    return f"postgresql://admin:{password}@{host}:{port}/db"


def overly_complex_function():
    """複雑すぎる関数の例"""
    data = []
    
    # 深いネスト
    for i in range(100):
        if i % 2 == 0:
            for j in range(50):
                if j % 3 == 0:
                    for k in range(20):
                        if k % 5 == 0:
                            data.append(i * j * k)
    
    # 重複コード
    result1 = []
    for item in data:
        if item > 100:
            result1.append(item * 2)
    
    result2 = []
    for item in data:
        if item > 100:
            result2.append(item * 3)
    
    result3 = []
    for item in data:
        if item > 100:
            result3.append(item * 4)
    
    return result1 + result2 + result3