import pyrogram, config, db, random, uuid, os, asyncio, pyromod.listen
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps


# Menjalankan bot
xbot = pyrogram.Client('GCoin-Bot-Drop', api_id=config.Config.APP_ID, api_hash=config.Config.API_HASH, bot_token=config.Config.BOT_TOKEN)


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


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('drop', '.'))
async def drop(bot, update):
    name, mention_name = await checking_user_name(update)
    angka = update.text.split(' ')[1]
    if not await db.is_user_exist(update.from_user.id):
        return await bot.send_message(update.chat.id, 'Anda tidak dapat melakukan drop GCoin, pastikan anda memiliki setidaknya 1 GCoin.\ngunakan .wallet untuk mengecek total GCoin anda.')
    if angka.isdigit():
        data = await db.get_user(update.from_user.id)
        if int(data['coin']) < int(angka):
            return await bot.send_message(update.chat.id, f'GCoin anda saat ini tidak mencukupi untuk melakukan drop sebesar {angka}.')
        elif int(angka) == 0:
            return await bot.send_message(update.chat.id, f'Drop GCoin 0 tidak di izinkan.')
        check_user_drop = await db.check_user_drop(update.from_user.id)
        await db.decrease_coin(update.from_user.id, angka)
        if not check_user_drop:
            text = str(uuid.uuid4()).split('-')[0]
            captcha = generate_captcha_image(text)
            await db.add_drop(update.from_user.id, name, angka, captcha)
            await bot.send_photo(update.chat.id, f'{captcha}.jpg', caption=f'Telah di-Drop GCoin sebesar {angka} oleh {mention_name}. Silahkan claim secepatnya.')
            os.remove(f'{captcha}.jpg')
        else: return await db.del_drop(check_user_drop['captcha'])
        is_claimed = False
        for _ in range(30):
            if is_claimed:
                break
            x = await update.chat.listen(filters='text')
            if x.text == f'.claim {captcha}':
                if int(x.from_user.id) != int(update.from_user.id):
                    await db.del_drop(captcha)
                    is_claimed = True
        if is_claimed:
            to_name, mention_name = await checking_user_name(x)
            if not await db.is_user_exist(x.from_user.id):
                await db.add_user(x.from_user.id, to_name, angka)
            else:
                await db.increase_coin(x.from_user.id, angka)
            await bot.send_message(update.chat.id, f'Selamat kepada user {mention_name} karena telah mendapatkan drop GCoin sebesar {angka} dari {name}.')
        else:
            await db.increase_coin(update.from_user.id, angka)
            await db.del_drop(captcha)


xbot.run()