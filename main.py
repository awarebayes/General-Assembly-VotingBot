import telebot
import gspread
import datetime
import time
import pickle
import random


# Функция сборки строки с позициями, за которые
# ещё не был отдан голос
def create_not_voted_caption(mas):
    str = ''
    for i in mas:
        str += i + '\n'
    return str


# Функция получения списка кандидатов из таблицы
def get_candidates(sheet, position):
    mas = sheet.sheet1.get('A1:E30')
    for i in mas:
        if i[0] == position:
            return i[1:]


# Функция нумерации заданного списка
def numerate_list(list):
    i = 0
    while i < len(list):
        list[i] = str(i + 1) + ' - ' + list[i]
        i += 1
    list.append(str(i + 1) + ' - ' + "Перевыборы!")
    return list


# Функция сборки надписи для голосования за оставшиесся позиции (?)
def show_left():
    caption = ''
    for i in not_voted_for:
        caption += '/' + i[1:] + '\n'
    return caption


# Функция получения списка членов комитета выборов
def get_voting_committee_members():
    vc_mem = data_sheet.sheet1.get('A1:J1')
    return vc_mem[0]


# Функция получения списка зарегестрированных избирателей
def get_registered():
    reg = ids_table.sheet1.get('A1:A500')
    return reg


# Функция очистки страницы результатов
def clean_res_sheet():
    result_sheet.values_clear("Sheet1!A2:D999")


# Функция сортировки списка кортежей
def sort_tuples(mas):
    for i in range(len(mas)):
        for j in range(i, len(mas)):
            if mas[i][1] < mas[j][1]:
                mas[i], mas[j] = mas[j], mas[i]
    return mas


# Функция получения моушенов из таблицы
def get_motions():
    cnt = int(candidate_sheet.worksheet("Sheet2").get("B1")[0][0])
    motions = []
    if (cnt > 0):
        motions = candidate_sheet.worksheet("Sheet2").get('A2:A' + str(cnt + 1))

    return motions


# Функция получения сообщения с моушенами
def message_motions():
    motions = get_motions()
    msg = ''
    i = 1
    for motion in motions:
        txt = motion[0]
        msg += "_Motion " + str(i) + "_\n"
        msg += txt + '\n\n'
        i += 1
    return msg


# Функция получения случайного ключа
def get_random_key():
    string = ''
    for i in range(10):
        string += str(random.randint(1, 9))
    return string


# Функция получения списка зарегестрированных ключей
def get_keys():
    keys = []
    reg_table = ids_table.worksheet("Sheet2").get_all_values()
    for reg in reg_table[1:]:
        keys.extend(reg[3:])
    return keys


# Функция получения статуса голосования за моушены
def get_motion_vote_status():
    return result_sheet.worksheet("Sheet2").get("F1")[0][0].strip()


# Файл с данными (адреса таблиц и токен бота)
data_file = open("data.bin", "rb")

# Данные бота
credentials = pickle.load(data_file)
gc = gspread.service_account_from_dict(credentials)

# Таблица с результатами
result_sheet = gc.open_by_key(pickle.load(data_file))

# Таблица с кандидатами
candidate_sheet = gc.open_by_key(pickle.load(data_file))

# Таблица с данными
data_sheet = gc.open_by_key(pickle.load(data_file))

# Токен
TOKEN = pickle.load(data_file)

# Таблица с ID чатов зарегестрированных пользователей
# Также содержит ключи
ids_table = gc.open_by_key(pickle.load(data_file))

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Получение избирательного комитета
voting_committee = get_voting_committee_members()

# Список непроголосованных позиций
not_voted_for = ["/President", "/PR", "/CR", "/HR", "/LR"]
voting_now = None

voted = []


