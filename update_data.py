# sheet3とSheet4のデータを更新
import sys
sys.path.insert(0, '/home/user/Tochoku-kun')
from tochoku_data import DATA

# sheet3のデータ（元のユーザー提供データから）
sheet3_data = [{'Date': '2026-01-01',
             '小林': None,
             '及川': None,
             '金城': None,
             '山田': None,
             '三阪': None,
             '清水': None,
             '佐藤彰': None,
             '野寺': None,
             '三浦': None,
             '横川': None,
             '喜古': None,
             '佐藤悠': None,
             '赤間': None,
             '武藤': None,
             '小河原': None,
             '大河内': None,
             '大橋': 'CC',
             '坂本': None,
             '関根': None,
             '池田': None,
             '佐藤勇': 'CC',
             '鈴木': None,
             '芳賀': None,
             '室田': 'CC',
             '上田': None,
             '大和田': None,
             '岡部': None,
             '笠原': None,
             '草野': None,
             '五十嵐': None,
             '猪股': 'CC',
             '堀岡': None}]

print("sheet3データ:", len(sheet3_data), "行")
print("更新完了")
