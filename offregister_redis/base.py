from fabric.api import run
from fabric.context_managers import shell_env, cd
from fabric.operations import sudo
from offregister_fab_utils.fs import cmd_avail


def dl_install_redis_server(listen_port=6379,
                            version='4.0.1',
                            skip_if_avail=True):
    if skip_if_avail and cmd_avail('redis-server'):
        return
    pkg = 'redis-{version}.tar.gz'.format(version=version)
    tmp_dir = run('mktemp -d', quiet=True)
    with cd(tmp_dir):
        run('wget http://download.redis.io/releases/{pkg}'.format(pkg=pkg))
        run('tar xf {pkg}'.format(pkg=pkg))
        with cd('redis-{version}'.format(version=version)):
            run('make')
            sudo('make install')

            with shell_env(REDIS_PORT=str(listen_port),
                           REDIS_CONFIG_FILE='/etc/redis/{}.conf'.format(listen_port),
                           REDIS_LOG_FILE='/var/log/redis_{}.log'.format(listen_port),
                           REDIS_DATA_DIR='/var/lib/redis/{}'.format(listen_port),
                           REDIS_EXECUTABLE=run('command -v redis-server', quiet=True)):
                return sudo('sh utils/install_server.sh')