# Обработчик начального сообщения и помощи
@bot.message_handler(commands=["start", "help"])
def send_welcome_all(message):
    if message.text == '/start':
        link = 'https://sun9-72.userapi.com/impg/osx5xMnfOhmKyXVxQqW1fy7-mH2EGX5jMbcOgA/FWBfN97jaww.jpg?size=2560x1701&quality=96&sign=6392327f48f1793fc179e23f938a9728&type=album'
        caption = "Ты попал в бот *для голосования на Генеральной Ассамблее*" \
                  " ESTIEM LG Moscow. Сегодня мы выбираем борд или голосуем по другим вопросам." \
                  "От твоего голоса зависит *очень многое*, поэтому *голосуй с умом* ;)\n\n" \
                  "Если ты член Voting Committee, смело пиши /config чтобы настроить голосование и смотреть результаты!"
        bot.send_photo(message.chat.id, photo=link, caption="Привет!", parse_mode='Markdown')
        bot.send_message(message.chat.id, caption, parse_mode='Markdown')
        # if len(not_voted_for) != 0:
        #     bot.send_message(message.chat.id,
        #                      "Вам осталось проголосовать за:\n" + create_not_voted_caption(not_voted_for),
        #                      parse_mode='Markdown')
        # else:
        #     bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
        bot.send_message(message.chat.id, "Регистрируйся (обязательно!) по команде /register", parse_mode='Markdown')
        bot.send_message(message.chat.id, "После получения кода голосуй по команде /vote", parse_mode='Markdown')
    else:
        help_caption = "Если вам нужна помощь, обратитесь в Voting Committee!"
        bot.send_message(message.chat.id, help_caption, parse_mode='Markdown')


# Команда конфигурации голосования
# Доступна только членам Избирательного Комитета
@bot.message_handler(commands=["config"])
def send_welcome(message):
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        caption = "\n\nСмотри, что можно делать в меню Voting Committee (VC):\n\n" \
                  "Общее:\n" \
                  "/start_registration - начать регистрацию избирателей (заканчивается автоматически после подведения итогов)\n" \
                  "/set_new_committee - добавление в VC нового члена. Обратите внимание, " \
                  "что при добавлении нового пользователя, вы потеряете доступ к этой панели управления\n" \
                  "/view_committee - просмотр состава комитета VC\n\n" \
                  "Весенняя Генеральная Ассамблея:\n" \
                  "/set_candidates - установка кандидатов\n" \
                  "/view_candidates - просмотр списка кандидатов\n" \
                  "/start_voting - запуск голосования\n" \
                  "/stop_voting - остановка голосования\n" \
                  "/results - результаты голосования. Во избежание ошибок голосование останавливается " \
                  "с того момента, как вы нажимаете эту команду.\n\n" \
                  "Важно! При установке кандидата предыдущие результаты голосований стираются." \
                  "Сделано это для корректной работы бота - установка новых кандидатов означает," \
                  "что началась новая Генеральная Ассамблея. \n\n" \
                  "Зимняя Генеральная Ассамблея:\n" \
                  "/add_motion - добавить моушен\n" \
                  "/see_motions - просмотр моушенов\n" \
                  "/delete_motion - удаление моушена\n" \
                  "/give_keys - раздать всем зарегестрированным ключи\n" \
                  "/enable_voting - начало голосования\n" \
                  "/disable_voting - конец голосования\n" \
                  "/motion_results - результаты голосования за моушены\n"
        link = "https://i.imgflip.com/1exd5c.jpg"
        bot.send_photo(message.chat.id, photo=link, caption='Привет, ' + message.from_user.first_name,
                       parse_mode='Markdown')
        bot.send_message(message.chat.id, caption)


