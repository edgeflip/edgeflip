import sys
from decimal import Decimal
from StringIO import StringIO

from mock import patch
from nose import tools

from gerry import models
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
        with STDIN_PATCH:
            self.execute(command, include_nicknames=False)

        tools.eq_(command.stdout.read(), "Header is:\n\t{}\n".format(HEADER))
        tools.eq_(command.stderr.read(), "")

        tools.eq_(sorted(fulldocs(models.StateNameVoter.items.all())), [
            {'state_lname_fname': 'NH_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_lname_fname': 'MN_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.1')},
        ])

        tools.eq_(sorted(fulldocs(models.StateCityNameVoter.items.all())), [
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_MILTON_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_city_lname_fname': 'MN_ST-PAUL_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.88')},
            {'state_city_lname_fname': 'MN_BLAINE_STANTON_JANE',
             'gotv_score': Decimal('0.005'),
             'persuasion_score': Decimal('4.1')},
        ])

    def test_stdin_nicks(self):
        command = loadscores.Command()
        with STDIN_PATCH, patch.object(loadscores, 'readlines') as mock_readlines:
            # Fake readlines to produce nicknames:
            mock_readlines.return_value = NICKNAMES.splitlines()
            self.execute(command, nicknames_path='/like/a/file/path')

        tools.eq_(command.stdout.read(), "Header is:\n\t{}\n".format(HEADER))
        tools.eq_(command.stderr.read(), "")

        tools.eq_(sorted(fulldocs(models.StateNameVoter.items.all())), [
            {'state_lname_fname': 'NH_BULLWINKLE_BORBOR',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BULLWINKLE_BORY',
             'gotv_score': Decimal('-0.009')},
            {'state_lname_fname': 'NH_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
            {'state_lname_fname': 'MN_STANTON_JANE',
             'gotv_score': Decimal('0.003'),
             'persuasion_score': Decimal('4.1')},
        ])

        tools.eq_(sorted(fulldocs(models.StateCityNameVoter.items.all())), [
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORBOR',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORIS',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_SEABROOK_BULLWINKLE_BORY',
             'gotv_score': Decimal('-0.009')},
            {'state_city_lname_fname': 'NH_MILTON_BEARINGTON_JOHN',
             'gotv_score': Decimal('-0.007'),
             'persuasion_score': Decimal('4.61')},
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
179637090,830822,f,t,t,6035888074,31686744,,JANE,J,STANTON,,999 Fake Rd,Blaine,MN,55449,,,,,,,4.1,0.005
187853015,857415,f,t,t,6036520982,102879307,,JOHN,J,BEARINGTON,,579 Everest Hwy,Milton,NH,03851,,PO Box 666,Milton,NH,03851,1166,4.61,-0.007
179147722,729176,f,t,t,6034743336,79527242,,BORIS,ALEXI,BULLWINKLE,,37 Tall Mill Ter,Seabrook,NH,03874,4037,PO Box 901,Seabrook,NH,03874,2946,,-0.009
178424405,382069,f,t,t,6036439293,81705921,,JUDY,A,NESS,,9 S Oak St Apt A,Lebanon,NH,03766,1336,PO Box 908,Lebanon,NH,03766,0421,,
'''

HEADER = INPUT.splitlines()[0]

NICKNAMES = '''\
name,nickname,gender
BORIS,BORBOR,M
BORIS,BORY,M
'''

STDIN_PATCH = patch.object(sys, 'stdin', StringIO(INPUT))
