import pyrogram, config, db, random, uuid, os, asyncio, pyromod.listen, pytz, time
from datetime import datetime
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps


# Menjalankan bot
xbot = pyrogram.Client('GCoin-Bot-Bet', api_id=config.Config.APP_ID, api_hash=config.Config.API_HASH, bot_token=config.Config.BOT_TOKEN)


async def get_user_id_from_tag(update):
    if update.entities:
        is_filled = False
        for entities in update.entities:
            if entities.type == 'text_mention':
                user_id = entities.user.id
                name = entities.user.first_name+' '+entities.user.last_name if entities.user.last_name else entities.user.first_name
                mention_name = entities.user.mention
                to_return = user_id, name, mention_name
                is_filled = True
            elif entities.type == 'mention':
                tag = update.text.split(' ')[1]
                try:
                    u = await update.chat.get_member(
                        user_id=tag
                    )
                    user_id = u.user.id
                    name = u.user.first_name+' '+u.user.last_name if u.user.last_name else u.user.first_name
                    mention_name = u.user.mention
                    to_return = user_id, name, mention_name
                    is_filled = True
                except:
                    to_return = None, 'User tidak dapat ditemukan di grup ini.', None
            else:
                if not is_filled:
                    to_return = None, None, None
        return to_return
    else:
        return None, None, None


def generate_captcha_image(text):
    width, height = 600, 300
    font_size = 100
    img = Image.new("L", (width, height), color=22)
    font = ImageFont.truetype("bahnschrift.ttf", font_size)
    draw = ImageDraw.Draw(img)
    w, h = draw.textsize(text, font=font)
    h += int(h*0.21)
    draw.text(((width-w)/2, (height-h)/2), text=text, fill='white', font=font)
    img.save(f'{text}.jpg')
    return text


async def checking_user_name(update):
    id = update.from_user.id
    name = update.from_user.first_name+' '+update.from_user.last_name if update.from_user.last_name else update.from_user.first_name
    mention_name = update.from_user.mention
    if not await db.is_user_exist(id):
        return name, mention_name
    else:
        data = await db.get_user(id)
        db_name = data['name']
        if name == db_name:
            return name, mention_name
        else:
            await db.edit_user_name(id, name)
            return name, mention_name