# Установка членов Избирательного Комитета
@bot.message_handler(commands=["set_new_committee", "view_committee"])
def edit_committee(message):
    voting_committee = get_voting_committee_members()  # Получение избирательного комитета
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        if message.text == "/set_new_committee":
            bot.send_message(message.chat.id, "Напишите в следующем сообщении, кого вы хотите добавить, с помощью "
                                              "указания ника в телеграме (например, @pauuserrr)\n\nРазделяйте людей, "
                                              "которых вы добавляете, пробелом.\n\n"
                                              "*Важно:* Как только вы это сделаете, *вы потеряете доступ к "
                                              "Voting committee!*", parse_mode='Markdown')

            # Считывание новых членов Избирательного Комитета
            @bot.message_handler(content_types=['text'])
            def add_people(message):
                to_add = message.text.strip().split()
                voting_committee.extend(to_add)
                voting_committee.remove('@' + message.from_user.username)
                data_sheet.sheet1.delete_rows(1, 1)
                data_sheet.sheet1.append_row(voting_committee)
                bot.send_message(message.chat.id, "Готово!", parse_mode='Markdown')

        # Вывод текущего состава Избирательного Комитета
        if message.text == "/view_committee":
            caption = create_not_voted_caption(voting_committee)
            bot.send_message(message.chat.id, "В состав VC входят:\n" + caption, parse_mode='Markdown')


# Обработчик команды начала регистрации
@bot.message_handler(commands=["start_registration"])
def start_reg(message):
    voting_committee = get_voting_committee_members()  # Доступ к команде - только у членов VC
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        reg_status = ids_table.sheet1.get("A1")[0][0].strip()  # текущий статус
        if reg_status == "STARTED":
            bot.send_message(message.chat.id, "Регистрация и так уже начата!")
        else:
            ids_table.sheet1.update("A1", "STARTED")  # изменение статуса
            bot.send_message(message.chat.id, "Регистрация началась!")


inside_reg = False  # переменная - флаг вхождения в обработчик регистрации


# Обработчик регистрации
@bot.message_handler(commands=["register"])
def reg(message):
    global inside_reg
    status = ids_table.sheet1.get("A1")[0][0].strip()  # статус регистрации
    if status == "STARTED":
        # если пользователь уже зарегестрирован
        if [str(message.chat.id)] in get_registered():
            bot.send_message(message.chat.id, "Вы уже зарегестрировались!")
        # если пользователь не зарегестрирован
        else:
            # добавляем нового пользователя
            ids_table.sheet1.append_row(
                [str(message.chat.id), message.from_user.first_name, message.from_user.last_name,
                 message.from_user.username])
            bot.send_message(message.chat.id, "Ваша регистрация прошла успешно. Теперь вы можете голосовать.")
    else:
        link = "https://2.bp.blogspot.com/-cq_YD9wqZZg/WNWcaiYt84I/AAAAAAACa1U/sFQJ7d8aw304uKGCzB7EyQSXXoOFML-jwCLcB/s1600/cat_late.jpg"
        bot.send_photo(message.chat.id, photo=link, caption="Регистрация ещё не началась.", parse_mode='Markdown')


add = False  # переменная - флаг вхождения в обработчик добавления моушена


# Обработчик добавления моушена
@bot.message_handler(commands=["add_motion"])
def add(message):
    # Обработчик доступен только членам Избирательного Комитета
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        global add
        add = True  # внутри обработчика
        # Вывод текущих моушенов
        cur = "Текущие моушены: \n\n" + message_motions()
        bot.send_message(message.chat.id, cur, parse_mode='Markdown')
        bot.send_message(message.chat.id, "В следующем сообщении напишите моушен, который надо добавить.")

        # Обработчик, собирающий моушен, который ему пришлют
        @bot.message_handler(func=(lambda message: add == True))
        def add_to_spread(message):
            global add
            add = False
            # Добавляем моушен, обновлем их количество
            candidate_sheet.worksheet("Sheet2").append_row([message.text])
            candidate_sheet.worksheet("Sheet2").update("B1",
                                                       int(candidate_sheet.worksheet("Sheet2").get("B1")[0][0]) + 1)
            bot.send_message(message.chat.id, "Успех!")


delete = False  # переменная - флаг вхождения в обработчик удаления моушена


