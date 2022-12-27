import pyrogram, config, db, random, uuid, os, asyncio, pyromod.listen, pytz, time, re
from datetime import datetime
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps


# Menjalankan bot
xbot = pyrogram.Client('GCoin-Bot-Lelang', api_id=config.Config.APP_ID, api_hash=config.Config.API_HASH, bot_token=config.Config.BOT_TOKEN)


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


def IsMultiple(bid, maxbid, fold):
    if (int(bid)-int(maxbid)) % int(fold) != 0:
        return False
    elif int(bid) >= int(maxbid):
        return True
    else:
        return False


def time_covert(regex):
    count = regex.groups(1)[0]
    format_ = regex.groups(2)[1]
    if format_ == 's':
        return int(count), f'{count} detik'
    elif format_ == 'm':
        return int(count)*60, f'{count} menit'
    elif format_ == 'h':
        return int(count)*3600, f'{count} jam'
    elif format_ == 'd':
        return int(count)*86400, f'{count} hari'
    else:
        return None, None


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('lelang', '.'))
async def lelang(bot, update):
    admins = await db.get_admins()
    if admins:
        if not update.from_user.id in admins:
            return
        else:
            pass
    name, mention_name = await checking_user_name(update)
    akun, maxbid, fold, time_format  = update.text.split(' ', 1)[1].split(' | ')
    if maxbid.isdigit() and fold.isdigit():
        regex = re.search(r'(\d+)(s|m|h|d)', time_format)
        the_time, waktu = time_covert(regex)
        if not the_time:
            return print(the_time)
        users = []
        higher_bargainer = {}
        await bot.send_message(update.chat.id, f'Dilelang sebuah {akun}!\n\nStart bid: {maxbid}\nKelipatan: {fold}\nDimulai dari {maxbid}. Silakan menawar dengan cara `.bid {maxbid}` dan seterusnya sesuai dengan kelipatan.\n\nTambahan: Jika tidak ditawar dalam {waktu}, maka lelang akan dibatalkan atau sang penawar tertinggi akan memenangkan lelang.`')
        for _ in range(10000):
            try:
                start = time.time()
                x = await bot.listen(update.chat.id, filters=pyrogram.filters.regex(r'\.bid \d+'), timeout=the_time)
            except asyncio.exceptions.TimeoutError:
                if higher_bargainer:
                    data = await db.get_user(higher_bargainer['user_id'])
                    name = data['name']
                    bid = higher_bargainer['bid']
                    for user in users:
                        if user['user_id'] == higher_bargainer['user_id']:
                            pass
                        else:
                            await db.increase_coin(user['user_id'], user['bid'])
                    await bot.send_message(update.chat.id, f'Selamat kepada user {name} karena telah memenangkan lelang {akun} dengan tawaran sebesar {bid}!')
                    break
                else:
                    break
            if higher_bargainer:
                maxbid = higher_bargainer['bid']
            bid = re.search(r'\.bid (\d+)', x.text).groups(1)[0]
            higher_bid = re.search(r'\.bid (\d+)', x.text).groups(1)[0]
            if IsMultiple(bid, maxbid, fold):
                already = False
                is_worked = False
                if users:
                    if higher_bid == higher_bargainer['bid']:
                        await bot.send_message(update.chat.id, 'Tidak dapat memberikan penawaran yang sama dengan penawar tertinggi saat ini.')
                        full_time = int(time.time() - start)
                        the_time -= full_time
                        continue
                    for user in users:
                        if user['user_id'] == x.from_user.id:
                            data = await db.get_user(user['user_id'])
                            if not int(bid)-int(user['bid']) <= int(data['coin']):
                                already = True
                                await bot.send_message(update.chat.id, 'GCoin anda tidak mencukupi untuk menawar, silakan deposit terlebih dahulu.')
                                break
                            else:
                                already = True
                                is_worked = True
                                bid = int(bid)-int(user['bid'])
                                await db.decrease_coin(x.from_user.id, bid)
                                higher_bargainer['user_id'] = x.from_user.id
                                higher_bargainer['bid'] = higher_bid
                                await bot.send_message(update.chat.id, f'User {x.from_user.mention} memberikan penawaran sebesar {higher_bid}.')
                                break
                if not already:
                    data = await db.get_user(x.from_user.id)
                    if int(bid) <= int(data['coin']):
                        await db.decrease_coin(x.from_user.id, bid)
                        users.append({'user_id': x.from_user.id, 'bid': bid})
                        higher_bargainer['user_id'] = x.from_user.id
                        higher_bargainer['bid'] = higher_bid
                        await bot.send_message(update.chat.id, f'User {x.from_user.mention} memberikan penawaran sebesar {higher_bid}.')
                    else:
                        await bot.send_message(update.chat.id, 'GCoin anda tidak mencukupi untuk menawar, silakan deposit terlebih dahulu.')
                if is_worked:
                    for i in range(len(users)):
                        if users[i]['user_id'] == x.from_user.id:
                            users[i] = {'user_id': x.from_user.id, 'bid': higher_bid}
            full_time = int(time.time() - start)
            the_time -= full_time

            
xbot.run()
