import concurrent
import concurrent.futures
import time
from concurrent.futures import as_completed
from os import linesep
from queue import Queue, Empty

import requests


def get_my_ip(): #Format: "117.212.162.150"
    r = (requests.get("https://api.ipify.org", timeout = 5))
    return (r.content.decode("UTF-8", "Ignore")).strip()


def __init__():
    #Declaration
    global testing_site, MYIP, MAXWAIT, grade, initialized
    
    #Values
    MAXWAIT = 3
    grade = {
             0 : "Off",
             1:"Very Bad",
             2:"Bad",
             3:"Average",
             4:"Good",
             5:"Very Reliable Proxy"
            }
    testing_site = "https://www.duckduckgo.com"
    print("{} will be used as the testing site".format(testing_site))
    MYIP = get_my_ip()
    initialized = True
            
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

        
def test_site(url, proxy_url, totaltime = 0.0):
    proxy = {'http':proxy_url, 'https':proxy_url}
    start = time.time()
    try:
        r = requests.get(url, proxies = proxy, timeout=(1.5,5))
        if r.status_code != 200:
            raise Exception ("Not 200", "Invalid Response")
        elif MYIP:
            for value in  r.headers.values():
                if str(value).find(MYIP) != -1:
                    raise Exception ("Leaking IP",
                    "Avoid This Proxy Like Plague")
                    break
    except:
        return 0, totaltime+(time.time()-start)
    return 1, totaltime+(time.time()-start)



def test_explode(proxy_site, totalTries, fastest, MAXWAIT):
    #Test Repetitively
    total_hits = total_duration = 0
    for _ in range(totalTries):
        try:
            hit, duration = test_site(testing_site,proxy_site)
            total_hits += hit
            total_duration += duration
        except:
            pass
    result = 'failed'
    time_taken = round(total_duration/totalTries, MAXWAIT)
    if total_hits == totalTries: #and total_duration/totalTries < 2:
        fastest.put(proxy_site, True, MAXWAIT*2)
        #print ("{},{}".format(proxy_site, time_taken))
        result = 'successful'
    return proxy_site, result ,time_taken

    
def read_file_links(fname, socks_mode):
    prefix = "socks5://" if socks_mode else "https://"
    motherset = list()
    with open(fname, 'r') as r:
        for line in r:
            line = line.strip().replace("https://","").replace("socks5://","")
            if line == '':
                continue
            line = prefix + line
            #Clean input has now entered the system.
            motherset.append(line.strip()) 
    return motherset

        
def write_file_links(fastest, output_file_name):
    with open(output_file_name, 'a', encoding='UTF-8') as w:
        while True:
            try:
                site = fastest.get(False)
                w.write(str.strip(site)+linesep)
            except Empty:
                break

                
def proxy_test(input_file_name, output_file_name,
                             socks_mode = True,
                             threads = True,
                             MAX_WORKERS = 20):

    if 'initialized' not in globals().keys():
        __init__()

    format_string = "{} \tResult: {} \t|Took {} secs. / Request"
    motherset = read_file_links(input_file_name, socks_mode)
    debug, using_threads = False, True
    fastest = Queue()
    if debug:
        for item in motherset:
            test_explode(item, fastest)
    elif using_threads:
            #futures = [executor.submit(test_explode,item) 
            #for item in motherset]To
        complete_chunk_list = list(chunks(motherset,MAX_WORKERS))
        for chunk_list in complete_chunk_list:
            workers = min(len(chunk_list),MAX_WORKERS)
            with concurrent.futures.ThreadPoolExecutor(workers) as executor:
                futures = [executor.submit(test_explode,site,10,fastest,MAXWAIT) for site in chunk_list]
                concurrent.futures.wait(futures, timeout=workers*MAXWAIT)
                for future in as_completed(futures):
                    print (future.result())
    elif __name__ == '__main__':
        with concurrent.futures.ProcessPoolExecutor(MAX_WORKERS) as executor:
            futures = executor.starmap(test_explode, (motherset, fastest))
            
    #No matter what the method is used earlier, input will be in enclosed params
    write_file_links(fastest, output_file_name)
                
#So it doesn't execute in imports
if __name__ == "__main__":
    #__init__()
    proxy_test("vipsocks.txt", "fastest-socks.txt")
    
    
"""global request_headers
request_headers = {"Accept-Language": "en-US,en;q=0.5",
"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0)"+
" Gecko/20100101 Firefox/40.0"),
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
"Connection": "keep-alive"}"""