async def check_if_cmd_valid(update):
    cmd, tag, nominal = update.text.split(' ')
    if tag.isdigit():
        return False
    if cmd in ['.depo', '.wd']:
        if not nominal.isdigit():
            return False
    if cmd == '.transfer':
        if nominal.isdigit():
            pass
        elif nominal == 'all':
            pass
        else:
            return False
        if tag == 'all':
            return False
    return True


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('bet', '.'))
async def bet(bot, update):
    from_name, from_mention_name = await checking_user_name(update)
    if not await check_if_cmd_valid(update):
        return await bot.send_message(update.chat.id, 'Contoh: `.bet @tag 10`')
    to_, to_name, to_mention_name = await get_user_id_from_tag(update)
    try:
        cmd, tag, ammount = update.text.split(' ')
    except:
        return await bot.send_message(update.chat.id, 'Contoh: `.bet @tag 10`')
    if not to_:
        if to_name:
            return await bot.send_message(update.chat.id, to_name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.bet @tag 10`')
    from_ = update.from_user.id
    if to_ == from_:
        return await bot.send_message(update.chat.id, 'Tidak dapat melakukan bet GCoin kepada diri sendiri.')
    if await db.is_user_exist(from_) and await db.is_user_exist(to_):
        from_data = await db.get_user(from_)
        to_data = await db.get_user(to_)
        if from_data['coin'] == '0':
            return await bot.send_message(update.chat.id, 'Anda tidak dapat melakukan bet GCoin, pastikan anda memiliki setidaknya 1 GCoin.\ngunakan .wallet untuk mengecek total GCoin anda.')
        if int(from_data['coin']) < int(ammount):
            return await bot.send_message(update.chat.id, f'GCoin anda saat ini tidak mencukupi untuk melakukan bet sebesar {ammount}.')
        if to_data['coin'] == '0':
            return await bot.send_message(update.chat.id, 'User yang anda tuju tidak dapat melakukan bet GCoin karena GCoin miliknya tidak mencukupi.')
        if int(to_data['coin']) < int(ammount):
            return await bot.send_message(update.chat.id, 'User yang anda tuju tidak dapat melakukan bet GCoin karena GCoin miliknya tidak mencukupi.')
        if int(ammount) == 0:
            return await bot.send_message(update.chat.id, f'Bet GCoin 0 tidak di izinkan.')
        captcha = str(uuid.uuid4()).split('-')[0]
        x = await bot.send_message(update.chat.id, f'Hey {to_mention_name}!\nKirimkan `.acc {captcha}` jika anda setuju untuk melakukan bet GCoin dengan {from_mention_name}.\nBet akan dibatalkan dalam 1 menit jika tidak dijawab.')
        await bot.listen(update.chat.id, filters=pyrogram.filters.regex(f'.acc {captcha}') & pyrogram.filters.user(to_), timeout=60)
        await x.delete()
        await asyncio.sleep(3)
        to_nums = int(random.randint(0, 36))
        from_nums = int(random.randint(0, 36))
        to_nums_str = str(to_nums)
        from_nums_str = str(from_nums)
        await bot.send_message(update.chat.id, f'{from_mention_name} memutar roda dan mendapatkan {from_nums_str}\n\n{to_mention_name} memutar roda dan mendapatkan {to_nums_str}')
        to_get_point = str(int((int(ammount)+int(ammount))*0.975))
        await asyncio.sleep(1)
        from_data = await db.get_user(from_)
        to_data = await db.get_user(to_)
        if int(from_data['coin']) < int(ammount):
            return await bot.send_message(update.chat.id, f'GCoin milik {from_mention_name} saat ini tidak mencukupi untuk melakukan bet sebesar {ammount}.')
        if int(to_data['coin']) < int(ammount):
            return await bot.send_message(update.chat.id, f'GCoin milik {to_mention_name} saat ini tidak mencukupi untuk melakukan bet sebesar {ammount}.')
        await db.decrease_coin(from_, ammount)
        await db.decrease_coin(to_, ammount)
        if from_nums == to_nums:
            await db.increase_coin(from_, ammount)
            await db.increase_coin(to_, ammount)
            return await bot.send_message(update.chat.id, f'Hasilnya seri. maka dari itu GCoin yang dipertaruhkan telah dikembalikan.')
        if to_nums == 0:
            gcurr = int(to_data['coin'])+int(to_get_point)-int(ammount)
            await db.increase_coin(to_, to_get_point)
            if await db.is_user_history_exist(to_):
                await db.update_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            if await db.is_user_history_exist(from_):
                await db.update_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            return await bot.send_message(update.chat.id, f'Selamat kepada user {to_mention_name} karena telah memenangkan bet GCoin! GCoin anda telah bertambah sebanyak {to_get_point} GCoin.\n\nGCoin saat ini: {gcurr} GCoin.')
        if from_nums == 0:
            gcurr = int(from_data['coin'])+int(to_get_point)-int(ammount)
            await db.increase_coin(from_, to_get_point)
            if await db.is_user_history_exist(from_):
                await db.update_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            if await db.is_user_history_exist(to_):
                await db.update_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            return await bot.send_message(update.chat.id, f'Selamat kepada user {from_mention_name} karena telah memenangkan bet GCoin! GCoin anda telah bertambah sebanyak {to_get_point} GCoin.\n\nGCoin saat ini: {gcurr} GCoin.')
        if to_nums > from_nums:
            gcurr = int(to_data['coin'])+int(to_get_point)-int(ammount)
            await db.increase_coin(to_, to_get_point)
            if await db.is_user_history_exist(to_):
                await db.update_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            if await db.is_user_history_exist(from_):
                await db.update_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            return await bot.send_message(update.chat.id, f'Selamat kepada user {to_mention_name} karena telah memenangkan bet GCoin! GCoin anda telah bertambah sebanyak {to_get_point} GCoin.\n\nGCoin saat ini: {gcurr} GCoin.')
        if from_nums > to_nums:
            gcurr = int(from_data['coin'])+int(to_get_point)-int(ammount)
            await db.increase_coin(from_, to_get_point)
            if await db.is_user_history_exist(from_):
                await db.update_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(from_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'win', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            if await db.is_user_history_exist(to_):
                await db.update_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            else:
                await db.add_user_history(to_, {'date': str(int(time.mktime(time.strptime(datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y:%m:%d %H:%M:%S'), '%Y:%m:%d %H:%M:%S')))), 'transaction': 'bet', 'status': 'lost', 'bet-gcoin': str(ammount), 'get-gcoin': str(to_get_point)})
            return await bot.send_message(update.chat.id, f'Selamat kepada user {from_mention_name} karena telah memenangkan bet GCoin! GCoin anda telah bertambah sebanyak {to_get_point} GCoin.\n\nGCoin saat ini: {gcurr} GCoin.')
        await db.increase_coin(from_, ammount)
        await db.increase_coin(to_, ammount)
        return await bot.send_message(update.chat.id, f'Terjadi hasil yang tidak diduga. maka dari itu GCoin yang ditaruhkan telah dikembalikan.')  
    else:
        await bot.send_message(update.chat.id, 'Di antara anda dan tujuan anda tidak memiliki cukup GCoin untuk melakukan bet GCoin.')


xbot.run()
