# -*- coding: utf-8 -*-
"""
This enables to parameterize unit tests - the tests are run by Travis each time you commit to the github repo
"""

#########
#
# Help on Tests:
#
##########

# Some useful commands:
#
# pytest tests.py
# pytest -k TestDemoClass tests.py
# pytest -k "test_ok" tests.py

# Start the interactive Python debugger on errors or KeyboardInterrupt.
# pytest tests.py --pdb

# --collect-only, --co  only collect tests, don't execute them.
# pytest tests.py --co

# -v run the tests in verbose mode, outputting one line per test
# pytest -v tests.py

# A "test_" prefix in classes and contributivity_methods is needed to make a test discoverable by pytest

# Main documentation:
# https://docs.pytest.org/en/latest/contents.html

# Gettig Started
# https://docs.pytest.org/en/latest/getting-started.html#group-multiple-tests-in-a-class

# Parametrize to generate parameters combinations
# https://docs.pytest.org/en/latest/example/parametrize.html#paramexamples

# Fixture to initialize test functions
# https://docs.pytest.org/en/latest/fixture.html

# Test architecture
# https://docs.pytest.org/en/latest/goodpractices.html#test-discovery

import numpy as np
import pytest
from ruamel.yaml import YAML

from mplc import utils
from mplc.contributivity import Contributivity
from mplc.corruption import Permutation, PermutationCircular, Randomize, Redundancy, RandomizeUniform, Duplication
from mplc.dataset import Mnist, Cifar10, Titanic, Imdb, Esc50
from mplc.experiment import Experiment
from mplc.mpl_utils import UniformAggregator
from mplc.multi_partner_learning import FederatedAverageLearning
from mplc.partner import Partner
from mplc.scenario import Scenario


######
# These are outdated comments, but they
# Fixture Create: to generate the objects that are used in the test functions,
#  use the 'iterate' fixtures to generate their parameters.
# It's probably better to maintain their independence in order
# to be free to create weird objects, then give them to the test functions.
######

# create_Mpl uses create_Dataset and create_Contributivity uses create_Scenario

@pytest.fixture(scope="class", params=(Mnist, Cifar10, Titanic, Imdb, Esc50))
def create_all_datasets(request):
    return request.param()


@pytest.fixture(scope="class")
def create_MultiPartnerLearning(create_all_datasets):
    data = create_all_datasets
    # Create partners_list (this is not a fixture):
    scenario = Scenario(3, [0.3, 0.3, 0.4], dataset=data)
    mpl = FederatedAverageLearning(
        scenario,
        epoch_count=2,
        minibatch_count=2,
        dataset=data,
        aggregation=UniformAggregator,
        is_early_stopping=True,
        is_save_data=False,
    )

    yield mpl


@pytest.fixture(scope='class')
def create_Partner(create_all_datasets):
    data = create_all_datasets
    partner = Partner(0)
    partner.y_train = data.y_train[:int(len(data.y_train) / 10)]
    partner.x_train = data.x_train[:int(len(data.x_train) / 10)]
    return partner


@pytest.fixture(scope="class",
                params=((Mnist, ["basic", "random"], ['not-corrupted'] * 3),
                        (Mnist, ["basic", "random"],
                         ['permutation', Redundancy(0.2), Duplication(duplicated_partner_id=0)]),
                        (Mnist, ["advanced", [[4, "specific"], [6, "shared"], [4, "shared"]]], ['not-corrupted'] * 3),
                        (Cifar10, ["basic", "random"], ['not-corrupted'] * 3),
                        (
                                Cifar10, ["advanced", [[4, "specific"], [6, "shared"], [4, "shared"]]],
                                ['not-corrupted'] * 3)),
                ids=['Mnist - basic',
                     'Mnist - basic - corrupted',
                     'Mnist - advanced',
                     'Cifar10 - basic',
                     'Cifar10 - advanced'])
