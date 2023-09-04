
class GeoOriginFrom:
    FROM_PLATFORM = 0
    FROM_FILL_IN = 1
    FROM_IP = 2
    FROM_MOBILE = 3

    PLATFORM_SET = {FROM_PLATFORM, FROM_FILL_IN, FROM_IP, FROM_MOBILE}

    @staticmethod
    def contains_platform(platform_from):
        try:
            return int(platform_from) in GeoOriginFrom.PLATFORM_SET
        except Exception as ex:
            return False
        
        
SUPPORT_PLATFORM = ["wechat", "alipay", "douyin", 'tmall']
        
        
PLATFORM_MAP = {
    "wechat": "微信",
    "alipay": "支付宝",
    "douyin": "抖音"
}