# Обработчик удаления моушена
@bot.message_handler(commands=["delete_motion"])
def delete(message):
    # Обработчик доступен только членам Избирательного Комитета
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        global delete
        delete = True
        # Вывод текущих моушенов
        cur = "Текущие моушены: \n\n" + message_motions()
        bot.send_message(message.chat.id, cur, parse_mode='Markdown')
        bot.send_message(message.chat.id, "В следующем сообщении напишите номер моушена, который нужно удалить.")

        # Обработчик ответного сообщения с номером моушена для удаления
        @bot.message_handler(func=(lambda message: delete == True))
        def add_to_spread(message):
            global delete
            delete = False
            # Изменяем количество моушенов
            candidate_sheet.worksheet("Sheet2").update("B1",
                                                       int(candidate_sheet.worksheet("Sheet2").get("B1")[0][0]) - 1)
            # Удаляем строку таблицы
            candidate_sheet.worksheet("Sheet2").delete_rows(int(message.text) + 1, int(message.text) + 1)
            bot.send_message(message.chat.id, "Успех!")


# Обработчик просмотра моушенов
@bot.message_handler(commands=["see_motions"])
def see(message):
    cur = "Текущие моушены: \n\n" + message_motions()
    bot.send_message(message.chat.id, cur, parse_mode='Markdown')


# Обработчик команды выдачи зарегестрированным пользователям ключей
@bot.message_handler(commands=["give_keys"])
def keys(message):
    # Обработчик доступен только членам Избирательного Комитета
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        alphabet = "ABCDEFGHIJKLMNOPQR"  # Алфавит для передвижения по строке вправо
        keys_dict = dict()  # Словарь типа "username" - ["ключи"]
        _cur = "C2"  # Текущая клетка (указывает на число ключей)
        num_of_votes = ids_table.worksheet("Sheet2").get(_cur)  # Число ключей для добавления

        # Пока не встретим пустую клетку, раздаём ключи
        while (num_of_votes != []):
            num_of_votes = int(num_of_votes[0][0])  # Преобразование в целое
            added = []  # Список добавленных ключей
            for j in range(num_of_votes):
                temp = get_random_key()  # Текущий ключ
                # Записываем его
                ids_table.worksheet("Sheet2").update(alphabet[alphabet.find("C") + j + 1] + _cur[1], temp)
                added.append(temp)  # Доабвляем в список ключей
            # Добавлем в словарь ключей
            keys_dict[ids_table.worksheet("Sheet2").get("B" + _cur[1])[0][0]] = added
            _cur = "C" + str(int(_cur[1]) + 1)  # Сдвигаемся вниз
            num_of_votes = ids_table.worksheet("Sheet2").get(_cur)

        # Рассылка ключей
        bot.send_message(message.chat.id, "Сделано! Начинаю рассылку...", parse_mode='Markdown')
        all_data = ids_table.sheet1.get_all_values()[1:]
        # Сопоставление таблицы HR и таблицы зарегестрированных
        for line in all_data:
            chat_id = line[0]
            user_name = line[3]
            if (keys_dict.get(user_name) != None):
                bot.send_message(chat_id, "Привет! Твои ключи: " + ", ".join(keys_dict.get(user_name)),
                                 parse_mode='Markdown')
            elif (keys_dict.get('@' + user_name) != None):
                bot.send_message(chat_id, "Привет! Твои ключи: " + ", ".join(keys_dict.get('@' + user_name)),
                                 parse_mode='Markdown')
            elif (keys_dict.get(user_name[1:]) != None):
                bot.send_message(chat_id, "Привет! Твои ключи: " + ", ".join(keys_dict.get(user_name[1:])),
                                 parse_mode='Markdown')
            else:
                print("Наден неопознанный пользователь! - это " + user_name)


