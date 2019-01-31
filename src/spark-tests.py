import unittest
import logging
from operator import add
from pyspark.sql import SparkSession

import malware_classifier


class PySparkTest(unittest.TestCase):

    @classmethod
    def suppress_py4j_logging(cls):
            logger = logging.getLogger('py4j')
            logger.setLevel(logging.WARN)

    @classmethod
    def create_testing_pyspark_session(cls):
            return (SparkSession.builder
                                .master('local[2]')
                                .appName('local-testing-pyspark-context')
                                .enableHiveSupport()
                                .getOrCreate())

    @classmethod
    def setUpClass(cls):
        cls.suppress_py4j_logging()
        cls.spark = cls.create_testing_pyspark_session()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()


class SimpleTest(PySparkTest):

    def test_tokenization_and_preproc(self):
        """
        This function will test the tokenize_and_preproc unit of the driver
        module. That unit should recieve a pairRDD of file names and file
        bodies split the body on whitespace to tokenize and filter out line
        pointer.
        """

        dat = [('filename1',
                '00401060 53 8F 48 00 A9 88 40 00 04 4E 00 00 F9 31 4F 00'),
               ('filename2',
                '00401070 1D 99 02 47 D5 4F 00 00 03 05 B5 42 CE 88 65 43')]
        test_rdd = self.spark.sparkContext.parallelize(dat, 2)
        results = malware_classifier.tokenize_and_preproc(test_rdd).collect()
        expected_results = [('filename1', '53'), ('filename1', '8F'),
                            ('filename1', '48'), ('filename1', '00'),
                            ('filename1', 'A9'), ('filename1', '88'),
                            ('filename1', '40'), ('filename1', '00'),
                            ('filename1', '04'), ('filename1', '4E'),
                            ('filename1', '00'), ('filename1', '00'),
                            ('filename1', 'F9'), ('filename1', '31'),
                            ('filename1', '4F'), ('filename1', '00'),
                            ('filename2', '1D'), ('filename2', '99'),
                            ('filename2', '02'), ('filename2', '47'),
                            ('filename2', 'D5'), ('filename2', '4F'),
                            ('filename2', '00'), ('filename2', '00'),
                            ('filename2', '03'), ('filename2', '05'),
                            ('filename2', 'B5'), ('filename2', '42'),
                            ('filename2', 'CE'), ('filename2', '88'),
                            ('filename2', '65'), ('filename2', '43')]
        self.assertEqual(set(results), set(expected_results))

    def test_prior_calculations(self):
        """
        This function tests the calculation the priors for each class by
        counting the occurances of each class type in a y_train set and
        dividing by the number of documents which exist
        """
        dat = ['6', '3', '1', '7', '9', '1', '6', '3', '3', '7', '2', '1', '6',
               '8', '2', '3', '2', '5', '3', '3', '1', '4', '3', '2', '8', '8',
               '8', '2', '4', '3', '6', '5', '2', '9', '7', '6', '5', '4', '3',
               '2', '2', '2', '5', '2', '1', '7', '3', '9', '8', '3']
        test_rdd = self.spark.sparkContext.parallelize(dat, 2)
        results = malware_classifier.calculate_priors(test_rdd).collect()
        expected_results = [('1', 0.1), ('2', 0.2), ('3', 0.22), ('4', 0.06),
                            ('5', 0.08), ('6', 0.1), ('7', 0.08), ('8', 0.1),
                            ('9', 0.06)]
        self.assertEqual(set(results), set(expected_results))

    def test_likelihood_calculations(self):
        """
        This function tests the calculations of likelihoods given a pair RDD of
        (label, word) where the likelihood is given in form
        ((label,word) likelihood) by counting word counts totally and by label
        """
        dat = [('1', '53'), ('1', '8F'), ('1', '48'),
               ('1', '00'), ('1', 'A9'), ('1', '88'),
               ('2', '40'), ('2', '00'), ('2', '04'),
               ('2', '4E'), ('2', '00'), ('2', '00'),
               ('3', 'F9'), ('3', '31'), ('3', '4F'),
               ('3', '00'), ('3', '1D'), ('3', '99'),
               ('4', '02'), ('4', '47'), ('4', 'D5'),
               ('4', '4F'), ('4', '00'), ('4', '00'),
               ('5', '03'), ('5', '05'), ('5', 'B5'),
               ('5', '42'), ('5', 'CE'), ('5', '88'),
               ('4', '8F'), ('4', '88'), ('4', '10'),
               ('4', 'CE'), ('4', '00'), ('4', 'A9'),
               ('4', 'A0'), ('4', '31'), ('4', '99'),
               ('4', '02'), ('4', 'B5'), ('4', '4E'),
               ('4', '1D'), ('4', 'D5'), ('4', '53'),
               ('4', '40'), ('4', '49'), ('4', '04'),
               ('4', '47'), ('4', '42'), ('4', '48'),
               ('4', '4F'), ('4', '03'), ('4', '05'),
               ('4', 'F9'), ('3', '8F'), ('3', '88'),
               ('3', '10'), ('3', 'CE'), ('3', '00'),
               ('3', 'A9'), ('3', 'A0'), ('3', '31'),
               ('3', '99'), ('3', '02'), ('3', 'B5'),
               ('3', '4E'), ('3', '1D'), ('3', 'D5'),
               ('3', '53'), ('3', '40'), ('3', '49'),
               ('3', '04'), ('3', '47'), ('3', '42'),
               ('3', '48'), ('3', '4F'), ('3', '03'),
               ('3', '05'), ('3', 'F9'), ('1', '8F'),
               ('1', '88'), ('1', '10'), ('1', 'CE'),
               ('1', '00'), ('1', 'A9'), ('1', 'A0'),
               ('1', '31'), ('1', '99'), ('1', '02'),
               ('1', 'B5'), ('1', '4E'), ('1', '1D'),
               ('1', 'D5'), ('1', '53'), ('1', '40'),
               ('1', '49'), ('1', '04'), ('1', '47'),
               ('1', '42'), ('1', '48'), ('1', '4F'),
               ('1', '03'), ('1', '05'), ('1', 'F9'),
               ('2', '8F'), ('2', '88'), ('2', '10'),
               ('2', 'CE'), ('5', '8F'), ('5', '88'),
               ('5', '10'), ('5', 'CE'), ('2', '00'),
               ('2', 'A9'), ('2', 'A0'), ('2', '31'),
               ('2', '99'), ('2', '02'), ('2', 'B5'),
               ('5', '00'), ('5', 'A9'), ('5', 'A0'),
               ('5', '31'), ('5', '99'), ('5', '02'),
               ('5', 'B5'), ('2', '4E'), ('2', '1D'),
               ('5', '4E'), ('5', '1D'), ('2', 'D5'),
               ('5', 'D5'), ('2', '53'), ('2', '40'),
               ('5', '53'), ('5', '40'), ('2', '49'),
               ('2', '04'), ('2', '47'), ('2', '42'),
               ('5', '49'), ('5', '04'), ('5', '47'),
               ('5', '42'), ('2', '48'), ('2', '4F'),
               ('2', '03'), ('2', '05'), ('5', '48'),
               ('5', '4F'), ('5', '03'), ('5', '05'),
               ('2', 'F9'), ('5', 'F9')]
        test_rdd = self.spark.sparkContext.parallelize(dat, 2)
        results = malware_classifier.calculate_likelihood(test_rdd).collect()
        expected_results = [('53', [0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('8F', [0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('88', [0.2857142857142857, 0.14285714285714285,
                                    0.14285714285714285, 0.14285714285714285,
                                    0.2857142857142857]),
                            ('10', [0.2, 0.2, 0.2, 0.2, 0.2]),
                            ('CE', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333]),
                            ('40', [0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('31', [0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('00', [0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666, 0.25,
                                    0.08333333333333333]),
                            ('99', [0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('A9', [0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('A0', [0.2, 0.2, 0.2, 0.2, 0.2]),
                            ('02', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666]),
                            ('B5', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333]),
                            ('49', [0.2, 0.2, 0.2, 0.2, 0.2]),
                            ('04', [0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('47', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666]),
                            ('42', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333]),
                            ('4F', [0.14285714285714285, 0.14285714285714285,
                                    0.2857142857142857, 0.2857142857142857,
                                    0.14285714285714285]),
                            ('4E', [0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('1D', [0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('48', [0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666]),
                            ('03', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333]),
                            ('05', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333]),
                            ('D5', [0.16666666666666666, 0.16666666666666666,
                                    0.16666666666666666, 0.3333333333333333,
                                    0.16666666666666666]),
                            ('F9', [0.16666666666666666, 0.16666666666666666,
                                    0.3333333333333333, 0.16666666666666666,
                                    0.16666666666666666])]

        self.assertEqual(set(results), set(expected_results))

    def test_smoothing(self):
        """
        The Function being tested should take labeled training data and
        tokenized testing data and return an RDD of the training data with a
        new entry added for each unique (label, word) pair to increase the
        count of all vocab by 1 for each label to avoid 0 probabilities
        """
        train_dat = [('1', '53'), ('1', '8F'),
                     ('1', '48'), ('1', '00'),
                     ('1', 'A9'), ('1', '88'),
                     ('2', '40'), ('2', '00'),
                     ('2', '04'), ('2', '4E'),
                     ('2', '00'), ('2', '00'),
                     ('3', 'F9'), ('3', '31'),
                     ('3', '4F'), ('3', '00'),
                     ('3', '1D'), ('3', '99'),
                     ('4', '02'), ('4', '47'),
                     ('4', 'D5'), ('4', '4F'),
                     ('4', '00'), ('4', '00'),
                     ('5', '03'), ('5', '05'),
                     ('5', 'B5'), ('5', '42'),
                     ('5', 'CE'), ('5', '88')]
        test_dat = [('filename1', '53'), ('filename1', '8F'),
                    ('filename1', '49'), ('filename1', '00'),
                    ('filename1', 'A9'), ('filename1', '88'),
                    ('filename2', '40'), ('filename2', 'A0'),
                    ('filename2', '04'), ('filename2', '4E'),
                    ('filename2', '10'), ('filename2', '00')]
        train = sc.parallelize(train_dat, 2)
        test = sc.parallelize(test_dat, 2)
        results = malware_classifier.smooth_vocab(train, test).collect()
        expected_results = [('1', '53'), ('1', '8F'), ('1', '48'),
                            ('1', '00'), ('1', 'A9'), ('1', '88'),
                            ('2', '40'), ('2', '00'), ('2', '04'),
                            ('2', '4E'), ('2', '00'), ('2', '00'),
                            ('3', 'F9'), ('3', '31'), ('3', '4F'),
                            ('3', '00'), ('3', '1D'), ('3', '99'),
                            ('4', '02'), ('4', '47'), ('4', 'D5'),
                            ('4', '4F'), ('4', '00'), ('4', '00'),
                            ('5', '03'), ('5', '05'), ('5', 'B5'),
                            ('5', '42'), ('5', 'CE'), ('5', '88'),
                            ('4', '8F'), ('4', '88'), ('4', '10'),
                            ('4', 'CE'), ('4', '00'), ('4', 'A9'),
                            ('4', 'A0'), ('4', '31'), ('4', '99'),
                            ('4', '02'), ('4', 'B5'), ('4', '4E'),
                            ('4', '1D'), ('4', 'D5'), ('4', '53'),
                            ('4', '40'), ('4', '49'), ('4', '04'),
                            ('4', '47'), ('4', '42'), ('4', '48'),
                            ('4', '4F'), ('4', '03'), ('4', '05'),
                            ('4', 'F9'), ('3', '8F'), ('3', '88'),
                            ('3', '10'), ('3', 'CE'), ('3', '00'),
                            ('3', 'A9'), ('3', 'A0'), ('3', '31'),
                            ('3', '99'), ('3', '02'), ('3', 'B5'),
                            ('3', '4E'), ('3', '1D'), ('3', 'D5'),
                            ('3', '53'), ('3', '40'), ('3', '49'),
                            ('3', '04'), ('3', '47'), ('3', '42'),
                            ('3', '48'), ('3', '4F'), ('3', '03'),
                            ('3', '05'), ('3', 'F9'), ('1', '8F'),
                            ('1', '88'), ('1', '10'), ('1', 'CE'),
                            ('1', '00'), ('1', 'A9'), ('1', 'A0'),
                            ('1', '31'), ('1', '99'), ('1', '02'),
                            ('1', 'B5'), ('1', '4E'), ('1', '1D'),
                            ('1', 'D5'), ('1', '53'), ('1', '40'),
                            ('1', '49'), ('1', '04'), ('1', '47'),
                            ('1', '42'), ('1', '48'), ('1', '4F'),
                            ('1', '03'), ('1', '05'), ('1', 'F9'),
                            ('2', '8F'), ('2', '88'), ('2', '10'),
                            ('2', 'CE'), ('5', '8F'), ('5', '88'),
                            ('5', '10'), ('5', 'CE'), ('2', '00'),
                            ('2', 'A9'), ('2', 'A0'), ('2', '31'),
                            ('2', '99'), ('2', '02'), ('2', 'B5'),
                            ('5', '00'), ('5', 'A9'), ('5', 'A0'),
                            ('5', '31'), ('5', '99'), ('5', '02'),
                            ('5', 'B5'), ('2', '4E'), ('2', '1D'),
                            ('5', '4E'), ('5', '1D'), ('2', 'D5'),
                            ('5', 'D5'), ('2', '53'), ('2', '40'),
                            ('5', '53'), ('5', '40'), ('2', '49'),
                            ('2', '04'), ('2', '47'), ('2', '42'),
                            ('5', '49'), ('5', '04'), ('5', '47'),
                            ('5', '42'), ('2', '48'), ('2', '4F'),
                            ('2', '03'), ('2', '05'), ('5', '48'),
                            ('5', '4F'), ('5', '03'), ('5', '05'),
                            ('2', 'F9'), ('5', 'F9')]
        self.assertEqual(set(results), set(expected_results))

    def test_classification(self):
        """
        The function applying the trained classifier should apply a log to
        each likelihood and to each prior passed in. Then it should join the
        likelihoods onto the test data and reduce the log likelihoods with an
        addition operator then add the priors and apply an index of max to
        determine the class. the output should be a class for each file in the
        order of the hashes in the test file
        """
        likelihoods = [('53', [0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('8F', [0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('88', [0.2857142857142857, 0.14285714285714285,
                               0.14285714285714285, 0.14285714285714285,
                               0.2857142857142857]),
                       ('10', [0.2, 0.2, 0.2, 0.2, 0.2]),
                       ('CE', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333]),
                       ('40', [0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('31', [0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666]),
                       ('00', [0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666, 0.25,
                               0.08333333333333333]),
                       ('99', [0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666]),
                       ('A9', [0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('A0', [0.2, 0.2, 0.2, 0.2, 0.2]),
                       ('02', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666]),
                       ('B5', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333]),
                       ('49', [0.2, 0.2, 0.2, 0.2, 0.2]),
                       ('04', [0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('47', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666]),
                       ('42', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333]),
                       ('4F', [0.14285714285714285, 0.14285714285714285,
                               0.2857142857142857, 0.2857142857142857,
                               0.14285714285714285]),
                       ('4E', [0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('1D', [0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666]),
                       ('48', [0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666]),
                       ('03', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333]),
                       ('05', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333]),
                       ('D5', [0.16666666666666666, 0.16666666666666666,
                               0.16666666666666666, 0.3333333333333333,
                               0.16666666666666666]),
                       ('F9', [0.16666666666666666, 0.16666666666666666,
                               0.3333333333333333, 0.16666666666666666,
                               0.16666666666666666])]
        priors = [('1', 0.2), ('2', 0.2), ('3', 0.2), ('4', 0.2), ('5', 0.2)]
        dat = [('filename1', '53'), ('filename1', '8F'),
               ('filename1', '49'), ('filename1', '00'),
               ('filename1', 'A9'), ('filename1', '88'),
               ('filename1', 'F9'), ('filename1', 'F9'),
               ('filename1', 'F9'), ('filename1', 'F9'),
               ('filename1', 'F9'), ('filename1', 'F9'),
               ('filename2', '40'), ('filename2', 'A0'),
               ('filename2', '04'), ('filename2', '4E'),
               ('filename2', '10'), ('filename2', '00'),
               ('filename2', '00'), ('filename2', '00'),
               ('filename2', '00'), ('filename2', '00'),
               ('filename2', '00'), ('filename2', '00')]
        likelihoods_rdd = sc.parallelize(likelihoods)
        priors_rdd = sc.parallelize(priors)
        dat_rdd = sc.parallelize(dat)
        results = malware_classifier.classify(likelihoods_rdd, priors_rdd,
                                              dat_rdd)
        expected_results = [('filename1', 3), ('filename2', 2)]
        self.assertEqual(set(results), set(expected_results))


if __name__ == '__main__':
    unittest.main()
