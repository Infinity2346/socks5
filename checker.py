import time
import socket
import socks

# Настройки
PROXY_FILE = 'proxies.txt'
TEST_HOST = 'ajax.googleapis.com'
TEST_PORT = 443
TIMEOUT = 4  # Таймаут в секундах

def check_proxy_raw(proxy_str):
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None
    
    # Сохраняем исходный вид для записи обратно в файл, если прокси живой
    original_proxy = proxy_str 

    # Очищаем от протоколов, если они случайно затесались в начале строки
    if "://" in proxy_str:
        proxy_str = proxy_str.split("://")[-1]

    # Парсим строку прокси (поддержка IP:PORT и USER:PASS@IP:PORT)
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
        print(f"[-] {original_proxy} -> Ошибка формата строки")
        return None

    # Создаем SOCKS5 сокет
    s = socks.socksocket()
    s.set_proxy(
        socks.SOCKS5, 
        addr=ip, 
        port=port, 
        username=username, 
        password=password,
        rdns=True  # Резолвим DNS на стороне прокси
    )
    s.settimeout(TIMEOUT)
    
    start_time = time.time()
    try:
        s.connect((TEST_HOST, TEST_PORT))
        elapsed = (time.time() - start_time) * 1000
        print(f"[+] {original_proxy} -> ЖИВОЙ ({int(elapsed)}ms)")
        s.close()
        return original_proxy  # Возвращаем исходную строку, чтобы не портить ваш формат файла
    except Exception as e:
        print(f"[-] {original_proxy} -> МЕРТВ ({type(e).__name__})")
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
        res = check_proxy_raw(proxy)
        if res:
            working_proxies.append(res)
            
        # Пауза в полсекунды между проверками
        if idx < len(proxies):
            time.sleep(0.5)

    # Перезаписываем файл только живыми прокси
    with open(PROXY_FILE, 'w') as f:
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
            
    print(f"\nПроверка завершена. Сохранено живых: {len(working_proxies)} из {len(proxies)}")

if __name__ == '__main__':
    main()
