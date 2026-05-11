import math

CITIES = {
    '北京': {'latitude': 39.9042, 'longitude': 116.4074, 'timezone': 8},
    '上海': {'latitude': 31.2304, 'longitude': 121.4737, 'timezone': 8},
    '广州': {'latitude': 23.1291, 'longitude': 113.2644, 'timezone': 8},
    '深圳': {'latitude': 22.5431, 'longitude': 114.0579, 'timezone': 8},
    '杭州': {'latitude': 30.2741, 'longitude': 120.1552, 'timezone': 8},
    '南京': {'latitude': 32.0603, 'longitude': 118.7969, 'timezone': 8},
    '成都': {'latitude': 30.5728, 'longitude': 104.0668, 'timezone': 8},
    '重庆': {'latitude': 29.4316, 'longitude': 106.9123, 'timezone': 8},
    '武汉': {'latitude': 30.5928, 'longitude': 114.3055, 'timezone': 8},
    '西安': {'latitude': 34.2619, 'longitude': 108.9463, 'timezone': 8},
    '天津': {'latitude': 39.1262, 'longitude': 117.2272, 'timezone': 8},
    '苏州': {'latitude': 31.3251, 'longitude': 120.6295, 'timezone': 8},
    '郑州': {'latitude': 34.7466, 'longitude': 113.6253, 'timezone': 8},
    '长沙': {'latitude': 28.2281, 'longitude': 112.9388, 'timezone': 8},
    '青岛': {'latitude': 36.0671, 'longitude': 120.3826, 'timezone': 8},
    '沈阳': {'latitude': 41.8047, 'longitude': 123.4328, 'timezone': 8},
    '大连': {'latitude': 38.9140, 'longitude': 121.6147, 'timezone': 8},
    '厦门': {'latitude': 24.4798, 'longitude': 118.0894, 'timezone': 8},
    '哈尔滨': {'latitude': 45.8038, 'longitude': 126.5350, 'timezone': 8},
    '长春': {'latitude': 43.8868, 'longitude': 125.3231, 'timezone': 8},
    '济南': {'latitude': 36.6682, 'longitude': 116.9850, 'timezone': 8},
    '合肥': {'latitude': 31.8654, 'longitude': 117.2264, 'timezone': 8},
    '福州': {'latitude': 26.0753, 'longitude': 119.3062, 'timezone': 8},
    '昆明': {'latitude': 24.8820, 'longitude': 102.8329, 'timezone': 8},
    '南宁': {'latitude': 22.8157, 'longitude': 108.3200, 'timezone': 8},
    '贵阳': {'latitude': 26.5726, 'longitude': 106.7131, 'timezone': 8},
    '太原': {'latitude': 37.8716, 'longitude': 112.5492, 'timezone': 8},
    '石家庄': {'latitude': 38.0423, 'longitude': 114.4786, 'timezone': 8},
    '南昌': {'latitude': 28.6898, 'longitude': 115.8953, 'timezone': 8},
    '无锡': {'latitude': 31.5976, 'longitude': 120.3198, 'timezone': 8},
}

SOLAR_TERMS = [
    {'name': '立春', 'angle': 315},
    {'name': '雨水', 'angle': 330},
    {'name': '惊蛰', 'angle': 345},
    {'name': '春分', 'angle': 0},
    {'name': '清明', 'angle': 15},
    {'name': '谷雨', 'angle': 30},
    {'name': '立夏', 'angle': 45},
    {'name': '小满', 'angle': 60},
    {'name': '芒种', 'angle': 75},
    {'name': '夏至', 'angle': 90},
    {'name': '小暑', 'angle': 105},
    {'name': '大暑', 'angle': 120},
    {'name': '立秋', 'angle': 135},
    {'name': '处暑', 'angle': 150},
    {'name': '白露', 'angle': 165},
    {'name': '秋分', 'angle': 180},
    {'name': '寒露', 'angle': 195},
    {'name': '霜降', 'angle': 210},
    {'name': '立冬', 'angle': 225},
    {'name': '小雪', 'angle': 240},
    {'name': '大雪', 'angle': 255},
    {'name': '冬至', 'angle': 270},
    {'name': '小寒', 'angle': 285},
    {'name': '大寒', 'angle': 300},
]

