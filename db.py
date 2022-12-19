import motor.motor_asyncio, config, collections

up = motor.motor_asyncio.AsyncIOMotorClient(config.Config.DB_URI)['GCoin']['users']
up_admin = motor.motor_asyncio.AsyncIOMotorClient(config.Config.DB_URI)['GCoin']['admins']
drop = motor.motor_asyncio.AsyncIOMotorClient(config.Config.DB_URI)['GCoin']['drop']

def int_checker(integer_):
    if integer_ > 0:
        return integer_
    elif integer_ == 0:
        return 0
    else:
        return 0

async def add_drop(id, name, ammount, captcha):
    await drop.insert_one({'x': 'x', 'id': str(id), 'name': name, 'ammount': ammount, 'captcha': captcha})

async def check_captcha(captcha):
    x = await drop.find_one({'captcha': captcha})
    return x if x else False

async def check_user_drop(id):
    x = await drop.find_one({'id': str(id)})
    return x if x else False

async def del_drop(captcha):
    await drop.delete_many({'captcha': captcha})

async def add_user(id, name='', coin='0'):
    await up.insert_one({'id': str(id), 'name': name, 'coin': coin})

async def add_admin(id, name):
    await up_admin.insert_one({'id': str(id), 'name': name})

async def is_admin_exist(id):
    return True if await up_admin.find_one({'id': str(id)}) else False

async def get_admin(id):
    return await up_admin.find_one({'id': str(id)})

async def get_admins():
    admins = up_admin.find({})
    owner_ids = config.Config.OWNER_IDS
    if admins:
        async for admin in admins:
            owner_ids.append(int(admin['id']))
        return owner_ids
    else:
        return owner_ids

async def del_admin(id):
    await up_admin.delete_many({'id': str(id)})

async def get_user(id):
    return await up.find_one({'id': str(id)})

async def edit_user_name(id, name):
    await up.update_one({'id': str(id)}, {'$set': {'name': str(name)}})

async def is_user_exist(id):
    return True if await up.find_one({'id': str(id)}) else False

async def increase_coin(id, ammount):
    old = await get_user(id)
    current_coin = int_checker(int(old['coin'])+int(ammount))
    await up.update_one({'id': str(id)}, {'$set': {'coin': str(current_coin)}})
    return str(current_coin)

async def decrease_coin(id, ammount):
    old = await get_user(id)
    current_coin = int_checker(int(old['coin'])-int(ammount))
    await up.update_one({'id': str(id)}, {'$set': {'coin': str(current_coin)}})
    return str(current_coin)

async def get_top_10():
    documents = up.find({})
    docs = {}
    async for doc in documents:
        docs[doc['id']] = int(doc['coin'])
    c = collections.Counter(docs)
    if c:
        top_10 = c.most_common(10)
        text = 'Top GCoin:\n\n'
        x = 1
        for u in top_10:
            id = u[0]
            name = (await get_user(id))['name']
            coins = u[1]
            count = str(x)
            text+=f"{count}. **{name}** — {coins} GCoin\n"
            x+=1
        return text
    else:
        return 'Tidak ditemukan satu user pun dalam top 10.'
