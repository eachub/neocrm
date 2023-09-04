import csv
import openpyxl
from common.biz.codec import define_cipher, decrypt_item
cipher = define_cipher("EROS#CRM987")

# 读取 CSV 文件中的第一列
with open('enc_mobile.csv', 'r') as csv_file:
    reader = csv.reader(csv_file)
    header = next(reader)
    first_column = [row[0] for row in reader]
# 解密
processed_data = [decrypt_item(cipher, x) for x in first_column]

# 创建一个新的 xlsx 文档
workbook = openpyxl.Workbook()
sheet = workbook.active

# 将处理后的数据写入到新的 xlsx 文档中
for i, value in enumerate(processed_data, 1):
    sheet.cell(row=i, column=1, value=value)

# 保存 xlsx 文档
workbook.save('output.xlsx')
