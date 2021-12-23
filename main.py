import telebot, requests
from telebot import types
from bs4 import BeautifulSoup as bs #подключаем библиотеку для работы с парсингом
import os

bot = telebot.TeleBot('5015825930:AAESRUm7OW2vD930X0jd5JCwBmZ_SFo2p8g');

menu= telebot.types.ReplyKeyboardMarkup(True,True)
menu.row('Получить все заголовики', 'Получить конкретный пост')

left= types.InlineKeyboardButton(text='<', callback_data='left'); #кнопочки для навигации
right= types.InlineKeyboardButton(text='>', callback_data='right');



pages ={ #словарик для храненния номера страницы
'titleName':'',
'pageNow':1
}
postURL = "https://habr.com/ru/post/" #Ссылка на пост к записи + добавляется айди записи


@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    bot.send_message(message.chat.id, '*Привет '+message.from_user.first_name + '*! Это поиск статьей на habr.com',  parse_mode= "Markdown", reply_markup = menu)



@bot.message_handler(content_types=['text'])
def get_text_message(message):
    if(message.text == 'Получить все заголовики'): #если нажата данная кнокпа с текстом
        m = bot.send_message(message.chat.id, text=f'Введите ключевое слово или словосочетание:', parse_mode= "Markdown") #записываем в перменную m данное сообщение
        bot.register_next_step_handler(m,getTitleName)  #регистрируем след сообщение от пользвоателя в функции getTitleName

    elif(message.text == 'Получить конкретный пост'):
        m = bot.send_message(message.chat.id, text=f'Введите название статьи:', parse_mode= "Markdown")
        bot.register_next_step_handler(m,getPost)



@bot.callback_query_handler(func=lambda call: True) #регистрируем нажатие кнпоок
def callback_worker(call):
    global pages
    if call.data == 'left': #если нажата кнопка влево
        if(pages['pageNow'] !=1 ): #првоерям что мы не на 1 старницы чтобы вернуться назаад
            pages['pageNow'] = pages['pageNow']-1 #уменьшаем номер старницы на которой мы сейчас
            getNextPage(call) #поулчаем статьи с новой страниы и отправялем зеру

    elif call.data == 'right': #если вправо
        pages['pageNow'] = pages['pageNow']+1 #номер увеличаиваем
        getNextPage(call) #то же самое

    else: #если надата любая другая кнопка
        resp = requests.get(postURL+call.data) #поулчаем страницу с данной статьей по url + id статьи из callback
        soup = bs(resp.text, "html.parser")
        body = soup.find('div', id='post-content-body') #получаем весь текст стати
        title = soup.find('h1', class_="tm-article-snippet__title tm-article-snippet__title_h1") #получаем навзание
        with open(title.span.text+'.txt', 'w', encoding="utf-8") as outfile: #записываем в тестовый файл и называние его названием статьи
            outfile.write(title.span.text+body.div.text)

        with open(title.span.text+'.txt', "r",  encoding="utf-8") as read_file: #окрываем файл для четния
            bot.send_document(call.message.chat.id, read_file) #отпарвялем юзеру
        os.remove(title.span.text+'.txt') #удаоляем данный файл из директории

    bot.answer_callback_query(call.id)#завершаяем обработку данного события


def getTitleName(message):
    global pages #объявляем глобальную перемннну
    pages['titleName'] = message.text #записываем навзание статьи которую ввел юзер
    m = bot.send_message(message.chat.id, "Введите кол-во старниц",  parse_mode= "Markdown")
    bot.register_next_step_handler(m,Page) #отправляем в след функцию Page


