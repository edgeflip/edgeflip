# -*- coding: utf-8 -*-
from decimal import Decimal
from StringIO import StringIO

from mock import patch
from nose import tools

from gerry.models import StateNameVoter, StateCityNameVoter
from gerry.management.commands import loadscores

from . import GerryTestCase


def fulldocs(items):
    """Generate dicts of items' non-meta data plus primary keys
    (excluding timestamp).

    """
    for item in items:
        yield dict(item.document, **item.get_keys())


class TestExecution(GerryTestCase):

    DEFAULTS = {'verbosity': '1',
                'include_nicknames': True}

    def execute(self, command, *args, **options):
        options.update(stdout=StringIO(), stderr=StringIO())
        fulloptions = dict(self.DEFAULTS, **options)
        command.execute(*args, **fulloptions)
        command.stdout.seek(0)
        command.stderr.seek(0)

    def test_stdin_nonicks(self):
        command = loadscores.Command()
        command.stdin = StringIO(INPUT)
        self.execute(command, include_nicknames=False)

        tools.eq_(command.stdout.read(), "Header is:\n\t{}\n".format(HEADER))
        tools.eq_(command.stderr.read(), "")

        tools.assert_sequence_equal(sorted(fulldocs(StateNameVoter.items.all())), [
            {'state_lname_fname': 'NH_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BEARINGTON_JAMES',
             'gotv_score': Decimal('-0.1'),
             'persuasion_score': Decimal('4.8')},
            {'state_lname_fname': 'NH_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_lname_fname': 'NH_ZIP_JOE',
             'persuasion_score': Decimal('0'),
             'gotv_score': Decimal('0')},
            {'state_lname_fname': 'MN_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.1')},
            {'state_lname_fname': 'NH_ZIP_JOSEPH',
             'persuasion_score': Decimal('3.1'),
             'gotv_score': Decimal('0.2')},
        ])

        tools.assert_sequence_equal(sorted(fulldocs(StateCityNameVoter.items.all())), [
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_ST-PAUL_BEARINGTON_JAMES',
             'gotv_score': Decimal('-0.1'),
             'persuasion_score': Decimal('4.8')},
            {'state_city_lname_fname': 'NH_MILTON_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_city_lname_fname': 'NH_LEBANON_ZIP_JOE',
             'persuasion_score': Decimal('0'),
             'gotv_score': Decimal('0')},
            {'state_city_lname_fname': 'MN_ST-PAUL_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.88')},
            {'state_city_lname_fname': 'MN_BLAINE_STANTON_JANE',
             'gotv_score': Decimal('0.005'),
             'persuasion_score': Decimal('4.1')},
            {'state_city_lname_fname': 'NH_LEBANON_ZIP_JOSEPH',
             'persuasion_score': Decimal('3.1'),
             'gotv_score': Decimal('0.2')},
        ])

    def test_stdin_nicks(self):
        command = loadscores.Command()
        command.stdin = StringIO(INPUT)
        with patch.object(loadscores, 'readlines') as mock_readlines:
            # Fake readlines to produce nicknames:
            mock_readlines.return_value = NICKNAMES.splitlines()
            self.execute(command, nicknames_path='/like/a/file/path')

        tools.eq_(command.stdout.read(), "Header is:\n\t{}\n".format(HEADER))
        tools.eq_(command.stderr.read(), "")

        tools.assert_sequence_equal(sorted(fulldocs(StateNameVoter.items.all())), [
            {'state_lname_fname': 'NH_BULLWINKLE_BORBOR',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BULLWINKLE_BORY',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BEARINGTON_JAY',
             'gotv_score': Decimal('-0.1'),
             'persuasion_score': Decimal('4.61')},
            {'state_lname_fname': 'NH_BEARINGTON_JAMES',
             'gotv_score': Decimal('-0.1'),
             'persuasion_score': Decimal('4.8')},
            {'state_lname_fname': 'NH_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_lname_fname': 'NH_ZIP_JOE',
             'persuasion_score': Decimal('0'),
             'gotv_score': Decimal('0')},
            {'state_lname_fname': 'NH_ZIP_JOSEPH',
             'persuasion_score': Decimal('0'),
             'gotv_score': Decimal('0')},
            {'state_lname_fname': 'MN_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.1')},
        ])

        tools.assert_sequence_equal(sorted(fulldocs(StateCityNameVoter.items.all())), [
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORBOR',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORY',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_ST-PAUL_BEARINGTON_JAMES',
             'gotv_score': Decimal('-0.1'),
             'persuasion_score': Decimal('4.8')},
            {'state_city_lname_fname': 'NH_ST-PAUL_BEARINGTON_JAY',
             'gotv_score': Decimal('-0.1'),
             'persuasion_score': Decimal('4.8')},
            {'state_city_lname_fname': 'NH_MILTON_BEARINGTON_JAY',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_city_lname_fname': 'NH_MILTON_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_city_lname_fname': 'NH_LEBANON_ZIP_JOE',
             'persuasion_score': Decimal('0'),
             'gotv_score': Decimal('0')},
            {'state_city_lname_fname': 'NH_LEBANON_ZIP_JOSEPH',
             'persuasion_score': Decimal('0'),
             'gotv_score': Decimal('0')},
            {'state_city_lname_fname': 'MN_ST-PAUL_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.88')},
            {'state_city_lname_fname': 'MN_BLAINE_STANTON_JANE',
             'gotv_score': Decimal('0.005'),
             'persuasion_score': Decimal('4.1')},
        ])


