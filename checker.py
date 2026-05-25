import os
import time
import requests

# Конфигурация
TIMEOUT = 4  # Максимальное время ожидания ответа от прокси
CHECK_URL = 'https://api.ipify.org?format=json'  # Легкий URL для проверки

def check_proxy(proxy_str):
    """
    Проверяет один прокси. 
    Возвращает кортеж: (proxy_str, is_alive, ping_ms, error_reason)
    """
    cleaned_proxy = proxy_str.strip()
    if not cleaned_proxy:
        return None
        
    # Форматируем строку под requests (добавляем socks5:// если нет)
    formatted_proxy = cleaned_proxy
    if not formatted_proxy.startswith('socks5://'):
        formatted_proxy = f'socks5://{formatted_proxy}'
        
    proxies = {
        'http': formatted_proxy,
        'https': formatted_proxy
    }
    
    start_time = time.time()
    try:
        # Делаем запрос через прокси
        response = requests.get(CHECK_URL, proxies=proxies, timeout=TIMEOUT)
        if response.status_code == 200:
            ping = int((time.time() - start_time) * 1000)
            return (cleaned_proxy, True, ping, None)
        else:
            return (cleaned_proxy, False, 0, f"Status{response.status_code}")
    except requests.exceptions.ProxyError as e:
        return (cleaned_proxy, False, 0, "ProxyError")
    except requests.exceptions.ConnectTimeout:
        return (cleaned_proxy, False, 0, "Timeout")
    except Exception as e:
        return (cleaned_proxy, False, 0, type(e).__name__)

def main():
    file_path = 'proxies.txt'
    
    if not os.path.exists(file_path):
        print(f"[-] Файл {file_path} не найден.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        proxies_list = [line.strip() for line in f if line.strip()]

    if not proxies_list:
        print("[-] Список прокси пуст.")
        return

    print(f"Начало поочередной проверки {len(proxies_list)} прокси...")
    
    alive_proxies = [] # Тут будем копить кортежи (proxy, ping)
    
    for current_proxy in proxies_list:
        result = check_proxy(current_proxy)
        if not result:
            continue
            
        proxy_str, is_alive, ping, error_reason = result
        
        if is_alive:
            print(f"[+] {proxy_str} -> ЖИВОЙ ({ping}ms)")
            alive_proxies.append((proxy_str, ping))
        else:
            print(f"[-] {proxy_str} -> МЕРТВ ({error_reason})")
            
        time.sleep(0.1) # Небольшая пауза, чтобы не спамить

    print("\n--- Фильтрация результатов ---")
    
    if not alive_proxies:
        print("[-] Ни один прокси не ответил. Файл будет очищен.")
        final_list = []
    else:
        # Проверяем, есть ли хоть один прокси с пингом <= 500 ms
        good_ping_proxies = [p for p in alive_proxies if p[1] <= 500]
        
        if good_ping_proxies:
            # Если есть быстрые прокси, оставляем только их (остальные > 500 отсеиваем)
            print(f"[!] Найдено прокси с пингом до 500мс. Применяем жесткий фильтр.")
            final_list = [p[0] for p in good_ping_proxies]
        else:
            # Если у ВСЕХ пинг больше 500, то включаем мягкий режим: оставляем тех, у кого пинг <= 1000 ms
            print(f"[!] У всех прокси пинг > 500мс. Переключаем порог на 1000мс.")
            soft_ping_proxies = [p for p in alive_proxies if p[1] <= 1000]
            final_list = [p[0] for p in soft_ping_proxies]
            
            if not final_list:
                print("[-] Даже до 1000мс никого нет. Все живые прокси слишком медленные и будут удалены.")

    # Перезаписываем файл proxies.txt отфильтрованными данными
    with open(file_path, 'w', encoding='utf-8') as f:
        for proxy in final_list:
            f.write(f"{proxy}\n")

    print(f"Проверка завершена. Сохранено в файл: {len(final_list)} из {len(proxies_list)}")

if __name__ == '__main__':
    main()
