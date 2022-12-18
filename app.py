import pyrogram, config, db

# Menjalankan bot
xbot = pyrogram.Client('GCoin-Bot', api_id=config.Config.APP_ID, api_hash=config.Config.API_HASH, bot_token=config.Config.BOT_TOKEN)


async def get_user_id_from_tag(update):
    if update.entities:
        is_filled = False
        for entities in update.entities:
            if entities.type == 'text_mention':
                user_id = entities.user.id
                name = entities.user.first_name+' '+entities.user.last_name if entities.user.last_name else entities.user.first_name
                to_return = user_id, name
                is_filled = True
            elif entities.type == 'mention':
                tag = update.text.split(' ')[1]
                try:
                    u = await update.chat.get_member(
                        user_id=tag
                    )
                    user_id = u.user.id
                    name = u.user.first_name+' '+u.user.last_name if u.user.last_name else u.user.first_name
                    to_return = user_id, name
                    is_filled = True
                except:
                    to_return = None, 'User tidak dapat ditemukan di grup ini.'
            else:
                if not is_filled:
                    to_return = None, None
        return to_return
    else:
        return None, None


async def checking_user_name(update):
    id = update.from_user.id
    if not await db.is_user_exist(id):
        pass
    else:
        name = update.from_user.first_name+' '+update.from_user.last_name if update.from_user.last_name else update.from_user.first_name
        data = await db.get_user(id)
        db_name = data['name']
        if name == db_name:
            pass
        else:
            await db.edit_user_name(id, name)


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
    list_commands = 'List Commands:\n\n`.top` - menampilkan top 10 pemilik GCoin teratas.\n`.wallet` - menampilkan total GCoin yang dimiliki.\n`.addcoin @tag nominal` - menambahkan GCoin kepada orang lain (khusus owner dan admin).\n`.delcoin @tag nominal` - mengurangi GCoin milik orang lain (khusus owner dan admin).\n`.transfer @tag nominal` - mentransfer GCoin milik anda kepada orang lain.\n`.addadmin @tag` - memasukkan user ke dalam list admin (khusus owner).\n`.deladmin @tag` - mengeluarkan user dari dari list admin (khusus owner).'
    await bot.send_message(update.chat.id, list_commands)


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('top', '.'))
async def top(bot, update):
    await checking_user_name(update)
    top = await db.get_top_10()
    await bot.send_message(update.chat.id, top)


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('wallet', '.'))
async def wallet(bot, update):
    await checking_user_name(update)
    if await db.is_user_exist(update.from_user.id):
        data = await db.get_user(update.from_user.id)
        coins = data['coin']
        await bot.send_message(update.chat.id, f'Total GCoin anda saat ini adalah: {coins}')
    else:
        await bot.send_message(update.chat.id, f'Total GCoin anda saat ini adalah: 0')


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
    id, name = await get_user_id_from_tag(update)
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
    await bot.send_message(update.chat.id, f'GCoin milik {name} telah ditambahkan ({coins})')


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
    id, name = await get_user_id_from_tag(update)
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
        return await bot.send_message(update.chat.id, f'Saat ini user {name} tidak memiliki GCoin, pastikan anda telah menambahkan GCoin kepada user {name}.')
    else:
        if (await db.get_user(id))['coin'] == '0':
            return await bot.send_message(update.chat.id, f'Saat ini user {name} tidak memiliki GCoin, pastikan anda telah menambahkan GCoin kepada user {name}.')
        else:
            coins = await db.decrease_coin(id, ammount)
    await bot.send_message(update.chat.id, f'GCoin milik {name} telah dikurangi ({coins})')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('transfer', '.'))
async def transfer(bot, update):
    await checking_user_name(update)
    if not await check_if_cmd_valid(update):
        return await bot.send_message(update.chat.id, 'Contoh: `.transfer @tag 10` atau `.transfer @tag all` untuk mengirim semua GCoin anda.')
    to_, to_name = await get_user_id_from_tag(update)
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
                await bot.send_message(update.chat.id, f'Semua GCoin anda telah ditransfer kepada {to_name}')
            else:
                await db.increase_coin(to_, ammount)
                await db.decrease_coin(from_, ammount)
                await bot.send_message(update.chat.id, f'GCoin sebanyak {ammount} telah ditransfer kepada {to_name}')
    else:
        await bot.send_message(update.chat.id, 'Anda tidak dapat melakukan transfer GCoin, pastikan anda memiliki setidaknya 1 GCoin.\ngunakan .wallet untuk mengecek total GCoin anda.')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('addadmin', '.') & pyrogram.filters.user(config.Config.OWNER_IDS))
async def addadmin(bot, update):
    await checking_user_name(update)
    id, name = await get_user_id_from_tag(update)
    if not id:
        if name:
            return await bot.send_message(update.chat.id, name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.addadmin @tag`')
    if not await db.is_admin_exist(id):
        await db.add_admin(id, name)
        return await bot.send_message(update.chat.id, f'{name} telah dimasukkan kedalam list admin.')
    else:
        return await bot.send_message(update.chat.id, f'{name} sudah ada di dalam list admin.')


@xbot.on_message(pyrogram.filters.group & pyrogram.filters.command('deladmin', '.') & pyrogram.filters.user(config.Config.OWNER_IDS))
async def deladmin(bot, update):
    await checking_user_name(update)
    id, name = await get_user_id_from_tag(update)
    if not id:
        if name:
            return await bot.send_message(update.chat.id, name)
        else:
            return await bot.send_message(update.chat.id, 'Contoh: `.addadmin @tag`')
    if await db.is_admin_exist(id):
        await db.del_admin(id)
        return await bot.send_message(update.chat.id, f'{name} telah dikeluarkan dari list admin.')
    else:
        return await bot.send_message(update.chat.id, f'{name} tidak dapat ditemukan di dalam list admin.')


xbot.run()