def create_Scenario(request):
    dataset = request.param[0]()
    samples_split_option = request.param[1]
    corruption = request.param[2]
    params = {"dataset": dataset}
    params.update(
        {
            "partners_count": 3,
            "amounts_per_partner": [0.3, 0.5, 0.2],
            "samples_split_option": samples_split_option,
            "corruption_parameters": corruption,
        }
    )
    params.update(
        {
            "contributivity_methods": ["Shapley values", "Independent scores"],
            "multi_partner_learning_approach": "fedavg",
            "aggregation": "uniform",
        }
    )
    params.update(
        {
            "gradient_updates_per_pass_count": 5,
            "epoch_count": 2,
            "minibatch_count": 2,
            "is_early_stopping": True,
        }
    )
    params.update({"init_model_from": "random_initialization"})
    params.update({"is_quick_demo": False})

    # scenario_.dataset object is created inside the Scenario constructor
    scenario_ = Scenario(
        **params, scenario_id=0
    )

    scenario_.mpl = scenario_._multi_partner_learning_approach(scenario_, is_save_data=True)

    return scenario_


@pytest.fixture(scope='class')
def create_experiment():
    return Experiment(experiment_name='test_exp', nb_repeats=10, is_save=True)


@pytest.fixture(scope="class")
def create_Contributivity(create_Scenario):
    scenario = create_Scenario
    contributivity = Contributivity(scenario=scenario)

    return contributivity


######
#
# Sub-function of fixture create to generate a sub-object without a call to another fixture create
#
######

######
#
# Tests modules with Objects
#
######
class Test_Experiment:
    def test_add_scenario(self, create_experiment):
        exp = create_experiment
        sc = Scenario(2, [0.5, 0.5], dataset_name='titanic')
        assert len(exp.scenarios_list) == 0, 'Scenario list should be empty when initialized'
        exp.add_scenario(sc)
        assert exp.scenarios_list[0] is sc, 'Failed to add a scenario'

    def test_raise_error_when_adding_a_string(self, create_experiment):
        exp = create_experiment
        with pytest.raises(Exception):
            exp.scenarios_list[0] = 'not a scenario'
        with pytest.raises(Exception):
            exp.scenarios_list.append('Still not a scenario')
        with pytest.raises(Exception):
            exp.add_scenario('for the last time, a string is NOT a scenario')

    def test_def_path(self, create_experiment):
        exp = create_experiment
        exp.name = 'new_name'
        path = exp.define_experiment_path()
        assert path != exp.experiment_path, 'the path should have changed'
        assert 'new_name' in str(path), 'the new name should be in path'
        assert path.exists(), f'{path} should exist'


class Test_Scenario:
    def test_scenar(self, create_Scenario):
        assert type(create_Scenario) == Scenario

    def test_raiseException(self, create_Scenario):
        scenario = create_Scenario
        with pytest.raises(Exception):
            scenario.instantiate_scenario_partners()


class Test_Corruption:
    def test_permutation_circular(self, create_Partner):
        partner = create_Partner
        partner.corruption = PermutationCircular(partner=partner)
        partner.corrupt()
        assert ((partner.y_train == 0) + (partner.y_train == 1)).all()
        if partner.y_train.ndim > 1:
            assert partner.y_train[-1].max() == 1
            assert partner.y_train[-1].sum() == 1

    def test_permutation(self, create_Partner):
        partner = create_Partner
        partner.corruption = Permutation(partner=partner)
        partner.corrupt()
        assert ((partner.y_train == 0) + (partner.y_train == 1)).all()
        ones_vect = np.ones(partner.corruption.matrix.shape[1])
        assert (partner.corruption.matrix.sum(axis=1) == ones_vect).all()
        assert (partner.corruption.matrix.sum(axis=0) == ones_vect.T).all()

    def test_random(self, create_Partner):
        partner = create_Partner
        partner.corruption = Randomize(partner=partner)
        partner.corrupt()
        assert ((partner.y_train == 0) + (partner.y_train == 1)).all()
        if partner.y_train.ndim > 1:
            assert partner.y_train[-1].max() == 1
            assert partner.y_train[-1].sum() == 1
        ones_vect = np.ones(partner.corruption.matrix.shape[1])
        assert (partner.corruption.matrix.sum(axis=1).round(1) == ones_vect).all()

    def test_random_uniform(self, create_Partner):
        partner = create_Partner
        partner.corruption = RandomizeUniform(partner=partner)
        partner.corrupt()
        assert ((partner.y_train == 0) + (partner.y_train == 1)).all()
        if partner.y_train.ndim > 1:
            assert partner.y_train[-1].max() == 1
            assert partner.y_train[-1].sum() == 1
        assert (partner.corruption.matrix == partner.corruption.matrix[0][0]).all(), 'Distribution isn\'t uniform'

    def test_redundancy(self, create_Partner):
        partner = create_Partner
        partner.corruption = Redundancy(partner=partner)
        partner.corrupt()
        assert (partner.y_train == partner.y_train[0]).all()
        assert (partner.x_train == partner.x_train[0]).all()


