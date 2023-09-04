from mtkext.regex import is_mobile

from common.biz.const import RC


class MobileFinder:

    def __init__(self, mobile_geo_file):
        self.mobile_relation = {}
        with open(mobile_geo_file, 'r') as f:
            for line in f:
                mobile_prefix7, province, city = line.strip().split('|')
                self.mobile_relation[mobile_prefix7] = f"{province}|{city}"

    def search(self, mobile):
        if not is_mobile(mobile):
            return RC.PARAMS_INVALID, "手机号码不正确"
            pass
        region = self.mobile_relation.get(mobile[:7], None)
        if not region:
            return RC.DATA_NOT_FOUND, "未找到对应的地理位置"
        return RC.OK, region


if __name__ == "__main__":
    finder = MobileFinder("./mobile-geo-201808.txt")
    status, region = finder.search("17721446845")
    print(status, region)