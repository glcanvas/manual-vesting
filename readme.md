
# How to run

1) Задеплоить Vesting в сеть
   * Выбрать rpc: configs -> provider
   * Ввести приватный ключ: configs -> private_key
2) python ./deploy.py -p full/path/to/config.json --vesting
3) После 2ого пункта получим адрес контракта vesting
   * Добавить этот адрес в конфиг: configs -> vesting
4) В config добавить список токенов в tokens
5) Добавить список получателей в recipients -- надо указать 2 параметра: address, amount (1 -- адрес получателя, 2 -- процент от токенов для получения)
6) python ./main.py -p full/path/to/config.json -f
   * -f -- падать на неверном конфиге или брать последний валидный

Особенности:
1) В списке recipients сумма % должна быть равна 100, иначе ничего не заработает
2) Раз в 10 секунд скрипт запрашивает балансы всех токенов в tokens
3) Если баланс != 0, то отправляет токены на адреса из списка recipients
4) Конфиг можно обновлять без выключения скрипта, если будет ошибка то программа или упадет или возьмет последний верный скрипт -- см флаг -f