# Функция отправки голоса за моушен в таблицу
def input_vote(message):
    global voting, motions

    # Получение времени
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    today = datetime.date.today().strftime("%d.%m.%Y") + " " + current_time

    # Добавление информации в таблицу
    result_sheet.worksheet("Sheet2").append_row(
        [today, '@' + message.from_user.username, str(in_key), motion[0], message.text])
    bot.send_message(message.chat.id, "Ваш голос учтён!", parse_mode='Markdown')
    voting = True


voting = False
getting_key = False
motions = get_motions()
in_key = 0
motion = ""

# Обработчик голосования за моушены
@bot.message_handler(commands=["vote"])
def see(message):
    status = result_sheet.worksheet("Sheet2").get("F1") # Статус голосвания
    if status[0][0] == "STARTED":
        global voting, getting_key, voted, motions, in_key, motion

        getting_key = True
        bot.send_message(message.chat.id, "В следующем сообщении пришлите *ключ* для голосования.",
                         parse_mode='Markdown')

        in_key = 0 # Введённый ключ

        # Обработчик получения ключа
        @bot.message_handler(func=(lambda message: getting_key == True))
        def key_handler(message):
            global getting_key, in_key, voting, motions, motion
            getting_key = False
            in_key = message.text

            # Сам процесс голосования
            if (in_key in get_keys() and in_key not in voted):
                voted.append(in_key)
                cur = "Текущие моушены: \n\n" + message_motions()
                bot.send_message(message.chat.id, cur, parse_mode='Markdown')
                clishe = "Ответ прислать *строго* в виде \"За\" или \"Против\"."
                voting = True
                while motions != []:
                    if (voting):
                        motion = motions.pop()
                        txt = motion[0] + "\n" + clishe
                        msg = bot.send_message(message.chat.id, txt, parse_mode='Markdown')
                        voting = False
                        bot.register_next_step_handler(msg, input_vote)
            else:
                bot.send_message(message.chat.id, "Нет такого ключа!", parse_mode='Markdown')
            link = "https://i.pinimg.com/736x/d0/e7/4a/d0e74a9052ff16f5be930229774d8bf1.jpg"
            bot.send_photo(message.chat.id, photo=link, caption="Всё!", parse_mode='Markdown')
            voting = False
    else:
        bot.send_message(message.chat.id, "Голосование ещё не началось!", parse_mode='Markdown')


# Обработка включения и выключения голосования
@bot.message_handler(commands=["enable_voting", "disable_voting"])
def start_stop(message):
    # Обработчик доступен только членам Избирательного Комитета
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        if message.text == '/enable_voting':
            status = result_sheet.worksheet("Sheet2").get("F1")
            if status[0][0].strip() == "STARTED":
                bot.send_message(message.chat.id, "Голосование и так уже началось!", parse_mode='Markdown')
            else:
                result_sheet.worksheet("Sheet2").update("F1", "STARTED")
                bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')
        if message.text == '/disable_voting':
            status = result_sheet.worksheet("Sheet2").get("F1")
            if status[0][0].strip() == "NOT STARTED":
                bot.send_message(message.chat.id, "Голосование и так уже кончилось!", parse_mode='Markdown')
            else:
                result_sheet.worksheet("Sheet2").update("F1", "NOT STARTED")
                bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')


