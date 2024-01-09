import geopandas as gpd
from shapely.geometry import box
from flask import Flask, render_template, request, jsonify
import requests
import json
from concurrent.futures import ThreadPoolExecutor

api_key = "AIzaSyDqijJYRZ_VE5NspD_mo1lZqcbbM2D7GEE"
app = Flask(__name__)

# 获取城市数量
@app.route('/get-city-count', methods=['POST'])
def get_city_count():
    data = request.json
    ne = data['ne']
    sw = data['sw']

    count = query_city_count(ne, sw)

    return jsonify({'count': count})

# 主页面设置
@app.route('/')
def index():
    return render_template('index.html')

# 查询城市数量
def query_city_count(ne, sw):
    # 读取城市数据的 GeoJSON 文件
    cities = gpd.read_file('cities.geojson')
    # 创建查询区域的矩形
    query_box = box(sw['lng'], sw['lat'], ne['lng'], ne['lat'])
    # 筛选位于矩形内的城市
    cities_in_box = cities[cities.geometry.within(query_box)]

    return len(cities_in_box)

# 从txt文件获取城市列表
def get_city_list(file_name='cities.txt'):
    list_city = []
    # 打开文件并读取每一行
    with open(file_name, 'r', encoding='utf-8') as file:
        for line in file:
            # 以顿号分割每行中的城市名称
            cities = line.strip().split('、')
            # 将分割得到的城市名称添加到列表中
            list_city.extend(cities)
    return list_city

# 获取城市坐标
def get_coordinates(city, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city},中国&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        if result["results"]:
            location = result["results"][0]["geometry"]["location"]
            return {"city": city, "location": location}
    return {"city": city, "location": None}

# 创建 Geojson文件
def create_geojson(cities_coordinates):
    features = []
    for city in cities_coordinates:
        if city["location"]:
            feature = {
                "type": "Feature",
                "properties": {"name": city["city"]},
                "geometry": {
                    "type": "Point",
                    "coordinates": [city["location"]["lng"], city["location"]["lat"]]
                }
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson

# 获取城市信息
def get_city_info():
    # 中国完整地级市以上城市列表
    cities = get_city_list()
    # 使用多线程 ThreadPoolExecutor 来并行执行
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_coordinates, city, api_key) for city in cities]
        cities_coordinates = [future.result() for future in futures]

    geojson = create_geojson(cities_coordinates)

    with open('cities.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)

# 在 Flask 应用启动时启动线程
if __name__ == '__main__':
    get_city_info()
    app.run(debug=True)
