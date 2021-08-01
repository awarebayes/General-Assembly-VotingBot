import telebot
import gspread
import datetime
import time
import pickle


# TO-DO
# add motions
# think how one person can vote for another 2
# add vote check with results table
# think more about security and clarity of election


def create_not_voted_caption(mas):
    str = ''
    for i in mas:
        str += i + '\n'
    return str


def get_candidates(sheet, position):
    mas = sheet.sheet1.get('A1:E30')
    for i in mas:
        if i[0] == position:
            return i[1:]


def numerate_list(list):
    i = 0
    while i < len(list):
        list[i] = str(i + 1) + ' - ' + list[i]
        i += 1
    list.append(str(i + 1) + ' - ' + "Перевыборы!")
    return list


def show_left():
    caption = ''
    for i in not_voted_for:
        caption += '/' + i[1:] + '\n'
    return caption


def get_voting_committee_members():
    vc_mem = data_sheet.sheet1.get('A1:J1')
    return vc_mem[0]


def clean_res_sheet():
    result_sheet.values_clear("Sheet1!A2:D999")


def sort_tuples(mas):
    for i in range(len(mas)):
        for j in range(i, len(mas)):
            if mas[i][1] < mas[j][1]:
                mas[i], mas[j] = mas[j], mas[i]
    return mas


data_file = open("data.bin", "rb")

credentials = pickle.load(data_file)

gc = gspread.service_account_from_dict(credentials)

result_sheet = gc.open_by_key(pickle.load(data_file))

candidate_sheet = gc.open_by_key(pickle.load(data_file))

data_sheet = gc.open_by_key(pickle.load(data_file))

TOKEN = pickle.load(data_file)
bot = telebot.TeleBot(TOKEN)

voting_committee = get_voting_committee_members()

not_voted_for = ["/President", "/PR", "/CR", "/HR", "/LR"]
voting_now = None


