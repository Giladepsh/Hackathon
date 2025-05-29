from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import os
import google.generativeai as genai

# === טעינת מפתחות ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# === שאלות בסיס קבועות ===
fixed_questions = [
    "מהי זהות המגדר שלך? (לדוגמה: גבר, אישה, אחר)",
    "בן/בת כמה אתה?",
    "מה המצב המשפחתי שלך?",
    "מאיפה אתה בארץ?",
    "מה הסיבה שבגללה אתה פונה אלינו כרגע?"
]

# === שמירת מידע ===
user_profiles = {}  # chat_id -> {answers: dict, step: int, done: bool}
gemini_chats = {}   # chat_id -> Gemini Chat object

# === התחלה ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_profiles[chat_id] = {"answers": {}, "step": 0, "done": False, "question_count": 0}
    await update.message.reply_text("שלום 🌿 כדי שנוכל להכיר אותך טוב יותר, נתחיל בכמה שאלות בסיסיות:\n" + fixed_questions[0])

# === שלב ראשוני של שאלות קבועות ===
async def handle_fixed_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    profile = user_profiles[chat_id]
    current_step = profile["step"]
    profile["answers"][fixed_questions[current_step]] = text
    profile["step"] += 1

    if profile["step"] < len(fixed_questions):
        await update.message.reply_text(fixed_questions[profile["step"]])
    else:
        await update.message.reply_text("תודה ❤️\nעכשיו נמשיך עם כמה שאלות נוספות שיסייעו לנו להבין אותך טוב יותר.")
        init_gemini(chat_id, profile)
        await ask_next_dynamic_question(update, context)

# === יצירת session עם Gemini ===
def init_gemini(chat_id, profile):
    profile_summary = "\n".join([f"{k} {v}" for k, v in profile["answers"].items()])
    base_prompt = (
        "אתה בונה פרופיל רגשי-אישיותי עבור אדם שמעוניין בטיפול נפשי. \n"
        "המטרה שלך היא לשאול שאלות ממוקדות ואישיות, כדי להבין את האדם \n"
        "ברמה שתאפשר להתאים לו מטפל מתאים מתוך מאגר. \n"
        "הימנע משאלות כלליות מדי. הבן את האדם דרך תחביבים, אורח חיים, דחיפות הפנייה, העדפות לטיפול וכו'. \n"
        "תהיה רגיש ומתחשב, אל תענה כמו רובוט, שיהיה תחושה של אדם נעים לשיחה \n"
        f"\nרקע על האדם:\n{profile_summary}"
    )
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    chat = model.start_chat(history=[{"role": "user", "parts": [base_prompt]}])
    gemini_chats[chat_id] = chat

# === שיחה חכמה: יצירת שאלה חדשה לפי פרופיל קיים ===
async def ask_next_dynamic_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    profile = user_profiles[chat_id]
    chat = gemini_chats[chat_id]

    if profile["question_count"] >= 10:
        await generate_final_profile(update, context)
        return

    try:
        prompt = "בהתבסס על מה שאתה יודע עד כה, שאל שאלה אחת בלבד שתעזור להשלים את הפרופיל לטובת התאמת טיפול."
        response = chat.send_message(prompt)
        next_question = response.text.strip()
        profile["last_question"] = next_question
        await update.message.reply_text(next_question)
    except Exception as e:
        await update.message.reply_text(f"שגיאה בעת יצירת שאלה: {e}")

# === קליטת תשובה והתקדמות בשאלות ===
async def handle_dynamic_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    profile = user_profiles[chat_id]

    if text.lower() == "סיימנו":
        await generate_final_profile(update, context)
        return

    profile["answers"][profile["last_question"]] = text
    profile["question_count"] += 1
    await ask_next_dynamic_question(update, context)

# === יצירת סיכום סופי מהפרופיל ===
async def generate_final_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    profile = user_profiles[chat_id]
    chat = gemini_chats[chat_id]

    try:
        profile_text = "\n".join([f"{k}: {v}" for k, v in profile["answers"].items()])
        summary_prompt = f"נסח פרופיל של 10 שורות שמתאר את האדם, תחושותיו והעדפותיו לצורך התאמת טיפול:\n\n{profile_text}"
        summary = chat.send_message(summary_prompt)
        await update.message.reply_text("\U0001F4DD פרופיל סופי:\n" + summary.text)
    except Exception as e:
        await update.message.reply_text(f"שגיאה בסיכום: {e}")

    del gemini_chats[chat_id]
    del user_profiles[chat_id]

# === ניתוב בין שלבים ===
async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_profiles:
        await update.message.reply_text("שלח /start כדי להתחיל")
        return

    profile = user_profiles[chat_id]
    if profile["step"] < len(fixed_questions):
        await handle_fixed_questions(update, context)
    else:
        await handle_dynamic_questions(update, context)

# === הרצה ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))
    app.run_polling()

if __name__ == "__main__":
    main()




