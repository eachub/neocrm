from sanic.log import logger


class GeoFilter:
    def __init__(self, base_path):
        self.base_path = base_path
        self.city_provinces = {}
        self.provinces = {}
        self.countries = set()
        self.cities = {}
        self.fix_cities = {}
        self.unknown_city = {"yichun", "taizhou", "fuzhou", "朝阳", "yulin", "suzhou", "qianjiang", "chaoyang", "wuxi", "west", "east", "baoshan"}
        self.init_geo_data()

    def init_geo_data(self):
        with open(f'{self.base_path}/country.data', 'r', encoding='utf-8') as country, \
                open(f'{self.base_path}/province_city.data', 'r', encoding='utf-8') as province_city, \
                open(f'{self.base_path}/fix_city.data', 'r', encoding='utf-8') as fix_city, \
                open(f'{self.base_path}/city_mapping.data', encoding='utf-8') as city:
            for province_city_item in province_city:
                province_city_item = province_city_item.strip()
                fields = province_city_item.split(',')
                str_province = fields[0].lower()
                str_city = fields[1].lower()
                str_provincep = fields[2].lower()
                str_cityP = fields[3].lower()
                self.city_provinces[str_city] = ["中国", str_province, str_city]
                self.city_provinces[str_cityP] = ["中国", str_province, str_city]
                self.provinces[str_province] = ["中国", str_province, "未知"]
                self.provinces[str_provincep] = ["中国", str_province, "未知"]

            for country_item in country:
                country_item = country_item.strip()
                self.countries.add(country_item)

            for fix_city_item in fix_city:
                fix_city_item = fix_city_item.strip()
                array_fix_city = fix_city_item.split(',')
                self.fix_cities[array_fix_city[0] + array_fix_city[1]] = ["中国", array_fix_city[0], array_fix_city[1]]
                self.fix_cities[array_fix_city[2] + array_fix_city[3]] = ["中国", array_fix_city[0], array_fix_city[1]]

            for city_item in city:
                city_item = city_item.strip()
                city_item_array = city_item.split(',')
                self.cities[city_item_array[0]] = city_item_array[1]
        logger.info("load geo data success")

    def geo_format(self, country, province, city):
        if province:
            province = province.replace("省", "").replace("市", "").lower()
        if city:
            city = city.replace("市", "").lower()
            if city in self.cities.keys():
                city = self.cities.get(city)

        if city in self.unknown_city:
            key = province + city
            return self.fix_cities.get(key) if self.fix_cities.get(key) else ["中国", "未知", "未知"]
        city_result = self.city_provinces.get(city)
        if city_result:
            return city_result
        if province:
            province_result = self.provinces.get(province)
            if province_result:
                return province_result
            if country in self.countries:
                return [country, "未知", "未知"]
        return ["未知", "未知", "未知"]


if __name__ == '__main__':
    geo_filter = GeoFilter('./geo_data')
    print(geo_filter.geo_format("", "hubei", "qianjiang"))