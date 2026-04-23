#!/usr/bin/env python3
"""
Quick Telegram Configuration Test
Run this after setting up your Telegram bot to verify it's working
"""

import json
import requests
import sys
from datetime import datetime
from datetime import datetime


def test_telegram():
    """Test Telegram configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config.json: {e}")
        return False

    telegram_config = config.get('alerts', {}).get('telegram', {})

    if not telegram_config.get('enabled', False):
        print("❌ Telegram alerts are disabled in config.json")
        print("   Set alerts.telegram.enabled to true")
        return False

    bot_token = telegram_config.get('bot_token', '').strip()
    chat_id = telegram_config.get('chat_id', '').strip()

    if not bot_token or bot_token == 'YOUR_TELEGRAM_BOT_TOKEN':
        print("❌ Bot token not configured")
        print("   Run: python telegram_setup.py")
        return False

    if not chat_id or chat_id == 'YOUR_TELEGRAM_CHAT_ID':
        print("❌ Chat ID not configured")
        print("   Run: python telegram_setup.py")
        return False

    print("🔍 Testing Telegram bot connection...")

    # Test bot token
    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        bot_info = response.json()
        if bot_info.get('ok'):
            bot_username = bot_info['result']['username']
            print(f"✅ Bot verified: @{bot_username}")
        else:
            print("❌ Invalid bot token")
            return False
    except Exception as e:
        print(f"❌ Bot verification failed: {e}")
        return False

    # Test sending message
    print("📤 Sending test message...")
    test_message = f"""🧪 *OSINT Alert System Test*

✅ Bot: @{bot_username}
✅ Chat ID: `{chat_id}`
✅ Status: Connected

🚨 *Test Alert:*
This is a test message from your Dark Web OSINT system.

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"""

    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get('ok'):
            print("✅ Test message sent successfully!")
            print("📱 Check your Telegram for the test message")
            return True
        else:
            print(f"❌ Test message failed: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Test message failed: {e}")
        return False


def test_alert_manager():
    """Test the AlertManager class"""
    try:
        from alerts import AlertManager

        print("🔍 Testing AlertManager...")

        am = AlertManager()

        # Create a unique test finding to bypass deduplication
        unique_suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        test_finding = {
            'id': 999,
            'url': f'http://test.onion/test?run={unique_suffix}',
            'keyword': 'password',
            'confidence': 95,
            'risk_score': 90,
            'snippet': f'Test finding with password data {unique_suffix}',
            'classification': 'credential_leak'
        }

        # Test sending alert
        result = am.send_alert(test_finding, 'high')

        if result['sent']:
            print("✅ AlertManager test successful!")
            print(f"📱 Alert sent to chat: {result.get('chat_id')}")
            return True
        else:
            print(f"❌ AlertManager test failed: {result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ AlertManager test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Telegram Alert System Test")
    print("=" * 40)

    print("\n1. Testing Telegram Configuration:")
    telegram_ok = test_telegram()

    if telegram_ok:
        print("\n2. Testing AlertManager:")
        alert_ok = test_alert_manager()

        if alert_ok:
            print("\n🎉 All tests passed! Telegram alerts are working correctly.")
        else:
            print("\n⚠️ Telegram works but AlertManager has issues.")
    else:
        print("\n❌ Telegram configuration needs to be fixed.")

    print("\n💡 Next steps:")
    print("1. If Telegram failed, run: python telegram_setup.py")
    print("2. Start the daemon: python daemon.py --start")
    print("3. Monitor logs: tail -f logs/osint_system.log")