# Обработчик резульататов голосования за моушен
@bot.message_handler(commands=["motion_results"])
def counter_of_votes(message):
    # Доступно только членам Избирательного Комитета
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        # Обновление статуса голосвания (останавливается)
        status = result_sheet.sheet1.get("F1")
        if status[0][0].strip() != "NOT STARTED":
            result_sheet.worksheet("Sheet2").update("F1", "NOT STARTED")
            bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')

        # Упаковка данных в текстовый файл
        bot.send_message(message.chat.id, "Началось скачивание данных.", parse_mode='Markdown')
        res = result_sheet.worksheet("Sheet2").get_all_values()
        bot.send_message(message.chat.id, "Скачивание завершено. Началась обработка данных.", parse_mode='Markdown')

        # Отправление текстового документа
        f = open("results.txt", "w+")
        for i in res:
            print(' '.join(i) + '\n', file=f)
        f.seek(0)
        bot.send_message(message.chat.id, "Вам доступны *бюллетени*. Начался подсчёт результатов.",
                         parse_mode='Markdown')
        bot.send_document(message.chat.id, f)
        f.close()

        # Обработка данных
        results = {}
        res.pop(0)
        for row in res:
            if results.get(row[3]) is None:
                results[row[3]] = {}
            if results[row[3]].get(row[4]) is None:
                results[row[3]][row[4]] = 1
            else:
                results[row[3]][row[4]] += 1

        bot.send_message(message.chat.id, "_Результаты посчитаны!_ Дождитесь публикации протокола.",
                         parse_mode='Markdown')

        caption_res = 'Результаты обработаны!\n\n'

        # Вывод результатов и сборка протокола
        mas = list(results.items())
        for temp in mas:
            position = temp[0]
            candidates_results = list(temp[1].items())
            candidates_results = sort_tuples(candidates_results)
            caption_res += "*" + position + "*\n"
            caption_res += "*Результат:* \n" + candidates_results[0][0] + ", голосов: " + str(
                candidates_results[0][1]) + '\n'
            for i in range(1, len(candidates_results)):
                caption_res += candidates_results[i][0] + ", голосов: " + str(candidates_results[i][1]) + '\n'
            caption_res += '\n'

        bot.send_message(message.chat.id, caption_res, parse_mode='Markdown')

        # Отправка протокола
        f = open("protocol.txt", "w+")
        f.write(caption_res)
        f.seek(0)
        bot.send_document(message.chat.id, f)
        f.close()


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(3)
            print(e)

