# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile
import shutil
import unittest

import h5py
import numpy

from tests.utils import helpers

from openquake.shapes import Site

from openquake.calculators.hazard.disagg import FULL_DISAGG_MATRIX
from openquake.calculators.hazard.disagg import subsets as disagg_subsets


class SubsetExtractionTestCase(unittest.TestCase):
    FULL_MATRIX_DATA = \
        'FullDisaggMatrix.dat'

    LATITUDE_BIN_LIMITS = [-0.6, -0.3, -0.1, 0.1, 0.3, 0.6]
    LONGITUDE_BIN_LIMITS = LATITUDE_BIN_LIMITS
    DISTANCE_BIN_LIMITS = [0.0, 20.0, 40.0, 60.0]
    MAGNITUDE_BIN_LIMITS = [5.0, 6.0, 7.0, 8.0, 9.0]
    EPSILON_BIN_LIMITS = [-0.5, +0.5, +1.5, +2.5, +3.5]

    NDIST = len(DISTANCE_BIN_LIMITS)
    NLAT = len(LATITUDE_BIN_LIMITS)
    NLON = len(LONGITUDE_BIN_LIMITS)
    NMAG = len(MAGNITUDE_BIN_LIMITS)
    NEPS = len(EPSILON_BIN_LIMITS)
    NTRT = 5
    FULL_MATRIX_SHAPE = (NLAT - 1, NLON - 1, NMAG - 1, NEPS - 1, NTRT)

    SITE = Site(0.0, 0.0)

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.full_matrix_path = os.path.join(cls.tempdir, 'full-matrix.hdf5')
        full_matrix = h5py.File(cls.full_matrix_path, 'w')
        ds = cls.read_data_file(cls.FULL_MATRIX_DATA, cls.FULL_MATRIX_SHAPE)
        full_matrix.create_dataset(FULL_DISAGG_MATRIX, data=ds)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    @classmethod
    def read_data_file(cls, data_filename, result_shape):
        data = open(helpers.demo_file('disaggregation/expected_results/%s'
                                      % data_filename))
        numbers = [float(line.split()[-1]) for line in data]
        return numpy.reshape(numbers, result_shape)

    def _test_pmf(self, name, result_shape):
        target_path = os.path.join(self.tempdir, '%s.hdf5' % name)
        disagg_subsets.extract_subsets(
            111, self.SITE, self.full_matrix_path,
            self.LATITUDE_BIN_LIMITS, self.LONGITUDE_BIN_LIMITS,
            self.MAGNITUDE_BIN_LIMITS, self.EPSILON_BIN_LIMITS,
            self.DISTANCE_BIN_LIMITS,
            target_path, [name]
        )
        expected_result = self.read_data_file('%s.dat' % name, result_shape)
        result = h5py.File(target_path, 'r')[name].value
        helpers.assertDeepAlmostEqual(self, expected_result, result)

    def test_magpmf(self):
        self._test_pmf('MagPMF', [self.NMAG - 1])

    def test_distpmf(self):
        self._test_pmf('DistPMF', [self.NDIST - 1])

    def test_trtpmf(self):
        self._test_pmf('TRTPMF', [self.NTRT])

    def test_magdistpmf(self):
        self._test_pmf('MagDistPMF',
                       [self.NMAG - 1, self.NDIST - 1])

    def test_magdistepspmf(self):
        self._test_pmf('MagDistEpsPMF',
                       [self.NMAG - 1, self.NDIST - 1, self.NEPS - 1])

    def test_latlonpmf(self):
        self._test_pmf('LatLonPMF', [self.NLAT - 1, self.NLON - 1])

    def test_latlonmagpmf(self):
        self._test_pmf('LatLonMagPMF',
                       [self.NLAT - 1, self.NLON - 1, self.NMAG - 1])

    def test_latlonmagepspmf(self):
        self._test_pmf('LatLonMagEpsPMF',
                       [self.NLAT - 1, self.NLON - 1,
                        self.NMAG - 1, self.NEPS - 1])

    def test_magtrtpmf(self):
        self._test_pmf('MagTRTPMF', [self.NMAG - 1, self.NTRT])

    def test_latlontrtpmf(self):
        self._test_pmf('LatLonTRTPMF',
                       [self.NLAT - 1, self.NLON - 1, self.NTRT])

    def test_full_matrix(self):
        self._test_pmf(FULL_DISAGG_MATRIX,
                       [self.NLAT - 1, self.NLON - 1, self.NMAG - 1,
                        self.NEPS - 1, self.NTRT])

    def test_multiple_matrices(self):
        target_path = os.path.join(self.tempdir, 'multiple.hdf5')
        pmfs = {
            'MagDistEpsPMF': ('MagDistEpsPMF.dat',
                              [self.NMAG - 1, self.NDIST - 1, self.NEPS - 1]),
            'LatLonPMF': ('LatLonPMF.dat',
                          [self.NLAT - 1, self.NLON - 1]),
            FULL_DISAGG_MATRIX: (self.FULL_MATRIX_DATA,
                                                 self.FULL_MATRIX_SHAPE)
        }
        disagg_subsets.extract_subsets(
            112, self.SITE, self.full_matrix_path,
            self.LATITUDE_BIN_LIMITS, self.LONGITUDE_BIN_LIMITS,
            self.MAGNITUDE_BIN_LIMITS, self.EPSILON_BIN_LIMITS,
            self.DISTANCE_BIN_LIMITS,
            target_path,
            pmfs.keys()
        )
        result = h5py.File(target_path, 'r')
        for name, (datafile, shape) in pmfs.items():
            expected_result = self.read_data_file(datafile, shape)
            helpers.assertDeepAlmostEqual(self, expected_result, result[name])

    def test_bug_932765(self):
        # Test to directly address this bug:
        # https://bugs.launchpad.net/openquake/+bug/932765

        # To make this test work, we basically have to define a list of epsilon
        # limits which has a different length from all of the others.
        eps_limits = [-0.5, +0.5, +1.5]
        subset_name = 'MagDistEpsPMF'
        file_name = '%s.dat' % subset_name

        target_path = os.path.join(self.tempdir,
                                   '%s_932765.hdf5' % subset_name)

        # load in the test data
        data = self.read_data_file(
            file_name, [self.NMAG - 1, self.NDIST - 1, self.NEPS - 1])
        # chop the test data to match what we expected with the shortened
        # epsilon limits we've defined (see above)
        expected_data = data[:, :, 0:2]

        disagg_subsets.extract_subsets(
            666, self.SITE, self.full_matrix_path,
            self.LATITUDE_BIN_LIMITS, self.LONGITUDE_BIN_LIMITS,
            self.MAGNITUDE_BIN_LIMITS, eps_limits,
            self.DISTANCE_BIN_LIMITS,
            target_path,
            [subset_name]
        )
        actual = h5py.File(target_path, 'r')[subset_name].value

        helpers.assertDeepAlmostEqual(self, expected_data, actual)
