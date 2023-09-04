

# 额度卡领券
curl --location  --X POST 'http://127.0.0.1:21100/api/crm/card/10080/member/receive' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "member_no":"admin1102",
    "receive_id":"receive_id_1102",
    "outer_str":"default",
    "card_info":[
        {"card_id":"AJ3R3Q5CTEZN4DHY9TZATH","qty":1,"cost_center":"cost_center0713"}
    ]
}'



# 验证额度卡核销
curl --location  --X POST 'http://127.0.0.1:21100/api/crm/card/10080/member/redeem' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "member_no":"admin1102",
    "outer_redeem_id":"redeem_id_11021",
    "store_code":"12",
    "card_id":"AJ3R3Q5CTEZN4DHY9TZATH",
    "card_code":"221102528329110400",
    "amount": 1
}'

# 验证额度卡核销冲正
curl --location  --X POST 'http://127.0.0.1:21100/api/crm/card/10080/member/redeem_reverse' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "member_no":"admin1102",
    "outer_redeem_id":"redeem_id_1102",
    "card_id":"AJ3R3Q5CTEZN4DHY9TZATH"
}'

# 查询卡包
curl --location  --X POST 'http://127.0.0.1:21100/api/crm/card/10080/member/card_list?member_no=admin1102&page=1&page_size=3&code_status=1'
