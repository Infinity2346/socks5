import concurrent.futures
import requests

# Настройки
PROXY_FILE = 'proxies.txt'
# Исландский или любой другой региональный блок Google CDN отдаст 200 OK, если прокси работает
TEST_URL = 'https://ajax.googleapis.com/ajax/libs/angularjs/1.8.2/angular.min.js'
TIMEOUT = 5  # Таймаут в секундах
MAX_WORKERS = 20  # Количество одновременных потоков

def check_proxy(proxy):
    proxy = proxy.strip()
    if not proxy:
        return None
    
    # Используем socks5h, чтобы DNS-запросы тоже шли через прокси (защита от утечки DNS)
    proxies = {
        'http': f'socks5h://{proxy}',
        'https': f'socks5h://{proxy}'
    }
    
    try:
        # Запрашиваем скрипт. Если прокси живой и достучался до Google CDN, вернется 200 OK
        response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if response.status_code == 200:
            return proxy
    except Exception:
        # Любая ошибка (таймаут, сброс соединения, handshake error) означает, что прокси мертв
        pass
    
    return None

def main():
    try:
        with open(PROXY_FILE, 'r') as f:
            proxies = f.readlines()
    except FileNotFoundError:
        print(f"Файл {PROXY_FILE} не найден.")
        return

    working_proxies = []
    
    # Проверяем весь список асинхронно в несколько потоков
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(check_proxy, proxies)
        
        for result in results:
            if result:
                working_proxies.append(result)

    # Перезаписываем файл, убирая те, что не ответили
    with open(PROXY_FILE, 'w') as f:
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
            
    print(f"Проверка завершена. Осталось живых прокси: {len(working_proxies)} из {len(proxies)}")

if __name__ == '__main__':
    main()
