import pyrogram, config, db, random, uuid, os
from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps

# Menjalankan bot
xbot = pyrogram.Client('GCoin-Bot', api_id=config.Config.APP_ID, api_hash=config.Config.API_HASH, bot_token=config.Config.BOT_TOKEN)


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
    if cmd in ['.addcoin', '.delcoin']:
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


@xbot.on_message((pyrogram.filters.group|pyrogram.filters.private) & pyrogram.filters.command('start', '.'))
async def start(bot, update):
    bot_name = (await bot.get_me()).first_name
    await bot.send_message(update.chat.id, f'Hai, saya adalah {bot_name}')


@xbot.on_message((pyrogram.filters.group|pyrogram.filters.private) & pyrogram.filters.command('help', '.'))
async def _help(bot, update):
    list_commands = 'List Commands:\n\n`.top` - menampilkan top 10 pemilik GCoin teratas.\n`.wallet` - menampilkan total GCoin yang dimiliki.\n`.addcoin @tag nominal` - menambahkan GCoin kepada orang lain (khusus owner dan admin).\n`.delcoin @tag nominal` - mengurangi GCoin milik orang lain (khusus owner dan admin).\n`.transfer @tag nominal` - mentransfer GCoin milik anda kepada orang lain.\n`.addadmin @tag` - memasukkan user ke dalam list admin (khusus owner).\n`.deladmin @tag` - mengeluarkan user dari dari list admin (khusus owner).\n`.gcoin` - pengertian gcoin.\n`.flip nominal` - flip GCoin milik anda (judi).\n`.drop nominal` - men-drop GCoin anda untuk diclaim oleh user lain (giveaway).\n`.claim <captcha>` - meng-claim GCoin yang di drop.'
    await bot.send_message(update.chat.id, list_commands)


@xbot.on_message((pyrogram.filters.group|pyrogram.filters.private) & pyrogram.filters.command('gcoin', '.'))
async def gcoin(bot, update):
    text = 'GCoin merupakan mata uang yang dibuat oleh @GrowtopiaIndonesia. GCoin bisa digunakan seperti mata uang pada umumnya (untuk berbelanja, transaksi, dan lain lain). GCoin bisa didapatkan dengan cara deposit dengan @PiuStore (tentu saja bisa withdraw, namun ada fee 1k). 1 GCoin = Rp 1.'
    await bot.send_message(update.chat.id, text)


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('flip', '.'))
async def flip(bot, update):
    if not await db.is_user_exist(update.from_user.id):
        return await bot.send_message(update.chat.id, 'Anda tidak dapat melakukan flip GCoin, pastikan anda memiliki setidaknya 1 GCoin.\ngunakan .wallet untuk mengecek total GCoin anda.')
    name, mention_name = await checking_user_name(update)
    angka = update.text.split(' ')[1]
    if angka.isdigit():
        data = await db.get_user(update.from_user.id)
        if int(data['coin']) < int(angka):
            return await bot.send_message(update.chat.id, f'GCoin anda saat ini tidak mencukupi untuk melakukan flip sebesar {angka}.')
        await bot.send_photo(
            chat_id=update.chat.id,
            photo='AgACAgUAAxkBAANlY594vkUoF7_amPyeJ803r7zgQdQAAsKvMRs-VAFVvKqmGx01FpMACAEAAwIAA3kABx4E',
            caption='Pilih antara angka atau gambar.',
            reply_markup=pyrogram.types.InlineKeyboardMarkup([
                [
                    pyrogram.types.InlineKeyboardButton('Angka', f'd-{update.from_user.id}-{angka}'),
                    pyrogram.types.InlineKeyboardButton('Gambar', f'b-{update.from_user.id}-{angka}')
                ]
            ])
        )