class Test_Mpl:
    def test_Mpl(self, create_MultiPartnerLearning):
        mpl = create_MultiPartnerLearning
        assert type(mpl) == FederatedAverageLearning


class Test_Contributivity:
    def test_Contributivity(self, create_Contributivity):
        contri = create_Contributivity
        assert type(contri) == Contributivity


######
#
# Test supported datasets
#
######

class Test_Dataset:

    def test_train_split_global(self, create_all_datasets):
        """train_val_split is used once, just after Dataset being instantiated
         - this is written to prevent its call from another place"""
        data = create_all_datasets
        assert len(data.x_val) < len(data.x_train)
        assert len(data.x_test) < len(data.x_train)
        with pytest.raises(Exception):
            data.train_val_split_global()

    def test_local_split(self, create_all_datasets):
        data = create_all_datasets
        x_train, x_val, y_train, y_val = data.train_val_split_local(data.x_train, data.y_train)
        assert len(x_train) == len(y_train)
        assert len(x_val) == len(y_val)
        x_train, x_test, y_train, y_test = data.train_val_split_local(data.x_train, data.y_train)
        assert len(x_train) == len(y_train)
        assert len(x_test) == len(y_test)

    def test_data_shape(self, create_all_datasets):
        data = create_all_datasets
        assert len(data.x_train) == len(data.y_train), "Number of train label is not equal to the number of data"
        assert len(data.x_val) == len(data.y_val), "Number of val label is not equal to the number of data"
        assert len(data.x_test) == len(data.y_test), "Number of test label is not equal to the number of data"

        if data.num_classes > 2:
            assert data.y_train[0].shape == (data.num_classes,)
            assert data.y_val[0].shape == (data.num_classes,)
            assert data.y_test[0].shape == (data.num_classes,)
        assert data.x_train[0].shape == data.input_shape
        assert data.x_test[0].shape == data.input_shape
        assert data.x_val[0].shape == data.input_shape

    def test_generate_new_model(self, create_all_datasets):
        dataset = create_all_datasets
        model = dataset.generate_new_model()
        assert callable(model.fit), ".fit() method is required for model"
        assert callable(model.evaluate), ".evaluate() method is required for model"
        assert callable(model.save_weights), ".save_weights() method is required for model"
        assert callable(model.load_weights), ".load_weights() method is required for model"
        assert callable(model.get_weights), ' .get_weights() method is required for model'
        assert callable(model.set_weights), ".set_weights() method is required for model"


#####
#
# Test Demo and config files
#
######


class _TestDemoClass:
    def test_ok(self):
        """
        Demo test
        """
        ok = "ok"
        assert "ok" in ok

    def test_ko(self):
        """
        Demo test 2
        """
        ko = "ko"
        assert "ok" not in ko

    def test_load_cfg(self):
        """
        Check if the two config files are present
        and loaded with the load_cfg method
        """
        config_file = utils.load_cfg("config.yml")
        config_quick_debug_file = utils.load_cfg("config_quick_debug.yml")
        assert config_file and config_quick_debug_file

    def test_load_config_files(self):
        """
        Check if the two config files are present
        and loaded with the load method
        """
        yaml = YAML(typ='safe')
        with open("config.yml", "r") as config_file:
            assert yaml.load(config_file)
        with open("config_quick_debug.yml", "r") as config_quick_debug_file:
            assert yaml.load(config_quick_debug_file)
