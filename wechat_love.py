# -*- coding: utf-8 -*-
import requests
import os
from datetime import datetime, timedelta, date
from zhdate import ZhDate

# ==========================================
# 环境变量读取与核心常量配置区
# ==========================================
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
OPEN_ID = os.environ.get("OPEN_ID")
TEMPLATE_ID = os.environ.get("TEMPLATE_ID")
TIANAPI_KEY = os.environ.get("TIANAPI_KEY")

CITY_NAME = "杭州"
LOVE_DATE = date(2019, 3, 10)
BIRTHDAY_LUNAR = (1998, 8, 18)

HOLIDAY_MESSAGES = {
    "01-01": "元旦",
    "02-14": "情人节",
    "03-08": "女神节",
    "05-20": "520",
    "10-01": "国庆节",
    "12-25": "圣诞节",
    "12-31": "跨年"
}

# ==========================================
# 基础时间与日期处理模块
# ==========================================
def get_beijing_today():
    """修正 GitHub Actions UTC 偏差的绝对时间基准"""
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    return beijing_now.date()

def get_love_days():
    return (get_beijing_today() - LOVE_DATE).days

def get_birthday_left():
    """农历至公历的动态投射与剩余计算"""
    today = get_beijing_today()
    try:
        birthday = ZhDate(today.year, BIRTHDAY_LUNAR[1], BIRTHDAY_LUNAR[2]).to_datetime().date()
    except Exception:
        birthday = date(today.year, 9, 20)
        
    if birthday < today:
        try:
            birthday = ZhDate(today.year + 1, BIRTHDAY_LUNAR[1], BIRTHDAY_LUNAR[2]).to_datetime().date()
        except Exception:
            birthday = date(today.year + 1, 9, 20)
            
    return (birthday - today).days

# ==========================================
# 高阶业务逻辑计算引擎
# ==========================================
def get_dynamic_holiday_str(today, birthday_left, love_days):
    """基于向量距离排序的下一节日测算算法"""
    if birthday_left == 0:
        return "今天是小胡胡的农历生日！🎂"
    if love_days > 0 and love_days % 365 == 0:
        return f"今天是恋爱 {love_days // 365} 周年纪念日！❤️"
    
    date_key = today.strftime("%m-%d")
    if date_key in HOLIDAY_MESSAGES:
        return f"今天是{HOLIDAY_MESSAGES[date_key]}快乐！❤️"
        
    candidates = {}
    candidates["农历生日"] = birthday_left
    
    try:
        anni_this_year = date(today.year, LOVE_DATE.month, LOVE_DATE.day)
    except ValueError:
        anni_this_year = date(today.year, LOVE_DATE.month, LOVE_DATE.day - 1)
        
    if anni_this_year > today:
        candidates["恋爱纪念日"] = (anni_this_year - today).days
    else:
        candidates["恋爱纪念日"] = (date(today.year + 1, LOVE_DATE.month, LOVE_DATE.day) - today).days
        
    for m_d, name in HOLIDAY_MESSAGES.items():
        m, d = map(int, m_d.split("-"))
        try:
            h_date = date(today.year, m, d)
        except ValueError:
            continue
            
        if h_date > today:
            candidates[name] = (h_date - today).days
        else:
            candidates[name] = (date(today.year + 1, m, d) - today).days
            
    next_name, next_days = min(candidates.items(), key=lambda x: x[1])
    return f"下个节日【{next_name}】还有 {next_days} 天 ⏳"

