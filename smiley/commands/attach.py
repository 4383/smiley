import logging
import getpass
import os
import sys

from cliff import command

from psutil import Process
from psutil import process_iter

from smiley import local
from smiley import publisher
from smiley import tracer


class ListProc(command.Command):
    """List all the Python process run by the current user.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ListProc, self).get_parser(prog_name)
        parser.add_argument(
            '--list-current-process',
            action='store_true',
            help='include the current process at the list of processes',
        )
        return parser

    def take_action(self, parsed_args):
        # Fix import path
        cwd = os.getcwd()
        if cwd not in sys.path and os.curdir not in sys.path:
            sys.path.insert(0, cwd)

        user = getpass.getuser()
        cpid = Process(os.getpid())

        results = []

        for proc in process_iter(
                ['pid', 'name', 'username', 'cmdline']):
            append = True
            if proc.info['username'] != user:
                continue
            if 'python' not in proc.info['cmdline'][0]:
                continue
            if not parsed_args.list_current_process:
                if cpid.pid == proc.info['pid']:
                    continue
                for parent in cpid.parents():
                    if parent.pid == proc.info['pid']:
                        append = False
            if append:
                results.append(proc)

        if results:
            print('PID   NAME')
            print('----------')
            for res in results:
                print('{pid} {name}'.format(
                    pid=res.info['pid'], name=res.info['name']))
        else:
            print('No Python process found')
        return


class Attach(command.Command):
    """Attach a specific Python process.

    The arguments to 'attach' are interpreted as a pid to track,
    but with tracing enabled.

    Available Python process could be retrieved by using the 'list-proc'
    command.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Attach, self).get_parser(prog_name)
        group.add_argument(
            '--local',
            action='store_const',
            dest='mode',
            const='local',
            help='write data to a local database',
        )
        group.add_argument(
            '--remote',
            action='store_const',
            dest='mode',
            const='remote',
            default='remote',
            help='send data to the remote monitor (default)',
        )
        include_group = parser.add_argument_group('covering')
        include_group.add_argument(
            '--include-stdlib',
            action='store_true',
            default=False,
            help='trace into standard library modules',
        )
        include_group.add_argument(
            '--no-include-stdlib',
            action='store_false',
            help='trace into standard library modules (default)',
        )
        include_group.add_argument(
            '--include-site-packages',
            action='store_true',
            default=True,
            help='trace into modules from site-packages (default)',
        )
        include_group.add_argument(
            '--no-include-site-packages',
            action='store_false',
            dest='include_site_packages',
            help='skip modules from site-packages',
        )
        include_group.add_argument(
            '--include-package',
            action='append',
            dest='include_packages',
            default=[],
            help='trace into a specific package',
        )
        parser.add_argument(
            '--database',
            default='smiley.db',
            help='filename for the database (%(default)s)',
        )
        parser.add_argument(
            '--socket',
            default='tcp://127.0.0.1:5556',
            help='URL for the socket where the listener will be (%(default)s)',
        )
        parser.add_argument(
            'pid',
            nargs='+',
            help='the pid to spy on',
        )
        return parser

    def take_action(self, parsed_args):
        # Fix import path
        cwd = os.getcwd()
        if cwd not in sys.path and os.curdir not in sys.path:
            sys.path.insert(0, cwd)

        # Fix command line args
        sys.argv = parsed_args.pid

        # Run the app
        if parsed_args.mode == 'remote':
            p = publisher.Publisher(parsed_args.socket)
        else:
            p = local.LocalPublisher(parsed_args.database)
        t = tracer.Tracer(
            p,
            include_stdlib=parsed_args.include_stdlib,
            include_site_packages=parsed_args.include_site_packages,
            include_packages=parsed_args.include_packages,
        )
        t.attach(parsed_args.command)
        return
