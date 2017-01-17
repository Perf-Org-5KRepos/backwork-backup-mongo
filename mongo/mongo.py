import argparse
import time
import logging
import os
import subprocess

from monsoon import BackupBase

log = logging.getLogger(__name__)

class MongoBackup(object):
    """Backup a MongoDB database.

    It uses `mongodump` so it's required to have it installed and added to the
    system's PATH. You can use any of the arguments supported by `mongodump`.
    Use `mongodump -h` for more information.
    """
    command = "mongo"

    def __init__(self, args, extra):
        self.args = args
        self.extra = extra

    @classmethod
    def parse_args(cls, subparsers):
        """Create the `mongo` subparser for the `backup` command."""
        mongo_parser = subparsers.add_parser(cls.command, description=cls.__doc__)

    def backup(self):
        """Backup a MongoDB database.

        If no output argument is specified (-o, --output, --archive) it will
        run `mongodump` with `--archive` and `--gzip` and store it into
        `./dumps` with a timestamped name.
        """
        log.info("starting mongo backup...")

        # parse extra arguments to check output options
        output_config_parser = argparse.ArgumentParser()
        output_config_parser.add_argument("-o", "--output")
        output_config_parser.add_argument("--archive")
        output_args, _ = output_config_parser.parse_known_args(self.extra)

        if not any([output_args.output, output_args.archive]):
            # generate sensible defaults for output file: timestamped gziped archived file
            filename = "mongo_backup_{}.archive.gz".format(time.strftime("%Y%m%d-%H%M%S"))
            path = os.path.join(os.getcwd(), "dumps", filename)
            dirname = os.path.dirname(path)

            if not os.path.exists(dirname):
                os.mkdir(dirname)

            self.extra.append("--archive={}".format(path))
            if "--gzip" not in self.extra:
                self.extra.append("--gzip")

            log.info("saving file to %s", path)

        cmd = ["mongodump"] + self.extra

        try:
            self.result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            log.info("output:\n\n\t%s", "\n\t".join(self.result.split("\n")))
            log.info("backup complete")

        except subprocess.CalledProcessError as e:
            self.result = e.output
            log.error("failed to back up mongo database")
            log.error("return code was %s", e.returncode)
            log.error("output:\n\n\t%s", "\n\t".join(self.result.split("\n")))
            log.error("backup process failed")
            raise e