@xbot.on_callback_query()
async def buttons(bot, update):
    cb = update.data
    depan = 'CAACAgUAAx0CYF-hHQABAhCnY59kAwABfZc5NgEyZV6-sEuKAyzaAAKgCAAC4pX5VGHmIZUoMQABrR4E'
    belakang = 'CAACAgUAAx0CYF-hHQABAhCoY59kB7kWoOBIe8UiH5uHrMDE9pAAAosGAAK3ZgFVQuwkTFykGugeBA'
    listed = [depan, belakang]
    side, id, angka = cb.split('-')
    if update.from_user.id != int(id):
        return await update.answer(f"Flip ini bukan milik anda.", show_alert=True)
    random_side = random.choice(listed)
    x = int(angka)/2
    y = int(x)/2
    z = int(x)*3-(x*2)
    final = int(z+y)
    await update.message.reply_sticker(random_side)
    angka = str(angka)
    final = str(final)
    if side == 'd':
        if random_side == depan:
            await update.answer(f"GCoin anda telah bertambah sebanyak {final}", show_alert=True)
            await db.increase_coin(id, final)
        else:
            await update.answer(f"GCoin anda telah berkurang sebanyak {angka}", show_alert=True)
            await db.decrease_coin(id, angka)
    elif side == 'b':
        if random_side == belakang:
            await update.answer(f"GCoin anda telah bertambah sebanyak {final}", show_alert=True)
            await db.increase_coin(id, str(final))
        else:
            await db.decrease_coin(id, str(angka))
            await update.answer(f"GCoin anda telah berkurang sebanyak {angka}", show_alert=True)
    else:
        pass
    await update.message.delete()


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
        check_user_drop = await db.check_user_drop(update.from_user.id)
        if not check_user_drop:
            text = str(uuid.uuid4()).split('-')[0]
            captcha = generate_captcha_image(text)
            await db.add_drop(update.from_user.id, name, angka, captcha)
            await bot.send_photo(update.chat.id, f'{captcha}.jpg', caption=f'Telah di-Drop GCoin sebesar {angka} oleh {mention_name}. Silahkan claim secepatnya.')
            os.remove(f'{captcha}.jpg')
        else:
            captcha = generate_captcha_image(check_user_drop['captcha'])
            angka = check_user_drop['ammount']
            await bot.send_photo(update.chat.id, f'{captcha}.jpg', caption=f'**Terdapat drop yang belum di claim.**\n\nTelah di-Drop GCoin sebesar {angka} oleh {mention_name}. Silahkan claim secepatnya.')
            os.remove(f'{captcha}.jpg')



@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('claim', '.'))
async def claim(bot, update):
    to_name, mention_name = await checking_user_name(update)
    captcha = update.text.split(' ')[1]
    is_drop_exist = await db.check_captcha(captcha)
    if is_drop_exist:
        angka = is_drop_exist['ammount']
        id = is_drop_exist['id']
        name = is_drop_exist['name']
        if int(update.from_user.id) != int(id):
            await db.del_drop(captcha)
            data = await db.get_user(id)
            if int(data['coin']) < int(angka):
                return await bot.send_message(update.chat.id, f'GCoin milik {name} saat ini tidak mencukupi untuk melakukan drop sebesar {angka}, drop telah dibatalkan.')
            if not await db.is_user_exist(update.from_user.id):
                await db.add_user(update.from_user.id, to_name, angka)
            else:
                await db.increase_coin(update.from_user.id, angka)
            await db.decrease_coin(id, angka)
            await bot.send_message(update.chat.id, f'Selamat kepada user {mention_name} karena telah mendapatkan drop GCoin sebesar {angka} dari {name}.')
      

@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('top', '.'))
async def top(bot, update):
    await checking_user_name(update)
    top = await db.get_top_10()
    await bot.send_message(update.chat.id, top)


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('wallet', '.'))
async def wallet(bot, update):
    name, mention_name = await checking_user_name(update)
    if await db.is_user_exist(update.from_user.id):
        data = await db.get_user(update.from_user.id)
        coins = data['coin']
        await bot.send_message(update.chat.id, f'Total GCoin {mention_name} saat ini adalah: {coins}')
    else:
        await bot.send_message(update.chat.id, f'Total GCoin {mention_name} saat ini adalah: 0')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('addcoin', '.'))
async def addcoin(bot, update):
    await checking_user_name(update)
    if not await check_if_cmd_valid(update):
        return await bot.send_message(update.chat.id, 'Contoh: .addcoin @tag 10')
    admins = await db.get_admins()
    if admins:
        if not update.from_user.id in admins:
            return
        else:
            pass
    else:
        return
    id, name, mention_name = await get_user_id_from_tag(update)
    try:
        cmd, tag, ammount = update.text.split(' ')
    except:
        return await bot.send_message(update.chat.id, 'Contoh: .addcoin @tag 10')
    if not id:
        if name:
            return await bot.send_message(update.chat.id, name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.addcoin @tag 10`')
    if await db.is_user_exist(id):
        coins = await db.increase_coin(id, ammount)
    else:
        await db.add_user(id, name, '0')
        coins = await db.increase_coin(id, ammount)
    await bot.send_message(update.chat.id, f'GCoin milik {mention_name} telah ditambahkan ({coins})')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('delcoin', '.'))
async def delcoin(bot, update):
    await checking_user_name(update)
    if not await check_if_cmd_valid(update):
        return await bot.send_message(update.chat.id, 'Contoh: `.delcoin @tag 10`')
    admins = await db.get_admins()
    if admins:
        if not update.from_user.id in admins:
            return
        else:
            pass
    else:
        return
    id, name, mention_name = await get_user_id_from_tag(update)
    try:
        cmd, tag, ammount = update.text.split(' ')
    except:
        return await bot.send_message(update.chat.id, 'Contoh: `.delcoin @tag 10`')
    if not id:
        if name:
            return await bot.send_message(update.chat.id, name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.delcoin @tag 10`')   
    if not await db.is_user_exist(id):
        return await bot.send_message(update.chat.id, f'Saat ini user {mention_name} tidak memiliki GCoin, pastikan anda telah menambahkan GCoin kepada user {name}.')
    else:
        if (await db.get_user(id))['coin'] == '0':
            return await bot.send_message(update.chat.id, f'Saat ini user {mention_name} tidak memiliki GCoin, pastikan anda telah menambahkan GCoin kepada user {name}.')
        else:
            coins = await db.decrease_coin(id, ammount)
    await bot.send_message(update.chat.id, f'GCoin milik {mention_name} telah dikurangi ({coins})')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('transfer', '.'))