INPUT = '''\
personid,votebuilder_identifier,is_deceased,is_current_reg,reg_voter_flag,primary_phone_number,addressid,prefix,firstname,middlename,lastname,suffix,regaddress,regcity,regstate,regzip5,regzip4,mailingaddress,mailingcity,mailstate,mailingzip5,mailingzip4,persuasion_score_dnc,gotv_2014
179637089,830821,f,t,t,6035888073,31686743,,JANE,,STANTON,,146 State Rd,St Paul,MN,55904,,,,,,,4.88,0.003
179637090,830822,f,t,t,6035888070,31686744,,JANE,J,STANTON,,999 Fake Rd,Blaine,MN,55449,,,,,,,4.1,0.005
187853015,857415,f,t,t,6036520982,102879307,,JOHN,J,BEARINGTON,,579 Everest Hwy,Milton,NH,03851,,PO Box 666,Milton,NH,03851,1166,4.61,-0.007
187853018,857418,f,t,t,6036520980,102879300,,JAMES,,BEARINGTON,,579 Fake Rd,St Paul,NH,55904,,,,,,,4.8,-0.1
179147722,729176,f,t,t,6034743336,79527242,,BÖRIS,ALÉXI,BULLWINKLE,,37 Tall Mill Ter,Seabrook,NH,03874,4037,PO Box 901,Seabrook,NH,03874,2946,,-0.009
178424405,382069,f,t,t,6036439293,81705921,,JUDY,A,NESS,,9 S Oak St Apt A,Lebanon,NH,03766,1336,PO Box 908,Lebanon,NH,03766,0421,,
178424415,382009,f,t,t,6036439294,81705922,,JOE,,ZIP,,99 N Elm St Apt A,Lebanon,NH,03766,1336,,,,,,0,0
178424416,382000,f,t,t,6036439295,81705920,,JOSEPH,J,ZIP,,1 S Elm St Apt G,Lebanon,NH,03766,1336,,,,,,3.1,0.2
'''

HEADER = INPUT.splitlines()[0]

NICKNAMES = '''\
name,nickname,gender
BORIS,BORBOR,M
BORIS,BORY,M
JAMES,JAY,M
JOHN,JAY,M
JOSEPH,JOE
JOE,JOSEPH
'''