# Отключенный код
#
# @bot.message_handler(commands=["President", "PR", "CR", "HR", "LR"])
# def vote(message):
#     global voting_now
#     voting_now = message.text
#     status = result_sheet.sheet1.get("F1")
#     if status[0][0] == "STARTED":
#         if voting_now in not_voted_for:
#             candidate_list = numerate_list(get_candidates(candidate_sheet, voting_now))
#             bot.send_message(message.chat.id, "*Вы можете проголосовать за:*\n\n" + "\n".join(
#                 candidate_list) + "\n\nДля того чтобы проголосовать, *напишите число вашего кандидата.*",
#                              parse_mode='Markdown')
#
#             @bot.message_handler(content_types=['text'])
#             def count_vote(message):
#                 global voting_now
#                 if voting_now in not_voted_for:
#                     candidate_list = numerate_list(get_candidates(candidate_sheet, voting_now))
#                     if 0 <= int(message.text) - 1 < len(candidate_list):
#                         choice = candidate_list[int(message.text) - 1]
#                         bot.send_message(message.chat.id, "Вы выбрали " + choice + "\n", parse_mode='Markdown')
#
#                         now = datetime.datetime.now()
#                         current_time = now.strftime("%H:%M:%S")
#
#                         today = datetime.date.today().strftime("%d.%m.%Y") + " " + current_time
#                         result_sheet.sheet1.append_row(
#                             [today, '@' + message.from_user.username, voting_now[1:], choice[3:]])
#                         bot.send_message(message.chat.id, "Ваш голос учтён!", parse_mode='Markdown')
#
#                         not_voted_for.remove(voting_now)
#                         caption = show_left()
#
#                         if caption.strip() == '':
#                             bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
#                         else:
#                             bot.send_message(message.chat.id, "Вам осталось проголосовать за:\n" + caption,
#                                              parse_mode='Markdown')
#                     else:
#                         bot.send_message(message.chat.id, "Вы что-то ввели не так!", parse_mode='Markdown')
#
#                 elif len(not_voted_for) == 0:
#                     bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
#                 else:
#                     bot.send_message(message.chat.id,
#                                      "Вы либо голосовали за этого кандидата, либо неверно ввели команду!",
#                                      parse_mode='Markdown')
#         elif len(not_voted_for) == 0:
#             bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
#         else:
#             bot.send_message(message.chat.id, "Вы либо голосовали за этого кандидата, либо неверно ввели команду!",
#                              parse_mode='Markdown')
#     else:
#         bot.send_message(message.chat.id, "Голосование ещё не началось!", parse_mode='Markdown')
#
#
#
#
# @bot.message_handler(commands=["set_candidates"])
# def set_candidates_notify(message):
#     messg = "Установка кандидатов производится с помощью пяти команд. ОБЯЗАТЕЛЬНО прочитайте инструкцию перед" \
#             "началом работы. Действия не по инструкции могут сломать систему, потому что защита от дурака ещё не " \
#             "интегрирована.\n\n" \
#             "Вы устанавливаете кандидатов с помощью команд:\n" \
#             "/set_president - установить кандидатов в президенты\n" \
#             "/set_HR - установить кандидатов в VP of HR\n" \
#             "/set_LR - установить кандидатов в LR\n" \
#             "/set_CR - установить кандидатов в VP of CR\n" \
#             "/set_PR - установить кандидатов в VP of PR\n\n" \
#             "После команды нужно *нажать CTRL + ENTER* или просто перевести строку, и указывать " \
#             "кандидатов В СТОЛБИК. Например:\n\n" \
#             "/set_HR\n" \
#             "Ксюша Лоскутова\n" \
#             "Лиза Исаева\n\n" \
#             "После этого вам придет подтверждение, что кандидаты добавлены. Проверить это также можно" \
#             "командой /view_candidates\n\n" \
#             "После установки кандидатов данные по голосам удалятся!"
#     bot.send_message(message.chat.id, messg)
#
#
# @bot.message_handler(commands=["set_president", "set_HR", "set_CR", "set_PR", "set_LR"])
# def set_candidates_real(message):
#     voting_committee = get_voting_committee_members()
#     if '@' + message.from_user.username not in voting_committee:
#         bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
#     else:
#         string = message.text.split('\n')
#         choice = string[0].strip()
#         to_add = string[1:]
#         if choice == '/set_president':
#             candidate_sheet.sheet1.delete_rows(1, 1)
#             to_add.insert(0, "/President")
#             candidate_sheet.sheet1.insert_row(to_add, 1)
#         if choice == '/set_PR':
#             candidate_sheet.sheet1.delete_rows(2, 2)
#             to_add.insert(0, "/PR")
#             candidate_sheet.sheet1.insert_row(to_add, 2)
#         if choice == '/set_CR':
#             candidate_sheet.sheet1.delete_rows(3, 3)
#             to_add.insert(0, "CR")
#             candidate_sheet.sheet1.insert_row(to_add, 3)
#         if choice == '/set_HR':
#             candidate_sheet.sheet1.delete_rows(4, 4)
#             to_add.insert(0, "/HR")
#             candidate_sheet.sheet1.insert_row(to_add, 4)
#         if choice == '/set_LR':
#             candidate_sheet.sheet1.delete_rows(5, 5)
#             to_add.insert(0, "/LR")
#             candidate_sheet.sheet1.insert_row(to_add, 5)
#         clean_res_sheet()
#         bot.send_message(message.chat.id, "Данные по голосам удалены!", parse_mode='Markdown')
#         bot.send_message(message.chat.id, "Канидадты обновлены!", parse_mode='Markdown')
#
#
# @bot.message_handler(commands=["view_candidates"])
# def view_candidates_list(message):
#     link = "https://sun9-14.userapi.com/impg/ajuSWVdrJMTFiuWYkaUPNytNXPZTHb3MT7YI5g/Nx_v2owSEkU.jpg?size=2560x1440&quality=96&sign=ec095573f83cb6612d7858ed7547ee29&type=album"
#     bot.send_photo(message.chat.id, photo=link, caption="Загрузка занимает до 5 секунд.", parse_mode='Markdown')
#     caption = ''
#     for i in range(1, 6):
#         row = candidate_sheet.sheet1.row_values(i)
#         caption += "*" + row[0][1:] + ":*\n"
#         for k in row[1:]:
#             caption += k + '\n'
#         caption += '\n'
#     bot.send_message(message.chat.id, caption, parse_mode='Markdown')
#
#
# @bot.message_handler(commands=["results"])
# def counter_of_votes(message):
#     voting_committee = get_voting_committee_members()
#     if '@' + message.from_user.username not in voting_committee:
#         bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
#     else:
#
#         status = result_sheet.sheet1.get("F1")
#         if status[0][0].strip() != "NOT STARTED":
#             result_sheet.sheet1.update("F1", "NOT STARTED")
#             bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')
#
#         bot.send_message(message.chat.id, "Началось скачивание данных.", parse_mode='Markdown')
#         res = result_sheet.sheet1.get_all_values()
#         bot.send_message(message.chat.id, "Скачивание завершено. Началась обработка данных.", parse_mode='Markdown')
#
#         f = open("results.txt", "w+")
#         for i in res:
#             print(' '.join(i) + '\n', file=f)
#         f.seek(0)
#         bot.send_message(message.chat.id, "Вам доступны *бюллетени*. Начался подсчёт результатов.",
#                          parse_mode='Markdown')
#         bot.send_document(message.chat.id, f)
#         f.close()
#
#         results = {}
#         res.pop(0)
#         for row in res:
#             if results.get(row[2]) is None:
#                 results[row[2]] = {}
#             if results[row[2]].get(row[3]) is None:
#                 results[row[2]][row[3]] = 1
#             else:
#                 results[row[2]][row[3]] += 1
#
#         bot.send_message(message.chat.id, "_Результаты посчитаны!_ Дождитесь публикации протокола.",
#                          parse_mode='Markdown')
#
#         caption_res = 'Результаты обработаны!\n\n'
#         mas = list(results.items())
#         for temp in mas:
#             position = temp[0]
#             candidates_results = list(temp[1].items())
#             candidates_results = sort_tuples(candidates_results)
#             caption_res += "*" + position + "*\n"
#             caption_res += "*Победитель:* " + candidates_results[0][0] + ", голосов: " + str(
#                 candidates_results[0][1]) + '\n'
#             for i in range(1, len(candidates_results)):
#                 caption_res += candidates_results[i][0] + ", голосов: " + str(candidates_results[i][1]) + '\n'
#             caption_res += '\n'
#
#         bot.send_message(message.chat.id, caption_res, parse_mode='Markdown')
#
#         f = open("protocol.txt", "w+")
#         f.write(caption_res)
#         f.seek(0)
#         bot.send_document(message.chat.id, f)
#         f.close()

# @bot.message_handler(commands=["start_voting", "stop_voting"])
# def start_stop(message):
#     voting_committee = get_voting_committee_members()
#     if '@' + message.from_user.username not in voting_committee:
#         bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
#     else:
#         if message.text == '/start_voting':
#             status = result_sheet.sheet1.get("F1")
#             if status[0][0].strip() == "STARTED":
#                 bot.send_message(message.chat.id, "Голосование и так уже началось!", parse_mode='Markdown')
#             else:
#                 result_sheet.sheet1.update("F1", "STARTED")
#                 bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')
#         if message.text == '/stop_voting':
#             status = result_sheet.sheet1.get("F1")
#             if status[0][0].strip() == "NOT STARTED":
#                 bot.send_message(message.chat.id, "Голосование и так уже кончилось!", parse_mode='Markdown')
#             else:
#                 result_sheet.sheet1.update("F1", "NOT STARTED")
#                 bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')
