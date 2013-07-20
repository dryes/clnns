#!/usr/bin/python3

# Author: Joseph Wiseman <joswiseman@gmail>
# URL: https://github.com/dryes/clnns/

import argparse,configparser,feedparser,shutil,os,socket,sys,time,urllib.request

def init_configparser(filename='~/.config/clnns/clnns.ini'):
    filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
        if not os.path.isdir(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except:
                if len(str(sys.exc_info()[1])) > 0:
                    print(sys.exc_info()[1])
                sys.exit(1)
        content = '[hosts]\nnzbs = https://www.nzbs.org/;12345fghijk;\nnzbsu = https://www.nzb.su;123cdefijk;\nalias = http://www.url.com;apikey;optional_desc'
        try:
            with open(filename, 'w') as f:
                f.write(content)
            print('Config file written to: %s.' % (filename))
            sys.exit(1)
        except:
            if len(str(sys.exc_info()[1])) > 0:
                print(sys.exc_info()[1])
            sys.exit(1)

    config = configparser.ConfigParser()
    config.read(filename)

    if len(config['hosts']) == 0:
        print('Hosts list is empty - edit config at: %s.' % (filename))
        sys.exit(1)

    return config

def init_argparse(config):
    parser = argparse.ArgumentParser(description='command line newznab search.', usage=os.path.basename(sys.argv[0]) + ' [--opts] query')
  
    parser.add_argument('query', nargs='*', help='search string', default='')
    parser.add_argument('--category', '-c', help='category #', default='')
    parser.add_argument('--output', '-o', help='output dir.', default=os.getcwd())
    parser.add_argument('--provider', '-p', help='alias of provider', default=None)
    parser.add_argument('--first', '-f', action='store_true', help='grab first result without prompt', default=False)
    parser.add_argument('--limit', '-l', help='maximum number of results', default=15)
    parser.add_argument('--maxage', '-m', help='maximum age of results in days', default=1500)
    parser.add_argument('--offset', help='results offset from 0', default=0)
    parser.add_argument('--sleep', '-s', help='number of seconds to wait between requests', default=3)

    args = parser.parse_args()
    args = vars(args)

    for h in config['hosts']:
         firsthost = h
         break

    if len(args['query']) > 0:
        args['query'] = '&q=' + str(args['query'])

    if len(args['category']) > 0:
        args['category'] = '&cat=' + str(args['category'])

    if args['provider'] is None:
        args['provider'] = config['hosts'][firsthost].split(';')
    else:
        try:
            config['hosts'][args['provider']]
        except:
            print('Provider %r not found in config.' % args['provider'])
            sys.exit(1)
        args['provider'] = config['hosts'][args['provider']].split(';')

    if len(args['provider'][1]) != 32:
        print('API key for %r is incorrect length - edit config file.' % (args['provider'][0]))
        sys.exit(1)

    args['limit'] = '&limit=' + str(args['limit'])
    args['maxage'] = '&maxage=' + str(args['maxage'])
    args['offset'] = '&offset=' + str(args['offset'])

    return args

def getnzb(link, title, output):
    if not os.path.isdir(output):
        try:
            os.makedirs(output)
        except:
            if len(str(sys.exc_info()[1])) > 0:
                print(sys.exc_info()[1])
            return False

    output = os.path.join(output, title + '.nzb')

    try: 
        socket.setdefaulttimeout(30)
        urllib.request.urlretrieve(link, output)
    except:
        if len(str(sys.exc_info()[1])) > 0:
            print(sys.exc_info()[1])
        return False

    if os.path.getsize(output) == 0 or not os.path.isfile(output):
        print('Error downloading: %s' % (title))
        try:
            os.unlink(output)
        except:
            if len(str(sys.exc_info()[1])) > 0:
                print(sys.exc_info()[1])
        return False

    print('%r downloaded successfully.' % (output))
    return True

def main(args):
    print('Searching on: %s ..' % args['provider'][0], end='')

    try:
        url = '%s/api?t=search%s&apikey=%s%s%s%s%s' % (args['provider'][0], args['category'], args['provider'][1], args['query'], args['limit'], args['maxage'], args['offset'])
        apiresponse = feedparser.parse(url.replace('//api?t', '/api?t'))
    except:
        if len(str(sys.exc_info()[1])) > 0:
            print(sys.exc_info()[1])
        return False

    results = len(apiresponse.entries)
    if apiresponse.entries is None or results == 0:
        print('. no results.')
        sys.exit()

    print('. ' + str(results) + ' results.\n')

    if args['first'] == True:
        if getnzb(apiresponse.entries[0]['link'], apiresponse.entries[0]['title'], args['output']) == False:
             return False
        return True

    i = 0
    for r in apiresponse.entries:
        print('[%s]\t%s\n\t   %s -- %s\n' % (str((i+1)), r['title'], r['category'], r['published']))
        i += 1

    rs = input('enter #s to download (eg.: 1 2 4-6): ')
    if len(rs) == 0:
        sys.exit()

    rs = rs.split(' ')
    get = []
    for n in rs:
        if n.strip() == '':
            continue
        if '-' in n:
            n = n.split('-')
            for i in range(int(n[0]), (int(n[1])+1)):
                if str(i).isdigit():
                    get.append((i-1))
        elif n.isdigit():
            get.append((int(n)-1))

    for i in get:
         if i > results:
             continue
         if getnzb(apiresponse.entries[i]['link'], apiresponse.entries[i]['title'], args['output']) == False:
             return False
         time.sleep(args['sleep'])

    return True

        
if __name__ == '__main__':
    args = init_argparse(init_configparser(filename='~/.config/clnns/clnns.ini'))
    if main(args) == False:
        sys.exit(1)