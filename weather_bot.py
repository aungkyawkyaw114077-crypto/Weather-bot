import requests
import os
from datetime import datetime

# API Keys from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
WEATHER_API_KEY = os.environ['WEATHER_API_KEY']

# မြို့ကို ပြောင်းလို့ရတယ်
CITY = "Yangon"

# အန္တရာယ် အဆင့်သတ်မှတ်ချက်များ (WHO/International Standards)
THRESHOLDS = {
    'temp_high': 35,        # °C - အလွန်ပူ
    'temp_low': 10,         # °C - အလွန်အေး
    'wind_speed': 10,       # m/s - လေပြင်း (36 km/h)
    'uv_high': 8,           # UV Index - အလွန်အန္တရာယ်
    'uv_extreme': 11,       # UV Index - အန္တရာယ်အလွန်ကြီးမား
    'humidity_high': 80,    # % - အလွန်စိုထိုင်း
    'feels_like_high': 40   # °C - ခံစားရသည့် အပူချိန် အလွန်မြင့်
}

def get_weather_data():
    """Weather API ကနေ data ယူ"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching weather: {e}")
        return None

def analyze_weather(data):
    """မိုးလေဝသ data ကို သုံးသပ်ပြီး အန္တရာယ်ရှိရင် alerts ပြန်"""
    
    if not data:
        return None
    
    # Data ထုတ်ယူ
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']  # m/s
    wind_deg = data['wind'].get('deg', 0)
    weather_desc = data['weather'][0]['description']
    
    # Wind direction
    directions = ['မြောက်', 'မြောက်အရှေ့', 'အရှေ့', 'အရှေ့တောင်', 
                  'တောင်', 'တောင်အနောက်', 'အနောက်', 'အနောက်မြောက်']
    wind_dir = directions[int((wind_deg + 22.5) / 45) % 8]
    
    # UV Index ယူ (OpenWeather က free tier မှာ မပါဘူး၊ ဒါကြောင့် estimate လုပ်မယ်)
    # UV ကို တကယ်လိုရင် OpenUV API သုံးရမယ် (free tier 50 requests/day)
    # ဒီမှာ dummy value သုံးထားတယ်
    uv_index = 5  # Placeholder
    
    # Alerts စာရင်း
    alerts = []
    recommendations = []
    
    # အပူချိန် စစ်ဆေး
    if temp >= THRESHOLDS['temp_high']:
        alerts.append(f"🔥 အပူချိန် အလွန်မြင့်: {temp}°C")
        recommendations.append("💧 ရေများများသောက်ပါ")
        recommendations.append("🏠 ပူသောအချိန်တွင် အပြင်မထွက်သင့်")
    
    if temp <= THRESHOLDS['temp_low']:
        alerts.append(f"❄️ အပူချိန် အလွန်နိမ့်: {temp}°C")
        recommendations.append("🧥 ပူနွေးသော အဝတ်အစား ဝတ်ဆင်ပါ")
    
    # ခံစားရသည့် အပူချိန်
    if feels_like >= THRESHOLDS['feels_like_high']:
        alerts.append(f"🌡️ ခံစားရတဲ့ အပူချိန် အလွန်မြင့်: {feels_like}°C")
        recommendations.append("☀️ နေရောင်ရှောင်ကြဉ်ပါ")
    
    # လေတိုက်နှုန်း စစ်ဆေး
    wind_kmh = wind_speed * 3.6  # km/h သို့ ပြောင်း
    if wind_speed >= THRESHOLDS['wind_speed']:
        alerts.append(f"💨 လေပြင်း: {wind_speed:.1f} m/s ({wind_kmh:.1f} km/h) {wind_dir}မှ တိုက်ခတ်")
        recommendations.append("⚠️ အပြင်ထွက်သောအခါ သတိထား")
        recommendations.append("🌲 သစ်ပင်၊ ဆိုင်းဘုတ်များ အနီးမှ ရှောင်")
    
    # စိုထိုင်းဆ စစ်ဆေး
    if humidity >= THRESHOLDS['humidity_high']:
        alerts.append(f"💦 အလွန်စိုထိုင်း: {humidity}%")
        recommendations.append("🌬️ လေဝင်လေထွက် ကောင်းစေပါ")
    
    # UV Index စစ်ဆေး (တကယ်တန်းရရင်)
    # if uv_index >= THRESHOLDS['uv_extreme']:
    #     alerts.append(f"☀️ UV Index အလွန်အန္တရာယ်: {uv_index}")
    #     recommendations.append("🧴 SPF 50+ သုံးပါ")
    #     recommendations.append("🕶️ နေမျက်မှန် ဆောင်းပါ")
    # elif uv_index >= THRESHOLDS['uv_high']:
    #     alerts.append(f"⚠️ UV Index မြင့်: {uv_index}")
    #     recommendations.append("🧴 ဆန်ခရင်းလိမ်းပါ")
    
    return {
        'has_alerts': len(alerts) > 0,
        'alerts': alerts,
        'recommendations': recommendations,
        'data': {
            'temp': temp,
            'feels_like': feels_like,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'wind_kmh': wind_kmh,
            'wind_dir': wind_dir,
            'weather_desc': weather_desc
        }
    }

def send_telegram(message):
    """Telegram notification ပို့"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def main():
    print(f"\n{'='*50}")
    print(f"🤖 Weather Alert Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 City: {CITY}")
    print(f"{'='*50}\n")
    
    # Weather data ယူ
    print("📡 Fetching weather data...")
    weather_data = get_weather_data()
    
    if not weather_data:
        error_msg = "❌ Failed to fetch weather data"
        print(error_msg)
        send_telegram(error_msg)
        return
    
    # Data သုံးသပ်
    print("🔍 Analyzing weather conditions...")
    analysis = analyze_weather(weather_data)
    
    if not analysis:
        print("❌ Analysis failed")
        return
    
    # Alert ရှိရင် notification ပို့
    if analysis['has_alerts']:
        print("⚠️ ALERTS DETECTED! Sending notification...")
        
        data = analysis['data']
        message = f"""
🚨 <b>မိုးလေဝသ သတိပေးချက်</b> 🚨

📍 <b>{CITY}</b>
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}

<b>⚠️ သတိပေးချက်များ:</b>
{chr(10).join(analysis['alerts'])}

<b>📊 လက်ရှိအခြေအနေ:</b>
🌡️ အပူချိန်: {data['temp']}°C (ခံစားရတာ: {data['feels_like']}°C)
💨 လေ: {data['wind_speed']:.1f} m/s ({data['wind_kmh']:.1f} km/h) {data['wind_dir']}မှ
💧 စိုထိုင်းဆ: {data['humidity']}%
☁️ အခြေအနေ: {data['weather_desc']}

<b>💡 အကြံပြုချက်များ:</b>
{chr(10).join(analysis['recommendations'])}

<i>သတိထားပြီး ဘေးကင်းစွာနေပါ!</i> 🙏
"""
        
        if send_telegram(message):
            print("✅ Alert sent successfully!")
        else:
            print("❌ Failed to send alert")
    else:
        print("✅ No alerts - Weather conditions are normal")
        print(f"   Temperature: {analysis['data']['temp']}°C")
        print(f"   Wind: {analysis['data']['wind_speed']:.1f} m/s")
        print(f"   Humidity: {analysis['data']['humidity']}%")
    
    print(f"\n{'='*50}")
    print("🏁 Bot execution completed")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
