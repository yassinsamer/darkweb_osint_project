#!/usr/bin/env python3
"""
Telegram Bot Setup Helper for Dark Web OSINT Alerts
Helps users create and configure Telegram bots for alert notifications
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime


def setup_telegram_bot():
    """Interactive setup for Telegram bot configuration"""
    print("🤖 Telegram Bot Setup for Dark Web OSINT Alerts")
    print("=" * 60)
    print()

    print("📋 Prerequisites:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot to create a new bot")
    print("3. Choose a name and username for your bot")
    print("4. Copy the bot token provided by BotFather")
    print()

    # Get bot token
    bot_token = input("🔑 Enter your Telegram bot token: ").strip()
    if not bot_token:
        print("❌ Bot token is required!")
        return False

    # Test bot token
    print("🔍 Testing bot token...")
    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        bot_info = response.json()
        if bot_info.get('ok'):
            bot_username = bot_info['result']['username']
            print(f"✅ Bot verified: @{bot_username}")
        else:
            print("❌ Invalid bot token!")
            return False
    except Exception as e:
        print(f"❌ Failed to verify bot token: {e}")
        return False

    print()
    print("📱 Next steps:")
    print("1. Open Telegram and start a chat with your bot")
    print("2. Send any message to activate the chat")
    print("3. The bot will respond (or you can send /start)")
    print()

    # Get chat ID
    chat_id = input("🆔 Enter your Telegram chat ID (or press Enter to auto-detect): ").strip()

    if not chat_id:
        print("🔍 Auto-detecting chat ID...")
        chat_id = get_chat_id(bot_token)

        if not chat_id:
            print("❌ Could not auto-detect chat ID.")
            print("Please manually get your chat ID:")
            print("1. Send a message to your bot")
            print("2. Visit: https://api.telegram.org/bot<YourBOTToken>/getUpdates")
            print("3. Find your chat ID in the response")
            chat_id = input("🆔 Enter your chat ID: ").strip()

    if not chat_id:
        print("❌ Chat ID is required!")
        return False

    # Test sending a message
    print("📤 Testing message sending...")
    test_message = f"""
🧪 *OSINT Alert System Setup Complete!*

✅ Bot: @{bot_username}
✅ Chat ID: `{chat_id}`
✅ Integration: Ready

🚨 *Test Alert:*
This is a test message from your Dark Web OSINT system.

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
    """.strip()

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
        else:
            print(f"❌ Failed to send test message: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Failed to send test message: {e}")
        return False

    # Update config.json
    print("💾 Updating configuration...")
    try:
        config_path = "config.json"
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        if 'alerts' not in config:
            config['alerts'] = {}

        config['alerts']['telegram'] = {
            'enabled': True,
            'bot_token': bot_token,
            'chat_id': chat_id
        }

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print("✅ Configuration updated successfully!")
        print(f"📁 Config file: {config_path}")

    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        print("Please manually add this to your config.json:")
        print(json.dumps({
            'alerts': {
                'telegram': {
                    'enabled': True,
                    'bot_token': bot_token,
                    'chat_id': chat_id
                }
            }
        }, indent=2))
        return False

    print()
    print("🎉 Telegram integration setup complete!")
    print()
    print("📋 Summary:")
    print(f"   Bot Username: @{bot_username}")
    print(f"   Chat ID: {chat_id}")
    print("   Status: ✅ Ready for alerts")
    print()
    print("🚀 You can now receive Dark Web OSINT alerts on Telegram!")
    print("   Run: python daemon.py --start")
    print()
    return True


def get_chat_id(bot_token):
    """Try to auto-detect chat ID from recent updates"""
    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        updates = response.json()
        if updates.get('ok') and updates.get('result'):
            # Get the most recent message
            for update in reversed(updates['result']):
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    return str(chat_id)
    except Exception as e:
        print(f"Auto-detection failed: {e}")

    return None


def test_telegram_config():
    """Test existing Telegram configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    telegram_config = config.get('alerts', {}).get('telegram', {})

    if not telegram_config.get('enabled'):
        print("❌ Telegram alerts are disabled in config")
        return False

    bot_token = telegram_config.get('bot_token')
    chat_id = telegram_config.get('chat_id')

    if not bot_token or not chat_id:
        print("❌ Bot token or chat ID missing in config")
        return False

    print("🔍 Testing Telegram configuration...")

    # Test bot
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

    # Test message
    test_message = f"🧪 *Configuration Test*\n\n✅ Telegram integration working!\n⏰ {requests.get('http://worldtimeapi.org/api/ip').json().get('datetime', 'Unknown time')}"

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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_telegram_config()
    else:
        success = setup_telegram_bot()

    if success:
        print("\n🎯 Next steps:")
        print("1. Start the OSINT daemon: python daemon.py --start")
        print("2. Monitor logs: tail -f logs/osint_system.log")
        print("3. Check alerts in Telegram when findings are detected")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)