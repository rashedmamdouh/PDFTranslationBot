import telebot
from deep_translator import GoogleTranslator
import pdfplumber
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from server import keep_alive  # Import the keep_alive function from server.py

# Initialize your bot with your bot's token
bot = telebot.TeleBot("Token")


# Define the translation function
def translate_text(text):
  translator = GoogleTranslator(source='auto', target='ar')
  translated_text = translator.translate(text)
  return translated_text


# Define the extraction function
def extract(page):
  """Extract PDF text and Delete in-paragraph line breaks."""
  # Get text
  extracted = page.extract_text()
  # Delete in-paragraph line breaks
  extracted = extracted.replace(
      ".\n",
      "**/m"  # keep par breaks
  ).replace(
      ". \n",
      "**/m"  # keep par breaks
  ).replace(
      "\n",
      ""  # delete in-par breaks
  ).replace("**/m", ".\n\n")  # restore par break
  return extracted


# Handler for the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message,
               "Welcome to the PDF Translator bot! Send me a PDF file.")


# Handler for messages containing PDF files
@bot.message_handler(content_types=['document'])
def handle_pdf(message):
  #sent PDF
  if message.document.mime_type == 'application/pdf':
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    #save sent PDF
    with open('input.pdf', 'wb') as new_file:
      new_file.write(downloaded_file)

    # Create a choice menu
    keyboard = InlineKeyboardMarkup()
    keyboard.row_width = 2
    text_button = InlineKeyboardButton("Text", callback_data='text')
    pdf_button = InlineKeyboardButton("PDF", callback_data='pdf')
    keyboard.add(text_button, pdf_button)

    bot.send_message(message.chat.id,
                     "Choose output format:",
                     reply_markup=keyboard)
  else:
    bot.reply_to(message, "Please send a PDF file.")


# Handler for callback queries (i.e., when the user clicks on a button)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  if call.data == 'text':
    # Translate the PDF and send back the translated text
    translated_text = ""
    with pdfplumber.open('input.pdf') as pdf:
      for page in pdf.pages:
        # Extract Page
        extracted = extract(page)
        # Translate Page
        translated_text += translate_text(extracted) + "\n\n"

    with open('output.txt', 'w') as output_file:
      output_file.write(translated_text)
    # Send the text file
    bot.send_document(call.message.chat.id, open('output.txt', 'rb'))

  elif call.data == 'pdf':
    # Translate the PDF and send back a PDF file
    translated_text = ""
    with pdfplumber.open('input.pdf') as pdf:
      for page in pdf.pages:
        # Extract Page
        extracted = extract(page)
        # Translate Page
        translated_text += translate_text(extracted) + "\n\n"

    with open('output.pdf', 'w') as output_file:
      output_file.write(translated_text)

    bot.send_document(call.message.chat.id, open('output.pdf', 'rb'))


# Start the bot
if __name__ == "__main__":
  keep_alive()  # Keep the Flask server alive
  bot.polling()
