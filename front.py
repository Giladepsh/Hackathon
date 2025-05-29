# from telegram import Update
# from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
# from dotenv import load_dotenv
# import os
#
# # טען את הטוקן מקובץ .env
# load_dotenv()
# TOKEN = os.getenv("TOKEN")
#
# # רשימת שאלות לצורך אפיון נותן השירות
# questions = [
#     "מה סוג הגישה הטיפולית שלך?",
#     "באיזה פורמט אתה עובד? (פרטני / קבוצתי / אונליין)",
#     "מה קהל היעד העיקרי שלך?",
#     "מה הייחוד של הגישה או הכלים שאתה משתמש בהם?",
#     "האם יש אוכלוסיות שאתה לא עובד איתן?"
# ]
#
# # אחסון זמני של תשובות לפי משתמש
# sessions = {}
#
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     chat_id = update.effective_chat.id
#     sessions[chat_id] = {"answers": [], "step": 0}
#     await update.message.reply_text("שלום! נתחיל באפיון נותן השירות.\n\n" + questions[0])
#
# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     chat_id = update.effective_chat.id
#     text = update.message.text
#
#     if chat_id not in sessions:
#         await update.message.reply_text("שלח /start כדי להתחיל את האפיון.")
#         return
#
#     session = sessions[chat_id]
#     step = session["step"]
#     session["answers"].append(text)
#     session["step"] += 1
#
#     if session["step"] < len(questions):
#         await update.message.reply_text(questions[session["step"]])
#     else:
#         await update.message.reply_text("תודה! הנה התשובות שסיפקת:")
#         for i, answer in enumerate(session["answers"]):
#             await update.message.reply_text(f"שאלה {i+1}: {questions[i]}\nתשובה: {answer}")
#         # פה נשלב בהמשך את החיבור ל-Gemini
#         del sessions[chat_id]
#
# def main():
#     app = ApplicationBuilder().token(TOKEN).build()
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
#     app.run_polling()
#
# if __name__ == "__main__":
#     main()


from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import os
import google.auth
import google.generativeai as genai

# === טעינת מפתחות ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
credentials, _ = google.auth.load_credentials_from_file("hackathon-team-16_gen-lang-client-0325865525_iam_gserviceaccount_com_1747757983.json")
genai.configure(credentials=credentials)

# === הגדרות שאלות סגורות (רקע טכני) ===
questions = [
    "מה שמך המלא?",
    "בן/בת כמה אתה?",
    "מאיפה אתה בארץ?",
    "מה הסיבה שבגללה אתה פונה אלינו כרגע?",
    "איך היית מגדיר את התחושה הכללית שלך בתקופה האחרונה?"
]

# === אחסון session לפי משתמש ===
user_sessions = {}  # chat_id -> dict
gemini_chats = {}   # chat_id -> Gemini Chat Object

# === התחלת תהליך ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {"answers": [], "step": 0}
    await update.message.reply_text("שלום 🌿\nכדי שנוכל להכיר אותך מעט טוב יותר, נתחיל בכמה שאלות קצרות.\n\n" + questions[0])

# === ניהול שלב השאלות הסגורות ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in user_sessions:
        await update.message.reply_text("שלח /start כדי להתחיל.")
        return

    session = user_sessions[chat_id]
    step = session["step"]
    session["answers"].append(text)
    session["step"] += 1

    if session["step"] < len(questions):
        await update.message.reply_text(questions[session["step"]])
    else:
        await update.message.reply_text("תודה ❤️\nעכשיו נעבור לשיחה חופשית יותר.\nאת/ה יכול/ה לשתף במה שתרצה, ואנו נמשיך משם.")
        init_gemini_session(chat_id, session["answers"])
        del user_sessions[chat_id]  # שחרור הזיכרון
        await update.message.reply_text("כמובן שאין לחץ. קח/י את הזמן ושתף/י במה שנוח לך 🌸")

# === התחלת שיחה עם Gemini ===
def init_gemini_session(chat_id, background_answers):
    # בניית prompt אישי ורגיש
    profile_context = ""
    for i, answer in enumerate(background_answers):
        profile_context += f"שאלה {i+1}: {questions[i]}\nתשובה: {answer}\n"

    system_prompt = (
        "אתה יועץ רגשי חכם, קשוב, סבלני ואמפתי. אתה מדבר עם אדם שפנה לתמיכה רגשית.\n"
        "שים לב לשפה רכה, לא שיפוטית, שנותנת מקום מלא למשתף. מותר שתהיה שתיקה, תהייה או קושי להסביר.\n"
        "אל תציע פתרונות מיד — אלא תעזור לשתף ולהבין את עצמו. נסה לעזור לו לבטא את התחושות שמעסיקות אותו.\n\n"
        "רקע טכני על האדם:\n" + profile_context
    )

    model = genai.GenerativeModel("models/gemini-1.5-pro")
    chat = model.start_chat(history=[{"role": "user", "parts": [system_prompt]}])
    gemini_chats[chat_id] = chat

# === שיחה חופשית עם הסוכן ===
async def continue_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in gemini_chats:
        await update.message.reply_text("שלח /start כדי להתחיל שיחה.")
        return

    chat = gemini_chats[chat_id]

    try:
        response = chat.send_message(text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"שגיאה מול Gemini: {e}")

# === סיום השיחה וסיכום פרופיל ===
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in gemini_chats:
        await update.message.reply_text("אין שיחה פתוחה כרגע.")
        return

    chat = gemini_chats[chat_id]
    try:
        summary_prompt = "בהתבסס על השיחה שלנו עד כה, אנא נסח סיכום עדין, מקצועי ואמפתי של האדם ששוחח איתך. אל תציע פתרונות, רק תתאר את התחושות והצורך הכללי כפי שהשתקף בשיחה."
        summary = chat.send_message(summary_prompt)
        await update.message.reply_text("📝 סיכום ראשוני:\n" + summary.text)
    except Exception as e:
        await update.message.reply_text(f"שגיאה בסיכום: {e}")
    del gemini_chats[chat_id]

# === הפעלת האפליקציה ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_or_conversation))
    app.run_polling()

# === ניתוב בין שלבי השיחה ===
async def handle_message_or_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_sessions:
        await handle_message(update, context)
    else:
        await continue_conversation(update, context)

if __name__ == "__main__":
    main()