def get_segmented_weather_tips(weather_info):
    """提取天气提示片段，通过内联 \n 在运行时撑开微信客户端排版边界"""
    weather_str = weather_info.get("weather", "")
    low_str = weather_info.get("low", "")
    high_str = weather_info.get("high", "")
    
    lines = ["今天天气不错哦，", "希望你这一天，", "都有好心情相伴 ❤️"]
    
    try:
        clean_low = float(low_str.replace("℃", "").replace("°C", "").strip())
        clean_high = float(high_str.replace("℃", "").replace("°C", "").strip())
        
        if clean_high >= 35.0:
            lines = ["今天杭州比较热，", "记得多喝点水，", "空调也不要吹太久哦 ❤️"]
        elif clean_high >= 30.0:
            lines = ["今天气温有点偏高，", "出门注意做好防晒，", "多喝水谨防中暑 ❤️"]
        elif clean_low <= 10.0:
            lines = ["今天有点降温啦，", "记得多穿两件厚衣服，", "千万别感冒了 ❤️"]
        elif "雨" in weather_str:
            lines = ["杭州今天有雨，", "出门记得带伞哦～", "希望一路顺顺利利 ❤️"]
        elif "雪" in weather_str:
            lines = ["今天下雪啦，", "路面可能会打滑，", "走路要注意安全哦 ❤️"]
    except Exception:
        pass
        
    tip1 = lines[0] + "\n" if len(lines) > 0 else ""
    tip2 = lines[1] + "\n" if len(lines) > 1 else ""
    tip3 = lines[2] if len(lines) > 2 else ""
    
    return tip1, tip2, tip3

# ==========================================
# API 外部交互模块
# ==========================================
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    return requests.get(url, timeout=10).json().get("access_token")

def get_weather():
    try:
        url = f"https://apis.tianapi.com/tianqi/index?key={TIANAPI_KEY}&city={CITY_NAME}&type=1"
        res = requests.get(url, timeout=10).json()
        if res.get("code") == 200:
            data = res["result"]
            return {"weather": data["weather"], "low": data["lowest"], "high": data["highest"]}
    except Exception:
        pass
    return {"weather": "多云", "low": "20℃", "high": "25℃"}

def get_caihongpi():
    """获取天行数据的彩虹屁，并进行脱敏与占位符清洗"""
    try:
        url = f"https://apis.tianapi.com/caihongpi/index?key={TIANAPI_KEY}"
        res = requests.get(url, timeout=10).json()
        if res.get("code") == 200:
            content = res["result"]["content"]
            # 过滤清洗 API 附带的泛用型变量符
            return content.replace("XXX", "小胡胡")
    except Exception:
        pass
    return "今天也超级喜欢你！"

# ==========================================
# 主运行管道与载荷封装
# ==========================================
def send_message():
    access_token = get_access_token()
    if not access_token:
        print("❌ Token 获取中断")
        return False

    weather = get_weather()
    caihongpi = get_caihongpi()
    love_days = get_love_days()
    birthday_left = get_birthday_left()
    today = get_beijing_today()
    today_str = today.strftime("%Y年%m月%d日")

    holiday_str = get_dynamic_holiday_str(today, birthday_left, love_days)
    tip1, tip2, tip3 = get_segmented_weather_tips(weather)

    q1 = caihongpi[:18]
    q2 = caihongpi[18:36]
    q3 = caihongpi[36:54]
    
    temp_str = f"{weather['low']} ~ {weather['high']}"

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    data = {
        "touser": OPEN_ID,
        "template_id": TEMPLATE_ID,
        "data": {
            "d": {"value": today_str, "color": "#173177"},
            "c": {"value": CITY_NAME, "color": "#173177"},
            "w": {"value": weather["weather"], "color": "#173177"},
            # 第一处视觉隔离：注入 \n 将基础信息区与纪念日区块拉开
            "t": {"value": f"{temp_str}\n", "color": "#FF0000"},
            "ld": {"value": str(love_days), "color": "#FF69B4"},
            "bl": {"value": str(birthday_left), "color": "#FF69B4"},
            # 第二处视觉隔离：注入 \n 将纪念日区与专属提醒区块拉开
            "h": {"value": f"{holiday_str}\n", "color": "#FF8C00"},
            "t1": {"value": tip1, "color": "#008000"},
            "t2": {"value": tip2, "color": "#008000"},
            # 第三处视觉隔离：注入 \n 将提醒区块与情话区块拉开
            "t3": {"value": f"{tip3}\n", "color": "#008000"},
            "q1": {"value": q1, "color": "#FF1493"},
            "q2": {"value": q2, "color": "#FF1493"},
            "q3": {"value": q3, "color": "#FF1493"},
        }
    }

    res = requests.post(url, json=data, timeout=10).json()
    if res.get("errcode") == 0:
        print("✅ 消息推送与渲染数据下发成功")
        return True
    print(f"❌ 微信网关返回错误: {res}")
    return False

if __name__ == "__main__":
    send_message()
