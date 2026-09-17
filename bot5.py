from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
def keep_alive():
    import os
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()
threading.Thread(target=keep_alive, daemon=True).start()

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetCommonChatsRequest
from datetime import datetime, timedelta, timezone
import asyncio
import json
import os
import hashlib

# =========================
# الإعدادات
# =========================
api_id = 33395256
api_hash = '534ab3c03be4f49e60b274a243f0aacd'
phone = '+967736529181'
channel_id = -1003533219656  

session_name = "vp_session_name"
duplicate_file = "sent_cache.json"
duplicate_hours = 1
manual_source_links = {}

# قائمة الكلمات المفتاحية مصححة ومفصولة بفاصلة
keywords = [
    'ابي مساعدة', 'عندي اختبار', 'عندي اختبار انجليزي', 'احتاج حد يحل اختبار', 'من يحل', 'ابي حد يحل لي كويز',
    'تعرفون حد يسوي ملخصات', 'من يسوي ملخصات', 'من عنده حد يسوي ملخصات',
    'عندي كويز', 'من يساعدني بلكويز', 'تعرفون حد يحل كويز',
    'عندي بحث', 'عندي واجب', 'تعرفون حد يحل واجب', 'من يحل واجب', 'تعرفون حد يسوي بحث', 
    'ابي حد يسوي لي بحث', 'حد يعرف شخص يحل',
    'عندي تقرير', 'ابي حد يحل واجب', 'تعرفون حد يحل واجبات', 'من يقدر يحله', 'ابي احد يحل لي واجب',
    'تعرفون حد يشرح', 'حد يشرح', 'تعرفون خصوصي ممتاز', 'من يعرف خصوصي', 'تعرفون خصوصي يشرح', 
    'من افضل خصوصي', 'في احد يشرح', 'من يعرف خصوصي للمواد', 'حد يعرف خصوصي', 
    'عندي تقرير مرحلي', 'من يسوي تقرير', 'تعرفون حد يسوي تقارير', 'تقرير نهائي مرحلي ميداني', 
    'في حد يحل تقرير', 'عندي برزنتيشن من يسويه', 'من يسوي عرض باور بونت', 'تعرفون حد يسوي عرض', 
    'برزنتيشن', 'من يحل ثقافه', 'من يحل تاريخ المملكه', 'تعرفون حد يحل', 'ابي سكليف', 
    'ابغى سكليف', 'تعرفون حد يسوي سكليف', 'من يسوي سكليف', 'ابغي اطلع سكليف', 
    'تعرفون حد يحل تكاليف', 'من يسوي تكليف', 'من يحل تكليف', 'عندي مشروع', 
    'ابي احد يسوي لي مشروع', 'من يسوي مشروع', 'من يسوي مشاريع', 'حد يعرف شخص يحل مشاريع', 
    'ابي حد يسوي لي مشروع تخرج'
]

client = TelegramClient(session_name, api_id, api_hash)
cache_lock = asyncio.Lock()

# الدوال المساعدة
def now_utc(): return datetime.now(timezone.utc)
def normalize_text(text): return ' '.join((text or '').lower().strip().split())
def contains_keyword(text): return any(word in normalize_text(text) for word in keywords)

def get_sender_display(sender):
    if not sender: return 'غير معروف'
    name = f"{getattr(sender, 'first_name', '')} {getattr(sender, 'last_name', '')}".strip()
    username = getattr(sender, 'username', '')
    if username: return f"{name} (@{username})"
    return f"{name} (ID: {getattr(sender, 'id', '')})"

def make_duplicate_key(sender, event, text):
    raw = f"{getattr(event, 'chat_id', '0')}|{getattr(sender, 'id', '0')}|{normalize_text(text)}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def load_cache():
    if not os.path.exists(duplicate_file): return {}
    try:
        with open(duplicate_file, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_cache(cache):
    with open(duplicate_file, 'w', encoding='utf-8') as f: json.dump(cache, f, ensure_ascii=False)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.raw_text or event.chat_id == channel_id or not contains_keyword(event.raw_text):
        return

    if len(event.raw_text.split()) > 12: return

    sender = await event.get_sender()
    chat = await event.get_chat()
    duplicate_key = make_duplicate_key(sender, event, event.raw_text)

    async with cache_lock:
        sent_cache = load_cache()
        if duplicate_key in sent_cache: return

        common_chats_count = 0
        try:
            common = await client(GetCommonChatsRequest(user_id=sender.id, max_id=0, limit=100))
            common_chats_count = len(common.chats)
        except: pass

        sender_username = getattr(sender, 'username', None)
        reply_link = f"https://t.me/{sender_username}" if sender_username else f"tg://user?id={sender.id}"
        
        final_message = (
            f"📥 📝\n\n{event.raw_text}\n\n"
            f"👤 المرسل: {get_sender_display(sender)}\n"
            f"📢 المصدر: {getattr(chat, 'title', 'خاص')}\n"
            f"👥 المجموعات المشتركة: {common_chats_count}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚡️ [اضغط هنا للرد السريع]({reply_link})\n"
            f"━━━━━━━━━━━━━━━━"
        )

        try:
            await client.send_message(channel_id, final_message, parse_mode='markdown', link_preview=False)
            sent_cache[duplicate_key] = now_utc().isoformat()
            save_cache(sent_cache)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)

async def main():
    await client.start(phone=phone)
    print("البوت يعمل الآن...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