@bot.message_handler(commands=["start", "help"])
def send_welcome_all(message):
    if message.text == '/start':
        link = 'https://sun9-72.userapi.com/impg/osx5xMnfOhmKyXVxQqW1fy7-mH2EGX5jMbcOgA/FWBfN97jaww.jpg?size=2560x1701&quality=96&sign=6392327f48f1793fc179e23f938a9728&type=album'
        caption = "Ты попал в бот *для голосования на Генеральной Ассамблее*" \
                  " ESTIEM LG Moscow. Как и всегда, мы выбираем новый борд: Президента, VPs of HR, CR, PR, LR. " \
                  "От твоего голоса зависит *очень многое*, поэтому *голосуй с умом* ;)\n\n" \
                  "Если ты член Voting Committee, смело пиши /config чтобы настроить голосование и смотреть результаты!"
        bot.send_photo(message.chat.id, photo=link, caption="Привет!", parse_mode='Markdown')
        bot.send_message(message.chat.id, caption, parse_mode='Markdown')
        if len(not_voted_for) != 0:
            bot.send_message(message.chat.id,
                             "Вам осталось проголосовать за:\n" + create_not_voted_caption(not_voted_for),
                             parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
    else:
        help_caption = "Если вам нужна помощь, обратитесь в Voting Committee!"
        bot.send_message(message.chat.id, help_caption, parse_mode='Markdown')


@bot.message_handler(commands=["President", "PR", "CR", "HR", "LR"])
def vote(message):
    global voting_now
    voting_now = message.text
    status = result_sheet.sheet1.get("F1")
    if status[0][0] == "STARTED":
        if voting_now in not_voted_for:
            candidate_list = numerate_list(get_candidates(candidate_sheet, voting_now))
            bot.send_message(message.chat.id, "*Вы можете проголосовать за:*\n\n" + "\n".join(
                candidate_list) + "\n\nДля того чтобы проголосовать, *напишите число вашего кандидата.*",
                             parse_mode='Markdown')

            @bot.message_handler(content_types=['text'])
            def count_vote(message):
                global voting_now
                if voting_now in not_voted_for:
                    candidate_list = numerate_list(get_candidates(candidate_sheet, voting_now))
                    if 0 <= int(message.text) - 1 < len(candidate_list):
                        choice = candidate_list[int(message.text) - 1]
                        bot.send_message(message.chat.id, "Вы выбрали " + choice + "\n", parse_mode='Markdown')

                        now = datetime.datetime.now()
                        current_time = now.strftime("%H:%M:%S")

                        today = datetime.date.today().strftime("%d.%m.%Y") + " " + current_time
                        result_sheet.sheet1.append_row(
                            [today, '@' + message.from_user.username, voting_now[1:], choice[3:]])
                        bot.send_message(message.chat.id, "Ваш голос учтён!", parse_mode='Markdown')

                        not_voted_for.remove(voting_now)
                        caption = show_left()

                        if caption.strip() == '':
                            bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
                        else:
                            bot.send_message(message.chat.id, "Вам осталось проголосовать за:\n" + caption,
                                             parse_mode='Markdown')
                    else:
                        bot.send_message(message.chat.id, "Вы что-то ввели не так!", parse_mode='Markdown')

                elif len(not_voted_for) == 0:
                    bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
                else:
                    bot.send_message(message.chat.id,
                                     "Вы либо голосовали за этого кандидата, либо неверно ввели команду!",
                                     parse_mode='Markdown')
        elif len(not_voted_for) == 0:
            bot.send_message(message.chat.id, "Вы больше не можете голосовать!", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "Вы либо голосовали за этого кандидата, либо неверно ввели команду!",
                             parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Голосование ещё не началось!", parse_mode='Markdown')


@bot.message_handler(commands=["config"])
def send_welcome(message):
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        caption = "\n\nСмотри, что можно делать в меню Voting Committee (VC):\n\n" \
                  "/set_new_committee - добавление в VC нового члена. Обратите внимание, " \
                  "что при добавлении нового пользователя, вы потеряете доступ к этой панели управления\n" \
                  "/view_committee - просмотр состава комитета VC\n" \
                  "/set_candidates - установка кандидатов\n" \
                  "/view_candidates - просмотр списка кандидатов\n" \
                  "/start_voting - запуск голосования\n" \
                  "/stop_voting - остановка голосования\n" \
                  "/results - результаты голосования. Во избежание ошибок голосование останавливается " \
                  "с того момента, как вы нажимаете эту команду.\n\n" \
                  "Важно! При установке кандидата предыдущие результаты голосований стираются." \
                  "Сделано это для корректной работы бота - установка новых кандидатов означает," \
                  "что началась новая Генеральная Ассамблея."
        link = "https://i.imgflip.com/1exd5c.jpg"
        bot.send_photo(message.chat.id, photo=link, caption='Привет, ' + message.from_user.first_name,
                       parse_mode='Markdown')
        bot.send_message(message.chat.id, caption)


@bot.message_handler(commands=["start_voting", "stop_voting"])
def start_stop(message):
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        if message.text == '/start_voting':
            status = result_sheet.sheet1.get("F1")
            if status[0][0].strip() == "STARTED":
                bot.send_message(message.chat.id, "Голосование и так уже началось!", parse_mode='Markdown')
            else:
                result_sheet.sheet1.update("F1", "STARTED")
                bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')
        if message.text == '/stop_voting':
            status = result_sheet.sheet1.get("F1")
            if status[0][0].strip() == "NOT STARTED":
                bot.send_message(message.chat.id, "Голосование и так уже кончилось!", parse_mode='Markdown')
            else:
                result_sheet.sheet1.update("F1", "NOT STARTED")
                bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')


@bot.message_handler(commands=["set_new_committee", "view_committee"])
def edit_committee(message):
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        if message.text == "/set_new_committee":
            bot.send_message(message.chat.id, "Напишите в следующем сообщении, кого вы хотите добавить, с помощью "
                                              "указания ника в телеграме (например, @pauuserrr)\n\nРазделяйте людей, "
                                              "которых вы добавляете, пробелом.\n\n"
                                              "*Важно:* Как только вы это сделаете, *вы потеряете доступ к "
                                              "Voting committee!*", parse_mode='Markdown')

            @bot.message_handler(content_types=['text'])
            def add_people(message):
                to_add = message.text.strip().split()
                voting_committee.extend(to_add)
                voting_committee.remove('@' + message.from_user.username)
                data_sheet.sheet1.delete_rows(1, 1)
                data_sheet.sheet1.append_row(voting_committee)
                bot.send_message(message.chat.id, "Готово!", parse_mode='Markdown')

        if message.text == "/view_committee":
            caption = create_not_voted_caption(voting_committee)
            bot.send_message(message.chat.id, "В состав VC входят:\n" + caption, parse_mode='Markdown')


@bot.message_handler(commands=["set_candidates"])
def set_candidates_notify(message):
    messg = "Установка кандидатов производится с помощью пяти команд. ОБЯЗАТЕЛЬНО прочитайте инструкцию перед" \
            "началом работы. Действия не по инструкции могут сломать систему, потому что защита от дурака ещё не " \
            "интегрирована.\n\n" \
            "Вы устанавливаете кандидатов с помощью команд:\n" \
            "/set_president - установить кандидатов в президенты\n" \
            "/set_HR - установить кандидатов в VP of HR\n" \
            "/set_LR - установить кандидатов в LR\n" \
            "/set_CR - установить кандидатов в VP of CR\n" \
            "/set_PR - установить кандидатов в VP of PR\n\n" \
            "После команды нужно *нажать CTRL + ENTER* или просто перевести строку, и указывать " \
            "кандидатов В СТОЛБИК. Например:\n\n" \
            "/set_HR\n" \
            "Ксюша Лоскутова\n" \
            "Лиза Исаева\n\n" \
            "После этого вам придет подтверждение, что кандидаты добавлены. Проверить это также можно" \
            "командой /view_candidates\n\n" \
            "После установки кандидатов данные по голосам удалятся!"
    bot.send_message(message.chat.id, messg)


@bot.message_handler(commands=["set_president", "set_HR", "set_CR", "set_PR", "set_LR"])
def set_candidates_real(message):
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:
        string = message.text.split('\n')
        choice = string[0].strip()
        to_add = string[1:]
        if choice == '/set_president':
            candidate_sheet.sheet1.delete_rows(1, 1)
            to_add.insert(0, "/President")
            candidate_sheet.sheet1.insert_row(to_add, 1)
        if choice == '/set_PR':
            candidate_sheet.sheet1.delete_rows(2, 2)
            to_add.insert(0, "/PR")
            candidate_sheet.sheet1.insert_row(to_add, 2)
        if choice == '/set_CR':
            candidate_sheet.sheet1.delete_rows(3, 3)
            to_add.insert(0, "CR")
            candidate_sheet.sheet1.insert_row(to_add, 3)
        if choice == '/set_HR':
            candidate_sheet.sheet1.delete_rows(4, 4)
            to_add.insert(0, "/HR")
            candidate_sheet.sheet1.insert_row(to_add, 4)
        if choice == '/set_LR':
            candidate_sheet.sheet1.delete_rows(5, 5)
            to_add.insert(0, "/LR")
            candidate_sheet.sheet1.insert_row(to_add, 5)
        clean_res_sheet()
        bot.send_message(message.chat.id, "Данные по голосам удалены!", parse_mode='Markdown')
        bot.send_message(message.chat.id, "Канидадты обновлены!", parse_mode='Markdown')


@bot.message_handler(commands=["view_candidates"])
def view_candidates_list(message):
    link = "https://sun9-14.userapi.com/impg/ajuSWVdrJMTFiuWYkaUPNytNXPZTHb3MT7YI5g/Nx_v2owSEkU.jpg?size=2560x1440&quality=96&sign=ec095573f83cb6612d7858ed7547ee29&type=album"
    bot.send_photo(message.chat.id, photo=link, caption="Загрузка занимает до 5 секунд.", parse_mode='Markdown')
    caption = ''
    for i in range(1, 6):
        row = candidate_sheet.sheet1.row_values(i)
        caption += "*" + row[0][1:] + ":*\n"
        for k in row[1:]:
            caption += k + '\n'
        caption += '\n'
    bot.send_message(message.chat.id, caption, parse_mode='Markdown')


@bot.message_handler(commands=["results"])
def counter_of_votes(message):
    voting_committee = get_voting_committee_members()
    if '@' + message.from_user.username not in voting_committee:
        bot.send_message(message.chat.id, "Вас нет в Voting Committee!", parse_mode='Markdown')
    else:

        status = result_sheet.sheet1.get("F1")
        if status[0][0].strip() != "NOT STARTED":
            result_sheet.sheet1.update("F1", "NOT STARTED")
            bot.send_message(message.chat.id, "Статус голосования обновлён!", parse_mode='Markdown')

        bot.send_message(message.chat.id, "Началось скачивание данных.", parse_mode='Markdown')
        res = result_sheet.sheet1.get_all_values()
        bot.send_message(message.chat.id, "Скачивание завершено. Началась обработка данных.", parse_mode='Markdown')

        f = open("../../lgmoscow-votingbot/src/results.txt", "w+")
        for i in res:
            print(' '.join(i) + '\n', file=f)
        f.seek(0)
        bot.send_message(message.chat.id, "Вам доступны *бюллетени*. Начался подсчёт результатов.",
                         parse_mode='Markdown')
        bot.send_document(message.chat.id, f)
        f.close()

        results = {}
        res.pop(0)
        for row in res:
            if results.get(row[2]) is None:
                results[row[2]] = {}
            if results[row[2]].get(row[3]) is None:
                results[row[2]][row[3]] = 1
            else:
                results[row[2]][row[3]] += 1

        bot.send_message(message.chat.id, "_Результаты посчитаны!_ Дождитесь публикации протокола.",
                         parse_mode='Markdown')

        caption_res = 'Результаты обработаны!\n\n'
        mas = list(results.items())
        for temp in mas:
            position = temp[0]
            candidates_results = list(temp[1].items())
            candidates_results = sort_tuples(candidates_results)
            caption_res += "*" + position + "*\n"
            caption_res += "*Победитель:* " + candidates_results[0][0] + ", голосов: " + str(
                candidates_results[0][1]) + '\n'
            for i in range(1, len(candidates_results)):
                caption_res += candidates_results[i][0] + ", голосов: " + str(candidates_results[i][1]) + '\n'
            caption_res += '\n'

        bot.send_message(message.chat.id, caption_res, parse_mode='Markdown')

        f = open("../../lgmoscow-votingbot/src/protocol.txt", "w+")
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
