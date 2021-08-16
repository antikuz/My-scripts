import paramiko
import logging
import time
from conf import HOSTS, USER, PASSWD, PORT

# Mikrotik commands
mikrotik = {'version check': 'system package update print',
           'firmware check': 'system routerboard print',
           'firmware upgrade': 'system routerboard upgrade',
           'update check': 'system package update check-for-updates',
           'update download': 'system package update download',
           'disable ssh': 'ip service disable ssh',
           'system reboot': 'system reboot'}

# Logging conf
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s;%(levelname)s;%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/info.log", encoding='utf8'),
        logging.StreamHandler()
    ]
)


def create_ssh_connect(ip, port=PORT, user=USER, passwd=PASSWD):
    '''
    Try to establish ssh connection
    '''
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, PORT, USER, SECRET)
        return client
    except TimeoutError:
        logging.error(f'{ip} TimeoutError')
        return False
    except paramiko.ssh_exception.NoValidConnectionsError:
        logging.error(f'{ip} SSH not enable')
        return False
    except Exception as err:
        logging.error(f'{ip} create_ssh_connect() unknown error [{str(err)}]')
        return False


def version_check(ssh, ip):
    '''
    Check version before update
    '''
    try:
        stdin, stdout, stderr = ssh.exec_command(mikrotik['version check'])
        version = stdout.read().decode().split()[3]
        return version
    except Exception as err:
        logging.error(f'{ip} version_check() unknown error [{str(err)}]')
        return False


def version_check_after_update(ip, oldversion):
    '''
    After the update, try to establish ssh connection 
    and compare versions within three attempts
    '''
    for attempt in range(3):
        ssh = create_ssh_connect(ip)
        
        if ssh:
            stdin, stdout, stderr = ssh.exec_command(mikrotik['version check'])
            data = stdout.read()
            newversion = data.decode("utf8").split()[3]
            
            if oldversion:
                if newversion > oldversion:
                    logging.info(f'{ip} newversion: {newversion}')
                elif oldversion == newversion:
                    logging.info(f'{ip} the latest update is installed: {oldversion} == {newversion}')
                else:
                    logging.error(f'{ip} error check after update [oldversion={oldversion} | newversion={newversion}]')
                ssh.close()
                return True
            else:
                logging.error(f'{ip} not old version')
            
            ssh.close()
            return
        else:
            time.sleep(20)
    
    logging.error(f'{ip} can\'t connect after update')
    return False


def firmware_check(ssh, ip):
    '''
    Check firmware before update
    '''
    try:
        stdin, stdout, stderr = ssh.exec_command(mikrotik['firmware check'])
        data = stdout.read().decode('utf8').split()
        return data
    except Exception as err:
        logging.error(f'{ip} firmware_check() unknown error [{str(err)}]')
        return False


def firmware_upgrade(ssh, ip):
    try:
        stdin, stdout, stderr = ssh.exec_command(mikrotik['firmware upgrade'])
        data = stdout.read()
        if data == b'':
            logging.info(f'{ip} Upgrade success, send to reboot')
            ssh.exec_command(mikrotik['system reboot'])
            return True
        else:
            logging.error(f'{ip} firmware_upgrade() unknown error [{data.decode("utf8")}]')
            return False
    except Exception as err:
        logging.error(f'{ip} firmware_upgrade() unknown error [{str(err)}]')
        return False


def firmware_check_after_upgrade(ip, oldversion):
    '''
    After the upgrade, try to establish ssh connection 
    and compare firmware within three attempts
    '''
    for attempt in range(3):
        ssh = create_ssh_connect(ip)
        
        if ssh:
            stdin, stdout, stderr = ssh.exec_command(mikrotik['firmware check'])
            data = stdout.read()
            newversion = data.decode("utf8").split()[15]

            if oldversion:
                if newversion > oldversion:
                    logging.info(f'{ip} newversion: {newversion}')
                elif oldversion == newversion:
                    logging.info(f'{ip} the latest update is installed: {oldversion} == {newversion}')
                else:
                    logging.error(f'{ip} error check after upgrade firmware [oldversion={oldversion} | newversion={newversion}]')
                ssh.close()
                return
            else:
                logging.error(f'{ip} not old firmware')
            
            ssh.close()
            return
        else:
            time.sleep(20)
    logging.error(f'{ip} can\'t connect after upgrade')
    return False


def update_check(ssh, ip):
    '''
    Check the update, if the response contains 'New version is available' then 
    return True otherwise, return False. Also, the new version may not be 
    available if there is no Internet, this check is not yet available
    '''
    try:
        stdin, stdout, stderr = ssh.exec_command(mikrotik['update check'])
        data = stdout.read()
        if b'status: New version is available' in data:
            logging.info(f'{ip} New version is available')
            return True
        else:
            logging.info(f'{ip} New version is not available')
            return False
    except Exception as err:
        logging.error(f'{ip} update_check() unknown error [{str(err)}]')
        return False


def update_download(ssh, ip):
    '''
    Download the update, if it succeeds, then we reboot the router to install. 
    Otherwise, check the error lack of download space or something else. 
    Return True or False. 
    '''
    try:
        stdin, stdout, stderr = ssh.exec_command(mikrotik['update download'])
        data = stdout.read()
        if b'status: Downloaded, please reboot router to upgrade it' in data:
            logging.info(f'{ip} update downloaded, reboot router for upgrade')
            ssh.exec_command(mikrotik['system reboot'])
            logging.info(f'{ip} send reboot')
            return True
        elif b'ERROR: not enough disk space' in data:
            logging.error(f'{ip} not enough disk space')
            return False
        else:
            logging.error(f'{ip} not download upgrade')
            return False
    except Exception as err:
        logging.error(f'{ip} update_download() unknown error [{str(err)}]')
        return False


def version_update_all_mikrotik(hosts=HOSTS):
    for ip in hosts:
        ssh = create_ssh_connect(ip)
        if ssh:
            logging.info(f'{ip} Connect success')
            version = version_check(ssh, ip)
            logging.info(f'{ip} version = {version}')
            if update_check(ssh, ip):
                if update_download(ssh, ip):
                    time.sleep(20)
                    version_check_after_update(ip, version)


def firmware_upgrade_all_mikrotik(hosts=HOSTS):
    '''
    Let's check the difference between the Routerboard firmware version, 
    if the upgrade and reboot are different. After rebooting, check the version.
    '''
    for ip in hosts:
        try:
            ssh = create_ssh_connect(ip)
            if ssh:
                data = firmware_check(ssh, ip)
                if data:
                    if data[15] != data[17]:
                        oldversion = data[15]
                        logging.info(f'{ip} firmware need upgrade')
                        if firmware_upgrade(ssh, ip):
                            time.sleep(20)
                            firmware_check_after_upgrade(ip, oldversion)
                    elif data[15] == data[17]:
                        logging.info(f'{ip} firmware is already up to date')
        except Exception as err:
            logging.error(f'{ip} firmware_upgrade_all_mikrotik() unknown error [{str(err)}]')


if __name__ == '__main__':
    version_update_all_mikrotik()
    firmware_upgrade_all_mikrotik()