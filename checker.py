import time
import socket
import socks

# Настройки
PROXY_FILE = 'proxies.txt'
# Будем стучаться на стандартный веб-порт Google CDN
TEST_HOST = 'ajax.googleapis.com'
TEST_PORT = 443
TIMEOUT = 4  # Таймаут ожидания ответа от прокси в секундах

def check_proxy_raw(proxy_str):
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None
    
    # Парсим строку прокси (формат IP:PORT или USER:PASS@IP:PORT)
    try:
        if '@' in proxy_str:
            auth, ip_port = proxy_str.split('@')
            username, password = auth.split(':')
            ip, port = ip_port.split(':')
        else:
            username, password = None, None
            ip, port = proxy_str.split(':')
        
        port = int(port)
    except Exception:
        print(f"[-] {proxy_str} -> Ошибка формата строки")
        return None

    # Создаем чистый SOCKS5 сокет
    s = socks.socksocket()
    s.set_proxy(
        socks.SOCKS5, 
        addr=ip, 
        port=port, 
        username=username, 
        password=password,
        rdns=True  # Удаленный резолв DNS (аналог socks5h)
    )
    s.settimeout(TIMEOUT)
    
    start_time = time.time()
    try:
        # Пытаемся установить TCP-соединение с Google через прокси
        s.connect((TEST_HOST, TEST_PORT))
        elapsed = (time.time() - start_time) * 1000
        print(f"[+] {proxy_str} -> ЖИВОЙ (Ping: {int(elapsed)}ms)")
        s.close()
        return proxy_str
    except Exception as e:
        # Выводим причину, почему прокси отвалился (Connection refused, Timeout и т.д.)
        print(f"[-] {proxy_str} -> МЕРТВ ({type(e).__name__})")
        return None

def main():
    try:
        with open(PROXY_FILE, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Файл {PROXY_FILE} не найден.")
        return

    if not proxies:
        print("Список прокси пуст.")
        return

    print(f"Начало поочередной проверки {len(proxies)} прокси...")
    working_proxies = []
    
    for idx, proxy in enumerate(proxies, 1):
        # Проверяем прокси
        res = check_proxy_raw(proxy)
        if res:
            working_proxies.append(res)
            
        # Небольшая пауза между проверками, чтобы избежать сетевых затыков
        if idx < len(proxies):
            time.sleep(0.5)

    # Перезаписываем файл
    with open(PROXY_FILE, 'w') as f:
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
            
    print(f"\nПроверка завершена. Сохранено живых: {len(working_proxies)} из {len(proxies)}")

if __name__ == '__main__':
    main()