def Page(message):
    global pages
    if(message.text.isdigit()): #проверям введено ли число
         maxPage = int(message.text) #записываем конвертируя строку в число
         page = 1 #стартовая страница поиска
         fullList="" #весь список статьей
         while page<=maxPage: #идем от 1 сраницы до последней которую ввел пользователь
             resp = requests.get(f"https://habr.com/ru/search/page{page}/?q="+pages['titleName']) #отпарвяем гет запрос по данному адресу вставляя неомер страниы в поиске и название статьи и записываем рещультат в перменную
             soup = bs(resp.text, "html.parser")  #создаем объект соупа для работы с тегами и поиска информации на поулченной ХТМЛ страницы
             titles = soup.find_all('a', class_='tm-article-snippet__title-link') #ищем все ссылки и дочерние теги с данным классом и записываем в переменую
             if(len(titles)>0): #если нашлось больше 0 статьей
                 for title in titles: #проходимся по каждой
                     fullList += title.span.text + ' - ' +postURL+ str(title.get('href').split('/')[-2]) + '\n' #дополняем наш список, тексом названяи стости и через - ссылка на статью
                 page+=1 #увеличиваем страницу на 1
                 # bot.send_message(message.chat.id, listTitles,  parse_mode= "Markdown")
             elif (page == 1 and len(titles)>0): #если на 1 старницы не нашлось статьей
                 m = bot.send_message(message.chat.id, text=f'Ничего не найдено!', parse_mode= "Markdown") #вывыодим сбщ
                 bot.register_next_step_handler(m,getTitleName) # и отправялем на функцию чтобы юзер снова ввел навзание
             else:  #если на n странице закончились статьи то выходим из цикла вайл
                 break
         with open('Titles.txt', 'w', encoding="utf-8") as outfile: #записываем в файл список поулченных статьей
             outfile.write(fullList)
         with open('Titles.txt', "r",  encoding="utf-8") as read_file: #открываем для чтения
             bot.send_document(message.chat.id, read_file) #опарвялем пользовател. данный список
    else: #еслич введено не число для кол-ва страницы, то снвоа отправялем в функцию для поулчения номера последней траницы
        m = bot.send_message(message.chat.id, "Введите кол-во старниц",  parse_mode= "Markdown")
        bot.register_next_step_handler(m,Page)

def getNextPage(call): #делаем все то же самое только для другой страницы
    resp = requests.get(f"https://habr.com/ru/search/page{pages['pageNow']}/?q="+pages['titleName']) #вот сюда вставляем номер новыйй стра
    soup = bs(resp.text, "html.parser")
    titles = soup.find_all('a', class_='tm-article-snippet__title-link')

    titlesKeyBoard = types.InlineKeyboardMarkup();
    if(len(titles)>0):
        for title in titles:
            titlesKeyBoard.row(types.InlineKeyboardButton(text=title.span.text, callback_data=(title.get('href').split('/'))[-2]))
        titlesKeyBoard.row(left,types.InlineKeyboardButton(text=pages['pageNow'], callback_data='x'), right)
        bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text= "Результаты поиска:",  parse_mode= "Markdown", reply_markup=titlesKeyBoard)
    else:
        pages['pageNow'] = pages['pageNow']-1 #если на страицны больше нет статьей то pageNow сохраняем предыдущий


def getPost(message):

    pages['titleName'] = message.text #сохраняем навзание статьи
    resp = requests.get(f"https://habr.com/ru/search/page1/?q="+message.text) #поулчаем страницу
    soup = bs(resp.text, "html.parser")
    titles = soup.find_all('a', class_='tm-article-snippet__title-link') #поулчаем ссылки на статьи и их навзания внутри тега

    if(len(titles)>0): #првоеряем что статьи есть по данному запроссу
        titlesKeyBoard = types.InlineKeyboardMarkup(); #создаем клавиатуру
        for title in titles: #проходимя п окаждой статье
            titlesKeyBoard.row(types.InlineKeyboardButton(text=title.span.text, callback_data=(title.get('href').split('/'))[-2])) #доавялем на новую строку кнопку с навзанием статьи и ее айдишником для callback
        titlesKeyBoard.row(left,types.InlineKeyboardButton(text=str(pages['pageNow']), callback_data='x'), right) #доабвляе в конце кнопки для навигаици и номер данной страницы
        bot.send_message(message.chat.id, "Результаты поиска:",  parse_mode= "Markdown", reply_markup=titlesKeyBoard) #отпраяем
    else:
        m = bot.send_message(message.chat.id, "Ничего не найдено! Попробуйте ещё раз",  parse_mode= "Markdown")
        bot.register_next_step_handler(m,getPost)

bot.polling(none_stop=True, interval=1);
