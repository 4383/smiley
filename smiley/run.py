import logging

from cliff import command


class Run(command.Command):
    """Run another program with monitoring enabled.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.add_argument(
            'command',
            nargs='+',
            help='the command to spy on',
        )
        parser.add_argument(
            '--socket',
            default='tcp://127.0.0.1:5556',
            help='URL for the socket where the listener will be (%(default)s)',
        )
        return parser

    def take_action(self, parsed_args):
        return
