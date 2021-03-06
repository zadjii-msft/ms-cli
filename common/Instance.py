import os
import imp
import _thread
import signal
import configparser
import json
from msgraph import helpers
from argparse import Namespace

from migrate.versioning import api

from common.SimpleDB import SimpleDB
from common.ResultAndData import *
from models import db_base
import time

SECRETS_FILE = "secrets.json"
CONFIG_FILE = "config.json"


def get_from_conf(config, key, default):
    return config.get("root", key) if config.has_option("root", key) else default


class Instance(object):
    def __init__(self):
        """
        Creates a Instance which can track database and authentication state
        """
        ms_cli_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self._working_dir = os.path.join(".localdata")
        self._db = None
        self._db_name = "ms-cli.db"
        self._db_models = db_base
        self._conf_file_name = "ms-cli.conf"
        self._db_map = {}

        self._appconfig = None
        self._session = None
        self._current_user_guid = None

        self.init_dir()

    def init_dir(self):
        """
        1. creates the WD if it doesn't exist
        2. Reads data from the working dir
        3. creates the db if it doesn't exist
        """

        # 1.
        exists = os.path.exists(self._working_dir)
        if not exists:
            os.makedirs(self._working_dir)
        else:
            # 2.
            self.load_conf()

        # 3.
        exists = os.path.exists(self._db_path())
        # print("The db does not exist" if not exists else "The db already exists")
        self._db = self.make_db_session()
        self._db.engine.echo = False
        if not exists:
            print("Creating db...")
            self._db.create_all_and_repo(self._db_migrate_repo())
            print(
                "The database ({}) should have been created here".format(
                    self._db_path()
                )
            )
            print("The migration repo should have been created here")

    def _parse_config(self, config=None):
        """
        config param exists so we can test this. Use the config param if it
        exists, otherwise default to the self._config.
        """
        # TODO: Load user configuration from the file
        # self._current_user_name = get_from_conf(
        #     config, "user_name", self._current_user_name
        # )
        pass

    def load_conf(self):
        conf_file = self.get_config_file_path()
        if not os.path.exists(conf_file):
            return

        config = configparser.RawConfigParser()
        with open(conf_file) as stream:
            config.readfp(stream)
            self._config = config
        self._parse_config(self._config)

    def _db_uri(self):
        return "sqlite:///" + self._db_path()

    def _db_migrate_repo(self):
        return os.path.join(self._working_dir, "db_repository")

    def get_db(self):
        thread_id = _thread.get_ident()

        if not (thread_id in list(self._db_map.keys())):
            db = self.make_db_session()
            self._db_map[thread_id] = db

        return self._db_map[thread_id]

    def make_db_session(self):
        db = SimpleDB(self._db_uri(), self._db_models)
        db.engine.echo = False
        return db

    def _db_path(self):
        return os.path.join(self._working_dir, self._db_name)

    def get_config_file_path(self):
        return os.path.join(self._working_dir, self._conf_file_name)

    def migrate(self):
        repo = self._db_migrate_repo()
        uri = self._db_uri()
        db = self.get_db()
        migration_name = "%04d_migration.py" % (api.db_version(uri, repo) + 1)
        migration = repo + "/versions/" + migration_name
        tmp_module = imp.new_module("old_model")
        old_model = api.create_model(uri, repo)
        exec(old_model, tmp_module.__dict__)
        script = api.make_update_script_for_model(
            uri, repo, tmp_module.meta, db.Base.metadata
        )
        open(migration, "wt").write(script)
        api.upgrade(uri, repo)
        print("New migration saved as " + migration)
        print("Current database version: " + str(api.db_version(uri, repo)))
        api.upgrade(uri, repo)
        print("New database version: " + str(api.db_version(uri, repo)))

    ############################################################################
    """
    Graph authentication stuff
    """

    def login_to_graph(self):
        from models.User import User

        self._appconfig = Instance._get_app_config()
        self._session = Instance._login_flow(secrets=self._appconfig)

        user_json = helpers.get_user(self._session)
        self._current_user_guid = user_json["id"]
        db = self.get_db()
        existing = (
            db.session.query(User).filter_by(guid=self._current_user_guid).first()
        )
        if existing is None:
            new_user = User.from_json(user_json)
            db.session.add(new_user)
            db.session.commit()

    @staticmethod
    def _get_app_config():
        secrets = json.load(open(SECRETS_FILE, "r", encoding="utf-8"))
        config = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

        appconfig = {}
        appconfig.update(secrets)
        appconfig.update(config)
        return appconfig

    @staticmethod
    def _login_flow(*, secrets):
        session = helpers.device_flow_session_msal(
            secrets["MS_GRAPH_CLIENT_ID"], secrets["MS_GRAPH_SCOPES"]
        )
        if not session:
            raise Exception("Couldn't connect to graph.")
        return session

    ############################################################################
    def get_current_user(self):
        from models.User import User

        if self._current_user_guid is None:
            return Error(f"no user currently logged in")
        db = self.get_db()
        user = db.session.query(User).filter_by(guid=self._current_user_guid).first()
        return ResultAndData(user is not None, user)

    def get_graph_session(self):
        return self._session