async def transfer(bot, update):
    from_name, from_mention_name = await checking_user_name(update)
    if not await check_if_cmd_valid(update):
        return await bot.send_message(update.chat.id, 'Contoh: `.transfer @tag 10` atau `.transfer @tag all` untuk mengirim semua GCoin anda.')
    to_, to_name, to_mention_name = await get_user_id_from_tag(update)
    try:
        cmd, tag, ammount = update.text.split(' ')
    except:
        return await bot.send_message(update.chat.id, 'Contoh: `.transfer @tag 10` atau `.transfer @tag all` untuk mentranfer semua GCoin anda.')
    if not to_:
        if to_name:
            return await bot.send_message(update.chat.id, to_name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.transfer @tag 10` atau `.transfer @tag all` untuk mentranfer semua GCoin anda.')
    from_ = update.from_user.id
    if to_ == from_:
        return await bot.send_message(update.chat.id, 'Tidak dapat mentransfer GCoin kepada diri sendiri.')
    if await db.is_user_exist(from_):
        from_data = await db.get_user(from_)
        if from_data['coin'] == '0':
            await bot.send_message(update.chat.id, 'Anda tidak dapat melakukan transfer GCoin, pastikan anda memiliki setidaknya 1 GCoin.\ngunakan .wallet untuk mengecek total GCoin anda.')
        else:
            if not await db.is_user_exist(to_):
                await db.add_user(to_, to_name, '0')
            if ammount == 'all':
                coins = from_data['coin']
                await db.increase_coin(to_, coins)
                await db.decrease_coin(from_, coins)
                await bot.send_message(update.chat.id, f'Semua GCoin {from_mention_name} telah ditransfer kepada {to_mention_name}')
            else:
                await db.increase_coin(to_, ammount)
                await db.decrease_coin(from_, ammount)
                await bot.send_message(update.chat.id, f'GCoin {from_mention_name} sebanyak {ammount} telah ditransfer kepada {to_mention_name}')
    else:
        await bot.send_message(update.chat.id, 'Anda tidak dapat melakukan transfer GCoin, pastikan anda memiliki setidaknya 1 GCoin.\ngunakan .wallet untuk mengecek total GCoin anda.')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('addadmin', '.') & pyrogram.filters.user(config.Config.OWNER_IDS))
async def addadmin(bot, update):
    await checking_user_name(update)
    id, name, mention_name = await get_user_id_from_tag(update)
    if not id:
        if name:
            return await bot.send_message(update.chat.id, name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.addadmin @tag`')
    if not await db.is_admin_exist(id):
        await db.add_admin(id, name)
        return await bot.send_message(update.chat.id, f'{mention_name} telah dimasukkan kedalam list admin.')
    else:
        return await bot.send_message(update.chat.id, f'{mention_name} sudah ada di dalam list admin.')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('deladmin', '.') & pyrogram.filters.user(config.Config.OWNER_IDS))
async def deladmin(bot, update):
    await checking_user_name(update)
    id, name, mention_name = await get_user_id_from_tag(update)
    if not id:
        if name:
            return await bot.send_message(update.chat.id, name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.addadmin @tag`')
    if await db.is_admin_exist(id):
        await db.del_admin(id)
        return await bot.send_message(update.chat.id, f'{mention_name} telah dikeluarkan dari list admin.')
    else:
        return await bot.send_message(update.chat.id, f'{mention_name} tidak dapat ditemukan di dalam list admin.')


xbot.run()
