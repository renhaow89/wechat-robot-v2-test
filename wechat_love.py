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

# V2.1 增量配置：公历固定节日字典（采用哈希结构确保 O(1) 检索复杂度）
HOLIDAY_MESSAGES = {
    "01-01": "元旦快乐！新的一年也要一直开心，爱你❤️",
    "02-14": "情人节快乐！谢谢你一直陪在我身边❤️",
    "03-08": "女神节快乐！愿我的宝宝永远闪闪发光，每天快乐❤️",
    "05-20": "520快乐！今天是表白日，再向你正式表白一次：我爱你❤️",
    "10-01": "国庆节快乐！好好享受假期，放松心情哦❤️",
    "12-25": "圣诞节快乐！要吃苹果哦，愿你平平安安❤️",
    "12-31": "跨年快乐！陪你迎接又一个崭新且充满希望的一年❤️"
}

# ==========================================
# 基础时间与日期处理模块
# ==========================================
def get_beijing_today():
    """获取准确的北京时间日期，基于绝对偏移量修正 GitHub Actions 的 UTC 偏差"""
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    return beijing_now.date()

def get_love_days():
    """计算自起始日以来的绝对累计恋爱天数"""
    return (get_beijing_today() - LOVE_DATE).days

def get_birthday_left():
    """
    计算距离下一农历生日的剩余自然日天数
    底层机制：将目标农历日期映射至当前公历年，若该日历节点已成为过去时，则自动递进至次年进行映射计算。
    """
    today = get_beijing_today()
    try:
        birthday = ZhDate(today.year, BIRTHDAY_LUNAR[1], BIRTHDAY_LUNAR[2]).to_datetime().date()
    except Exception:
        # 异常兜底机制：若因历法规则或闰月解析失败，采用静态公历常量进行灾备计算
        birthday = date(today.year, 9, 20)
        
    if birthday < today:
        try:
            birthday = ZhDate(today.year + 1, BIRTHDAY_LUNAR[1], BIRTHDAY_LUNAR[2]).to_datetime().date()
        except Exception:
            birthday = date(today.year + 1, 9, 20)
            
    return (birthday - today).days

# ==========================================
# V2.1 增量业务逻辑模块
# ==========================================
def get_today_holiday(today, birthday_left, love_days):
    """
    多级优先级的节日祝福生成算法。
    判别顺序：当前农历生日(0距) > 整年周年纪念 > 哈希表内的静态公历节日 > 默认保底文本。
    """
    if birthday_left == 0:
        return "今天是小胡胡的农历生日！祝我最爱的小公主生日快乐，永远美丽幸福！🎂🎉❤️"
    
    if love_days > 0 and love_days % 365 == 0:
        years = love_days // 365
        return f"今天是我们恋爱 {years} 周年纪念日！感谢这路途中的相守与陪伴，我一直爱你❤️"
    
    date_key = today.strftime("%m-%d")
    if date_key in HOLIDAY_MESSAGES:
        return HOLIDAY_MESSAGES[date_key]
    
    return "今天也是平淡日子里超级爱你的一天❤️"

def get_weather_tip(weather_info):
    """
    根据气象维度构建动态预警提示。
    涉及机制：子字符串匹配（识别特定天候状况），以及对带有物理单位（℃/°C）的非纯净温度数值进行浮点数转化过滤与极值阈值判定。
    """
    weather_str = weather_info.get("weather", "")
    low_str = weather_info.get("low", "")
    high_str = weather_info.get("high", "")
    
    tips_pool = []
    
    # 状态匹配节点
    if "雨" in weather_str:
        tips_pool.append("杭州今天有雨，出门一定要带好雨伞，注意路滑🌧️")
    elif "雪" in weather_str:
        tips_pool.append("今天有雪，天冷路滑，出门记得穿厚点，慢点走❄️")
    elif "晴" in weather_str:
        tips_pool.append("今天天气晴好，适合迎接一份灿烂又美丽的好心情☀️")
    elif "阴" in weather_str or "云" in weather_str:
        tips_pool.append("今天是多云或阴天，气候舒适，愿我的宝宝顺心快乐☁️")
    else:
        tips_pool.append("祝我的宝宝今天也拥有闪闪发光的一天✨")
        
    # 数值极值处理节点
    try:
        clean_low = float(low_str.replace("℃", "").replace("°C", "").strip())
        clean_high = float(high_str.replace("℃", "").replace("°C", "").strip())
        
        if clean_high >= 30.0:
            tips_pool.append("气温达到30度以上，稍微有些炎热，记得多喝水防止中暑🥤")
        elif clean_low <= 10.0:
            tips_pool.append("最低气温降到10度以下啦，早晚偏凉，注意多套件厚衣服防止感冒🧣")
    except Exception as parse_err:
        print(f"气温数据解析跳过 (非数值字符介入): {parse_err}")
        
    return " | ".join(tips_pool)