def get_city_data(city_name):
    return CITIES.get(city_name, CITIES['北京'])

def calculate_julian_day(year, month, day, hour=12):
    if month <= 2:
        year -= 1
        month += 12
    
    A = year // 100
    B = 2 - A + A // 4
    C = int(365.25 * (year + 4716))
    D = int(30.6001 * (month + 1))
    
    jd = B + C + D + day + hour / 24 - 1524.5
    return jd

def calculate_solar_time_difference(year, month, day, hour=12):
    jd = calculate_julian_day(year, month, day, hour)
    T = (jd - 2451545.0) / 36525.0
    
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    L0 = L0 % 360
    
    g = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    g = g % 360
    
    center = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(math.radians(g))
    center += (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * g))
    center += 0.000289 * math.sin(math.radians(3 * g))
    
    lambda_sun = L0 + center
    omega = 125.04 - 1934.136 * T
    
    equation_of_time = (omega - lambda_sun) * 4
    equation_of_time = ((equation_of_time + 720) % 1440) - 720
    
    return equation_of_time

def calculate_true_solar_time(year, month, day, hour, minute, longitude, timezone=8):
    if hour == 24:
        hour = 0
        day += 1
    
    std_time_minutes = hour * 60 + minute
    
    longitude_offset = (longitude - timezone * 15) * 4
    
    solar_diff = calculate_solar_time_difference(year, month, day, hour)
    
    true_solar_minutes = std_time_minutes + longitude_offset + solar_diff
    
    if true_solar_minutes < 0:
        true_solar_minutes += 1440
        day -= 1
    elif true_solar_minutes >= 1440:
        true_solar_minutes -= 1440
        day += 1
    
    true_hour = int(true_solar_minutes // 60)
    true_minute = int(round(true_solar_minutes % 60))
    
    if true_minute >= 60:
        true_minute -= 60
        true_hour += 1
    
    return {
        'hour': true_hour,
        'minute': true_minute,
        'day_adjust': day,
        'correction': int(round(longitude_offset + solar_diff))
    }

def get_solar_term_info(year, month, day):
    jd = calculate_julian_day(year, month, day)
    T = (jd - 2451545.0) / 36525.0
    
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    L0 = L0 % 360
    
    g = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    g = g % 360
    
    center = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(math.radians(g))
    center += (0.019993 - 0.000101 * T) * math.sin(math.radians(2 * g))
    center += 0.000289 * math.sin(math.radians(3 * g))
    
    sun_longitude = L0 + center
    sun_longitude = sun_longitude % 360
    
    prev_term = None
    next_term = None
    days_to_next = 999
    
    for i, term in enumerate(SOLAR_TERMS):
        term_angle = term['angle']
        diff = (term_angle - sun_longitude) % 360
        
        if diff < days_to_next:
            days_to_next = diff
            next_term = term['name']
            prev_term = SOLAR_TERMS[i-1]['name'] if i > 0 else SOLAR_TERMS[-1]['name']
    
    month_solar = (int(sun_longitude // 15) + 3) % 12 + 1
    month_names = ['', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
    
    return {
        'sun_longitude': round(sun_longitude, 2),
        'current_term': prev_term,
        'next_term': next_term,
        'days_to_next': round(days_to_next * 365 / 360),
        'monthly_term': month_names[month_solar]
    }

def get_timezone_offset(longitude):
    return int(longitude // 15)

def get_correction_display(correction_minutes):
    if correction_minutes == 0:
        return "±0分"
    elif correction_minutes > 0:
        return f"+{correction_minutes}分"
    else:
        return f"{correction_minutes}分"