# ==========================================
# 外部接口交互模块
# ==========================================
def get_access_token():
    """向微信基础授权服务请求鉴权 Token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    return requests.get(url, timeout=10).json().get("access_token")

def get_weather():
    """获取指定城市的基础气象指标序列"""
    try:
        url = f"https://apis.tianapi.com/tianqi/index?key={TIANAPI_KEY}&city={CITY_NAME}&type=1"
        res = requests.get(url, timeout=10).json()
        if res.get("code") == 200:
            data = res["result"]
            return {
                "weather": data["weather"],
                "low": data["lowest"],
                "high": data["highest"],
            }
    except Exception as e:
        print(f"气象 API 阻断异常: {e}")
    # 标准化降级数据返回格式，维持系统健壮性
    return {"weather": "晴", "low": "20℃", "high": "30℃"}

def get_caihongpi():
    """向随机文本生成端点请求情话数据序列"""
    try:
        url = f"https://apis.tianapi.com/caihongpi/index?key={TIANAPI_KEY}"
        res = requests.get(url, timeout=10).json()
        if res.get("code") == 200:
            return res["result"]["content"]
    except Exception as e:
        print(f"情话 API 阻断异常: {e}")
    return "今天也超级喜欢你！"

# ==========================================
# 主执行管道
# ==========================================
def send_message():
    access_token = get_access_token()
    if not access_token:
        print("❌ Token 请求被拒绝或超时终止。")
        return False

    # 1. 获取核心状态与变量参数
    weather = get_weather()
    caihongpi = get_caihongpi()
    love_days = get_love_days()
    birthday_left = get_birthday_left()
    today = get_beijing_today()
    today_str = today.strftime("%Y年%m月%d日")

    holiday_str = get_today_holiday(today, birthday_left, love_days)
    tip_str = get_weather_tip(weather)

    print(f"执行时戳: {today_str}")
    print(f"天气状态: {weather}")
    print(f"原始情话: {caihongpi}")
    print(f"运算提醒: {tip_str}")
    print(f"运算节日: {holiday_str}")

    # 2. 对长字符串执行定长分段切片，规避微信测试号20字符渲染截断限制
    q1 = caihongpi[:18]
    q2 = caihongpi[18:36]
    q3 = caihongpi[36:54]

    # 3. 构建发送载荷 (Payload) 并执行推演
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    data = {
        "touser": OPEN_ID,
        "template_id": TEMPLATE_ID,
        "data": {
            "riqi": {"value": today_str, "color": "#333333"},
            "city": {"value": CITY_NAME, "color": "#333333"},
            "weather": {"value": weather["weather"], "color": "#333333"},
            "low": {"value": weather["low"], "color": "#333333"},
            "high": {"value": weather["high"], "color": "#333333"},
            "love_days": {"value": str(love_days), "color": "#FF69B4"},
            "birthday_left": {"value": str(birthday_left), "color": "#FF69B4"},
            "tip": {"value": tip_str, "color": "#FF8C00"},
            "holiday": {"value": holiday_str, "color": "#FF1493"},
            "qinghua1": {"value": q1, "color": "#FF69B4"},
            "qinghua2": {"value": q2, "color": "#FF69B4"},
            "qinghua3": {"value": q3, "color": "#FF69B4"},
        }
    }

    res = requests.post(url, json=data, timeout=10).json()
    if res.get("errcode") == 0:
        print("✅ 通道层推送成功，载荷数据已被平台接受。")
        return True
    else:
        print(f"❌ 通道层拒收: {res}")
        return False

if __name__ == "__main__":
    send_message()
